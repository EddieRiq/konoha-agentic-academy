# v1.0 Release Readiness

The v1.0 release-readiness layer is the final stabilization gate before publishing Konoha Agentic Academy as a stable local-first dry-run runtime.

It does not add runtime authority. It verifies that the public safe toolchain exists, that core boundary language is present, that tests pass, that integrated smoke checks pass, that the dogfood suite passes, that public repository inspection passes, and that Git readiness is clean or explicitly allowed during pre-commit checks.

## Target release

```text
v1.0.0 - Stable local-first dry-run runtime
```

The v1.0 promise is:

```text
Konoha can safely run local-first, human-approved, dry-run-centered agentic workflows that generate, validate, inspect, propose, apply, stage, and commit changes under explicit gates.
```

## What the readiness checker may do

The checker may:

- verify required public files exist;
- verify release boundary language is present;
- run unit tests;
- delegate to integrated smoke tests;
- delegate to the Dogfood Mission Suite;
- delegate to read-only repository inspection;
- delegate to read-only Git readiness;
- write a readiness report under `sandbox/reports/`.

## What the readiness checker may not do

The checker may not:

- execute mission actions;
- invoke real adapters;
- call external APIs;
- use network access;
- access private Village context;
- apply files to the repository;
- stage files;
- create commits;
- push changes;
- clean or reset files;
- authorize runtime actions;
- close a release without human review.

## Local command

During pre-commit work, use `--allow-dirty` because the release files are not committed yet:

```powershell
python .\tools\release_readiness\check_v1_release_readiness.py `
  --repo-root "." `
  --sandbox-root ".\sandbox" `
  --run-id "v1-0-readiness-smoke" `
  --allow-dirty `
  --force
```

After all commits are done, run without `--allow-dirty`:

```powershell
python .\tools\release_readiness\check_v1_release_readiness.py `
  --repo-root "." `
  --sandbox-root ".\sandbox" `
  --run-id "v1-0-release-readiness" `
  --force
```

## Report

The checker writes:

```text
sandbox/reports/<run_id>_v1_release_readiness_report.json
```

The report is local evidence. It is not an approval artifact by itself. Human review is still required before tagging v1.0.0.

## Stable boundary

v1.0.0 remains local-first and dry-run-centered.

Stable does not mean autonomous. Stable means the safety contract is coherent, tested, repeatable, documented, and bounded.
