# Self-Review, Optimization and Git Operation Gate

v2.9.0 introduces the review and Git operation layer before the v3.0 beta.

This is the last large pre-beta block.

## Purpose

The goal is to make Konoha able to evaluate a supervised mission before it asks for repository operations.

Konoha should answer:

- What did it do?
- What evidence exists?
- How much model/token usage was recorded?
- Where did it ask for too much handholding?
- What should be optimized next?
- Are there safe Git operations ready for explicit approval?

## Central rules

```text
Self-review is evidence only.
Optimization plans are not permission.
Git plans are not permission.
Git stage, commit and push require separate explicit approvals.
```

## Commands

```text
review
optimize
git-plan
stage
commit
push
states
```

## Approval tokens

```text
RECORD_SELF_REVIEW
RECORD_OPTIMIZATION_PLAN
PLAN_GIT_OPERATION
APPROVE_GIT_STAGE
APPROVE_GIT_COMMIT
APPROVE_GIT_PUSH
```

Each token authorizes only that specific operation.

## Git operation sequence

Git operations must follow this order:

```text
1. git-plan
2. human diff review
3. tests and audit
4. stage
5. commit
6. push
```

Push also requires `--allow-network`, because a Git push may contact a remote.

## Safety boundary

The tool may:

- inspect mission-local reports, plans and evidence;
- summarize token ledger data;
- write self-review reports;
- write optimization plans;
- record Git operation plans;
- run `git status`, `git diff --stat`, and `git branch --show-current` for planning;
- run `git add`, `git commit`, or `git push` only through explicit gated commands.

The tool may not:

- run arbitrary shell commands;
- use `shell=True`;
- invoke models;
- invoke adapters;
- access private context by default;
- apply repository files outside approved paths;
- stage denied paths such as `.env`, secrets, credentials, `.git`, or private Village roots;
- push without explicit approval and `--allow-network`;
- close missions.

## v3.0 relationship

v2.9.0 prepares the gate Konoha needs for beta missions.

In v3.0, after Eduardo reviews the work and says that the corrections are complete, Konoha may use these gates to stage, commit and push with explicit approval.
