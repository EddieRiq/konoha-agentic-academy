# Adapter Runtime Boundary Review Scroll

Status: public Scroll.

Use this Scroll when reviewing whether an adapter runtime may be implemented, enabled, or moved to a higher execution class.

## Purpose

This Scroll prevents Konoha from confusing adapter design with adapter execution.

A runtime must not execute merely because:

- an adapter profile exists;
- a tool is available;
- a model can generate commands;
- a dry-run looked reasonable;
- previous work succeeded.

## Inputs

Required inputs:

- Mission Charter;
- adapter manifest;
- adapter permission matrix;
- invocation request;
- execution gate template or decision;
- evidence pack plan;
- dry-run protocol;
- runtime readiness review;
- proposed runtime class.

## Review steps

### 1. Confirm runtime class

Identify the requested class:

- Class 0: declarative only;
- Class 1: dry-run only;
- Class 2: patch proposal;
- Class 3: controlled local execution;
- Class 4: Git operation execution;
- Class 5: release operation execution;
- Class 6: private-context execution.

If the class is not explicit, stop.

### 2. Confirm authority

Check whether the Mission Charter explicitly authorizes the requested class.

If authorization is inferred, stop.

### 3. Confirm scope

Review:

- allowed paths;
- blocked paths;
- allowed commands;
- blocked commands;
- Git scope;
- release scope;
- private-context scope.

If scope is broad or ambiguous, stop.

### 4. Confirm evidence

The runtime must produce evidence before and after execution.

Required evidence:

- request;
- dry-run;
- approval gate;
- commands;
- files touched;
- validation;
- Git status;
- errors;
- rollback notes;
- final status.

If evidence cannot be safely recorded, stop.

### 5. Confirm public/private boundary

Check that implementation will not publish or expose:

- private Village content;
- credentials;
- local memory;
- private literature;
- generated private summaries;
- local dependency locks;
- local venvs.

If the boundary is unclear, stop.

### 6. Confirm rollback

The reviewer must understand how to undo or contain runtime effects.

If rollback is unknown, stop.

## Required output

The review must produce:

```text
Verdict:
- Not ready
- Ready for dry-run only
- Ready for patch proposal only
- Ready for controlled local execution
- Ready for Git operations
- Ready for release operations
- Ready for private-context execution

Reason:
Evidence reviewed:
Required changes:
Stop conditions:
Approval status:
```

## Stop conditions

Stop if:

- no Mission Charter exists;
- runtime class is not explicit;
- permission is inferred;
- scope is ambiguous;
- private context is involved without explicit approval;
- Git or release operations are requested without explicit scope;
- rollback is missing;
- evidence is missing;
- the user cannot explain what the runtime will do.

## Final rule

Runtime power must be earned gradually.

Konoha should prefer dry-run, evidence, and human approval over autonomy.
