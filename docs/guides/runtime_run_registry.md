# Runtime Run Registry

Status: documentation-backed CLI baseline.

The Runtime Run Registry lists dry-run runtime runs from a local sandbox and reports their review state without executing missions.

It belongs after the Dry-run Runtime Runner. The runner can create run folders and summaries; the registry reads those folders and produces a registry view.

## Purpose

The registry answers a simple question:

```text
What dry-run runtime runs exist, and which ones are passed, incomplete, blocked, or review-required?
```

It is useful for:

- reviewing local sandbox history;
- detecting incomplete dry-run runs;
- checking whether validation and inspection artifacts exist;
- confirming that safety boundaries remain blocked;
- preparing future run dashboards or reports.

## Non-goals

The registry does not:

- execute missions;
- execute shell commands;
- invoke adapters;
- perform Git operations;
- repair packages;
- delete runs;
- access private Village context;
- decide whether a mission is authorized.

## CLI

```powershell
python .\tools\runtime_registry\list_runtime_runs.py --sandbox-root ".\sandbox"
```

JSON output:

```powershell
python .\tools\runtime_registry\list_runtime_runs.py --sandbox-root ".\sandbox" --json
```

Passed-only output:

```powershell
python .\tools\runtime_registry\list_runtime_runs.py --sandbox-root ".\sandbox" --passed-only
```

## Expected run folder

The registry expects dry-run runs under:

```text
sandbox/
  runs/
    <run_id>/
      sandbox_run_manifest.json
      runtime_package.json
      validation_report.json
      inspection_report.json
      runtime_run_summary.json
```

Missing files do not cause mutation. They are reported as blockers.

## Run states

### passed

The run has:

- sandbox manifest;
- runtime package;
- validation report;
- inspection report;
- runtime run summary;
- validation marked as passed;
- inspection marked as passed;
- safety fields blocked or sandbox-only.

### review_required

The run has no hard blockers, but validation or inspection does not clearly pass.

### incomplete_or_blocked

The run is missing required artifacts or has an unsafe boundary field.

Examples:

- missing runtime run summary;
- missing runtime package;
- execution not blocked;
- Git operations not blocked;
- private context access not blocked;
- adapter execution not blocked;
- filesystem mutation not sandbox-only.

## Safety boundary

The registry may:

- read files under `sandbox/runs`;
- parse JSON;
- print text reports;
- print JSON reports to stdout.

The registry may not:

- write files;
- delete files;
- execute shell commands;
- perform Git operations;
- access network;
- invoke adapters;
- authorize actions.

## Relationship to prior releases

```text
v0.10.0 Validator: checks package validity.
v0.11.0 Builder: generates dry-run packages.
v0.12.0 Inspector: inspects dry-run packages.
v0.13.0 Sandbox Boundary: prepares sandbox runs.
v0.14.0 Runner: orchestrates dry-run package generation/validation/inspection.
v0.15.0 Registry: lists and summarizes sandbox run history.
```

The registry turns local dry-run runs into an auditable inventory.
