# v3.1.0 Hokage Terminal Shell scope

## Objective

Add a minimal terminal-first UI for Konoha so missions can be started and supervised from an SSH-friendly console.

## Included

- Hokage shell CLI.
- ASCII panels for Hokage desk and active agents.
- Persona selection.
- Non-interactive smoke mode.
- Mission session file.
- Event log.
- Deterministic repo marker scan.
- Optional local model audit handoff to existing v3.0.1/v3.0.2 local audit tool.
- Private Obsidian-compatible memory note writing.

## Excluded

- Web UI.
- Background autonomous agents.
- Direct arbitrary shell execution.
- Automatic patch application.
- Automatic Git operations.
- Remote model invocation by default.

## Success criteria

- The shell starts locally in WSL.
- It runs over SSH without a browser.
- It can create a mission.
- It records a session and event log.
- It writes a local Obsidian-compatible mission note.
- It can run deterministic repo scan.
- It can optionally call Ollama repo audit through the approved local model audit tool.
