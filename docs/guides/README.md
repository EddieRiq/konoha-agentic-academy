# Guides

This folder contains practical walkthroughs for using Konoha Agentic Academy.

Guides explain how to apply doctrine. They do not override doctrine.

## Core rule

Guides teach usage.

They do not grant permission.

## Recommended reading order

For a first user:

```text
docs/guides/first_mission_walkthrough.md
docs/guides/local_village_bootstrap.md
docs/guides/private_literature_library.md
docs/guides/agentic_coding_loop.md
docs/guides/repository_audit_checklist.md
```

## Guide types

Guides may cover:

- first mission flow;
- Local Village bootstrap;
- private literature management;
- coding and review loops;
- repository audits;
- release preparation;
- contribution workflows.

## Safety

Guides must not include:

- secrets;
- private paths that identify a real local setup unless clearly generic;
- customer data;
- copyrighted content copied from private literature;
- commands that bypass approval;
- instructions that weaken Academy rules.

## Maintenance

When a guide changes agent behavior, check whether the change belongs in:

- a Scroll;
- a Clan;
- a protocol;
- AGENTS.md;
- local Village doctrine.

Do not hide doctrine changes inside guides.

- [Public/private boundary](public_private_boundary.md): explains what can be public, what must stay local, and how agents must handle private context.

## Local knowledge

- `local_knowledge_ingestion.md`: safe local workflow for turning private knowledge sources into local notes, principle cards, and learning proposals.

## Adapter contracts

- `adapter_contracts.md`: public guide for defining safe adapter contracts before executable integrations exist.

## Adapter permissions

- `adapter_permission_matrix.md`: defines adapter permission levels, authorization boundaries, and stop conditions.

## Adapter invocation

- `adapter_invocation_contract.md`: defines controlled request and result envelopes for adapter invocation.

## Adapter execution gate

- `adapter_execution_gate.md`: defines when an adapter invocation may move from dry-run or propose-only into execution.

## Adapter evidence

- `adapter_evidence_pack.md`: defines evidence requirements before, during, and after adapter invocation.

## Adapter dry-run protocol

- `adapter_dry_run_protocol.md`: defines how adapters simulate work before any file mutation, command execution, Git operation, or release action.

## Adapter runtime boundary

- `adapter_runtime_boundary.md`: defines the boundary between declarative adapter doctrine and future executable runtime implementation.

## Evaluation baseline

- `evaluation_baseline.md`: defines the documentation-first evaluation baseline for behavior, safety, and adapter checks.

## Eval runner boundary

- `eval_runner_boundary.md`: defines the boundary between manual/documentation-first evals and future automated eval runners.

## Runtime planning

- `runtime_planning_baseline.md`: defines planning boundaries for future runtime architecture before executable implementation.

## Command runner boundary

- `command_runner_boundary.md`: defines the safety boundary for any future component that may execute commands.

## Filesystem mutation boundary

- `filesystem_mutation_boundary.md`: defines the safety boundary for future file creation, editing, movement, overwrite, and deletion behavior.

## Git operation boundary

- `git_operation_boundary.md`: defines the safety boundary for future Git operations such as add, commit, push, tags, releases, branches, and history changes.

## Rollback boundary

- `rollback_boundary.md`: defines rollback evidence, readiness, approval, and stop conditions before reversible or risky runtime behavior.

## Runtime lifecycle

- `runtime_lifecycle.md`: defines the planned runtime lifecycle from Mission Charter through closure without implementing execution.

## Runtime audit checklist

- `runtime_audit_checklist.md`: checklist for auditing runtime planning boundaries before release or executable implementation.

## Model routing and token governance

- `model_routing_and_token_governance.md`: defines model tiering, context budgets, token governance, capability review, and escalation rules.
- `context_capsules.md`: defines validated summarized context packs for reducing repeated instruction intake.
- `session_resource_probe.md`: defines how a session may check available model/token resources without inventing unavailable metrics.

## Model tier matrix

- `model_tier_matrix.md`: defines model tiers, task suitability, escalation, demotion, and capability review rules.

## Context capsule lifecycle

- `context_capsule_lifecycle.md`: defines how context capsules are created, reviewed, approved, invalidated, refreshed, and blocked.

## Token budget enforcement

- `token_budget_enforcement.md`: defines soft budgets, hard stops, overage justification, escalation, and token efficiency review.

## First runtime skeleton

- `first_runtime_skeleton.md`: defines the first dry-run-only runtime skeleton, including mission intake, planning, adapter stubs, evidence stubs, and runtime state.

## Runtime validation checklist

- `runtime_validation_checklist.md`: defines validation criteria for dry-run runtime packages, including authority, context, model routing, token budget, evidence, and privacy boundaries.

## Runtime trace log

- `runtime_trace_log.md`: defines append-only dry-run runtime trace logging for planning steps, blockers, evidence, approvals, and supersession.

## Runtime package assembly

- `runtime_package_assembly.md`: defines how dry-run runtime artifacts are assembled into a complete, reviewable package.

## Dry-run mission examples

- `dry_run_mission_examples.md`: defines public, generic dry-run mission examples and the safety rules for publishing them.

## Runtime contract and validator

- `runtime_contract_and_validator.md`: defines the runtime contract schemas and the first read-only dry-run package validator.

## Dry-run package builder

- `dry_run_package_builder.md`: defines the dry-run package builder CLI, output boundaries, validation flow, and non-execution rules.

## Read-only runtime inspector

- `read_only_runtime_inspector.md`: defines the read-only runtime inspector, package coherence checks, boundary checks, report output, and non-mutation rules.

## Local sandbox boundary

- `local_sandbox_boundary.md`: defines the local sandbox boundary, allowed sandbox writes, path safety checks, run manifests, and non-execution rules.

## Dry-run runtime runner

- `dry_run_runtime_runner.md`: defines the dry-run runtime runner, orchestration flow, sandbox-only outputs, run summaries, and non-execution rules.

## Runtime run registry

- `runtime_run_registry.md`: defines the read-only runtime run registry, run states, blockers, registry reports, and non-mutation rules.

## Read-only repo inspector

- `read_only_repo_inspector.md`: defines the read-only repo inspector, public scan boundary, findings, safety checks, and non-mutation rules.

## Controlled artifact writer

- `controlled_artifact_writer.md`: defines the controlled sandbox artifact writer, proposed outputs, apply plans, write reports, path safety, and non-apply rules.

## Human-approved apply plan

- `human_approved_apply_plan.md`: defines the human-approved apply plan prototype, preview mode, explicit approval token, allowlisted destinations, apply reports, and non-execution rules.

## Git read-only gate

- `git_read_only_gate.md`: defines the Git read-only gate, allowed Git inspection commands, readiness reports, dirty-state handling, and no-write rules.

## Git staging gate

- `git_staging_gate.md`: defines the Git staging gate, explicit path allowlists, approval token, preview mode, staging reports, and no-commit/no-push rules.

## Unified CLI entrypoint

- `unified_cli_entrypoint.md`: defines the unified CLI entrypoint, command groups, allowlisted dispatch, delegated tool boundaries, and non-authority rules.

## Project config and policy contract

- `project_config_and_policy_contract.md`: defines the project config contract, sandbox policy, allowlists, blocked private paths, approval tokens, and read-only config validation.

## End-to-end dry-run mission workflow

- `end_to_end_dry_run_mission_workflow.md`: defines the end-to-end dry-run mission workflow, delegated toolchain, workflow report, sandbox outputs, and non-execution boundaries.

## Proposed artifact workflow

- `proposed_artifact_workflow.md`: defines the proposed artifact workflow, sandbox proposed outputs, apply preview, optional approved apply, workflow report, and non-execution boundaries.

## Git commit gate

- `git_commit_gate.md`: defines the Git commit gate, staged-file validation, approval token, commit message policy, preview mode, and no-push/no-stage rules.

## Integrated tests and CI

- `integrated_tests_and_ci.md`: defines the integrated smoke-test runner, CI workflow, integrated reports, safety checks, and non-execution boundaries.
