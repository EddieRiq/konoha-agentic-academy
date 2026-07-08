# Product Runtime Bootstrap

## Purpose

Product Runtime Bootstrap is the first product-oriented command layer after v1.0.0.

It turns the safe dry-run runtime into something easier to initialize, diagnose, and operate from a predictable command surface.

## CLI

Primary command:

```powershell
python .\tools\product_runtime\konoha_product.py --help
```

Supported commands:

```text
init
doctor
config validate
mission new
run dry-run
```

## What it may do

The bootstrap CLI may:

- initialize a local workspace under an explicit workspace root;
- create workspace directories for missions, reports, state, and temporary files;
- create a Mission Charter skeleton;
- validate public config shape;
- run a read-only product doctor;
- delegate dry-run mission execution to the existing end-to-end dry-run mission workflow.

## What it may not do

The bootstrap CLI may not:

- execute mission actions;
- invoke real adapters;
- use network access;
- access private Village context;
- apply repository changes;
- stage files;
- create commits;
- push changes;
- clean or reset files;
- authorize runtime actions.

## Default workspace

The default workspace is:

```text
sandbox/workspace
```

This keeps product bootstrap outputs inside the already-local sandbox boundary.

## Mission workspace

`mission new` creates:

```text
sandbox/workspace/missions/<mission_id>/
  charter.md
  mission_manifest.json
  inputs/
  context/
  plans/
  outputs/
  reports/
  approvals/
```

The generated Charter is a starting point for human review. It is not automatic approval.

## Doctor

`doctor` checks required public files, config shape, workspace state, and stable safety boundaries.

It is read-only.

## Dry-run delegation

`run dry-run` delegates to:

```text
tools/mission_workflow/run_dry_run_mission.py
```

The bootstrap CLI does not bypass that workflow. It preserves the existing sandbox and non-execution boundaries.

## UI gate reminder

The local UI remains future work.

Before any UI implementation, Konoha must present a draft covering:

- UI goals;
- proposed screens;
- navigation;
- backend/frontend stack;
- permission model;
- approval boundaries;
- files to be created.

No UI files should be generated before explicit human approval.
