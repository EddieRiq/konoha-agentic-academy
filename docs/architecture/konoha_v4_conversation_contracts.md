# Konoha v4 — Conversational approval and mission contracts

This correction establishes explicit approval states (`pending`, `approved`,
`rejected`, `changes_requested`). Blank input and buffered whitespace keep the
plan pending. Only explicit human approval permits execution.

Codex is the Mission Conductor. Hokage is a separate constitutional authority
and is never represented as an operational assignment.

Teachback defaults to `disabled`. Plans must separate read-only workspace
constraints from private runtime persistence, and budgets must be itemized per
task, provider and family. Provider subprocesses receive isolated temporary and
Python cache roots under the private state root. Execution compares Git status
before and after each task and stops on unexpected workspace mutation.
