# Git Staging Gate

Status: pre-release / Git-staging alpha.

## Purpose

The Git Staging Gate is the first controlled Git write boundary in Konoha Agentic Academy.

It can stage explicitly allowlisted files with `git add -- <paths>` only after human approval is provided through:

- `--confirm-stage`;
- exact approval token `STAGE_ALLOWLISTED_FILES`;
- explicit repo-relative paths or a JSON stage plan.

This is not Git automation. It does not commit, push, clean, reset, rewrite history, execute missions, invoke adapters, access private context, or authorize runtime actions.

## Position in the runtime path

The Git Staging Gate comes after:

1. dry-run package generation;
2. validation;
3. inspection;
4. sandbox boundary;
5. sandbox artifact writing;
6. human-approved apply plan;
7. Git read-only readiness gate.

It stages already-approved repository changes. It does not create or apply those changes.

## Allowed behavior

The gate may:

- inspect that the provided repository root is the Git top-level;
- normalize and validate repo-relative paths;
- reject path traversal and absolute paths;
- reject private, ignored, local-only, or blocked paths;
- preview staging without changing the Git index;
- stage explicit allowlisted files with `git add -- <paths>`;
- print text or JSON reports to stdout.

## Blocked behavior

The gate must not:

- use broad `git add .`, `git add -A`, or `git add --all`;
- create commits;
- push changes;
- clean files;
- reset files;
- rewrite history;
- execute shell commands through `shell=True`;
- invoke adapters;
- access private Village context;
- stage private or ignored content;
- authorize runtime actions.

## Allowlisted staging areas

The initial allowlist is intentionally narrow:

- `docs/`;
- `scrolls/`;
- `examples/`;
- `runtime/templates/`;
- `schemas/runtime/`;
- `tools/`;
- `tests/`;
- selected root documentation files.

The gate blocks known private and local-only areas, including `alliance/`, `sandbox/runs/`, `sandbox/tmp/`, local memory, vaults, credentials, secrets, and private context fragments.

## Preview mode

Without `--confirm-stage`, the gate runs in preview mode.

Preview mode validates the requested paths and reports what would be staged, but it does not change the Git index.

Example:

```powershell
python .\tools\git_staging\stage_allowlisted_files.py `
  --repo-root "." `
  --path "docs/guides/example.md"
```

## Confirmed staging mode

Confirmed staging requires the exact approval token.

```powershell
python .\tools\git_staging\stage_allowlisted_files.py `
  --repo-root "." `
  --path "docs/guides/example.md" `
  --confirm-stage `
  --approval-token "STAGE_ALLOWLISTED_FILES"
```

## Stop conditions

Stop if:

- the repo root is not the Git top-level;
- any path is absolute;
- any path uses traversal;
- any path is outside the allowlist;
- any path matches private or local-only boundaries;
- any path is ignored;
- any path does not exist;
- approval is missing for confirmed staging;
- the requested operation implies commit, push, clean, reset, or broad staging.

## Relationship to Git Read-only Gate

The Git Read-only Gate inspects repository readiness.

The Git Staging Gate may stage files, but only explicit allowlisted files and only with approval.

Passing this gate does not authorize commit or push. Those require separate future gates.
