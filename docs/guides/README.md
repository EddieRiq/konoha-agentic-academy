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
