# Hokage Terminal Shell

Konoha v3.1.0 introduces a terminal-first Hokage Shell.

The goal is to make Konoha usable as an SSH-friendly local tool instead of a sequence of isolated commands. The shell keeps the same safety doctrine: UI output is not permission, model output is evidence only, and Git or file mutations still require explicit gates.

## Scope

The first shell is intentionally minimal:

- terminal UI only;
- no web UI;
- no daemon;
- no background autonomous agents;
- ASCII/ANSI panels;
- persona selection;
- start mission flow;
- deterministic repo scan;
- optional Ollama local repo audit handoff;
- Obsidian-compatible private memory notes;
- event log per mission.

## Command

```bash
python tools/hokage_shell/run_hokage_shell.py \
  --repo-root "." \
  --workspace-root "./sandbox/hokage-shell" \
  --memory-root "alliance/kirigakure/memory/obsidian" \
  --persona "sarcastic_lab_ai"
```

For non-interactive smoke testing:

```bash
python tools/hokage_shell/run_hokage_shell.py \
  --repo-root "." \
  --workspace-root "./sandbox/hokage-shell-smoke" \
  --memory-root "alliance/kirigakure/memory/obsidian" \
  --persona "sarcastic_lab_ai" \
  --no-animation \
  smoke \
  --task "Review README, CHANGELOG and roadmap alignment with v3.0.1." \
  --json
```

## Personas

Built-in personas:

- `sarcastic_lab_ai`;
- `naruto_hokage`;
- `strict_auditor`;
- `calm_mentor`;
- `silent_operator`.

Personas change communication style only. They do not override safety, approval tokens, deterministic checks or Git gates.

## Obsidian memory

By default memory is written to:

```text
alliance/kirigakure/memory/obsidian/
```

This path is private/local and should remain ignored by Git.

The public repository only contains schemas, examples and templates.

## Boundary

The shell may display an agent working in a cubicle, but it does not create autonomous background agents. It records events and calls existing approved tools only when the human explicitly approves that step.
