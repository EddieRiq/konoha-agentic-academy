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


class TerminalTurnReaderLineFramingTests(unittest.TestCase):
    def make_reader(self, *, freshness_quiet: float = 0.08):
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
        self.addCleanup(os.close, master_fd)
        self.addCleanup(os.close, slave_fd)
        return reader, master_fd, output

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


if __name__ == "__main__":
    unittest.main()
