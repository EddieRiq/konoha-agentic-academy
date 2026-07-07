# Runtime Contract and Dry-run Validator

Status: documentation-first alpha with read-only executable MVP.

This guide defines the first executable boundary for Konoha Agentic Academy runtime artifacts.

The validator is intentionally narrow. It validates dry-run runtime package JSON files. It does not execute mission steps, invoke adapters, mutate files, perform Git operations, or authorize private context access.

## Principle

Konoha can validate structure before it can execute behavior.

The first runtime executable must prove that a package is safe to review, not safe to execute.

## Scope

This baseline covers:

- runtime artifact JSON schemas;
- a read-only validator CLI;
- public fixtures for valid and invalid dry-run packages;
- unit tests for the validator;
- explicit failure when execution permissions appear enabled.

## Out of scope

This baseline does not include:

- shell execution;
- filesystem mutation;
- Git operations;
- adapter execution;
- automatic model routing;
- automatic token enforcement;
- private Village access;
- runtime package generation;
- automatic repair of invalid packages.

## Runtime package contract

A runtime package must include:

- Mission Intake;
- Dry-run Execution Plan;
- Adapter Invocation Stub;
- Evidence Collection Stub;
- Runtime State;
- Runtime Validation Report;
- Runtime Trace Events;
- Runtime Package Manifest;
- Runtime Package Index.

The package must be `dry_run` mode and must explicitly block:

- shell execution;
- filesystem mutation;
- Git operations;
- adapter execution;
- private context access;
- autonomous execution.

## Validator CLI

Example:

```powershell
python tools/runtime_validator/validate_runtime_package.py tests/runtime_validator/fixtures/valid_runtime_package.json
```

Expected successful output:

```text
VALIDATION PASSED
Package: docs-update-dry-run-example
Mode: dry_run
Execution: blocked
Filesystem mutation: blocked
Git operations: blocked
Private context access: blocked
Adapter execution: blocked
```

Directory input is also supported when the directory contains either:

- `runtime_package.json`; or
- exactly one `*.runtime_package.json` file.

## Test command

```powershell
python -m unittest discover -s tests/runtime_validator -p "test_*.py"
```

## Review expectations

Before this validator is treated as a release artifact, reviewers should confirm:

- the validator is read-only;
- the validator does not call shell commands;
- the validator does not write files;
- invalid execution flags fail validation;
- valid dry-run packages pass validation;
- private context access is blocked for public examples;
- error messages are clear enough to support manual repair.

## Stop conditions

Stop if:

- a validator path would read private Village content by default;
- validation failure is silently ignored;
- execution flags are allowed to be true;
- the validator writes into the repository;
- tests require secrets or network access;
- examples include private context, credentials, project data, or copyrighted private material.

## Relationship to future runtime

This validator is a foundation for future runtime behavior. Passing validation does not authorize execution. It only means the package is structured enough for review.
