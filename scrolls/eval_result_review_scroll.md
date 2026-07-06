# Eval Result Review Scroll

Status: public Scroll.

This Scroll reviews eval results and eval run reports before they are used as evidence for adapter work, runtime work, doctrine changes, or release decisions.

## Purpose

Eval Result Review checks whether evaluation outcomes are clear, safe, reproducible, and strong enough to support a decision.

It does not execute evals by itself.

## Inputs

Required inputs:

- eval case;
- eval result;
- evidence;
- repository state or commit reference;
- expected behavior;
- actual behavior;
- verdict;
- safety notes.

Optional inputs:

- eval run report;
- related Mission Charter;
- related adapter contract;
- related permission matrix;
- related execution gate;
- related issue or release checklist.

## Reviewer responsibilities

The reviewer must check:

- whether the expected behavior is explicit;
- whether the actual behavior is described without private leakage;
- whether the verdict follows from evidence;
- whether safety checks were completed;
- whether failures are actionable;
- whether blockers are clearly identified;
- whether release or runtime decisions are justified.

## Review procedure

### 1. Confirm scope

Identify what decision the eval result supports.

Examples:

- release readiness;
- adapter profile review;
- runtime readiness;
- doctrine update;
- safety boundary validation.

### 2. Check source eval case

Confirm that the eval case defines:

- scenario;
- expected behavior;
- forbidden behavior;
- pass criteria;
- fail criteria;
- evidence requirements.

If the eval case is unclear, the result cannot be approved.

### 3. Check evidence

Evidence must be safe and sufficient.

Acceptable evidence:

- public command output;
- public file references;
- safe excerpts from generated outputs;
- Git status;
- tag or commit references;
- reviewer notes.

Blocked evidence:

- private Village content;
- secrets;
- credentials;
- private literature excerpts;
- copyrighted source content;
- sensitive local paths when not necessary;
- unverifiable claims.

### 4. Check verdict

The verdict must match the evidence.

Valid verdicts:

- Pass;
- Pass with notes;
- Fail;
- Blocked;
- Not run.

If evidence is missing, the verdict should be Blocked or Not run.

### 5. Check safety

The result must confirm:

- no private context exposure;
- no unauthorized command execution;
- no unauthorized Git operation;
- no release action without approval;
- no memory or doctrine promotion without approval;
- stop conditions were respected.

### 6. Decide use

The reviewer must decide whether the result can be used as evidence.

Possible decisions:

- Accept result;
- Accept with notes;
- Reject result;
- Request re-run;
- Escalate.

## Stop conditions

Stop the review if:

- the result includes private or sensitive content;
- the evidence contradicts the verdict;
- command execution occurred without authorization;
- a private Village was exposed;
- a release decision depends on a failed or blocked eval;
- the reviewer cannot determine what was tested.

## Output

The review output must include:

- reviewed eval result;
- verdict on result quality;
- accepted or rejected;
- blockers;
- required follow-up;
- whether the result can support the intended decision.

## Non-goals

This Scroll does not:

- run automated tests;
- implement an eval runner;
- approve runtime execution;
- approve releases by itself;
- rewrite doctrine;
- expose private evidence.

## Completion criteria

Eval Result Review is complete when:

- the result quality verdict is recorded;
- blockers are listed;
- unsafe evidence is removed or rejected;
- the decision impact is clear;
- the user can explain whether the eval result supports the next step.
