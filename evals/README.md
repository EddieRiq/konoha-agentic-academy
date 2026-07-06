# Evals

Evals are test cases for Konoha behavior.

They check whether agents, Scrolls, tools, adapters, memory workflows, and review paths follow approved doctrine.

## Core rule

Behavior must be tested before it is trusted.

An eval may reveal risk, failure, ambiguity, or regression. It may not authorize execution, bypass review, or replace human approval.

## Current layout

```text
evals/
  README.md
  behavior/
  regression/
  security/
  templates/
    eval_case_template.md
    scroll_eval_template.md
```

The folders may start as placeholders. New evals should use the templates unless a Mission Charter approves another format.

## What evals test

Evals may test:

```text
- whether an agent stops when context is missing;
- whether a Scroll refuses forbidden actions;
- whether a tool request stays inside the Mission Charter;
- whether a reviewer catches unsafe output;
- whether local context stays local;
- whether a memory note avoids inventing authority;
- whether a release review catches private data or license risk;
- whether a coding workflow requires review before closure.
```

## What evals do not test

Evals do not prove that a real-world task is correct.

They do not replace:

```text
- user approval;
- Jounin review;
- Kage Summit review;
- security review;
- real tests for code;
- release readiness review;
- teachback.
```

Synthetic success is not production success.

## Templates

Generic eval cases use:

```text
evals/templates/eval_case_template.md
```

Scroll-specific evals use:

```text
evals/templates/scroll_eval_template.md
```

A Scroll eval should define:

```text
- Scroll under test;
- mission scenario;
- allowed inputs;
- forbidden actions;
- expected stop behavior;
- expected output;
- required evidence;
- pass criteria;
- fail criteria.
```

## Eval categories

### Behavior

```text
evals/behavior/
```

Use for general agent behavior, mission boundaries, stop-and-ask rules, review behavior, and teachback behavior.

### Regression

```text
evals/regression/
```

Use when a past failure must not reappear.

### Security

```text
evals/security/
```

Use for private context, sensitive data, publication safety, dependency risk, adapter risk, and prompt injection scenarios.

## Evals for Scrolls

A Scroll should get evals when:

```text
- it affects execution behavior;
- it changes review or safety behavior;
- it handles sensitive context;
- it handles publication;
- it handles dependencies, adapters, or tools;
- it is promoted from draft to active;
- it was changed after a failure.
```

A Scroll may remain draft without evals, but it should not be treated as trusted for higher-risk missions.

## Evals for coding workflows

Coding-related evals should check that the workflow:

```text
- does not modify files without approval;
- separates planning from execution;
- checks repo structure before edits;
- asks for tests or validation evidence;
- prevents secret or private data commits;
- requires review before closure;
- records unresolved risks.
```

Relevant Scrolls include:

```text
scrolls/code_change_scroll.md
scrolls/code_review_scroll.md
scrolls/python_code_review_scroll.md
scrolls/python_project_scroll.md
scrolls/refactor_scroll.md
scrolls/test_first_scroll.md
```

## Evals for learning

When a Learning Proposal becomes an Approved Tactic or doctrine candidate, it should produce or update at least one eval when possible.

This prevents Konoha from learning a rule that cannot be checked.

## Pass and fail

A passing eval must show evidence.

A failing eval must be preserved, fixed, or explicitly marked as blocked.

Do not change expected results just to make a failure disappear.

## Sensitive content

Eval fixtures must not include:

```text
- credentials;
- tokens;
- private keys;
- real personal data;
- private project context;
- local literature;
- copyrighted source material;
- work emails;
- private assets.
```

Use synthetic examples unless a Mission Charter explicitly allows a sanitized fixture.

## Violations

The following are violations:

```text
- marking a risky Scroll as active without required evals;
- deleting failed evals instead of archiving or resolving them;
- changing expected results to hide a regression;
- using evals to bypass human review;
- using synthetic eval success as proof of real-world correctness;
- storing sensitive input in eval fixtures without explicit approval.
```

## Completion checklist

Before a target is marked as tested:

```text
- required eval cases exist;
- pass and fail criteria are explicit;
- results are recorded;
- failures are either fixed, blocked, or documented;
- sensitive content has been sanitized;
- required review level has approved the result;
- any new learning is routed through Learning Policy.
```

## Evaluation case templates

- `templates/behavior_eval_case.template.md`: template for evaluating agent behavior against Konoha doctrine.
- `templates/safety_eval_case.template.md`: template for evaluating safety boundaries, stop conditions, privacy, and approval requirements.
- `templates/adapter_eval_case.template.md`: template for evaluating adapter contracts, permissions, dry-runs, evidence, and execution gates.

## Initial manual eval cases

- `behavior/mission_charter_required.md`: manual eval for refusing execution without a Mission Charter.
- `security/private_context_stop_condition.md`: manual eval for stopping before private-context access.
- `adapter/dry_run_before_execution.md`: manual eval for requiring dry-run, evidence, and execution gate before adapter execution.

## Eval result templates

- `templates/eval_result.template.md`: template for recording the result of a single eval case.
- `templates/eval_run_report.template.md`: template for summarizing a manual or future automated eval run.
