from __future__ import annotations

import errno
import os
import sys
from typing import TextIO


class TerminalTurnReader:
    """Single-owner, line-framed terminal input reader.

    Every human turn has a deterministic end boundary: a single
    newline-terminated line (read_line/read_exact_line), or an explicit
    exact-line terminator (read_block_until: ":fin"/":cancelar"/EOF). No
    read here ever depends on silence duration, PTY chunk boundaries, or
    any other timing signal - a blocking read simply keeps blocking,
    however many OS chunks and however much delay it takes, until its own
    deterministic boundary is reached.

    Freshness for authority-granting decisions (a plan approval, a
    requested-change confirmation) is established at the protocol layer in
    conversation.py, via an explicit post-boundary challenge generated only
    after the relevant prior boundary was already consumed - never inside
    this reader, and never by inferring anything from timing or buffer
    availability.
    """

    def __init__(
        self,
        stream: TextIO | None = None,
        output: TextIO | None = None,
    ) -> None:
        self.stream = stream or sys.stdin
        self.output = output or sys.stdout
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
        try:
            chunk = os.read(self._fd, 65536)
        except OSError as exc:
            if exc.errno != errno.EIO:
                # Only a PTY peer disconnecting mid-read (EIO) is treated
                # as EOF. Any other failure (e.g. EBADF) is a real error
                # and must stay observable, not be silently reclassified
                # as human EOF/cancellation - fail closed does not mean
                # swallow arbitrary I/O failures.
                raise
            self._eof = True
            return False
        if not chunk:
            self._eof = True
            return False
        self._buffer.extend(chunk)
        return True

    def _read_line_blocking(self) -> str | None:
        """Logical-line text: CRLF-normalized and decoded, but never
        stripped of interior or edge whitespace. Blocks on os.read() as
        many times as needed, with no deadline, so an arbitrarily delayed
        or chunked delivery is fully absorbed here - never inferred from
        timing."""
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

    def read_line(self, prompt: str = "Vos> ") -> str | None:
        """One complete human turn: a single newline-terminated line,
        stripped. For a control word (sí/no/salir/...) this is the correct
        read. For content that must be preserved faithfully (mission text,
        free-form feedback), use read_exact_line instead and normalize a
        separate copy only for control-word matching."""
        self._prompt(prompt)
        line = self._read_line_blocking()
        return None if line is None else line.strip()

    def read_exact_line(self, prompt: str = "Vos> ") -> str | None:
        """One complete human turn as an unstripped logical line: CRLF is
        still normalized and bytes are still decoded (there is no literal
        byte-exact terminal read), but no leading/trailing whitespace is
        removed. Used both for content that must be preserved faithfully
        and for exact-command comparisons (assignment/plan-approval
        challenges), which must not silently forgive a stray space or a
        casing difference."""
        self._prompt(prompt)
        return self._read_line_blocking()

    def read_block_until(
        self,
        *,
        prompt: str,
        continuation_prompt: str,
        first_line: str | None = None,
        terminator: str = ":fin",
        cancel_token: str = ":cancelar",
    ) -> tuple[str | None, bool]:
        """Deterministic multi-line capture: keeps blocking for more lines,
        however many OS chunks or however much delay it takes, until an
        exact-line terminator, an exact-line cancel token, or EOF - never
        based on silence duration. Each captured line (including
        first_line, when the caller passes one already read) is stored
        exactly as read, only CRLF-normalized; only the terminator/cancel
        check uses a separately normalized copy, so a control word is
        matched leniently while the stored content never is. The final
        joined text has its outer edges trimmed once - an existing,
        intentional, already-tested contract for requested-change capture,
        now shared by mission capture too, not a new normalization path.

        Returns (text, cancelled); cancelled is also true on EOF before the
        terminator, so an incomplete capture never becomes the captured
        text (fail-closed)."""
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
