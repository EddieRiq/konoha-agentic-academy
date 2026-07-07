# Runtime Dry-Run Review Scroll

Status: review Scroll.

## Purpose

This Scroll reviews whether a First Runtime Skeleton output is safe, scoped, dry-run only, and ready for the next reviewed step.

It must be used before treating any runtime skeleton output as acceptable evidence.

## Review boundary

This Scroll does not authorize:

- command execution;
- filesystem mutation;
- Git operations;
- adapter execution;
- private context access;
- model escalation;
- release publication;
- mission closure;
- doctrine changes.

It only reviews whether the dry-run package is coherent and safe.

## Required review inputs

- Mission Intake.
- Dry-Run Execution Plan.
- Runtime State.
- Evidence Collection Stub.
- Adapter Invocation Stubs, if any.
- Mission Charter reference.
- Model Routing Decision, if applicable.
- Context Budget, if applicable.
- Token Budget Enforcement record, if applicable.

## Review checklist

### 1. Mission Charter alignment

- Is the Mission Charter referenced?
- Does the dry-run objective match the Mission Charter?
- Are out-of-scope actions explicitly excluded?
- Are inferred requirements marked as inference, not permission?

Decision:

- `pass`
- `needs_revision`
- `block`

### 2. Dry-run boundary

Confirm that the package does not claim to have:

- executed shell commands;
- changed files;
- run Git operations;
- invoked adapters;
- accessed private context automatically;
- published releases;
- changed doctrine.

Decision:

- `pass`
- `needs_revision`
- `block`

### 3. Context boundary

Review:

- approved context sources;
- denied context sources;
- context capsules used;
- full-source fallback needs;
- private context approval requirements;
- stale or missing source references.

Decision:

- `pass`
- `needs_revision`
- `block`

### 4. Model and token governance

Review:

- assigned model tier;
- capability sufficiency evidence;
- escalation triggers;
- demotion opportunities;
- context budget;
- soft and hard token limits;
- overage handling.

Decision:

- `pass`
- `needs_revision`
- `block`

### 5. Step quality

Each dry-run step must have:

- actor or role;
- proposed action;
- input;
- expected output;
- required evidence;
- approval requirement before execution;
- stop condition.

Decision:

- `pass`
- `needs_revision`
- `block`

### 6. Adapter stubs

If adapter stubs exist, verify:

- adapter profile is named;
- permission matrix is referenced;
- mode is non-executing unless separately approved;
- private context is not included without approval;
- expected output is clear;
- adapter result is not treated as authorization.

Decision:

- `pass`
- `needs_revision`
- `block`
- `not_applicable`

### 7. Evidence plan

Review whether the evidence plan can prove:

- scope match;
- dry-run-only behavior;
- no hidden mutation;
- no private leakage;
- validation path;
- later execution requirements.

Decision:

- `pass`
- `needs_revision`
- `block`

### 8. Runtime state

Review:

- allowed state value;
- valid state transition;
- current artifacts;
- open risks;
- next allowed action.

Decision:

- `pass`
- `needs_revision`
- `block`

## Hard block conditions

Block the dry-run package if:

- no Mission Charter is referenced;
- execution is implied or claimed;
- file mutation is implied or claimed;
- Git operation is implied or claimed;
- private context is accessed without approval;
- adapter invocation is treated as already approved;
- model tier sufficiency is asserted without evidence;
- token budget is missing for a high-risk task;
- the next action would bypass user approval;
- the plan cannot be explained to the user.

## Review output

### Decision

Choose one:

- `approved_as_dry_run_package`
- `needs_revision`
- `blocked`
- `rejected`

### Required changes

- 

### Evidence accepted

- 

### Evidence missing

- 

### Teachback requirement

Before closure, the user must be able to explain:

- what the runtime skeleton planned;
- what it did not do;
- what would require separate approval;
- what evidence supports the next step.

## Reviewer notes

- 
