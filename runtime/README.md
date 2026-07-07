# Runtime

Status: planning-only.

This directory defines the public planning boundary for future Konoha runtime work.

It does not contain an executable runtime.

## Purpose

The runtime layer will eventually coordinate approved adapter invocations, evidence collection, execution gates, filesystem changes, Git operations, rollback records, and user-facing reports.

Until runtime readiness is explicitly approved, this directory is documentation-first only.

## Current boundary

The runtime may be discussed, designed, reviewed, and evaluated.

The runtime may not yet:

- execute commands;
- mutate files;
- call adapters automatically;
- perform Git operations;
- access local private Villages;
- create memory;
- publish releases;
- bypass Mission Charter requirements.

## Required upstream controls

Future runtime work must respect:

- `core/laws/KONOHA_LAWS.md`
- `core/conduct/AGENT_CONDUCT.md`
- `protocols/mission-charter/mission_charter.md`
- `protocols/approval/approval_policy.md`
- `protocols/safety/safety_policy.md`
- `docs/guides/adapter_contracts.md`
- `docs/guides/adapter_permission_matrix.md`
- `docs/guides/adapter_invocation_contract.md`
- `docs/guides/adapter_execution_gate.md`
- `docs/guides/adapter_evidence_pack.md`
- `docs/guides/adapter_dry_run_protocol.md`
- `docs/guides/adapter_runtime_boundary.md`
- `docs/guides/evaluation_baseline.md`
- `docs/guides/eval_runner_boundary.md`

## Runtime principle

Technical ability is not authority.

A future runtime may only act when the Mission Charter, adapter contract, permission matrix, dry-run result, execution gate, evidence pack, and user approval all align.

## Command runner boundary

- `templates/command_execution_request.template.md`: template for requesting command execution under explicit scope and approval.
- `templates/command_execution_result.template.md`: template for recording command execution result, evidence, output, and status.
- `templates/command_runner_readiness.template.md`: template for assessing whether command runner implementation is ready.

## Filesystem mutation boundary

- `templates/filesystem_mutation_request.template.md`: template for requesting file creation, modification, movement, rename, overwrite, or deletion.
- `templates/filesystem_mutation_result.template.md`: template for recording filesystem mutation evidence and outcome.
- `templates/filesystem_mutation_readiness.template.md`: template for assessing readiness before implementing filesystem mutation behavior.

## Git operation boundary

- `templates/git_operation_request.template.md`: template for requesting Git operations under explicit approval.
- `templates/git_operation_result.template.md`: template for recording Git operation evidence, output, and status.
- `templates/git_operation_readiness.template.md`: template for assessing readiness before implementing Git operation behavior.

## Rollback boundary

- `templates/rollback_request.template.md`: template for requesting a rollback, revert, restore, or recovery action.
- `templates/rollback_result.template.md`: template for recording rollback evidence, result, and residual risk.
- `templates/rollback_readiness.template.md`: template for assessing rollback readiness before risky runtime behavior.

## Runtime lifecycle

- `templates/runtime_lifecycle.template.md`: template for documenting the full runtime lifecycle from plan to closure.
- `templates/runtime_closure_report.template.md`: template for closing runtime work with evidence, validation, residual risk, and teachback.

## Runtime audit checklist

- `templates/runtime_audit_checklist.template.md`: template for auditing runtime planning before release or implementation.

## Model routing and token governance

- `templates/model_routing_decision.template.md`: template for documenting model tier choice, capability rationale, and escalation triggers.
- `templates/context_budget.template.md`: template for planning context intake, source loading, and budget limits.
- `templates/token_usage_report.template.md`: template for reporting estimated or measured token usage after a mission.

## Model tier governance

- `templates/model_tier_assignment.template.md`: template for assigning a model tier to a mission or task.
- `templates/capability_review.template.md`: template for reviewing whether a model tier was sufficient after execution or review.

## Context capsule lifecycle

- `templates/context_capsule_manifest.template.md`: template for declaring capsule sources, hashes, status, scope, and validity.
- `templates/context_capsule_refresh_report.template.md`: template for refreshing capsules when source doctrine changes.

## Token budget enforcement

- `templates/token_budget_enforcement.template.md`: template for defining soft limits, hard stops, overage rules, and escalation triggers.
- `templates/token_overage_review.template.md`: template for reviewing whether token overage was justified, avoidable, or caused by poor routing.
