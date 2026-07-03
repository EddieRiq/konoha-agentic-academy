# Code change scroll

This Scroll defines the safe workflow for modifying code.

## Core rule

Code changes require explicit scope, a clean baseline, and traceable evidence.

## Status

Draft.

## Activation

Use this Scroll when a mission may create, edit, delete, move, or rename code files.

Do not use it for read-only review. Use `repo_review_scroll.md` or `code_review_scroll.md` instead.

## Required inputs

Before execution, the Hokage must confirm:

- mission objective;
- allowed files or directories;
- forbidden files or directories;
- allowed commands;
- expected validation;
- review level;
- rollback expectation;
- whether Git operations are allowed.

## Default mode

Code change missions are not allowed by default.

The agent must not edit files until the Mission Charter explicitly allows edits.

## Baseline checks

Before editing, collect:

```bash
git status
git branch --show-current
git diff --stat
```

If the working tree is not clean, stop unless the Mission Charter explicitly allows working with existing changes.

## Planning

Before editing, the worker must report:

- files expected to change;
- reason for each change;
- validation command;
- risks;
- assumptions;
- stop conditions.

## Execution rules

The worker must:

- make the smallest safe change;
- preserve existing behavior unless change is approved;
- avoid unrelated cleanup;
- avoid broad refactors unless approved;
- avoid formatting unrelated files;
- avoid touching generated files unless approved;
- avoid changing dependencies unless approved.

## Forbidden by default

Do not run or perform:

- `git add`;
- `git commit`;
- `git push`;
- `git reset`;
- `git rebase`;
- dependency installation;
- network calls;
- destructive commands;
- production commands;
- secret or credential changes;
- edits outside approved paths.

## Validation

After editing, run only approved validation commands.

Examples:

```bash
pytest
python -m pytest tests/
ruff check .
python script.py --help
```

If validation cannot be run, say so and explain why.

Do not invent test results.

## Diff report

After changes, report:

```bash
git diff --stat
git diff -- <changed-files>
```

Summarize:

- what changed;
- why it changed;
- how it was validated;
- what remains unvalidated;
- what risks remain.

## Review

Code change missions require review based on risk.

Low risk may use a Clerk review if allowed.

Medium and high risk require Jounin review.

Security, doctrine, dependencies, CI, deployment, and public release changes require stricter review.

## Completion

A code change mission is not complete until:

- scope was respected;
- diff was shown or summarized with evidence;
- validation was performed or limitations were stated;
- required review passed;
- teachback completed;
- user approved closure.
