# v3.2.5 Package Installation Scope Guard Scope

## Objective

Eliminate the repeated failure mode where ZIP extraction legitimately changes tracked files but a package helper incorrectly requires a clean diff.

## Included

- package installation manifest;
- direct/helper/public path separation;
- exact union and disjointness checks;
- bounded idempotent helper execution;
- direct-file hash preservation;
- staged and private-path blocking;
- preview and apply modes;
- idempotent installed reentry;
- sandbox reports and helper logs;
- schemas, examples, tests, guide and review Scroll.

## Excluded

- ZIP extraction;
- rollback of a defective helper;
- Git stage, commit or push;
- tag and release mutation;
- network access;
- model invocation;
- private-memory access;
- arbitrary helper argv;
- automatic release continuation.

## Acceptance criteria

1. New suite contains 12 tests.
2. Canonical target is 50 suites / 383 tests.
3. Direct and helper paths are disjoint.
4. Public scope is their exact union.
5. Preview recognizes only direct extraction scope.
6. Apply requires an explicit installation token.
7. Helper runs with bounded argv and `python -S`.
8. Direct hashes remain unchanged.
9. Final scope equals 17 paths.
10. Second apply is idempotent.
11. Extra paths block.
12. Staged paths block.
13. Private paths block.
14. Output stays under sandbox.
15. No Git, network, release or model mutation exists.
