# Dry-run Package Builder CLI

Status: validation-tool alpha.

## Purpose

The Dry-run Package Builder CLI creates a runtime package JSON file that can be validated by the read-only runtime validator.

It exists to reduce manual package assembly while preserving Konoha's non-execution boundary.

## Boundary

The builder is not a runtime executor.

It may:

- create a dry-run runtime package JSON file;
- write only to the requested package output path;
- create parent directories for that output path;
- generate Mission Intake, Dry-Run Execution Plan, Adapter Stub, Evidence Stub, Runtime State, Validation Report placeholder, Trace Event, Manifest, and Index records;
- print the next validator command.

It may not:

- execute shell commands;
- perform Git operations;
- invoke adapters;
- read private Village context;
- authorize runtime actions;
- execute missions;
- write into blocked private or repository-control paths.

## Preferred output locations

Use one of these locations by default:

```text
sandbox/tmp/
sandbox/runs/
examples/dry_run_packages/
```

Writing elsewhere requires an explicit override flag and still may not target private or repository-control paths.

## Example

```powershell
python .\tools\runtime_builder\create_dry_run_package.py `
  --title "Documentation update dry-run" `
  --scope "Create a public dry-run package for a documentation-only change." `
  --output ".\sandbox\tmp\docs-update-dry-run"
```

Then validate:

```powershell
python .\tools\runtime_validator\validate_runtime_package.py .\sandbox\tmp\docs-update-dry-run\runtime_package.json
```

## Expected behavior

The generated package should remain dry-run only:

```text
Execution: blocked
Filesystem mutation: package output only
Git operations: blocked
Private context access: blocked
Adapter execution: blocked
```

## Stop conditions

Stop and review if:

- the requested output path points to private Village content;
- the generated package fails validation;
- any safety flag is true;
- the package implies execution authorization;
- the package requires private context;
- the builder is asked to modify real project docs, runtime files, Git state, or adapter configuration.

## Relationship to the validator

The builder produces a package. The validator decides whether that package satisfies the runtime contract.

A generated package is not automatically trusted. It must be validated and reviewed.
