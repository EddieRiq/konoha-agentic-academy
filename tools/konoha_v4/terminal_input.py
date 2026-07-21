from __future__ import annotations

import os
import select
import sys
import time
from typing import TextIO


class TerminalTurnReader:
    """Single-owner, line-framed terminal input reader."""

    def __init__(
        self,
        stream: TextIO | None = None,
        output: TextIO | None = None,
        *,
        freshness_quiet_seconds: float = 0.30,
    ) -> None:
        self.stream = stream or sys.stdin
        self.output = output or sys.stdout
        self.freshness_quiet_seconds = freshness_quiet_seconds
        self.encoding = getattr(self.stream, "encoding", None) or "utf-8"
        self._buffer = bytearray()
        self._eof = False
        try:
            self._fd: int | None = self.stream.fileno()
        except (AttributeError, OSError, ValueError):
            self._fd = None

    def _prompt(self, prompt: str) -> None:
        self.output.write(prompt)
        self.output.flush()

    def _extract_line(self) -> str | None:
        newline = self._buffer.find(b"\n")
        if newline < 0:
            return None
        raw = bytes(self._buffer[:newline])
        del self._buffer[: newline + 1]
        if raw.endswith(b"\r"):
            raw = raw[:-1]
        return raw.decode(self.encoding, errors="replace")

    def _read_chunk(self) -> bool:
        if self._fd is None:
            return False
        chunk = os.read(self._fd, 65536)
        if not chunk:
            self._eof = True
            return False
        self._buffer.extend(chunk)
        return True

    def _read_line_blocking(self) -> str | None:
        if self._fd is None:
            line = self.stream.readline()
            if line == "":
                return None
            return line.rstrip("\r\n")

        while True:
            line = self._extract_line()
            if line is not None:
                return line
            if self._eof:
                if not self._buffer:
                    return None
                raw = bytes(self._buffer)
                self._buffer.clear()
                return raw.decode(self.encoding, errors="replace")
            self._read_chunk()

    def _read_ready_chunk(self, timeout: float) -> bool:
        if self._fd is None or self._eof:
            return False
        ready, _, _ = select.select([self._fd], [], [], max(timeout, 0.0))
        if not ready:
            return False
        return self._read_chunk()

    def read_line(self, prompt: str = "Vos> ") -> str | None:
        self._prompt(prompt)
        line = self._read_line_blocking()
        return None if line is None else line.strip()

    def read_turn(self, prompt: str = "Vos> ") -> str | None:
        return self.read_line(prompt)

    def read_block_until(
        self,
        *,
        prompt: str,
        continuation_prompt: str,
        first_line: str | None = None,
        terminator: str = ":fin",
        cancel_token: str = ":cancelar",
    ) -> tuple[str | None, bool]:
        lines: list[str] = []
        if first_line is not None:
            lines.append(first_line)

        current_prompt = prompt
        terminator_cf = terminator.casefold()
        cancel_cf = cancel_token.casefold()

        while True:
            self._prompt(current_prompt)
            line = self._read_line_blocking()
            if line is None:
                return None, True

            command = line.strip().casefold()
            if command == cancel_cf:
                return None, True
            if command == terminator_cf:
                feedback = "\n".join(lines).strip()
                return (feedback or None), False

            lines.append(line)
            current_prompt = continuation_prompt

    def drain_until_quiet(self) -> list[str]:
        discarded: list[str] = []
        if self._fd is None:
            return discarded

        deadline = time.monotonic() + self.freshness_quiet_seconds
        while True:
            consumed = False
            while True:
                line = self._extract_line()
                if line is None:
                    break
                discarded.append(line)
                consumed = True

            if consumed:
                deadline = time.monotonic() + self.freshness_quiet_seconds
                continue

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            if self._read_ready_chunk(remaining):
                deadline = time.monotonic() + self.freshness_quiet_seconds
                continue
            break

        if self._buffer:
            discarded.append(
                bytes(self._buffer).decode(self.encoding, errors="replace")
            )
            self._buffer.clear()
        return discarded

    def read_fresh_line(
        self,
        prompt: str,
    ) -> tuple[str | None, list[str]]:
        discarded = self.drain_until_quiet()
        return self.read_line(prompt), discarded
