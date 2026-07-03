# Test first scroll

This Scroll defines a test first workflow for code changes.

## Core rule

Write the evidence before claiming the fix.

## Status

Draft.

## Activation

Use this Scroll when a mission involves bug fixes, behavior changes, validation logic, parsing, transformations, scoring inputs, or reusable functions.

Do not force test first when the mission is purely exploratory, documentation only, or the codebase has no test harness and the Mission Charter does not allow creating one.

## Workflow

1. Understand the expected behavior.
2. Identify the smallest testable unit.
3. Write or propose a failing test.
4. Run the test if allowed.
5. Make the smallest change.
6. Run the test again.
7. Run relevant regression checks.
8. Report evidence.

## Required context

Before writing tests, confirm:

- expected behavior;
- current behavior;
- test framework;
- allowed test files;
- allowed commands;
- fixture policy;
- sensitive data restrictions.

## Test design

Good tests are:

- small;
- deterministic;
- named clearly;
- focused on behavior;
- independent of private data;
- easy to run;
- useful when they fail.

Avoid tests that only check implementation details unless implementation is the contract.

## Sensitive data

Tests must not include real personal data, credentials, production secrets, or private identifiers.

Use synthetic examples.

## When tests cannot be added

If the codebase has no test harness or tests are out of scope, the agent must propose:

- minimal manual validation;
- expected command;
- expected output;
- limitation of the evidence.

Do not pretend manual validation is equivalent to automated tests.

## Commands

Allowed commands must come from the Mission Charter.

Examples:

```bash
pytest
pytest tests/test_transform.py
python -m pytest
```

Do not install test frameworks without approval.

## Report

The report must include:

```text
Expected behavior:
Test added or proposed:
Initial result:
Code change:
Final result:
Regression checks:
Remaining gaps:
```

## Completion

A test first mission is complete only when the test evidence is shown or the inability to run tests is clearly documented and accepted.
