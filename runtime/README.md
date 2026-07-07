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
