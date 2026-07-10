# Hokage Shell Mission Continuity

## Purpose

v3.1.5 adds deterministic, local mission reentry to the terminal shell.

The continuity layer answers:

- which valid missions exist;
- which mission is latest by `updated_at`;
- whether a session file is valid;
- what state the mission was in;
- what the last valid event was;
- what report was produced most recently;
- what the next recommended action is;
- whether recorded repo and workspace roots still match.

Mission continuity does not execute tools, invoke models, read private memory, mutate Git, or authorize the next action.

## Commands

List valid and invalid local missions:

```bash
python tools/hokage_shell/run_hokage_shell.py \
  --repo-root "." \
  --workspace-root "./sandbox/hokage-shell" \
  missions \
  --json
```

Build a read-only snapshot for the latest valid mission:

```bash
python tools/hokage_shell/run_hokage_shell.py \
  --repo-root "." \
  --workspace-root "./sandbox/hokage-shell" \
  resume \
  --latest \
  --json
```

Build a snapshot for an explicit mission:

```bash
python tools/hokage_shell/run_hokage_shell.py \
  --repo-root "." \
  --workspace-root "./sandbox/hokage-shell" \
  resume \
  --mission-id "20260710-190000-review-repo" \
  --json
```

Interactive mode can still use:

```bash
python tools/hokage_shell/run_hokage_shell.py \
  --repo-root "." \
  --workspace-root "./sandbox/hokage-shell" \
  --continue-latest \
  interactive
```

The shell now validates the selected session instead of choosing a directory name blindly.

## Selection rule

The latest mission is selected deterministically by:

1. valid `updated_at`;
2. valid `created_at`;
3. mission id as a deterministic tie-breaker.

Invalid or malformed sessions are listed separately and are never selected as latest.

## Integrity checks

A resumable session must have:

```text
schema_version
report_type = hokage_shell_session
mission_id
task
state
created_at
updated_at
repo_root
workspace_root
next_recommended_action
```

The directory name and session `mission_id` must match.

Mission ids are restricted to:

```text
^[a-z0-9][a-z0-9._-]{0,79}$
```

This blocks path traversal.

## Events

`events.ndjson` is read defensively.

Valid events contribute to:

- event count;
- latest event type;
- latest event timestamp.

Invalid lines are counted and surfaced but do not silently become truth.

## Private-memory boundary

The continuity layer does not read:

```text
alliance/kirigakure/memory/obsidian/
```

Session and event evidence under the ignored sandbox workspace are enough to reconstruct terminal context. Memory remains optional evidence and never grants authority.

## Exit codes

```text
0  continuity report produced successfully
1  requested mission not found or no valid missions exist
2  invalid mission id or corrupt requested mission
```

A successful resume report is evidence only. It does not authorize repository inspection, model invocation, patching, Git operations, or mission closure.
