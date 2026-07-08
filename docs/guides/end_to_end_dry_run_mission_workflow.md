# End-to-End Dry-run Mission Workflow

## Status

Pre-release / dry-run workflow alpha.

## Purpose

The End-to-End Dry-run Mission Workflow connects the existing Konoha safe toolchain into one mission-level workflow.

The workflow prepares a sandbox run, generates a runtime package, validates it, inspects it, lists the resulting run through the registry, optionally inspects the public repository, and writes a mission workflow report inside the sandbox run.

## Boundary

This workflow is not a mission executor.

It does not:

- execute mission actions;
- execute arbitrary shell commands;
- invoke adapters;
- access private Village context;
- perform Git write operations;
- apply files to the repository;
- authorize runtime actions;
- use the network.

It may:

- call allowlisted internal Konoha tools;
- create sandbox-only run outputs;
- read public repo files through the read-only repo inspector;
- write `mission_workflow_report.json` inside `sandbox/runs/<run_id>/`;
- return pass/fail status.

## Command

```powershell
python .\tools\mission_workflow\run_dry_run_mission.py `
  --title "Example dry-run mission" `
  --scope "Generate, validate, inspect, and register a dry-run mission package." `
  --run-id "example-dry-run-mission" `
  --repo-root "." `
  --sandbox-root ".\sandbox" `
  --config ".\konoha.config.example.json" `
  --force
```

The same workflow is exposed through the unified CLI:

```powershell
python .\tools\konoha_cli.py mission dry-run `
  --title "Example dry-run mission" `
  --scope "Generate, validate, inspect, and register a dry-run mission package." `
  --run-id "example-dry-run-mission" `
  --repo-root "." `
  --sandbox-root ".\sandbox" `
  --config ".\konoha.config.example.json" `
  --force
```

## Workflow steps

1. Validate the optional project config.
2. Run the dry-run runtime runner.
3. Validate the generated runtime package.
4. Inspect the generated runtime package.
5. List sandbox runs through the runtime registry.
6. Optionally inspect the public repository.
7. Write `mission_workflow_report.json`.

## Required outputs

A successful run should create:

```text
sandbox/runs/<run_id>/
  sandbox_run_manifest.json
  runtime_package.json
  runtime_run_summary.json
  mission_workflow_report.json
```

## Stop conditions

The workflow must stop if:

- the run id is unsafe;
- required internal tools are missing;
- the runtime runner fails;
- the runtime package is missing;
- package validation fails;
- package inspection fails;
- the workflow would write outside the sandbox run.

## Relationship to previous releases

This workflow connects:

- Project Config and Policy Contract;
- Unified CLI Entrypoint;
- Dry-run Runtime Runner;
- Runtime Run Registry;
- Read-only Repo Inspector;
- Runtime Contract and Validator;
- Read-only Runtime Inspector;
- Local Sandbox Boundary.

## Review requirement

A workflow report does not authorize execution, repository mutation, Git commits, adapter calls, or private context access.
