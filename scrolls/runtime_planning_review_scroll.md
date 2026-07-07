# Runtime Planning Review Scroll

Status: public review Scroll.

Use this Scroll to review proposed Konoha runtime plans before implementation.

## Purpose

This Scroll helps reviewers verify that a runtime plan remains bounded, non-executing, evidence-driven, and subordinate to Konoha doctrine.

## Required inputs

- Runtime plan.
- Related Mission Charter, if applicable.
- Related adapter contracts.
- Related permission matrices.
- Related dry-run, execution gate, and evidence templates.
- Related eval cases.
- Public/private boundary notes.

## Review questions

### Scope

- Is the runtime plan documentation-only?
- Does it avoid implementing execution?
- Are purpose and non-goals explicit?
- Are allowed inputs and outputs explicit?

### Authority

- Does the plan preserve Mission Charter requirements?
- Does it avoid treating capability as authorization?
- Does it require approval before mutating actions?
- Does it respect adapter permission matrices?

### Safety

- Are stop conditions explicit?
- Are private context boundaries explicit?
- Are Git and release operations blocked by default?
- Are secrets and credentials excluded?
- Are rollback expectations documented?

### Evidence

- Are pre-execution evidence requirements defined?
- Are post-execution evidence requirements defined?
- Is dry-run required before execution?
- Is the execution gate required before mutating actions?

### Evaluation

- Are behavior, safety, and adapter evals identified?
- Are eval result expectations defined?
- Is the eval runner boundary respected?

## Allowed reviewer outputs

The reviewer may produce:

- pass;
- pass with notes;
- needs changes;
- blocked.

## Blocking findings

Block the runtime plan if:

- it grants autonomous execution;
- it bypasses Mission Charter;
- it weakens approval policy;
- it allows private context access by default;
- it allows Git or release operations by default;
- it lacks dry-run requirements;
- it lacks evidence requirements;
- it lacks eval coverage;
- it introduces executable code under a planning milestone.

## Completion checklist

- [ ] Scope reviewed.
- [ ] Authority reviewed.
- [ ] Safety reviewed.
- [ ] Evidence reviewed.
- [ ] Evaluation coverage reviewed.
- [ ] Public/private boundary reviewed.
- [ ] Verdict recorded.

## Final rule

Runtime planning may prepare future execution.

Runtime planning is not execution.
