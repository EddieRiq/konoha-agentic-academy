# End-to-End Mission Workflow Review Scroll

## Purpose

Review an end-to-end dry-run mission workflow before treating the result as valid evidence.

## Scope

This Scroll reviews:

- workflow command inputs;
- sandbox run id safety;
- project config validation evidence;
- runtime runner result;
- runtime package validation;
- runtime package inspection;
- registry visibility;
- public repo inspection;
- mission workflow report;
- non-execution boundaries.

## Required artifacts

A reviewer should verify:

```text
sandbox/runs/<run_id>/sandbox_run_manifest.json
sandbox/runs/<run_id>/runtime_package.json
sandbox/runs/<run_id>/runtime_run_summary.json
sandbox/runs/<run_id>/mission_workflow_report.json
```

## Checklist

- [ ] The run id does not contain path traversal or separators.
- [ ] The workflow wrote outputs only inside the sandbox run.
- [ ] The runtime runner passed.
- [ ] The runtime package validator passed.
- [ ] The runtime package inspector passed.
- [ ] The runtime registry can see the run.
- [ ] Public repo inspection passed or was explicitly skipped.
- [ ] The workflow report records all delegated steps.
- [ ] The report declares execution as blocked.
- [ ] The report declares Git operations, commits, and pushes as blocked.
- [ ] The report declares adapter execution as blocked.
- [ ] The report declares private context access as blocked.
- [ ] No approval gate was bypassed.

## Blockers

Block the workflow if:

- any required package artifact is missing;
- validation or inspection failed;
- any path escapes the sandbox;
- the workflow attempted to write outside the sandbox run;
- the workflow attempted arbitrary shell execution;
- private context was accessed;
- Git write operations were attempted;
- adapter execution was attempted.

## Non-authority rule

A passed workflow report is evidence of dry-run coherence only. It does not authorize execution, repository apply, Git staging, Git commit, Git push, adapter calls, or private context access.
