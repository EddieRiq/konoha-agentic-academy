# Hokage Terminal Operator Baseline

## Purpose

v3.1.6 adds one read-only terminal command that summarizes the current operator context:

```bash
python tools/hokage_shell/run_hokage_shell.py \
  --repo-root "." \
  --workspace-root "./sandbox/hokage-shell" \
  status
```

JSON output:

```bash
python tools/hokage_shell/run_hokage_shell.py \
  --repo-root "." \
  --workspace-root "./sandbox/hokage-shell" \
  status \
  --json
```

## What the report shows

### Repository

- branch and HEAD;
- working-tree cleanliness;
- changed-path count without listing private filenames;
- configured upstream;
- behind/ahead counts;
- latest local tag.

Only local Git read operations are used. The command never fetches or contacts a remote.

### Mission

- valid and invalid mission counts;
- latest valid mission;
- mission state;
- next recommended action;
- latest Markdown report, audit JSON, patch plan and event-log availability.

Mission state is evidence only.

### Terminal

- TTY state;
- terminal width;
- plain-mode request;
- `TERM`;
- viewer availability;
- fallback order: `glow`, `bat`, `less`, plain.

### Authority

The report exposes approval tokens and safety boundaries, but never treats them as approval.

## Read-only guarantee

`status` does not call `make_paths()`.

Therefore it does not create:

```text
workspace_root
memory_root
mission directories
report files
```

It also blocks:

```text
model invocation
network access
private-memory reads
Git writes
repository mutation
workspace mutation
```

## Operator states

```text
ready
attention_required
```

Attention is required when:

- the working tree is dirty;
- the configured upstream is not synchronized;
- invalid mission sessions exist.

A dirty tree is not automatically repaired. An unsynchronized branch is not fetched. Invalid sessions are not modified.

## Scope boundary

This release does not add an interactive refresh loop, daemon, watcher, model invocation, patching or Git mutation. Those require separate releases and explicit gates.
