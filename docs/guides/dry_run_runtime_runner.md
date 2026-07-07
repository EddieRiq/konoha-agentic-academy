# Dry-run Runtime Runner

Status: v0.14.0 baseline.

The Dry-run Runtime Runner is the first orchestration runner in Konoha Agentic Academy.

It is not a mission executor. It does not execute shell commands, mutate repository source files, perform Git operations, invoke adapters, access private context, or authorize runtime actions.

## Purpose

The runner connects the safe toolchain introduced in previous releases:

```text
Sandbox Boundary
-> Dry-run Package Builder
-> Runtime Validator
-> Runtime Inspector
-> Runtime Run Summary
```

The goal is to prove that a mission can be transformed into a sandboxed, validated, inspected dry-run package without performing the mission.

## Allowed behavior

The runner may:

- create a sandbox run folder under the configured sandbox root;
- write sandbox artifacts inside `sandbox/runs/<run_id>/`;
- generate `runtime_package.json`;
- generate `validation_report.json`;
- generate `inspection_report.json`;
- generate `runtime_run_summary.json`;
- print a pass/fail result;
- return a non-zero exit code on failure.

## Blocked behavior

The runner must not:

- execute shell commands;
- perform Git operations;
- invoke adapters;
- access private Village context;
- write outside the configured sandbox root;
- modify repository documentation, runtime contracts, adapters, examples, or Scrolls;
- authorize mission execution.

## Generated run layout

```text
sandbox/runs/<run_id>/
  sandbox_run_manifest.json
  runtime_package.json
  validation_report.json
  inspection_report.json
  runtime_run_summary.json
```

## CLI

Example:

```powershell
python .\tools\runtime_runner\run_dry_run_runtime.py `
  --title "Documentation update dry-run" `
  --scope "Generate, validate, and inspect a public dry-run package." `
  --run-id "docs-update-dry-run" `
  --sandbox-root ".\sandbox" `
  --force
```

Expected outcome:

```text
DRY-RUN RUNTIME PASSED
Execution: blocked
Filesystem mutation: sandbox only
Git operations: blocked
Private context access: blocked
Adapter execution: blocked
Network access: blocked
```

## JSON output

```powershell
python .\tools\runtime_runner\run_dry_run_runtime.py `
  --title "Documentation update dry-run" `
  --scope "Generate, validate, and inspect a public dry-run package." `
  --run-id "docs-update-dry-run" `
  --sandbox-root ".\sandbox" `
  --json `
  --force
```

The JSON output is a run summary suitable for later registry work.

## Safety model

The runner is allowed to orchestrate internal Konoha tools through Python APIs. It is not allowed to call shell commands or external processes.

This distinction matters:

```text
Allowed: Python function call to builder, validator, inspector, sandbox guard.
Blocked: shell subprocess, Git command, adapter process, network request.
```

## Failure policy

The runner fails closed.

It returns a non-zero exit code when:

- the run ID is unsafe;
- the sandbox boundary rejects a path;
- the output already exists and `--force` was not provided;
- package validation fails;
- package inspection fails;
- a required artifact cannot be written inside the sandbox root.

## Review requirements

Before release, reviewers must confirm:

- tests pass;
- path traversal is rejected;
- generated artifacts remain under the sandbox root;
- validation and inspection reports are produced;
- private context is not referenced;
- no shell, Git, adapter, or network execution exists.

## Relationship to future runtime

This release introduces dry-run orchestration only.

Future releases may add a run registry, read-only repository inspection, controlled artifact writing inside sandbox, and human-approved apply plans. Those capabilities are not authorized by this runner.
