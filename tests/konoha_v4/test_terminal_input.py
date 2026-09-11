from __future__ import annotations

import io
import os
import pty
import termios
import threading
import time
import unittest

from tools.konoha_v4.terminal_input import TerminalTurnReader

# Larger than the OLD freshness_quiet_seconds default (0.30s) and the OLD
# test fixture's threshold (0.08s) - used to prove chunk delivery delay no
# longer matters at all, not just that it's within some window.
OLD_QUIET_THRESHOLD_EXCEEDED = 0.5


class _FDStream:
    encoding = "utf-8"

    def __init__(self, fd: int) -> None:
        self._fd = fd

    def fileno(self) -> int:
        return self._fd


def _make_reader(test_case: unittest.TestCase):
    """Shared PTY-backed TerminalTurnReader fixture. Registers cleanup for
    both fds - callers that need to close master_fd early (e.g. to force
    EOF) must NOT also rely on this helper's cleanup for that same fd."""
    master_fd, slave_fd = pty.openpty()
    attrs = termios.tcgetattr(slave_fd)
    attrs[3] &= ~termios.ECHO
    termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)

    output = io.StringIO()
    reader = TerminalTurnReader(_FDStream(slave_fd), output)
    test_case.addCleanup(os.close, master_fd)
    test_case.addCleanup(os.close, slave_fd)
    return reader, master_fd, output


class TerminalTurnReaderLineFramingTests(unittest.TestCase):
    def make_reader(self):
        return _make_reader(self)

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

    def test_normal_decision_line(self) -> None:
        reader, master_fd, output = self.make_reader()
        os.write(master_fd, b"no\n")
        self.assertEqual(reader.read_line("Decision> "), "no")
        self.assertEqual(output.getvalue(), "Decision> ")

    def test_read_exact_line_preserves_edge_whitespace(self) -> None:
        # BLOCK_4 human-content-preservation contract: read_exact_line must
        # not strip leading/trailing whitespace the way read_line does -
        # only CRLF is normalized away.
        reader, master_fd, _ = self.make_reader()
        os.write(master_fd, b"  indented content  \r\n")
        self.assertEqual(
            reader.read_exact_line(), "  indented content  ",
        )

    def test_block_lines_preserve_interior_content_only_outer_edges_trimmed(
        self,
    ) -> None:
        # The existing, intentional, already-established contract for
        # requested-change capture (outer .strip() on the joined block,
        # interior lines untouched) - now shared by mission capture too.
        # Explicitly proven here rather than merely assumed.
        reader, master_fd, _ = self.make_reader()
        os.write(
            master_fd,
            b"  leading space kept mid-line\n\tsecond line\ttab kept\n:fin\n",
        )
        first = reader.read_exact_line()
        feedback, cancelled = reader.read_block_until(
            prompt="...> ",
            continuation_prompt="...> ",
            first_line=first,
        )
        self.assertFalse(cancelled)
        self.assertEqual(
            feedback,
            "leading space kept mid-line\n\tsecond line\ttab kept",
        )

    def test_text_immediately_after_fin_is_the_next_logical_read(
        self,
    ) -> None:
        # Deterministic-by-construction: whatever the human wrote after
        # their own ':fin' is simply the next line in the stream - not
        # something silently discarded, and not something that arrives
        # only because of timing. This is the primitive-level building
        # block that conversation.py's fresh-challenge protocol (never a
        # bare "sí") builds real authority integrity on top of.
        reader, master_fd, _ = self.make_reader()
        os.write(master_fd, b"first\nsecond\n:fin\nsi\n")

        first = reader.read_line()
        feedback, cancelled = reader.read_block_until(
            prompt="...> ",
            continuation_prompt="...> ",
            first_line=first,
        )
        self.assertFalse(cancelled)
        self.assertEqual(feedback, "first\nsecond")

        self.assertEqual(reader.read_line("Confirm? "), "si")


class TerminalTurnReaderDeterministicMissionFramingTests(unittest.TestCase):
    """BLOCK_4 FINDING #21 root-cause regression: a multiline paste must be
    captured as one complete logical turn no matter how many OS/PTY chunks
    it arrives in or how much delay separates them - proven with a real
    inter-chunk delay exceeding the OLD (now-removed) quiet-window
    threshold, not merely a single os.write() burst."""

    def make_reader(self):
        return _make_reader(self)

    def test_delayed_multi_chunk_mission_is_one_complete_turn(self) -> None:
        reader, master_fd, _ = self.make_reader()

        def delayed_writer() -> None:
            os.write(master_fd, b"Revisa el repositorio.\n")
            os.write(master_fd, b"si\n")
            time.sleep(OLD_QUIET_THRESHOLD_EXCEEDED)
            os.write(master_fd, b"No modifiques archivos.\n")
            os.write(master_fd, b":fin\n")

        thread = threading.Thread(target=delayed_writer)
        thread.start()
        try:
            first = reader.read_exact_line("Vos> ")
            mission, cancelled = reader.read_block_until(
                prompt="...> ",
                continuation_prompt="...> ",
                first_line=first,
            )
        finally:
            thread.join()

        self.assertFalse(cancelled)
        self.assertEqual(
            mission,
            "Revisa el repositorio.\nsi\nNo modifiques archivos.",
        )

    def test_cross_turn_isolation_after_delayed_mission(self) -> None:
        # Nothing from the delayed mission paste above leaks into a
        # completely separate, later read - proven with genuinely new
        # bytes written only after the mission block already returned.
        reader, master_fd, _ = self.make_reader()

        def delayed_writer() -> None:
            os.write(master_fd, b"Mission line one.\n")
            time.sleep(OLD_QUIET_THRESHOLD_EXCEEDED)
            os.write(master_fd, b"Mission line two.\n:fin\n")

        thread = threading.Thread(target=delayed_writer)
        thread.start()
        try:
            first = reader.read_exact_line("Vos> ")
            mission, cancelled = reader.read_block_until(
                prompt="...> ",
                continuation_prompt="...> ",
                first_line=first,
            )
        finally:
            thread.join()

        self.assertFalse(cancelled)
        self.assertEqual(mission, "Mission line one.\nMission line two.")

        os.write(master_fd, b"no\n")
        decision = reader.read_line()
        self.assertEqual(decision, "no")

    def test_ordinary_single_line_then_fin(self) -> None:
        reader, master_fd, _ = self.make_reader()
        os.write(master_fd, b"Revisar el estado del repo.\n:fin\n")
        first = reader.read_exact_line("Vos> ")
        mission, cancelled = reader.read_block_until(
            prompt="...> ",
            continuation_prompt="...> ",
            first_line=first,
        )
        self.assertFalse(cancelled)
        self.assertEqual(mission, "Revisar el estado del repo.")

    def test_eof_before_fin_fails_closed(self) -> None:
        # master_fd is closed by this test itself (to force EOF on the
        # slave side) rather than via _make_reader's cleanup, to avoid a
        # double-close.
        master_fd, slave_fd = pty.openpty()
        attrs = termios.tcgetattr(slave_fd)
        attrs[3] &= ~termios.ECHO
        termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)
        self.addCleanup(os.close, slave_fd)

        reader = TerminalTurnReader(_FDStream(slave_fd), io.StringIO())
        os.write(master_fd, b"Mision incompleta sin terminador.\n")
        first = reader.read_exact_line("Vos> ")

        def close_master() -> None:
            time.sleep(0.05)
            os.close(master_fd)

        thread = threading.Thread(target=close_master)
        thread.start()
        try:
            mission, cancelled = reader.read_block_until(
                prompt="...> ",
                continuation_prompt="...> ",
                first_line=first,
            )
        finally:
            thread.join()
        self.assertTrue(cancelled)
        self.assertIsNone(mission)

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

        reader = TerminalTurnReader(_FDStream(slave_fd), io.StringIO())
        os.close(master_fd)

        self.assertIsNone(reader.read_exact_line())


if __name__ == "__main__":
    unittest.main()
