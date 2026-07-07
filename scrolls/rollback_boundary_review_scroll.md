# Rollback Boundary Review Scroll

Status: public review Scroll.

Use this Scroll to review rollback planning before runtime work performs side effects or before rollback behavior is implemented.

## Purpose

This Scroll checks whether a proposed action has a clear recovery path.

Rollback planning does not grant permission to execute. It only determines whether execution could be reviewed safely.

## Required inputs

- Mission Charter.
- Proposed action.
- Affected scope.
- Pre-action evidence.
- Expected changes.
- Rollback request or plan.
- Related command, filesystem, Git, adapter, or runtime boundary.
- Private boundary notes.

## Review steps

### 1. Confirm authorization

Check that the Mission Charter allows the proposed mutation or execution.

If authorization is missing, stop.

### 2. Confirm scope

Verify:

- allowed paths are explicit;
- out-of-scope paths are explicit;
- private Village handling is explicit;
- destructive actions are identified.

### 3. Confirm rollback plan

Check that the rollback plan explains:

- what could go wrong;
- how failure is detected;
- how recovery works;
- which commands or manual steps are needed;
- which parts are irreversible.

### 4. Confirm evidence

Required evidence should include:

- current status;
- planned diff or dry-run when possible;
- affected files or systems;
- expected success criteria;
- post-action verification.

### 5. Confirm privacy

Reject the plan if it could expose:

- private Village content;
- credentials;
- local memory;
- private knowledge sources;
- personal data;
- proprietary project data.

### 6. Confirm stop conditions

The plan must stop if:

- Git state is unexpected;
- affected scope expands;
- rollback cannot be described;
- irreversible risk is unclear;
- approval is missing;
- private boundary is uncertain.

## Verdicts

### Pass

Rollback planning is clear enough for the next review gate.

### Pass with notes

Rollback planning is mostly clear, but minor evidence or wording should be improved.

### Needs changes

Rollback plan is incomplete or ambiguous.

### Blocked

The plan is unsafe, unauthorized, irreversible without acknowledgement, or exposes private content.

## Output

The review output must include:

- verdict;
- evidence reviewed;
- risks;
- required changes;
- whether execution remains blocked;
- approval requirements.

## Reviewer rule

Rollback review is not rollback execution.

Do not run commands, revert files, delete files, reset Git, or modify state unless a separate approved Mission Charter explicitly authorizes it.
