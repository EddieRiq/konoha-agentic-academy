# Python code review Scroll

## Purpose

This Scroll guides a Code Jounin reviewing Python code.

It is read-only by default. It may identify issues, request changes, recommend tests, and propose follow-up work. It may not modify files unless the Mission Charter explicitly grants editing authority.

## Core rule

```text
Python review checks whether the code is correct, maintainable, safe, testable, and consistent with the approved project conventions.
```

## Activation

Use this Scroll when the Mission Charter requests:

- Python code review;
- review of an agent-generated script;
- review before commit or merge;
- review after a bug fix;
- review of data, ETL, ML, API, CLI, or automation scripts;
- validation against a local Python rubric;
- review of coding practices derived from approved local learning.

## Required inputs

Before reviewing, collect only what the Mission Charter allows:

```text
- Mission Charter
- target files or diff
- relevant README or project docs
- local Village coding conventions, if allowed
- approved Python review rubric, if allowed
- test commands, if known
- runtime constraints, if known
```

If the review needs local private literature or local rubrics, that access must be explicitly allowed.

## Default permissions

Allowed by default:

- read target code;
- read approved docs;
- inspect diffs;
- identify risks;
- suggest changes;
- classify findings;
- recommend tests;
- produce a review report.

Not allowed by default:

- edit files;
- run state-changing commands;
- install dependencies;
- access secrets;
- inspect private local paths;
- use private literature;
- update doctrine;
- commit, amend, push, or open a pull request.

## Review levels

### Level 1: basic Python review

Use for simple scripts, small functions, and low-risk changes.

Check:

- readability;
- obvious bugs;
- input validation;
- error handling;
- basic testability;
- secrets in code or logs.

### Level 2: production-oriented review

Use for ETL, CLI, APIs, model scoring, scheduled jobs, or scripts used by others.

Check:

- architecture;
- configuration;
- logging;
- safe file writes;
- dependency usage;
- tests;
- performance;
- failure modes;
- backward compatibility;
- operational documentation.

### Level 3: high-risk review

Use when the code touches:

- money or credit decisions;
- customer data;
- credentials;
- production systems;
- model inference;
- destructive operations;
- external services;
- CI/CD;
- public releases.

Requires Jounin review and may require Kage Summit or user decision.

## Review checklist

### Scope and mission fit

- Does the code match the approved Mission Charter?
- Are there unrelated changes?
- Are assumptions stated?
- Are out-of-scope concerns separated from blocking issues?

### Structure

- Is the code organized into clear functions or modules?
- Is core logic separated from I/O?
- Is configuration separated from behavior?
- Are side effects easy to identify?
- Is there avoidable duplication?

### Naming and readability

- Are names clear and specific?
- Are abbreviations understandable in the project context?
- Are comments used to explain decisions instead of restating code?
- Is complexity justified?

### Inputs and validation

- Are required inputs validated?
- Are paths, dates, IDs, schemas, and flags checked before use?
- Does the code fail clearly when required inputs are missing?
- Are defaults safe?

### Errors and logging

- Are errors explicit?
- Does the code avoid swallowing exceptions silently?
- Are logs useful for debugging?
- Are secrets, credentials, personal data, or private paths excluded from logs?
- Are warning messages actionable?

### Filesystem safety

- Are output paths controlled?
- Does the code avoid overwriting important files accidentally?
- Are temporary files handled safely?
- Are generated files ignored when appropriate?
- Are local/private outputs kept out of public commits?

### Data handling

For data scripts, also check:

- expected schema;
- key normalization;
- duplicate handling;
- null handling;
- join granularity;
- row counts;
- coverage checks;
- temporal leakage;
- reproducibility of outputs.

### ML and scoring

For model code, also check:

- feature order;
- feature names;
- preprocessing compatibility;
- model version;
- metadata;
- missing categories;
- calibration or score interpretation;
- target leakage;
- training vs inference consistency;
- monitoring hooks when relevant.

### Security and privacy

- No hardcoded secrets.
- No printed tokens or passwords.
- No committed `.env`.
- No personal data in examples.
- No private context copied into public docs.
- No unsafe shell command construction.
- No unapproved network calls.

### Dependencies

- Are imports necessary?
- Are heavy dependencies justified?
- Are versions pinned when needed?
- Is dependency risk documented?
- Are standard library options enough?

### Tests and validation

- Are tests present or proposed?
- Are edge cases covered?
- Are manual validation steps documented when tests are unavailable?
- Is there evidence that the code runs?
- Are expected outputs clear?

## Finding severity

Use these severities:

```text
blocker
major
minor
note
```

Definitions:

- `blocker`: unsafe, out of scope, unvalidated, destructive, sensitive, or likely to break required behavior.
- `major`: should be fixed before merge or completion.
- `minor`: worthwhile improvement, but not blocking.
- `note`: observation or future improvement.

## Review report format

Use this format:

```text
# Python code review report

## Scope reviewed

## Evidence checked

## Verdict
pass | pass-with-notes | changes-requested | blocked | escalate

## Blocking findings

## Major findings

## Minor findings

## Notes

## Tests or validation reviewed

## Tests or validation still needed

## Sensitive data check

## Recommended next action
```

For each finding:

```text
Severity:
File:
Location:
Issue:
Why it matters:
Suggested fix:
Evidence:
```

## Review verdicts

### pass

No blocking or major issues found.

### pass-with-notes

The code is acceptable, but there are minor suggestions.

### changes-requested

The code needs changes before completion.

### blocked

The review cannot safely pass because required context, evidence, tests, permission, or safety conditions are missing.

### escalate

The issue exceeds the reviewer authority or requires a broader design, safety, legal, security, or doctrine decision.

## Learning loop

When the same issue appears repeatedly:

```text
1. Record it as a review pattern.
2. Propose a local learning note.
3. If useful, draft a learning proposal.
4. User approves or rejects.
5. Shikamaru updates approved local conventions or doctrine.
6. Future Kagebunshin agents use the updated rule.
```

The reviewer may suggest learning. The reviewer may not update doctrine silently.

## Use with private literature

If a local Village has a private literature library, this Scroll may use approved local rubrics derived from that library.

Rules:

- do not quote protected source text;
- do not reveal local source contents;
- do not copy private notes into public reports;
- cite local rubric names instead of book content;
- use only Mission Charter-approved local context.

Example:

```text
Reviewed against:
- alliance/kirigakure/review-rubrics/python_code_review_rubric.md
```

## Stop conditions

Stop and ask when:

- target files are unclear;
- review requires private context not approved in the Mission Charter;
- tests require credentials or external systems;
- code contains secrets or personal data;
- findings require broad refactor beyond mission scope;
- the code touches production, credit decisions, or destructive operations without explicit approval;
- the reviewer cannot distinguish project convention from defect;
- the expected behavior is unknown.

## Completion checklist

Before completing review:

```text
- Scope reviewed.
- Evidence listed.
- Verdict assigned.
- Findings separated by severity.
- Sensitive data check completed.
- Tests or missing validations stated.
- Next action is clear.
- No private or protected content copied into the report.
```
