# Runtime Validation Checklist

Status: documentation-first baseline  
Scope: public repository doctrine and runtime planning  
Runtime mode: dry-run only

## Purpose

The Runtime Validation Checklist defines how Konoha reviews a dry-run runtime package before any future execution capability is considered.

It validates whether a Mission Charter has been transformed into a coherent, bounded, reviewable runtime plan.

This checklist does not execute commands, mutate files, invoke adapters, access private context, perform Git operations, or authorize execution.

## Core principle

Passing validation means the dry-run package is internally consistent.

It does not mean the mission is approved for execution.

Execution, mutation, private context access, Git operations, release actions, and doctrine changes still require explicit authorization through their own gates.

## What must be validated

A runtime dry-run package should include, at minimum:

- Mission Intake;
- Dry-Run Execution Plan;
- Adapter Invocation Stub, when adapter work is proposed;
- Evidence Collection Stub;
- Runtime State;
- Model Routing Decision, when model selection matters;
- Context Budget, when non-trivial context is loaded;
- Token Budget Enforcement, when budget limits apply.

Missing required inputs should stop validation.

## Validation levels

### Valid

The package is complete, bounded, and consistent with the Mission Charter.

A valid package may proceed to human review or a later approval gate, but it still does not authorize execution.

### Conditional

The package is mostly coherent but has open questions, weak evidence, unclear scope, or non-blocking inconsistencies.

A conditional package may be revised, but should not be treated as ready.

### Blocked

The package contains a safety, authority, scope, privacy, evidence, or technical blocker.

A blocked package must stop until the blocker is resolved and reviewed again.

## Required validation domains

### 1. Mission alignment

The runtime package must preserve the Mission Charter.

Reviewers should confirm:

- the mission objective is explicit;
- the requested output is clear;
- the runtime plan does not expand the mission;
- assumptions are listed instead of hidden;
- unresolved ambiguity is marked as a question or blocker.

If the runtime plan changes the mission, validation is blocked.

### 2. Authority boundary

The runtime package must distinguish capability from permission.

Reviewers should confirm that the plan does not treat any of the following as authorization:

- model confidence;
- adapter capability;
- passing validation;
- prior success;
- memory;
- context capsules;
- user intent inferred from conversation;
- a checklist entry marked complete.

If authority is inferred instead of explicit, validation is blocked.

### 3. Dry-run boundary

The first runtime skeleton is dry-run only.

Reviewers should confirm that the plan does not perform or request:

- shell command execution;
- file mutation;
- Git operation;
- dependency installation;
- network call;
- credential use;
- private context access;
- release creation;
- automated model routing;
- autonomous adapter invocation.

Commands may appear only as proposed commands, not executed commands.

### 4. Public/private boundary

The runtime package must not leak private Village content or local knowledge sources.

Reviewers should confirm:

- public artifacts remain generic;
- local Village paths are not required by public docs;
- private source text is not copied into public output;
- summaries do not disclose restricted content;
- private context access is not assumed;
- ignored paths remain ignored.

Any private leakage blocks validation.

### 5. Context boundary

Loaded context must be necessary and bounded.

Reviewers should confirm:

- the context sources are named;
- the reason for each source is stated;
- context capsules are marked with validity status;
- stale or unreviewed capsules are not treated as truth;
- full-source fallback is required when capsule sufficiency is uncertain.

Summaries support review, but they are not authority.

### 6. Model routing boundary

Model tier selection must be justified by task risk and capability evidence.

Reviewers should confirm:

- the selected tier is documented;
- cheaper sufficient tiers are considered when safe;
- escalation triggers are stated;
- demotion evidence is recorded when a lower tier is used;
- reviewer tier is separated from worker tier when needed;
- the model does not self-certify sufficiency.

Konoha optimizes for safe, sufficient intelligence, not maximum intelligence by default.

### 7. Token and resource boundary

Token budgets should be explicit when context or generation size is non-trivial.

Reviewers should confirm:

- intake budget is stated;
- work budget is stated;
- output budget is stated;
- review budget is stated when review is required;
- soft limits and hard stops are defined;
- overage requires justification;
- excessive budget use triggers routing or context review.

A mission that repeatedly exceeds budget should not be normalized without review.

### 8. Adapter stub boundary

Adapter invocation stubs must describe proposed calls without executing them.

Reviewers should confirm:

- adapter identity is explicit;
- requested capability is within the adapter contract;
- permission matrix is respected;
- inputs and expected outputs are documented;
- execution gate status is not bypassed;
- dry-run output is clearly separated from execution output.

If the adapter contract is missing or incompatible, validation is blocked.

### 9. Evidence boundary

Evidence collection must be planned before conclusions are accepted.

Reviewers should confirm:

- required evidence is listed;
- evidence sources are available or marked unavailable;
- expected evidence is not presented as collected evidence;
- missing evidence has an impact statement;
- validation results cite evidence, not assumptions.

No evidence, no acceptance.

### 10. Runtime state boundary

Runtime state must be descriptive, minimal, and auditable.

Reviewers should confirm:

- state transitions are explicit;
- status values are consistent;
- blockers are recorded;
- no hidden execution is implied;
- retry attempts are documented;
- final state matches validation outcome.

Runtime state describes planning. It does not authorize action.

## Stop conditions

Validation must stop if any of the following occur:

- Mission Charter is missing;
- user approval is required but absent;
- scope is ambiguous and material;
- plan expands beyond the approved mission;
- private content appears in public output;
- command execution is requested;
- file mutation is requested;
- Git operation is requested;
- adapter capability is treated as permission;
- model confidence is treated as permission;
- context capsule is stale or unreviewed and material to the decision;
- evidence is missing for a material claim;
- token budget hard stop is reached;
- rollback or recovery path is absent for a risky future action.

## Validation outcome

A runtime validation result must state one of:

- `valid_for_review`;
- `conditional_revision_required`;
- `blocked`.

The result must include:

- validation scope;
- inputs reviewed;
- checklist result;
- blockers;
- unresolved questions;
- evidence reviewed;
- recommended next action.

## Relationship to later runtime work

This checklist prepares Konoha for future runtime implementation without granting execution authority.

Future runtime implementation must still preserve:

- explicit Mission Charter;
- dry-run before execution;
- adapter contracts;
- execution gates;
- evidence packs;
- model routing governance;
- token budget enforcement;
- rollback planning;
- human approval for sensitive actions.

## Non-goals

This guide does not define:

- an executable runtime engine;
- a command runner;
- an adapter SDK;
- a persistence layer;
- automatic validation;
- automatic routing;
- automatic approval;
- private context ingestion.

## Minimal reviewer question

Before accepting a dry-run package, the reviewer should be able to answer:

> What exactly would happen, what evidence supports it, what boundaries prevent overreach, and what still requires explicit approval?
