# v3.1.4 Release Readiness and Closure Guard Scope

## Objective

Detect and explain incomplete release states while preserving separate human gates for commit, push, tag and GitHub Release publication.

## Included

- canonical test evidence tied to current `HEAD`;
- reusable evidence restricted to `sandbox/`;
- working-tree and branch checks;
- local tracking synchronization;
- local tag target verification;
- optional read-only remote branch and tag verification;
- GitHub CLI authentication and release inspection;
- stable status codes and next actions;
- JSON report, schema, example, tests, guide and review Scroll.

## Excluded

- Git fetch;
- stage, commit or push;
- tag creation or deletion;
- GitHub Release creation or editing;
- automatic Latest promotion;
- model invocation;
- Mission Continuity.

## Acceptance criteria

1. Dirty worktrees are blocked.
2. Test evidence is bound to the current commit.
3. Reused evidence is rejected after `HEAD` changes.
4. Local and remote tag targets must equal tested `HEAD`.
5. Network operations require `--allow-network`.
6. Missing tag, remote tag, release and Latest produce distinct codes.
7. No mutation command is executed.
8. Reports can only be written below `sandbox/`.
