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

- `unified_cli_entrypoint.md`: defines the v3.2.6 canonical CLI, command registry, active/deprecated surfaces, delegated boundaries and non-authority rules.

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

## Mock adapter clerk interface

- `mock_adapter_clerk_interface.md`: defines the deterministic mock adapter, Clerk boundary, sandbox-only outputs, mock invocation reports, and no-real-adapter rules.

## Adapter invocation gate

- `adapter_invocation_gate_disabled_by_default.md`: defines the adapter invocation gate, disabled-by-default real adapter boundary, mock-only approval flow, sandbox outputs, and no-network rules.

## Dogfood mission suite

- `dogfood_mission_suite.md`: defines the dogfood mission suite, delegated safe workflow checks, report output, pre-1.0 evidence role, and non-authority boundaries.

## v1.0 release readiness

- `v1_release_readiness.md`: defines the v1.0 release-readiness checker, final stabilization evidence, stable release boundary, and non-authority rules.

## Product runtime bootstrap

- `product_runtime_bootstrap.md`: defines the product runtime bootstrap CLI, init, doctor, config validation, mission workspace creation, dry-run delegation, and non-authority boundaries.

## Mission workspace

- `mission_workspace.md`: defines the mission workspace structure, manifest, charter, approval log, validation flow, path safety rules, and non-authority boundaries.

## Human approval console CLI

- `human_approval_console_cli.md`: defines mission status, inspection, approval, rejection, approval events, evidence listing, report listing, tokens, and non-authority boundaries.

## Model provider contract

- `model_provider_contract.md`: defines model-provider request planning, provider allowlists, token and cost budgets, context-source rules, redaction requirements, and real-model invocation blockers.

## Real model invocation gate

- `real_model_invocation_gate.md`: defines explicitly approved model invocation, provider boundaries, network approval, credential handling, sandbox-only outputs, and non-authority rules.

## Hokage planner loop

- `hokage_planner_loop.md`: defines the planning-only Hokage loop, gated model evidence, plan proposals, planner reports, and model-output non-authority.

## Local Web UI Alpha

- `local_web_ui_alpha.md`: defines the localhost-only UI alpha, dashboard, missions, approvals, reports, system page, dependency boundary, safety model, and blocked actions.

## Controlled Tool Execution Gate

- `controlled_tool_execution_gate.md`: defines allowlisted internal tool execution, approval token, sandbox reports, blocked shell/network/Git/model/private-context actions, and evidence-only outputs.

## Human-in-the-loop Agent Runtime

- `human_in_loop_agent_runtime.md`: defines the human-in-the-loop agent runtime, delegated gates, planning evidence, controlled tool evidence, reports, approval requirements, and non-authority rules.

## v2.0 Integration, Memory and Mission Closure

- `integration_memory_and_mission_closure.md`: defines v2.0 integration, minimal Yamanaka memory, teachback, context packs, notification state, and mission closure boundaries.
- `teachback_protocol_gate.md`: defines structured Teachback levels, human evidence, source binding, clarification, skip policy and idempotent conflict handling.

## Notifications and UI State Escalation

- `notifications_and_ui_state_escalation.md`: defines mission notification states, UI escalation states, required human action, state reports, and no-new-authority boundaries.

## Asset Resolver and Local Visual Layer

- `asset_resolver_and_local_visual_layer.md`: defines logical UI asset resolution, local/user/public/text fallback tiers, public asset policy, private asset boundaries, and no-new-authority rules.

## Yamanaka Advanced Memory and Context Packs

- `yamanaka_advanced_memory_and_context_packs.md`: defines advanced Yamanaka memory capture, Obsidian-compatible notes, context packs, memory indexing, approval tokens, and non-authority boundaries.

## Scroll Lifecycle and Learning Proposals

- `scroll_lifecycle_and_learning_proposals.md`: defines Scroll learning proposals, review decisions, promotion plans, approval tokens, lifecycle states, and doctrine non-rewrite boundaries.

## Local Village Bootstrap and Hardware Profile

- `local_village_bootstrap_and_hardware_profile.md`: defines private Local Village bootstrap, read-only hardware profiling, local config, privacy boundaries, approval tokens, and non-authority rules.

## Unified Mission Runtime

- `unified_mission_runtime.md`: defines the v2.6 mission runtime spine, command proposal model, reports, notification state, optional memory note, approval tokens, and non-authority boundaries.

## Model Router and Token Economy

- `model_router_and_token_economy.md`: defines model runtime profiling, local/remote model routing, download planning, token usage ledgers, calibration, efficiency summaries, and non-authority boundaries.

## General Task Execution Workbench

- `general_task_execution_workbench.md`: defines the general task workbench, playbooks, command batches, evidence recording, verification checklists, rollback notes, and non-authority boundaries.

## Self-Review, Optimization and Git Operation Gate

- `self_review_optimization_and_git_operation_gate.md`: defines mission self-review, optimization plans, Git operation plans, stage/commit/push gates, approval tokens, and non-authority boundaries.

## Konoha Beta Runtime

- `konoha_beta_real_supervised_task_runtime.md`: defines v3.0 beta terminal runtime, Claude/Codex/Ollama adapters, approved command execution, token ledger, Git gates, and teachback closure.

## Local Model Bootstrap and Repo Audit

- `local_model_bootstrap_repo_audit_and_patch_flow.md`: defines local computer profiling, Ollama recommendation, approved model download, local model repo consistency audit, documentation patch planning, and Git gate handoff.

## Repo Audit Deterministic Guard

- `../roadmap/v3_0_2_repo_audit_deterministic_guard.md`: defines the v3.0.2 false-positive suppression guard for local model repository audits.

## Hokage Terminal Shell

- `hokage_terminal_shell.md`: defines the terminal-first SSH-friendly Hokage Shell with personas, ASCII mission panels, deterministic repo scan, local model audit handoff, event logs, and private Obsidian-compatible memory notes.

## Hokage Shell Review Panels

- `hokage_terminal_shell_review_panels.md`: defines review panels, Markdown step reports, detail viewer fallback, raw JSON/patch-plan views, and false-positive summary behavior.

## Sandbox Evidence Hygiene

- `sandbox_evidence_hygiene.md`: defines the public sandbox allowlist, local runtime evidence boundary and deterministic verification steps.

## Canonical Release Test Gate

- `canonical_release_test_gate.md`: defines deterministic suite discovery, continue-after-failure execution, aggregate results, sandbox-only reports and non-authority boundaries.

## Release Readiness and Closure Guard

- `release_readiness_and_closure_guard.md`: documents tested-commit evidence, release-state codes, read-only remote checks and separate publication gates.

## Hokage Shell Mission Continuity

- `hokage_shell_mission_continuity.md`: documents deterministic mission inventory, validated latest selection, resume snapshots and reentry boundaries.

## Hokage Terminal Operator Baseline

- `hokage_terminal_operator_baseline.md`: documents the read-only `status` command, operator states, terminal fallback and authority boundaries.

## Supervised Task Contract Validator

- `supervised_task_contract_validator.md`: documents the normalized pre-execution policy contract, readiness blockers and non-authorization boundaries.

## Supervised Task Evidence Bundle

- `supervised_task_evidence_bundle.md`: documents deterministic evidence coverage, hashes, states and human-review boundaries.

## Supervised Action Proposal

- `supervised_action_proposal.md`: documents proposal composition, evidence gates, argv boundaries, approvals, rollback and non-authority.

## Unified Supervised Release Gate

- `unified_supervised_release_gate.md`: documents the one-command release state machine, evidence reuse, explicit mutation tokens and minimal output.

## Supervised Release Recovery and Status

- `supervised_release_recovery_status.md`: documents local/remote read-only status, recovery states, stale evidence and reentry after closure.

## Package Installation Scope Guard

- `package_installation_scope_guard.md`: documents direct extraction scope, bounded helper scope, union validation and idempotent reentry.


## Repository consolidation and capability references

- `../reference/capability_matrix.md`: maps canonical commands to delegated components, mutation levels, network boundaries and approval requirements.
- `../reference/release_safety_boundaries.md`: separates product and maintainer surfaces and records package, release and public/private stop conditions.
- `../roadmap/v3_2_6_repository_consolidation_scope.md`: freezes the final `v3.2.x` consolidation scope and the `v3.3.0`/`v3.4.0` path.

## Installable Terminal Distribution

- `installable_terminal_distribution.md`: one-line managed installation and global `konoha`.
- `managed_install_upgrade_and_uninstall.md`: verified status, explicit-tag upgrade and recoverable uninstall.
- `supervised_package_to_release_wrapper.md`: package → tests → clean install → release → final status.
- `../roadmap/v3_3_0_installable_terminal_distribution_scope.md`: frozen v3.3.0 scope.

## Finished terminal product

- `finished_local_first_terminal_product.md`: installed product surface and safety boundaries.
- `quickstart_and_mission_journey.md`: first-run setup and supervised mission flow.
- [Conversational Hokage foundation](conversational_hokage_foundation.md)
- [Conversational Hokage actions](conversational_hokage_actions.md)
- [Conversational Hokage lifecycle](conversational_hokage_lifecycle.md)
- [Conversational Hokage real supervised audit](conversational_hokage_real_supervised_audit.md)
