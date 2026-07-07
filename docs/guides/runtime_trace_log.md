# Runtime Trace Log

Status: documentation-first baseline.

## Purpose

The Runtime Trace Log defines how Konoha records dry-run runtime planning steps in a structured, reviewable, and audit-friendly way.

A trace log helps reviewers understand:

- what the runtime skeleton considered;
- which inputs were used;
- which boundaries were checked;
- which decisions were proposed;
- which blockers or stop conditions were detected;
- which evidence should be attached later.

The trace log is not an execution engine.

## Core rule

A trace record describes what was planned, checked, proposed, or blocked.

It does not authorize execution.

## Boundary

This guide does not introduce:

- shell command execution;
- filesystem mutation;
- Git operations;
- automatic adapter calls;
- automatic model routing;
- automatic private context access;
- autonomous approval;
- background execution.

Every trace entry must remain compatible with the dry-run-only runtime skeleton.

## Relationship to other runtime artifacts

The Runtime Trace Log should reference, but not replace:

- Mission Intake;
- Dry-Run Execution Plan;
- Adapter Invocation Stub;
- Evidence Collection Stub;
- Runtime State;
- Runtime Validation Checklist;
- Runtime Validation Report;
- Model Routing Decision;
- Context Budget;
- Token Budget Enforcement.

The trace log is the chronological audit layer across those artifacts.

## Trace principles

### 1. Append-only by default

A trace log should be treated as append-only during a mission.

Corrections should be added as new trace entries instead of silently rewriting prior entries.

### 2. Evidence before claims

Trace entries should cite the artifact, source, checklist item, or user instruction that supports the recorded event.

When evidence is missing, the trace entry must say so.

### 3. Decisions are proposals unless approved

A trace entry may record a proposed decision.

It must not present proposed actions as approved actions unless user approval or an explicit authorized gate is documented.

### 4. Summaries are not truth

A trace entry may summarize a source, but the source remains authoritative.

If a capsule, summary, or extracted context conflicts with source doctrine, the source doctrine wins.

### 5. Stop conditions must be visible

If a mission reaches a boundary, blocker, ambiguity, missing approval, missing evidence, token budget hard stop, stale capsule, or private context issue, the trace log must record it clearly.

## Minimum trace fields

Each trace entry should include:

```text
trace_id:
timestamp:
mission_id:
phase:
event_type:
actor_role:
artifact_reference:
input_reference:
decision_or_observation:
evidence:
boundary_check:
status:
next_required_action:
review_required:
```

## Recommended phases

Use one of these phase names unless a mission defines a stricter local taxonomy:

```text
mission_intake
context_selection
model_routing
token_budgeting
planning
adapter_stub_preparation
evidence_stub_preparation
validation
review
revision
closure
blocked
```

## Recommended event types

```text
intake_received
assumption_declared
context_source_selected
context_source_rejected
context_capsule_used
context_capsule_blocked
model_tier_proposed
model_tier_rejected
token_budget_set
token_budget_warning
token_budget_hard_stop
plan_step_added
plan_step_revised
adapter_stub_created
evidence_requirement_added
validation_check_passed
validation_check_failed
review_requested
review_blocked
user_approval_recorded
user_approval_missing
stop_condition_detected
closure_ready
```

## Status values

```text
recorded
proposed
validated
needs_revision
blocked
approved_by_user
rejected
superseded
```

## Actor roles

Trace entries should use role-level labels, not hidden model assumptions.

Examples:

```text
Hokage
Local Kage
Kagebunshin
Jounin
Shikamaru
User
Adapter Stub
Clerk
```

If a model generated a draft, the trace may record the assigned tier, but model identity does not imply permission.

## Boundary checks

Each relevant trace entry should answer:

```text
Was this dry-run only?
Was execution avoided?
Was file mutation avoided?
Was Git mutation avoided?
Was private context avoided unless explicitly authorized?
Was model routing documented?
Was token budget respected?
Was evidence attached or marked missing?
Was approval required?
Was approval present?
```

## Stop conditions

The trace log must mark a mission as blocked when:

- the Mission Charter is missing or ambiguous;
- approval is missing for a sensitive or mutating action;
- private context is requested without authorization;
- a context capsule is stale or unsupported;
- token budget hard stop is reached;
- model tier sufficiency is not demonstrated;
- evidence is missing for a material claim;
- an adapter stub implies real execution;
- the runtime state contradicts the dry-run boundary.

## Trace correction protocol

If a trace entry is wrong:

1. Add a new entry with `event_type: plan_step_revised` or `event_type: assumption_declared`.
2. Reference the incorrect or superseded `trace_id`.
3. Explain the correction.
4. Mark the previous entry as superseded only if the log format supports status updates.
5. Preserve the audit trail.

## Completion rule

A mission is not ready for closure just because a trace log exists.

Closure requires:

- runtime validation;
- review outcome;
- evidence package;
- unresolved blocker review;
- user-facing teachback when applicable;
- user approval where required.
