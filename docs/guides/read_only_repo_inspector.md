# Read-only Repo Inspector

Status: v0.16.0 baseline.

The Read-only Repo Inspector checks public Konoha repository artifacts without mutating files or executing missions.

It is part of the safe runtime progression after:

```text
Builder -> Validator -> Inspector -> Sandbox Boundary -> Runner -> Registry
```

## Purpose

The inspector gives Konoha a read-only way to review public repository coherence before moving toward controlled artifact generation.

It can report:

- missing public runtime artifacts;
- risky Python patterns requiring human review;
- private-boundary signals in public files;
- executable files accidentally added under examples;
- missing safety-boundary language.

## Non-goals

The inspector is not a runtime executor.

It does not:

- execute missions;
- execute shell commands;
- perform Git operations;
- modify files;
- repair files automatically;
- invoke adapters;
- access private Village context;
- read ignored private folders intentionally;
- authorize runtime actions.

## Public scan boundary

The inspector scans only allowlisted public repository areas.

It skips private or local-only path parts such as:

```text
.git
.venv
private-library
vault
kirigakure
local-memory
```

The sandbox is treated carefully. Runtime outputs under `sandbox/runs` and `sandbox/tmp` are local run artifacts and are not part of the public repo inspection.

## Finding levels

### Error

An error means the public repo state is not acceptable for the inspected contract.

Examples:

- required public artifact missing;
- executable source file added under `examples/`.

### Warning

A warning requires review but does not fail the inspection by default.

Examples:

- private-boundary signal appears in public text;
- Python tool contains a risky pattern that needs human review.

Use `--strict` when warnings should make the command fail.

## CLI

```powershell
python .\tools\repo_inspector\inspect_public_repo.py --repo-root "."
```

JSON output:

```powershell
python .\tools\repo_inspector\inspect_public_repo.py --repo-root "." --json
```

Strict mode:

```powershell
python .\tools\repo_inspector\inspect_public_repo.py --repo-root "." --strict
```

## Safety boundary

The inspector may:

- read public files from allowlisted repo areas;
- inspect public Python tools for risky patterns;
- inspect public examples for executable file types;
- report errors and warnings;
- print text or JSON to stdout.

The inspector may not:

- write files;
- delete files;
- run shell commands;
- call Git;
- call network APIs;
- invoke adapters;
- read private Village content;
- approve actions.

## Relationship to previous tools

The runtime package inspector checks one dry-run runtime package.

The repo inspector checks public repository coherence around the toolchain and examples.

They are complementary and both remain read-only.
