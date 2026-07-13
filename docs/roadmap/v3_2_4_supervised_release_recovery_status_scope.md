# v3.2.4 Supervised Release Recovery and Status Scope

## Objective

Add deterministic, read-only release recovery inspection after the successful dogfood of the unified release workflow.

## Included

- `--status` mode in the existing release workflow tool;
- local-only status by default;
- optional read-only remote inspection;
- exact recovery-state derivation;
- cached evidence validation;
- stale and corrupt evidence detection;
- safe-to-resume indicator;
- exact next action;
- closed-release reinspection;
- status report schema;
- ten focused recovery tests;
- guide and review Scroll.

## Excluded

- new Git or GitHub mutations;
- fetch in status mode;
- branch repair;
- force push;
- tag deletion, rewrite or replacement;
- release deletion or overwrite;
- automatic rollback;
- credential repair;
- background execution;
- model invocation;
- private-memory access;
- automatic execution after status.

## State precedence

1. Branch and scope consistency.
2. Exact release commit consistency.
3. Working-tree and tracking consistency.
4. Remote branch consistency.
5. Local annotated tag consistency.
6. Remote tag consistency.
7. GitHub Release metadata.
8. Latest status.
9. Final closed state.

A divergence state always wins over an actionable continuation.

## Acceptance criteria

1. Existing 14 release workflow tests remain green.
2. Ten new tests pass; focused total is 24.
3. Canonical target is 49 suites / 371 tests.
4. Status mode requires no mutation tokens.
5. Status mode performs no fetch.
6. Local-only status performs no network operation.
7. Network status uses read-only Git/GitHub commands.
8. Exact dirty scope reports `NEEDS_GIT_DELIVERY`.
9. Local release commit ahead by one reports `NEEDS_BRANCH_PUSH`.
10. Local tag without remote tag reports `NEEDS_TAG_PUBLICATION`.
11. Remote tag without release reports `NEEDS_RELEASE_PUBLICATION`.
12. Non-Latest release reports `NEEDS_LATEST_PROMOTION`.
13. Aligned release reports `RELEASE_CLOSED`.
14. Scope mismatch blocks.
15. Stale evidence is not reusable.
16. Corrupt evidence is not reusable.
17. Status output remains under sandbox.
18. Full release resume still requires explicit mutation tokens.
