# Hokage Planner Loop

The Hokage Planner Loop turns a Mission Workspace and a gated model output into a mission-local plan proposal.

It is planning only. It does not execute mission actions.

## Flow

```text
Mission Workspace
-> dry-run sandbox run
-> Real Model Invocation Gate
-> model output evidence
-> Hokage Plan Proposal
-> planner loop report
-> Human Approval Console review
```

## Core rules

```text
A valid model request plan is not permission to call a model.
Model inference is never permission.
Model output is evidence only.
A plan proposal is not permission to execute.
```

## Outputs

The planner loop may write:

- `missions/<mission_id>/plans/<run_id>_hokage_plan_proposal.md`
- `missions/<mission_id>/reports/<run_id>_hokage_planner_loop_report.json`
- `sandbox/runs/<run_id>/hokage_planner_loop_report.json`
- delegated model outputs under `sandbox/runs/<run_id>/model_outputs/`

## Preview mode

Without `--confirm-invocation`, the planner loop runs in preview mode. It prepares the sandbox run and previews the model invocation gate but does not write a plan proposal.

## Confirmed invocation

Confirmed invocation requires:

- `--confirm-invocation`
- exact token `INVOKE_REAL_MODEL`
- a valid model invocation contract
- a valid request plan
- no private context blockers
- `--allow-network` when the delegated model gate requires network access

## Non-authority boundary

The Hokage Planner Loop may not:

- execute mission actions;
- execute arbitrary shell commands;
- invoke tools from model output;
- apply files to the repository;
- stage files;
- create commits;
- push changes;
- clean or reset files;
- access private Village context;
- close missions;
- treat model output as permission.

## Human review

Every plan proposal is `review_required`. Downstream transitions must be recorded through the Human Approval Console CLI.
