# Dogfood Mission Suite

The Dogfood Mission Suite runs Konoha against itself using the safe local-first workflow gates already present in the repository.

It is intended as the final pre-1.0 confidence layer before release-candidate stabilization.

## Purpose

The suite validates that the public Konoha toolchain can operate as one coordinated workflow without expanding authority.

It exercises:

- project config validation;
- end-to-end dry-run mission workflow;
- proposed artifact workflow preview;
- adapter invocation gate preview;
- explicitly approved mock adapter invocation;
- public repo inspection;
- Git readiness inspection.

## Non-authority boundary

The Dogfood Mission Suite does not authorize new behavior.

It may not:

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
- close a release without human review.

## Outputs

The suite writes one report under:

```text
sandbox/reports/<run_id>_dogfood_mission_suite_report.json
```

Delegated workflows may also write bounded sandbox outputs under `sandbox/runs/`.

## Success criteria

A dogfood run is considered passed only when all delegated safe workflow steps return success.

A passed dogfood report is still evidence, not permission. Human review remains required before release closure.

## Command

```powershell
python .\tools\dogfood\run_dogfood_mission_suite.py `
  --repo-root "." `
  --sandbox-root ".\sandbox" `
  --run-id "dogfood-smoke"
```

## Review requirement

Before using this suite as pre-1.0 evidence, review:

- the generated dogfood report;
- delegated sandbox run reports;
- Git readiness output;
- adapter gate report;
- private-data grep results;
- current roadmap and release notes.
