# v3.1.5 Hokage Shell Mission Continuity Scope

## Objective

Make terminal mission reentry deterministic, inspectable, and safe without adding a daemon, background autonomy, or private-memory dependency.

## Included

- mission inventory under the configured sandbox workspace;
- deterministic latest-mission selection by timestamps;
- session schema and field integrity checks;
- mission-id path traversal protection;
- read-only resume snapshots;
- valid and invalid mission separation;
- event timeline summary with invalid-line count;
- latest step-report path;
- repo-root and workspace-root match indicators;
- `missions` and `resume` shell commands;
- validated `--continue-latest` behavior;
- JSON schema, example, tests, guide and review Scroll.

## Excluded

- automatic execution after resume;
- automatic model invocation;
- automatic repository inspection;
- reading Obsidian memory during resume;
- mission migration;
- cross-machine synchronization;
- daemon or background watcher;
- mission closure automation.

## Acceptance criteria

1. Latest mission selection uses `updated_at`, not directory name.
2. Invalid sessions never become the latest mission.
3. Explicit mission ids cannot escape the workspace.
4. Resume reports expose state, last event, latest report and next action.
5. Invalid NDJSON event lines are counted.
6. Private memory is not read.
7. Resume does not mutate workspace, Git or repository source.
8. Shell list and resume commands support JSON output.
9. Existing Hokage Shell tests remain green.
10. Canonical Release Test Gate passes.
