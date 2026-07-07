# Runtime Validation Review Scroll

Status: documentation-first baseline  
Runtime mode: dry-run only  
Primary reviewer role: Jounin or equivalent reviewer

## Purpose

This Scroll defines how to review a Runtime Validation Checklist and Runtime Validation Report.

It helps determine whether a dry-run runtime package is coherent, bounded, evidence-backed, and ready for human review.

It does not authorize execution.

## When to use this Scroll

Use this Scroll when reviewing:

- Mission Intake;
- Dry-Run Execution Plan;
- Adapter Invocation Stub;
- Evidence Collection Stub;
- Runtime State;
- Runtime Validation Checklist;
- Runtime Validation Report;
- any proposed transition from planning to a later execution gate.

## Required inputs

Before review, confirm that the reviewer has access to:

- the Mission Charter;
- runtime dry-run package;
- validation checklist;
- validation report, when available;
- relevant adapter contracts;
- model routing decision, when applicable;
- context budget, when applicable;
- token budget enforcement plan, when applicable.

If the Mission Charter is missing, stop.

## Review posture

The reviewer should assume:

- the runtime is dry-run only;
- validation is not approval;
- capability is not permission;
- summaries are not truth;
- memory does not authorize action;
- model confidence does not authorize action;
- context capsules can be stale;
- missing evidence matters.

## Review steps

### 1. Confirm mission alignment

Check whether the runtime package matches the Mission Charter.

Reject or block if:

- the mission objective changed;
- the requested output changed materially;
- optional work became required work;
- assumptions were hidden;
- ambiguity was treated as permission.

### 2. Confirm dry-run boundary

Check whether every proposed action remains non-executed.

Block if the package performs or requests:

- shell command execution;
- file mutation;
- Git operation;
- network call;
- dependency installation;
- adapter execution;
- private context access;
- release operation.

Proposed commands may exist only as reviewable text.

### 3. Confirm authority boundary

Check whether any part of the package treats a signal as approval.

Block if authorization is inferred from:

- previous user messages;
- model confidence;
- adapter capability;
- passing validation;
- memory;
- capsule content;
- expected evidence;
- reviewer silence.

### 4. Confirm public/private safety

Review all generated public text for accidental leakage.

Block if the package includes:

- private Village content;
- copied private source text;
- secrets;
- credentials;
- local-only paths that expose private structure;
- copyrighted private material;
- hidden assumptions about private context availability.

### 5. Confirm context sufficiency

Check whether the selected context is enough but not excessive.

Request revision if:

- source selection is unexplained;
- context capsules lack status;
- stale capsules are used materially;
- full-source fallback is missing;
- the context budget is too broad;
- the plan depends on a summary without evidence.

### 6. Confirm model tier sufficiency

Check whether the selected model tier is appropriate.

Request escalation if:

- task risk exceeds the tier;
- the model failed a similar eval;
- the task requires specialized reasoning;
- the model is reviewing its own high-risk output;
- the package relies on self-certification.

Request demotion evidence if a lower tier could safely do the work in future.

### 7. Confirm token budget discipline

Check whether token use is planned and bounded.

Request revision if:

- budget categories are missing;
- hard stops are absent;
- overage is normalized without explanation;
- repeated large context intake could be replaced with capsules;
- output scope is too broad.

### 8. Confirm adapter contract fit

When adapter stubs are present, check whether the adapter request fits the contract.

Block if:

- the adapter is unnamed;
- the requested capability is outside contract;
- permission matrix is missing;
- the stub implies execution;
- expected output is presented as actual output.

### 9. Confirm evidence quality

Check whether claims and validation outcomes are tied to evidence.

Request revision if:

- material evidence is missing;
- evidence is expected but not collected;
- claims exceed evidence;
- missing evidence has no impact statement;
- validation outcome is stronger than evidence supports.

### 10. Confirm runtime state consistency

Check whether runtime state is clear and consistent.

Request revision if:

- state transitions are unclear;
- blockers are omitted;
- retries are not recorded;
- final state conflicts with validation outcome;
- state implies hidden execution.

## Outcome rules

### Accept for human review

Use this only when:

- no blockers remain;
- dry-run boundary is preserved;
- Mission Charter alignment is clear;
- evidence supports the validation result;
- remaining questions are non-material.

### Request revision

Use this when:

- package is mostly coherent;
- issues are fixable;
- no critical safety blocker exists;
- evidence gaps are non-critical but relevant.

### Block

Use this when:

- Mission Charter is missing;
- execution is attempted or requested;
- private content appears;
- authorization is inferred;
- material evidence is missing;
- adapter permissions are unclear;
- model tier is unsafe for task risk;
- token hard stop is exceeded without approval.

## Required reviewer output

The reviewer must produce:

- outcome;
- blockers, if any;
- required revisions, if any;
- evidence reviewed;
- unresolved questions;
- explicit non-authorization statement.

## Non-authorization statement

This Scroll does not authorize execution, shell commands, file mutation, Git operations, adapter invocation, private context access, release actions, doctrine changes, or autonomous runtime behavior.

## Minimal acceptance statement

A reviewer may use the following statement when accepting a dry-run package:

```text
The runtime dry-run package is internally consistent and ready for human review. This acceptance does not authorize execution or mutation.
```
