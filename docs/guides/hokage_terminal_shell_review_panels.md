# Hokage Terminal Shell Review Panels

v3.1.1 improves the terminal-first Hokage Shell by replacing path-heavy output with human review panels and on-demand details.

## Goal

The default UI should answer:

- what happened;
- what the agents found;
- whether an approval is required;
- whether patches are recommended;
- how many tokens were used;
- what the next safe step is.

Detailed evidence remains available, but it is no longer printed as the primary output.

## Review controls

The shell adds a review flow:

```text
4. Review latest result
5. View mission timeline
```

The review panel supports:

```text
v. view markdown report
j. view raw audit JSON
p. view patch plan JSON
b. back
```

## Detail viewer

The viewer is terminal-first and SSH-friendly.

Resolution order:

1. `glow` if installed.
2. `bat` if installed.
3. `less` if installed.
4. built-in plain text preview.

No viewer is installed automatically.

## Step Markdown reports

Every major step can write a Markdown report under:

```text
sandbox/hokage-shell/missions/<mission-id>/step_reports/
```

Reports are evidence only. They do not authorize patches, commands, Git operations, or mission closure.

## Local model audit summary

After local model audit, the UI shows:

- status;
- model;
- suggested issues count;
- validated issues count;
- suppressed issues count;
- patch operations count;
- recommendation;
- token usage.

Raw JSON paths are hidden unless requested.

## False-positive handling

If the local model suggests an issue but deterministic evidence suppresses it, Hokage should communicate this explicitly and avoid recommending a patch.

Example:

```text
El agente local parece haber producido un falso positivo.
No recomiendo patch.
```

## Boundaries

- UI is not permission.
- Hokage orchestrates but does not execute.
- Model output is evidence only.
- Markdown reports are evidence only.
- Patch plans are not permission.
- Git operations still require the beta Git Gate.
