# Clans

Clans are specialization domains inside Konoha Agentic Academy.

A Clan groups related Scrolls, reviewers, tactics, examples, policies, and mission patterns around a type of work.

Clans exist to prevent the Academy from becoming a flat collection of unrelated prompts and rules.

## Core rule

A Clan may specialize behavior, but it may not override Konoha Laws, Safety Policy, Context Policy, Approval Policy, Review Policy, Learning Policy, or Mission Charter boundaries.

If a Clan rule conflicts with higher-level doctrine, the higher-level rule wins.

## Current public Clans

The repository currently includes these public Clan areas:

```text
clans/
  software-engineering/
    README.md
  python/
    README.md
  data-engineering/
  machine-learning/
  devops/
  research/
  security/
  writing/
```

Some folders are placeholders. A placeholder Clan is not active doctrine until it has a README or approved Clan documentation.

## Active Clan documents

```text
clans/software-engineering/README.md
clans/python/README.md
```

The software engineering Clan defines general coding behavior.

The Python Clan defines Python-specific expectations.

Local Villages may add their own project-specific coding conventions, but they may not weaken Academy rules.

## What a Clan is

A Clan is a structured specialization area.

A Clan may define:

```text
- domain-specific mission patterns;
- recommended Scrolls;
- required reviewers;
- risk triggers;
- acceptance criteria;
- examples;
- failure patterns;
- approved tactics;
- local model recommendations;
- escalation rules.
```

## What a Clan is not

A Clan is not:

```text
- a Git branch;
- a separate repository;
- a place for private project context;
- a shortcut around approvals;
- a place for secrets;
- a place for copyrighted local assets;
- a replacement for the Mission Charter;
- permission to execute work.
```

## Clan vs Scroll

A Clan is a specialization domain.

A Scroll is an activable skill, workflow, or capability.

Example:

```text
Clan:
software-engineering

Scrolls:
code_change_scroll
code_review_scroll
refactor_scroll
test_first_scroll
```

The Clan organizes the field. The Scroll performs a specific workflow.

## Clan vs Village

A Clan is general.

A Village is local.

Example:

```text
clans/software-engineering/
```

Defines general engineering behavior for the Academy.

```text
alliance/kirigakure/
```

Contains private local project context, local memory, local literature, local assets, local style, and local configuration.

Local Village rules may specialize how a Clan is used, but may not weaken Konoha rules.

## Coding conventions

General coding expectations belong in public Clans when they are reusable and safe to publish.

Project-specific conventions belong in local Villages.

Example:

```text
Public:
clans/software-engineering/README.md
clans/python/README.md

Local:
alliance/kirigakure/doctrine/coding_conventions.md
alliance/kirigakure/review-rubrics/python_code_review_rubric.md
```

Private books, paid material, converted sources, proprietary documents, and local literature must not be committed to public Clans.

Only distilled, license-safe, user-approved principles may be promoted from local literature into public or local doctrine.

## Recommended Scrolls by Clan

### Software engineering

```text
scrolls/code_change_scroll.md
scrolls/code_review_scroll.md
scrolls/refactor_scroll.md
scrolls/test_first_scroll.md
scrolls/error_triage_scroll.md
scrolls/dependency_review_scroll.md
scrolls/git_safety_scroll.md
```

### Python

```text
scrolls/python_project_scroll.md
scrolls/python_code_review_scroll.md
scrolls/test_first_scroll.md
scrolls/dependency_review_scroll.md
```

### Documentation and writing

```text
scrolls/documentation_review_scroll.md
scrolls/release_notes_scroll.md
scrolls/changelog_maintenance_scroll.md
```

### Safety and publication

```text
scrolls/sensitive_data_review_scroll.md
scrolls/publication_safety_scroll.md
scrolls/release_readiness_scroll.md
```

## Creating a Clan

A new Clan requires:

```text
- explicit purpose;
- scope;
- non-scope;
- expected mission types;
- related Scrolls;
- risk levels;
- required review level;
- stop-and-ask triggers;
- safety constraints;
- relationship with local Villages;
- examples or intentional deferral of examples.
```

New Clans that affect agent behavior require Shikamaru drafting, Jounin review, and human approval.

## Naming rules

Clan names must be lowercase and hyphenated.

Good:

```text
data-engineering
machine-learning
software-engineering
technical-writing
security
```

Avoid:

```text
DataEngineering
data_engineering
misc
other
random
```

If a Clan name is too broad or vague, Shikamaru must request clarification before creating it.

## Review and escalation

A Clan requires Jounin review when:

```text
- it changes coding, review, safety, memory, or publication behavior;
- it introduces a new specialization;
- it affects multiple Scrolls;
- it changes risk or approval rules;
- it may expose local or private context.
```

Escalate to Kage Summit when:

```text
- the Clan changes doctrine-level behavior;
- multiple Clans disagree;
- the change may weaken safety or review;
- the change may affect public release readiness.
```

## Completion checklist for new Clans

Before a Clan is considered ready:

```text
- purpose is explicit;
- scope and non-scope are defined;
- risk levels are defined;
- required review level is defined;
- stop-and-ask triggers are defined;
- relationship with Scrolls is clear;
- relationship with local Villages is clear;
- no private context is included;
- no sensitive data is included;
- no copyrighted local assets or literature are included;
- Jounin review is complete;
- user approval is recorded.
```

## Final rule

Clans specialize the Academy.

They do not weaken it.
