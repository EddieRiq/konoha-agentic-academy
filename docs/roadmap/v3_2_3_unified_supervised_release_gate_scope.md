# v3.2.3 Unified Supervised Release Gate Scope

## Objective

Replace long ad hoc release command blocks with one versioned, deterministic and supervised release state machine.

## Problem addressed

Previous release closures correctly returned intermediate states such as:

```text
NEEDS_TAG_CREATION
NEEDS_RELEASE_PUBLICATION
```

Several shell wrappers then stopped because auxiliary scripts assumed optional report fields or treated every nonzero return code as failure.

The canonical guard was correct. The orchestration around it was fragile.

## Included

- release workflow plan schema;
- release workflow report schema;
- deterministic Python stdlib orchestrator;
- exact public-scope verification;
- beta Git Gate plan/stage/commit/push reuse;
- one canonical test run for the committed HEAD;
- reusable guard evidence chain;
- expected RC plus expected state validation;
- local commit resume;
- annotated tag create/push;
- GitHub Release create;
- Latest promotion;
- direct Git/GitHub final verification;
- command logs under sandbox;
- minimal terminal output;
- focused tests, guide, example and review Scroll.

## Excluded

- arbitrary commands from the plan;
- shell command strings;
- force push;
- branch repair or merge;
- tag rewrite or deletion;
- release deletion or overwrite;
- draft publication repair;
- prerelease conversion;
- authentication repair;
- credential-manager repair;
- model invocation;
- private-memory access;
- autonomous background execution;
- rollback of a partially published release.

## State machine

```text
local exact scope
    ↓
local release commit
    ↓
canonical tests
    ↓
BLOCKED_BRANCH_NOT_SYNCED
    ↓
push main
    ↓
NEEDS_TAG_CREATION
    ↓
create annotated tag
    ↓
NEEDS_TAG_PUBLICATION
    ↓
push tag
    ↓
NEEDS_RELEASE_PUBLICATION
    ↓
publish release
    ↓
NEEDS_LATEST_PROMOTION (only when needed)
    ↓
RELEASE_CLOSED
```

## Approval model

The single command requires all mutation approvals explicitly:

- workflow run;
- Git plan;
- Git stage;
- Git commit;
- Git push;
- tag creation;
- tag publication;
- release publication;
- Latest promotion.

Unused transition tokens grant no extra operation. The workflow invokes only the action selected by the observed canonical state.

## Acceptance criteria

1. Focused suite passes 14 tests.
2. Canonical gate discovers 49 suites and 361 tests.
3. Exact 16-path public scope is enforced.
4. Missing or extra paths block before staging.
5. Private public paths block.
6. Missing approval tokens block before mutation.
7. The release commit has the exact parent, subject and paths.
8. Tests run against the committed HEAD.
9. `BLOCKED_BRANCH_NOT_SYNCED` advances only to push main.
10. Every later guard consumes a prior guard report.
11. Unexpected RC or state stops.
12. Local and remote annotated tag objects match.
13. Tag targets equal the tested HEAD.
14. Release title and tag match exactly.
15. Draft and prerelease are false.
16. Latest is true.
17. Tracking ends at 0/0.
18. Working tree ends clean.
19. Output remains under sandbox.
20. Detailed logs remain under sandbox.
21. No force, delete, rewrite, model or private-context operation exists.
