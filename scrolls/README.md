# Scrolls

Scrolls are reusable, activatable workflows that guide agent behavior for a specific kind of mission.

A Scroll is not general doctrine. Doctrine defines what agents must always respect. A Scroll defines how an agent should perform a bounded task when that Scroll is selected by the Hokage and allowed by the Mission Charter.

## Core rule

A Scroll may guide execution, but it may not override Konoha Laws, Safety Policy, Context Policy, Approval Policy, Review Policy, Mission Charter boundaries, or local Village rules.

If a Scroll conflicts with higher doctrine, the Scroll loses.

A Scroll is not permission.

## Current repository layout

The current public repository uses a simple MVP layout:

```text
scrolls/
  repo_review_scroll.md
  documentation_review_scroll.md
  mission_planning_scroll.md
  code_change_scroll.md
  code_review_scroll.md
  python_code_review_scroll.md
  ...
```

The repository also contains placeholder category folders for future organization:

```text
scrolls/coding/
scrolls/data-engineering/
scrolls/research/
scrolls/security/
scrolls/writing/
```

Flat `scrolls/*.md` files are valid during the early phase.

A mature Scroll may later move into a nested structure if it needs examples, tests, assets, or scripts:

```text
scrolls/<clan-or-domain>/<scroll-name>/
  SCROLL.md
  examples/
  tests/
  assets/
  scripts/
  README.md
```

Moving Scrolls changes paths and documentation references. It requires a Mission Charter and review.

## Current public Scrolls

### Mission and planning

```text
scrolls/mission_planning_scroll.md
scrolls/repo_review_scroll.md
scrolls/documentation_review_scroll.md
```

### Coding and engineering

```text
scrolls/code_change_scroll.md
scrolls/code_review_scroll.md
scrolls/python_code_review_scroll.md
scrolls/python_project_scroll.md
scrolls/refactor_scroll.md
scrolls/test_first_scroll.md
scrolls/error_triage_scroll.md
scrolls/dependency_review_scroll.md
scrolls/git_safety_scroll.md
```

### Local context, memory, and learning

```text
scrolls/local_context_scroll.md
scrolls/memory_review_scroll.md
scrolls/learning_capture_scroll.md
scrolls/private_literature_extraction_scroll.md
scrolls/doctrine_update_scroll.md
```

### Tools, adapters, and dependencies

```text
scrolls/tool_review_scroll.md
scrolls/adapter_review_scroll.md
scrolls/dependency_review_scroll.md
```

### Publication and release

```text
scrolls/sensitive_data_review_scroll.md
scrolls/publication_safety_scroll.md
scrolls/release_readiness_scroll.md
scrolls/release_notes_scroll.md
scrolls/changelog_maintenance_scroll.md
```

### Teachback

```text
scrolls/teachback_scroll.md
```

## What a Scroll is

A Scroll is a reusable workflow, capability, checklist, or operating pattern.

Examples:

```text
- repository exploration;
- code change;
- code review;
- Python project review;
- systematic debugging;
- dependency review;
- sensitive data review;
- local context handling;
- documentation review;
- release readiness;
- learning capture.
```

A Scroll should help an agent do one job clearly.

## What a Scroll is not

A Scroll is not:

```text
- a law;
- a Mission Charter;
- a full project context;
- a memory entry;
- a personality file;
- a place to hide assumptions;
- permission to execute actions;
- proof that a task is complete.
```

## Required fields

Every Scroll should define:

```yaml
name:
version:
status: draft | active | deprecated | archived
language:
clan:
purpose:
activation_triggers:
allowed_tasks:
forbidden_tasks:
required_inputs:
outputs:
risk_level: low | medium | high | critical
review_level: none | clerk | jounin | kage_summit
requires_hokage_approval: true | false
requires_human_approval: true | false
```

For early Markdown Scrolls, these fields may be represented as prose sections instead of YAML, as long as the meaning is explicit.

## Required sections

Every Scroll should include:

```text
# <Scroll name>

## Purpose
## Activation triggers
## Required inputs
## Allowed tasks
## Forbidden tasks
## Workflow
## Evidence requirements
## Stop-and-ask triggers
## Review requirements
## Outputs
## Violations
```

## Activation

A Scroll becomes active for a mission only when:

```text
- the Hokage selects it;
- the Mission Charter allows it;
- required inputs are available;
- required approvals are in place;
- safety constraints are satisfied.
```

The existence of a Scroll in the repository does not authorize its use.

## Scrolls and coding work

Coding work should use the relevant Clan and Scroll combination.

Example for a Python code change:

```text
Read:
AGENTS.md
core/laws/KONOHA_LAWS.md
protocols/mission-charter/mission_charter.md
protocols/safety/safety_policy.md
clans/software-engineering/README.md
clans/python/README.md
scrolls/code_change_scroll.md
scrolls/python_project_scroll.md

Review with:
scrolls/code_review_scroll.md
scrolls/python_code_review_scroll.md
```

Local project rules may add constraints through an Allied Village, but they may not weaken Academy rules.

## Scrolls and private literature

Private literature is local evidence, not public doctrine.

A Scroll may define how to extract principles from private literature, but it may not copy protected content into the public repo.

Use:

```text
scrolls/private_literature_extraction_scroll.md
docs/guides/private_literature_library.md
```

Only distilled, license-safe, user-approved learning may be promoted.

## Scrolls and local Villages

Local Villages may define local Scrolls or local overrides.

Local overrides may specialize:

```text
- project paths;
- commands;
- tools;
- coding conventions;
- data constraints;
- review rubrics;
- local memory usage.
```

Local overrides may not weaken:

```text
- safety;
- approval;
- context;
- review;
- teachback;
- learning;
- publication boundaries.
```

## Importing external Scrolls

External Scrolls are untrusted by default.

Before a Scroll from outside the repository is used, it must be reviewed for:

```text
- source;
- license;
- scope;
- hidden permissions;
- tool calls;
- network access;
- file access;
- prompt injection risk;
- data exposure risk;
- doctrine conflicts.
```

The Marketplace policy governs external discovery and import.

## Evals

Behavior should be tested before it is trusted.

Scroll eval templates live in:

```text
evals/templates/eval_case_template.md
evals/templates/scroll_eval_template.md
```

A high-risk or behavior-changing Scroll should have evals before it is marked active.

## Violations

Violations include:

```text
- using a Scroll outside its scope;
- treating a Scroll as permission;
- hiding assumptions inside a Scroll;
- modifying Scroll doctrine without approval;
- importing external Scrolls without review;
- claiming a Scroll succeeded without evidence;
- lowering review requirements through a Scroll;
- storing sensitive local context in a public Scroll.
```

## Completion checklist for a Scroll

A Scroll is ready for active use only when:

```text
- purpose is clear;
- activation triggers are explicit;
- required inputs are listed;
- forbidden tasks are listed;
- workflow is actionable;
- evidence requirements are defined;
- stop-and-ask triggers are defined;
- review level is defined;
- examples exist or are intentionally deferred;
- related doctrine is referenced;
- evals exist when risk requires them;
- Shikamaru drafted or approved the Markdown;
- user approved the behavior if it affects doctrine.
```

## Local Village bootstrap

- local_village_bootstrap_scroll.md: creates a local Allied Village from public templates while preserving the public/private boundary.

## Local knowledge ingestion

- `local_knowledge_ingestion_scroll.md`: guides local ingestion of private knowledge sources without publishing source content or weakening doctrine.

## Adapter contract review

- `adapter_contract_review_scroll.md`: reviews adapter manifests, capabilities, and safety boundaries before implementation.

## Adapter permission review

- `adapter_permission_review_scroll.md`: reviews adapter permissions before command, patch, release, or private-context access.

## Adapter invocation review

- `adapter_invocation_review_scroll.md`: reviews adapter invocation requests before execution, delegation, or result acceptance.

## Adapter execution gate review

- `adapter_execution_gate_review_scroll.md`: reviews whether an adapter execution request may proceed beyond dry-run or propose-only mode.

## Adapter evidence review

- `adapter_evidence_review_scroll.md`: reviews whether adapter evidence is complete, safe, and sufficient.

## Adapter dry-run review

- `adapter_dry_run_review_scroll.md`: reviews dry-run requests and results before approval to execute.

## Adapter runtime boundary review

- `adapter_runtime_boundary_review_scroll.md`: reviews whether proposed runtime work respects the adapter execution boundary.

## Evaluation review

- `evaluation_review_scroll.md`: reviews eval cases for clarity, safety coverage, expected behavior, and evidence requirements.

## Eval result review

- `eval_result_review_scroll.md`: reviews eval results for evidence, reproducibility, safety, and pass/fail justification.

## Eval runner boundary review

- `eval_runner_boundary_review_scroll.md`: reviews whether proposed eval runner work respects safety, privacy, reproducibility, and non-execution boundaries.

## Runtime planning review

- `runtime_planning_review_scroll.md`: reviews runtime plans before implementation, focusing on safety, boundaries, evidence, rollback, and non-autonomy.

## Command runner boundary review

- `command_runner_boundary_review_scroll.md`: reviews proposed command runner work before implementation or use.

## Filesystem mutation boundary review

- `filesystem_mutation_boundary_review_scroll.md`: reviews proposed filesystem mutation behavior before implementation or use.

## Git operation boundary review

- `git_operation_boundary_review_scroll.md`: reviews proposed Git operation behavior before implementation or use.

## Rollback boundary review

- `rollback_boundary_review_scroll.md`: reviews rollback readiness before risky changes, reversions, restores, or recovery actions.

## Runtime lifecycle review

- `runtime_lifecycle_review_scroll.md`: reviews runtime lifecycle plans before implementation or execution.

## Runtime audit review

- `runtime_audit_review_scroll.md`: reviews runtime audit checklists before release, runtime proposal, or implementation.

## Model routing and context budget review

- `model_routing_review_scroll.md`: reviews model tier choice, capability sufficiency, escalation triggers, and cost-quality tradeoffs.
- `context_budget_review_scroll.md`: reviews context intake plans, capsule use, source loading, and token budget discipline.

## Model tier review

- `model_tier_review_scroll.md`: reviews model tier assignment, sufficiency, escalation triggers, and demotion evidence.

## Context capsule lifecycle review

- `context_capsule_lifecycle_review_scroll.md`: reviews capsule manifests, source hashes, refresh reports, stale states, and authority boundaries.

## Token budget enforcement review

- `token_budget_enforcement_review_scroll.md`: reviews token budgets, overages, hard stops, and cost-quality evidence.

## Runtime dry-run review

- `runtime_dry_run_review_scroll.md`: reviews dry-run runtime plans, adapter stubs, evidence stubs, state boundaries, and execution blockers.

## Runtime validation review

- `runtime_validation_review_scroll.md`: reviews runtime validation checklists, validation reports, blockers, revisions, and dry-run readiness.

## Runtime trace review

- `runtime_trace_review_scroll.md`: reviews runtime trace logs, trace events, blockers, evidence references, approvals, and supersession records.

## Runtime package review

- `runtime_package_review_scroll.md`: reviews runtime package manifests, package indexes, closure records, trace logs, validation reports, and execution blockers.
