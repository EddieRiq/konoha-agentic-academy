# Clans README

## Purpose

Clans are specialization domains inside Konoha Agentic Academy.

A Clan groups related Scrolls, reviewers, tactics, examples, policies, and mission patterns around a specific type of work.

Clans exist to prevent the Academy from becoming a flat collection of unrelated prompts and rules.

## Core rule

A Clan may specialize behavior, but it may not override Konoha Laws, Safety Policy, Context Policy, Approval Policy, or Mission Charter boundaries.

If a Clan rule conflicts with a higher-level rule, the higher-level rule wins.

## What a Clan is

A Clan is a structured specialization area.

Examples:

```text
clans/
  software-engineering/
  data-engineering/
  machine-learning/
  writing/
  research/
  security/
  devops/
```

Each Clan may define:

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
- a replacement for the Mission Charter.
```

## Clan vs Scroll

A Clan is a specialization domain.

A Scroll is an activable skill, workflow, or capability.

Example:

```text
Clan:
data-engineering

Scrolls:
docker-pipeline-review
airflow-dag-debugging
parquet-dataset-validation
dbt-model-review
```

The Clan organizes the field. The Scroll performs a specific workflow.

## Clan vs Village

A Clan is general.

A Village is local.

Example:

```text
clans/data-engineering/
```

Defines general data engineering behavior for the Academy.

```text
alliance/kirigakure/
```

Contains private local project context, local memory, local assets, local style, and local configuration.

Local Village rules may specialize how a Clan is used, but may not weaken Academy safety rules.

## When to create a new Clan

A new Clan may be proposed when repeated missions show that a domain needs its own rules, reviewers, Scrolls, examples, or acceptance criteria.

A new Clan may be justified when:

```text
- the same type of mission appears repeatedly;
- existing Clans do not cover the work clearly;
- the domain has distinct safety risks;
- the domain has distinct validation rules;
- the domain needs specialized reviewers;
- the domain needs its own Scrolls;
- repeated failures show that general rules are not enough.
```

A new Clan should not be created for a one-off task.

## Who may create a Clan

A Kagebunshin, Jounin, Clerk, Hokage, Local Kage, or user may propose a new Clan.

Only Shikamaru may create the official Clan folder and Markdown doctrine after approval.

Technical files inside a Clan must be implemented by assigned Kagebunshin unless the Mission Charter explicitly allows Shikamaru to create them.

## Clan creation workflow

```text
1. A mission reveals a repeated or specialized need.
2. A Learning Proposal is created.
3. The Hokage reviews the proposal.
4. If the impact is local, the Local Kage may keep it inside the Village.
5. If the impact is general, the Hokage may escalate to Kage Summit.
6. The Kage Summit produces a verdict when needed.
7. Shikamaru drafts the Clan structure and doctrine.
8. The user approves the proposed diff.
9. Shikamaru creates the Clan folder and Markdown files.
10. Jounin reviews consistency.
```

No Clan becomes official without approval.

## Recommended Clan structure

A mature Clan may use this structure:

```text
clans/<clan-name>/
  README.md
  policies/
  scrolls/
  examples/
  reviews/
  tactics/
  failures/
  evals/
```

Minimal Clans may start with only:

```text
clans/<clan-name>/
  README.md
```

Do not create empty structure unless the purpose is clear.

## Suggested Clan README sections

Each Clan README should explain:

```text
- purpose;
- scope;
- non-scope;
- common mission types;
- required context;
- common risks;
- required review level;
- recommended Scrolls;
- stop-and-ask triggers;
- acceptance criteria;
- memory requirements;
- escalation rules.
```

## Clan risk levels

A Clan should define when work is low, medium, high, or critical risk.

Example:

```text
low:
  - formatting documentation;
  - summarizing existing context;
  - generating non-sensitive examples.

medium:
  - editing scripts;
  - creating tests;
  - updating project documentation.

high:
  - changing production logic;
  - modifying pipelines;
  - changing dependencies;
  - touching sensitive data;
  - changing model behavior.

critical:
  - modifying safety rules;
  - changing doctrine;
  - promoting local memory to Academy memory;
  - creating new permissions;
  - handling credentials or personal data.
```

## Clan reviewers

Each Clan may recommend reviewers.

Examples:

```text
software-engineering:
  reviewer: jounin-code-reviewer

data-engineering:
  reviewer: jounin-data-pipeline-reviewer

machine-learning:
  reviewer: jounin-model-risk-reviewer

writing:
  reviewer: clerk-review for low-risk drafts, jounin-review for sensitive communications

security:
  reviewer: jounin-security-reviewer
```

A Clerk may review formatting, completeness, and low-risk structure.

A Clerk may not approve technical correctness, safety-sensitive changes, doctrine, or high-risk mission closure.

## Clan-specific Scrolls

Scrolls may live inside a Clan when they are domain-specific.

Example:

```text
clans/data-engineering/scrolls/parquet-dataset-validation/
clans/security/scrolls/secrets-scan-review/
clans/writing/scrolls/humanize-es/
```

General Scrolls should live in the top-level `scrolls/` directory.

## Clan memory

Clan memory may include reusable tactics, failure patterns, and examples.

Public Clan memory must not contain private Village context.

Local Village memory may reference Clan tactics, but should remain inside the local Village.

## Promotion from Village to Clan

A local Village may discover a tactic that belongs in a public Clan.

Promotion requires:

```text
- sanitized Learning Proposal;
- no secrets or private context;
- evidence from at least one mission;
- Hokage review;
- Shikamaru drafting;
- user approval;
- Jounin review.
```

Local learning stays local by default.

## Stop-and-ask triggers

A Clan must stop and ask when:

```text
- the mission requires context outside the Mission Charter;
- the domain is unclear;
- the required reviewer is unknown;
- the risk level is unclear;
- the task may belong to another Clan;
- the action may change doctrine;
- the action may expose sensitive context;
- the action may require human approval.
```

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

## Completion checklist for new Clans

Before a Clan is considered ready:

```text
- purpose is explicit;
- scope and non-scope are defined;
- risk levels are defined;
- required review level is defined;
- stop-and-ask triggers are defined;
- relationship with Scrolls is clear;
- no private context is included;
- no sensitive data is included;
- no copyrighted local assets are included;
- Jounin review is complete;
- user approval is recorded.
```

## Final rule

Clans specialize the Academy.

They do not weaken it.
