# v3.1.3 Canonical Release Test Gate Scope

## Objective

Provide one reliable command that executes every discoverable Konoha test
suite without depending on Python package recursion.

## Included

- immediate-suite discovery;
- independent unittest execution;
- continue-after-failure behavior;
- aggregate terminal summary;
- optional sandbox-only JSON report;
- per-suite timeout and filters;
- tests, schema, example, guide, roadmap scope and review Scroll.

## Excluded

- test parallelism;
- model invocation;
- network access;
- Git operations;
- CI changes;
- Mission Continuity;
- Release Closure Guard.

## Acceptance criteria

1. Directories without `__init__.py` are discovered.
2. Hidden directories and `__pycache__` are ignored.
3. Later suites run after an earlier failure.
4. Any suite failure returns exit code `1`.
5. Configuration blockers return exit code `2`.
6. Reports cannot be written outside `sandbox/`.
7. The canonical command discovers the full current suite set.
