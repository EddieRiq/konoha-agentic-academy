# Git Operation Boundary Review Scroll

Status: public review Scroll.

Use this Scroll to review any proposal, template, adapter, or runtime behavior involving Git operations.

## Purpose

This Scroll protects the repository from unauthorized staging, commits, pushes, tags, releases, branch changes, history rewrites, and accidental publication of private content.

## Inputs

Required inputs:

- Mission Charter;
- Git operation request;
- runtime or adapter profile;
- permission matrix;
- evidence pack;
- current `git status`;
- diff or file list;
- private-boundary checks;
- approval record.

Optional inputs:

- release notes;
- changelog diff;
- CI/CD notes;
- rollback plan;
- branch protection notes.

## Review questions

### 1. Mission scope

- Does the Mission Charter explicitly allow Git operations?
- Is the exact operation listed?
- Is the target repository clear?
- Is the target branch or tag clear?
- Is the adapter/runtime allowed to perform this operation?

### 2. Operation class

Classify the operation:

- read-only;
- staging;
- commit;
- push;
- tag;
- release;
- branch mutation;
- history-changing;
- other.

If the operation is history-changing, destructive, or release-related, escalate.

### 3. Path and file scope

Check:

- affected paths are explicit;
- broad staging is justified;
- generated files are expected;
- local/private paths are excluded;
- no local Village content is staged;
- no credentials, tokens, logs, caches, or private outputs are included.

### 4. Evidence

Required evidence:

```text
git status
git diff --stat
git diff --cached --stat
git branch --show-current
git log --oneline --decorate -5
```

For private-boundary checks:

```text
git ls-files alliance/<village>
git check-ignore -v alliance/<village>/test.md
```

### 5. Approval

Confirm:

- user approval is recorded;
- reviewer approval is recorded when required;
- release approval is recorded when required;
- exact command matches approval;
- command has not changed since approval.

### 6. Remote and release risk

Check:

- remote target is correct;
- branch target is correct;
- push scope is clear;
- tag points to intended commit;
- release notes are reviewed;
- pre-release/stable status is explicit;
- CI/CD side effects are understood.

### 7. Rollback or recovery

Confirm:

- rollback notes exist;
- irreversible operations are identified;
- recovery owner is clear;
- no destructive command is executed without exceptional approval.

## Stop conditions

Stop if:

- Mission Charter is missing;
- Git operation is not explicitly authorized;
- command differs from request;
- diff is not reviewed;
- private-boundary check is missing or fails;
- local Village content is visible to Git;
- unexpected files are present;
- remote or branch target is unclear;
- tag/release intent is unclear;
- user approval is missing;
- rollback notes are missing for risky operations;
- operation involves force push, reset hard, destructive clean, or history rewrite without escalation.

## Verdicts

### Pass

The Git operation may proceed under the approved scope.

### Pass with notes

The operation may proceed, but notes must be addressed after completion.

### Needs changes

The request must be clarified or corrected before execution.

### Blocked

The operation must not proceed.

### Escalate

The operation requires higher-level approval, such as release review, security review, or Kage Summit.

## Output

The review output must include:

- operation type;
- approved command/action;
- allowed scope;
- blocked scope;
- required evidence;
- stop conditions;
- approval status;
- final verdict.

## Reviewer rule

Reviewing a Git operation does not execute it.

Execution requires a separate approved request and execution gate.
