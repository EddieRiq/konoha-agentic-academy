# Git Read-only Gate

Status: pre-release / read-only gate alpha.

## Purpose

The Git Read-only Gate inspects repository readiness using read-only Git commands.

It exists before any Git write automation so Konoha can learn to inspect repository state without staging, committing, pushing, cleaning, or rewriting anything.

## Boundary

The gate may:

- read Git status;
- read changed file names;
- read tracked file names;
- check whether selected paths are ignored;
- print text reports;
- print JSON reports to stdout;
- fail with a non-zero exit code when blockers exist.

The gate may not:

- stage files;
- create commits;
- move references;
- publish changes;
- delete files;
- repair files;
- execute missions;
- invoke adapters;
- access private Village context;
- authorize runtime actions.

## Commands

The gate is limited to read-only Git subcommands:

```text
git rev-parse --show-toplevel
git status --porcelain=v1
git diff --name-only
git ls-files
git check-ignore -v <path>
```

Any other Git command is outside this baseline.

## Default behavior

A clean repository passes.

A dirty repository is blocked by default because later write gates must not operate on ambiguous state.

During local development, `--allow-dirty` may be used to downgrade modified or untracked files to warnings. Release audits should not use `--allow-dirty`.

## Private boundary checks

The gate checks tracked files for local-only or private path patterns such as:

- private libraries;
- local memory;
- virtual environments;
- environment files;
- secrets;
- credentials;
- vaults.

This is a tracked-file check. It does not read ignored private content.

## Example

```powershell
python .\tools\git_readiness\inspect_git_readiness.py --repo-root "."
```

JSON output:

```powershell
python .\tools\git_readiness\inspect_git_readiness.py --repo-root "." --json
```

Optional ignore checks:

```powershell
python .\tools\git_readiness\inspect_git_readiness.py `
  --repo-root "." `
  --check-ignore-path "alliance/example-private-village/private-library/example-source.md"
```

## Stop conditions

Stop if:

- the path is not inside a Git repository;
- read-only Git commands fail;
- the working tree is dirty and `--allow-dirty` is not set;
- private or local-only paths are tracked;
- ignore checks show that required local-only paths are not ignored.

## Relationship to future gates

This gate prepares for future Git operation gates by proving that Konoha can inspect repository state safely.

It does not grant permission to run Git write operations.
