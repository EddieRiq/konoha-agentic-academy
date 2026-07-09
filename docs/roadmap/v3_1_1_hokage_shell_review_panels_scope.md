# v3.1.1 Hokage Shell Review Panels Scope

## Purpose

Improve the usability of the terminal-first Hokage Shell without adding a Web UI or heavy TUI dependency.

## Adds

- Human review summaries instead of path-heavy output.
- Markdown step reports.
- Review latest result flow.
- On-demand raw JSON and patch plan views.
- Mission timeline view.
- Optional terminal viewer handoff to `glow`, `bat`, or `less`.
- Plain text fallback viewer.
- False-positive summary messaging when deterministic guard suppresses local model claims.

## Does not add

- Web UI.
- Background agents.
- Automatic patch approval.
- Automatic Git operations.
- External service dependency.
- Non-local memory.

## Success criteria

- Shell remains usable over SSH.
- The main UI displays summaries, not long file paths.
- Full details are available on demand.
- Local model audit output is summarized with token usage and issue counts.
- Suppressed issues do not create patch recommendations.
