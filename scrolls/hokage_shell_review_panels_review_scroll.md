# Hokage Shell Review Panels Review Scroll

## Review questions

- Does the shell show concise summaries by default?
- Can the human view full Markdown reports on demand?
- Can raw JSON and patch plans be opened only when requested?
- Are false positives clearly marked as suppressed?
- Are token usage summaries visible?
- Are patches still gated by explicit approval?
- Are Git operations still delegated to the beta Git Gate?

## Safety checks

- No Web UI dependency.
- No background agent loop.
- No automatic patch application.
- No direct Git operations from the review panel.
- No private memory committed to the public repository.

## Expected behavior

When a local model suggests an issue and the deterministic guard suppresses it, the UI should say that no patch is recommended.
