# Runtime Package Assembly

## Status

Documentation-first baseline.

This guide defines how Konoha assembles a dry-run runtime package from existing mission planning artifacts.

It does not define executable runtime behavior.

## Purpose

A runtime package is a reviewable bundle that connects a Mission Charter to dry-run planning artifacts, validation outputs, trace logs, and closure notes.

The package exists to make runtime planning auditable before any future execution capability is considered.

## Core rule

A runtime package may organize evidence, plans, and review records.

It does not authorize execution.

A complete package means that the mission is ready for human review, not that any command, file mutation, Git operation, adapter execution, model escalation, or private context access is permitted.

## Required package artifacts

A complete dry-run runtime package should reference:

- Mission Charter or approved mission scope.
- Mission intake object.
- Dry-run execution plan.
- Adapter invocation stubs.
- Evidence collection stubs.
- Runtime state record.
- Runtime validation checklist.
- Runtime validation report.
- Runtime trace log.
- Runtime trace events.
- Model routing decision, when model choice matters.
- Context budget, when source/context intake matters.
- Token usage report, when usage was estimated or measured.
- Capability review, when a lower or different model tier was used.
- Review Scroll outputs.
- Closure notes and teachback status.

## Package assembly phases

### 1. Intake binding

The package must bind the mission to its approved scope.

Required checks:

- The Mission Charter exists.
- The requested work matches the approved scope.
- Any ambiguity is listed as a blocker.
- The package does not infer missing authority.
- Private context access is explicitly declared or blocked.

### 2. Planning bundle

The package must include the dry-run execution plan.

The plan must document:

- intended steps;
- expected inputs;
- expected outputs;
- non-goals;
- stop conditions;
- required approvals;
- adapter stubs, if any;
- evidence stubs, if any;
- rollback considerations, if relevant.

### 3. Governance bundle

The package must include governance records when relevant:

- model tier assignment;
- model routing decision;
- context budget;
- token budget enforcement record;
- capsule manifest;
- capsule refresh report;
- capability review.

These records are not optional when the mission depends on model selection, context compression, private/local knowledge, or token-sensitive execution.

### 4. Validation bundle

The package must include validation results.

Possible outcomes:

- `valid_for_review`: the package can move to Jounin or human review.
- `conditional_revision_required`: the package needs specific revisions before review.
- `blocked`: the package cannot proceed.

Validation does not authorize execution.

### 5. Trace bundle

The package must include trace records for meaningful decisions.

Trace entries should show:

- what was planned;
- what was reviewed;
- what was blocked;
- what evidence was used;
- what was superseded;
- what remains unresolved.

The trace log should be append-only. Corrections should be made through supersession, not deletion.

### 6. Closure bundle

The package must include closure notes.

Closure must document:

- final package status;
- unresolved blockers;
- user-facing explanation;
- teachback readiness;
- whether the mission is ready for review only;
- whether a future execution gate is required.

## Package status values

Use one of the following status values:

- `draft`: package is incomplete.
- `ready_for_validation`: package has required artifacts but has not been validated.
- `revision_required`: validation or review found gaps.
- `blocked`: package cannot proceed.
- `ready_for_review`: package passed validation and can be reviewed.
- `reviewed_no_execution`: package was reviewed but no execution is authorized.
- `deprecated`: package was superseded by another package.

## Authority boundaries

A package may never be treated as authorization for:

- shell command execution;
- filesystem mutation;
- Git operations;
- adapter execution;
- private context access;
- doctrine changes;
- release publication;
- autonomous task expansion;
- model escalation without review;
- token overage without justification.

## Stop conditions

Stop and request review when:

- the Mission Charter is missing or ambiguous;
- the plan includes real execution;
- the package includes private or local paths not intended for public release;
- a capsule is stale or unverified;
- source evidence is missing;
- token budget is exceeded without justification;
- model capability is unproven;
- validation outcome is `blocked`;
- review requires human approval.

## Relationship to existing guides

This guide depends on:

- First Runtime Skeleton;
- Runtime Validation Checklist;
- Runtime Trace Log;
- Model Routing and Token Governance;
- Context Capsules;
- Context Capsule Lifecycle;
- Token Budget Enforcement;
- Adapter Invocation Contract;
- Evidence Pack;
- Runtime Lifecycle.

## Review requirement

A runtime package should be reviewed with the Runtime Package Review Scroll before it is considered ready for any future execution gate.

Passing package review means the package is coherent, auditable, and safe to discuss.

It still does not authorize execution.
