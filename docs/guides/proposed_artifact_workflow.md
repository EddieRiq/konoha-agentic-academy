# Proposed Artifact Workflow

Status: pre-release / proposed-artifact workflow alpha.

## Purpose

The Proposed Artifact Workflow connects the dry-run runtime runner, controlled sandbox
artifact writer, and human-approved apply plan preview into one bounded workflow.

It is intended to make proposed outputs easier to generate and review without granting
new runtime authority.

## What it does

The workflow may:

- prepare a dry-run sandbox run through the runtime runner;
- write a proposed artifact inside `sandbox/runs/<run_id>/proposed_outputs/`;
- create or update the sandbox apply plan through the artifact writer;
- preview the apply plan through the human-approved apply gate;
- optionally delegate approved apply when `--confirm-apply` and the exact approval token are provided;
- write `proposed_artifact_workflow_report.json` inside the sandbox run.

## What it does not do

The workflow may not:

- execute mission actions;
- execute arbitrary shell commands;
- perform Git operations;
- invoke adapters;
- access private Village context;
- bypass apply-plan approval;
- bypass destination allowlists;
- authorize runtime actions.

## Required approval boundary

Repository apply is preview-only by default.

A confirmed apply requires:

- `--confirm-apply`;
- exact approval token `APPLY_SANDBOX_PLAN`;
- a valid sandbox apply plan;
- allowlisted destination paths enforced by the delegated apply-plan gate.

## Outputs

A successful run writes:

```text
sandbox/runs/<run_id>/
  runtime_package.json
  apply_plan.json
  artifact_write_report.json
  proposed_artifact_workflow_report.json
  proposed_outputs/
```

## Safety model

The workflow is an orchestrator. It does not implement new authority. It delegates to
existing bounded tools and preserves their approval gates and exit codes.

## Reviewer checklist

Reviewers should verify that:

- the run ID is safe;
- proposed outputs stay inside the sandbox run;
- intended repo paths are allowlisted;
- preview mode was used unless explicit apply approval is documented;
- no Git operation is performed;
- no private context is accessed;
- the workflow report records all delegated steps.
