# Read-only Runtime Inspector

Status: CLI-inspector alpha.

## Purpose

The Read-only Runtime Inspector checks dry-run runtime packages for internal consistency, traceability, and safety-boundary signals.

It builds on:

- the Runtime Contract and Dry-run Validator MVP;
- the Dry-run Package Builder CLI;
- dry-run runtime package examples.

The inspector does not validate every JSON schema detail. The validator remains responsible for contract validation. The inspector adds package-level coherence checks.

## Boundary

The inspector is not a runtime executor and not an auto-fixer.

It may:

- read one dry-run runtime package JSON file;
- inspect required sections;
- inspect manifest and index coherence;
- inspect trace events;
- inspect safety flags and execution blockers;
- detect obvious private/local reference fragments;
- print a text or JSON inspection report to stdout.

It may not:

- execute shell commands;
- mutate files;
- perform Git operations;
- invoke adapters;
- access private Village context;
- authorize runtime actions;
- execute missions;
- repair packages automatically.

## Example

```powershell
python .\tools\runtime_inspector\inspect_runtime_package.py .\examples\dry_run_packages\builder_generated_docs_update.runtime_package.json
```

Expected outcome:

```text
INSPECTION PASSED
Package: builder-generated-docs-update
Mode: dry_run
Execution: blocked
Filesystem mutation: blocked
Git operations: blocked
Private context access: blocked
Adapter execution: blocked
```

JSON output:

```powershell
python .\tools\runtime_inspector\inspect_runtime_package.py .\examples\dry_run_packages\builder_generated_docs_update.runtime_package.json --json
```

## Inspection checks

The inspector checks:

- root package fields;
- `mode = dry_run`;
- `execution_authorized = false`;
- all required safety flags blocked;
- required runtime package sections;
- mission ID consistency;
- trace events and `execution_performed = false`;
- manifest included artifacts;
- index artifact records;
- validation report status;
- blocked private/local reference fragments.

## Relationship to the validator

The validator answers:

```text
Does this package satisfy the runtime contract?
```

The inspector answers:

```text
Does this package look coherent, traceable, and safe to review?
```

Both are read-only tools.

## Stop conditions

Stop and review if:

- any safety flag is true;
- the package authorizes execution;
- trace events report execution performed;
- private/local references are detected;
- required sections are missing;
- validation report errors are present;
- manifest or index records are incomplete;
- the package implies action rather than dry-run review.

## Release boundary

This release still does not introduce runtime execution.

The inspector is a read-only CLI utility. It supports review, not action.
