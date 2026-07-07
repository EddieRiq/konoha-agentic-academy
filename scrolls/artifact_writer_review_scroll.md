# Artifact Writer Review Scroll

Status: review Scroll.

Use this Scroll to review the Controlled Artifact Writer inside Sandbox.

## Review target

Review:

```text
tools/artifact_writer/write_sandbox_artifact.py
tests/artifact_writer/
schemas/runtime/sandbox_apply_plan.schema.json
schemas/runtime/sandbox_artifact_write_report.schema.json
examples/sandbox_runs/sandbox_apply_plan.example.json
docs/guides/controlled_artifact_writer.md
```

## Required checks

Confirm that the writer:

- writes only inside `sandbox/runs/<run_id>/proposed_outputs/`;
- requires an existing `sandbox_run_manifest.json`;
- rejects unsafe run ids;
- rejects path traversal;
- rejects absolute artifact paths;
- rejects unsupported executable extensions;
- validates JSON artifact content;
- creates or updates `apply_plan.json`;
- creates `artifact_write_report.json`;
- keeps repository apply blocked;
- requires human approval for any future apply.

## Safety checks

Confirm that the writer does not:

- execute shell commands;
- perform Git operations;
- invoke adapters;
- use network access;
- access private Village context;
- write outside the sandbox run;
- delete files;
- apply files to the repository.

## Evidence expected

A reviewer should see:

- passing unit tests;
- a successful smoke test writing a sandbox artifact;
- a failed path traversal test;
- a clean Git status after smoke cleanup;
- no private content findings.

## Review outcome

Use one of:

```text
approved_for_dry_run_use
revision_required
blocked
```

Approval for dry-run use does not authorize repository mutation or mission execution.
