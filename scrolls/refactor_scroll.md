# Refactor scroll

This Scroll defines the workflow for refactoring without changing intended behavior.

## Core rule

Refactor behavior only when behavior change is explicitly approved.

## Status

Draft.

## Activation

Use this Scroll when a mission asks to improve code structure, readability, modularity, naming, or maintainability while preserving behavior.

If behavior must change, use `code_change_scroll.md` and state the behavior change clearly.

## Required inputs

Before refactoring, confirm:

- target files;
- reason for refactor;
- behavior that must remain unchanged;
- tests or validation available;
- allowed commands;
- review level;
- rollback approach.

## Baseline

Before edits, gather:

```bash
git status
git diff --stat
```

When possible, run the existing tests before refactoring.

If tests are missing, document the gap before editing.

## Refactor plan

The plan must identify:

- code smell or maintenance issue;
- files to change;
- expected structural change;
- validation method;
- risks.

## Allowed refactors

Allowed only when in scope:

- extract function;
- rename local variables for clarity;
- split large functions;
- remove duplication;
- separate configuration from logic;
- separate I/O from pure transformation;
- add type hints where helpful;
- improve error messages;
- improve testability.

## Forbidden by default

Do not:

- change outputs;
- change public APIs;
- change schemas;
- change model behavior;
- change dependency versions;
- change runtime environment;
- rewrite whole modules without approval;
- mix refactor with feature work;
- remove tests;
- hide failures.

## Validation

A refactor needs stronger validation than a small edit because it can break behavior silently.

Preferred evidence:

- before and after tests;
- sample input and output comparison;
- snapshot comparison;
- CLI help still works;
- row counts unchanged for data transformations;
- model outputs unchanged when behavior should be preserved.

## Report

The final report must include:

```text
Refactor objective:
Files changed:
Behavior intended to remain unchanged:
Validation performed:
Validation not performed:
Risks:
Diff summary:
```

## Review

Refactors require Jounin review when they touch:

- many files;
- shared modules;
- production code;
- data transformations;
- model scoring logic;
- public interfaces;
- CI/CD;
- dependency or packaging files.

## Completion

A refactor is complete only when behavior preservation has evidence or the lack of evidence is clearly stated and accepted by the user.
