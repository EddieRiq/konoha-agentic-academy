from __future__ import annotations

import io
import os
import pty
import termios
import threading
import time
import unittest

from tools.konoha_v4.terminal_input import TerminalTurnReader


class _FDStream:
    encoding = "utf-8"

    def __init__(self, fd: int) -> None:
        self._fd = fd

    def fileno(self) -> int:
        return self._fd


def _make_reader(test_case: unittest.TestCase, *, freshness_quiet: float = 0.08):
    """Shared PTY-backed TerminalTurnReader fixture. Registers cleanup for
    both fds - callers that need to close master_fd early (e.g. to force
    EOF) must NOT also rely on this helper's cleanup for that same fd."""
    master_fd, slave_fd = pty.openpty()
    attrs = termios.tcgetattr(slave_fd)
    attrs[3] &= ~termios.ECHO
    termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)

    output = io.StringIO()
    reader = TerminalTurnReader(
        _FDStream(slave_fd),
        output,
        freshness_quiet_seconds=freshness_quiet,
    )
    test_case.addCleanup(os.close, master_fd)
    test_case.addCleanup(os.close, slave_fd)
    return reader, master_fd, output


class TerminalTurnReaderLineFramingTests(unittest.TestCase):
    def make_reader(self, *, freshness_quiet: float = 0.08):
        return _make_reader(self, freshness_quiet=freshness_quiet)

    def test_pasted_lines_are_consumed_until_fin(self) -> None:
        reader, master_fd, _ = self.make_reader()
        os.write(
            master_fd,
            b"Primera regla.\nSegunda regla.\n:fin\n",
        )

        first = reader.read_line("Vos> ")
        feedback, cancelled = reader.read_block_until(
            prompt="...> ",
            continuation_prompt="...> ",
            first_line=first,
        )

        self.assertFalse(cancelled)
        self.assertEqual(
            feedback,
            "Primera regla.\nSegunda regla.",
        )

    def test_cancel_token_stops_block(self) -> None:
        reader, master_fd, _ = self.make_reader()
        os.write(master_fd, b"first\n:cancelar\n")
        first = reader.read_line()
        feedback, cancelled = reader.read_block_until(
            prompt="...> ",
            continuation_prompt="...> ",
            first_line=first,
        )
        self.assertTrue(cancelled)
        self.assertIsNone(feedback)

    def test_text_after_fin_is_drained_before_confirmation(self) -> None:
        reader, master_fd, _ = self.make_reader(
            freshness_quiet=0.08
        )
        os.write(master_fd, b"first\nsecond\n:fin\nsi\n")

        first = reader.read_line()
        feedback, cancelled = reader.read_block_until(
            prompt="...> ",
            continuation_prompt="...> ",
            first_line=first,
        )
        self.assertFalse(cancelled)
        self.assertEqual(feedback, "first\nsecond")

        def fresh_writer() -> None:
            time.sleep(0.16)
            os.write(master_fd, b"no\n")

        thread = threading.Thread(target=fresh_writer)
        thread.start()
        try:
            decision, discarded = reader.read_fresh_line(
                "Confirm? "
            )
        finally:
            thread.join()

        self.assertEqual(discarded, ["si"])
        self.assertEqual(decision, "no")

    def test_normal_decision_line(self) -> None:
        reader, master_fd, output = self.make_reader()
        os.write(master_fd, b"no\n")
        self.assertEqual(reader.read_line("Decision> "), "no")
        self.assertEqual(output.getvalue(), "Decision> ")


class TerminalTurnReaderReadTurnFramingTests(unittest.TestCase):
    """BLOCK_4 FINDING #21: read_turn() must fold an entire pasted/burst
    multiline mission into one turn, and leave nothing from that paste
    buffered for the next read_line()/approval read - proven behaviorally,
    never by inspecting private _buffer state directly."""

    def make_reader(self, *, freshness_quiet: float = 0.08):
        return _make_reader(self, freshness_quiet=freshness_quiet)

    def test_multiline_paste_is_one_turn_with_no_residual(self) -> None:
        reader, master_fd, _ = self.make_reader()
        os.write(
            master_fd,
            "Revisá el repositorio.\nsí\nNo modifiques archivos.\n".encode("utf-8"),
        )

        # Test A: the exact reproduced bug - one pasted burst must come
        # back as a single joined turn, not just its first line.
        mission = reader.read_turn()
        self.assertEqual(
            mission,
            "Revisá el repositorio.\nsí\nNo modifiques archivos.",
        )

        # Test B: nothing from that paste (in particular the "sí" line,
        # which used to look like a stray approval answer) remains
        # buffered - a fresh read_line() must only see genuinely new input.
        os.write(master_fd, b"no\n")
        decision = reader.read_line()
        self.assertEqual(decision, "no")

    def test_ordinary_single_line_turn(self) -> None:
        # Test C
        reader, master_fd, _ = self.make_reader()
        os.write(master_fd, b"Revisar el estado del repo.\n")
        mission = reader.read_turn()
        self.assertEqual(mission, "Revisar el estado del repo.")

    def test_turn_returns_none_on_immediate_eof(self) -> None:
        # EOF before any first line must still return None. master_fd is
        # closed early here to force EOF on the slave side, so it is NOT
        # registered via addCleanup - only slave_fd is, avoiding a
        # double-close of master_fd.
        master_fd, slave_fd = pty.openpty()
        attrs = termios.tcgetattr(slave_fd)
        attrs[3] &= ~termios.ECHO
        termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)
        self.addCleanup(os.close, slave_fd)

        reader = TerminalTurnReader(
            _FDStream(slave_fd),
            io.StringIO(),
            freshness_quiet_seconds=0.08,
        )
        os.close(master_fd)

        self.assertIsNone(reader.read_turn())


if __name__ == "__main__":
    unittest.main()
