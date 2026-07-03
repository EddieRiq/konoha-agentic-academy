# Code review scroll

This Scroll defines a read-only workflow for reviewing code.

## Core rule

Code review checks evidence, not confidence.

## Status

Draft.

## Activation

Use this Scroll when the mission is to review code without editing it.

Use language specific review Scrolls when available, such as `python_code_review_scroll.md`.

## Default mode

Code review is read-only by default.

The reviewer may inspect files, diffs, tests, configuration, and logs allowed by the Mission Charter.

The reviewer may not edit files, stage changes, commit, install dependencies, or run destructive commands.

## Review inputs

The reviewer should identify:

- mission objective;
- changed files;
- affected behavior;
- entry points;
- tests;
- dependencies;
- configuration;
- sensitive files;
- generated outputs.

## Review areas

Review for:

- correctness;
- scope control;
- readability;
- maintainability;
- error handling;
- input validation;
- secrets safety;
- data privacy;
- dependency changes;
- test coverage;
- logging quality;
- performance risks;
- compatibility with local conventions.

## Evidence

Use concrete evidence such as:

- file paths;
- functions;
- changed lines;
- commands run;
- test outputs;
- observed errors;
- missing validation.

Do not say "looks good" without evidence.

## Findings

Classify findings as:

```text
blocker
required-change
suggestion
question
approved-with-notes
approved
```

A blocker prevents mission closure.

A required change must be resolved or explicitly accepted by the user.

A suggestion may be deferred.

## Red flags

Stop and escalate if the review detects:

- credentials;
- personal data;
- hidden network calls;
- broad unrelated changes;
- dependency or lockfile changes without approval;
- generated files committed unexpectedly;
- tests removed or weakened;
- security checks bypassed;
- production paths modified;
- doctrine modified without approval.

## Review report

The report should include:

```text
Scope reviewed:
Evidence:
Findings:
Required changes:
Suggestions:
Validation status:
Residual risk:
Verdict:
```

## Verdicts

Valid verdicts:

```text
approved
approved-with-notes
changes-requested
blocked
escalate-to-kage-summit
```

## Completion

A code review is complete only when the reviewer has provided a verdict and the user can understand what was checked, what remains risky, and what decision is being recommended.
