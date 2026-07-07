# Model Routing and Token Governance

Status: documentation-first baseline.

This guide defines how Konoha selects models, budgets context, monitors token usage, and reviews whether a model was sufficient for a mission.

It does not implement model routing, token metering, autonomous execution, billing integration, or adapter runtime.

## Purpose

Konoha should be safe, useful, and economically sustainable.

The goal is not to always use the strongest model. The goal is to use the cheapest sufficiently capable model while preserving safety, evidence, review, and user trust.

Core principle:

```text
Use the cheapest capable model, but prove capability through evals, evidence, and review.
```

Operational phrasing:

```text
Konoha optimizes for safe, sufficient intelligence, not maximum intelligence by default.
```

## Problems this guide addresses

Large instruction repositories can create hidden operational cost.

If every mission loads all doctrine, all Scrolls, all guides, all role files, and all adapter policies, then the system may spend most of its budget understanding what it is allowed to do instead of solving the mission.

This guide exists to prevent:

- excessive instruction intake;
- unnecessary use of expensive models;
- repeated loading of irrelevant Markdown files;
- retries caused by underpowered model selection;
- false economy from cheap models that require multiple corrections;
- unsafe delegation to models that cannot handle the mission;
- unreviewed downgrades in model tier;
- untracked token overages.

## Non-goals

This guide does not:

- grant runtime execution authority;
- authorize private-context access;
- replace the Mission Charter;
- replace Konoha laws;
- replace adapter permission matrices;
- require any specific provider;
- assume token availability can always be measured;
- treat estimated token usage as exact accounting.

## Model tiers

Konoha may describe model choices using tiers rather than vendor-specific names.

### Tier 0: Clerk

Used for low-risk mechanical tasks.

Examples:

- classify files;
- generate indexes;
- summarize non-sensitive public docs;
- extract headings;
- prepare checklists;
- format reports;
- draft simple Markdown.

Default permissions:

- read public allowed scope;
- propose-only;
- no execution authority;
- no private-context access by default.

### Tier 1: Draft Worker

Used for constrained drafting and template completion.

Examples:

- write first-pass docs;
- fill approved templates;
- draft eval cases;
- draft release notes from known changes;
- prepare Mission Charter drafts.

Default permissions:

- propose-only;
- dry-run allowed when authorized;
- no self-approval.

### Tier 2: Specialist Worker

Used for bounded technical tasks.

Examples:

- code review with a rubric;
- adapter manifest review;
- eval case design;
- Python design proposals;
- documentation consistency checks.

Default permissions:

- propose-only unless explicitly authorized;
- may request source-on-demand;
- must provide evidence.

### Tier 3: Reviewer / Jounin

Used for quality, safety, permission, and evidence review.

Examples:

- approve whether lower-tier work is sufficient;
- identify missing guardrails;
- validate eval results;
- review promotion proposals;
- review release readiness.

Default permissions:

- review only;
- cannot execute unless Mission Charter explicitly grants execution authority.

### Tier 4: Orchestrator / Hokage

Used for mission planning, routing, escalation, and closure.

Examples:

- assign tasks;
- choose initial tier;
- decide when to escalate;
- manage tradeoffs between cost, quality, and risk;
- close missions after teachback.

Default permissions:

- orchestrates;
- does not execute directly;
- does not bypass safety rules.

## Routing inputs

A model routing decision should consider:

- mission type;
- expected risk;
- required files;
- private-context exposure;
- required reasoning depth;
- reversibility of the action;
- availability of validated context capsules;
- eval history for similar tasks;
- required reviewer tier;
- expected token budget;
- user urgency;
- whether exactness matters more than speed or cost.

## Mission complexity classes

### Simple

Examples:

- index update;
- formatting;
- typo correction;
- non-sensitive README update;
- template filling.

Default routing:

- Tier 0 or Tier 1;
- capsule-first;
- reviewer optional unless publishing or policy changes are involved.

### Standard

Examples:

- guide creation;
- Scroll creation;
- public documentation package;
- changelog update;
- safe release note drafting.

Default routing:

- Tier 1 or Tier 2;
- capsule-first with source-on-demand;
- reviewer required for doctrine, release, security, or adapter changes.

### Complex

Examples:

- runtime planning;
- permission architecture;
- eval strategy;
- public/private boundary design;
- model routing design.

Default routing:

- Tier 2 with Tier 3 review;
- source-on-demand;
- full-source required for policy conflicts.

### Sensitive

Examples:

- private Village context;
- local memory;
- private literature;
- credentials;
- project-specific internal data;
- command, filesystem, Git, or release operations.

Default routing:

- explicit Mission Charter required;
- least-context necessary;
- full source for relevant safety rules;
- Tier 3 review;
- user approval before action.

## Context modes

### Capsule-first

Use a validated context capsule before loading full sources.

Allowed for:

- common tasks;
- low-risk tasks;
- repeated workflows;
- template generation;
- simple index updates.

### Source-on-demand

Start from a capsule and open source files only when needed.

Allowed for:

- standard docs;
- bounded technical design;
- review tasks.

### Full-source required

Read the authoritative source files directly.

Required for:

- doctrine changes;
- safety conflicts;
- approval decisions;
- release readiness;
- private-boundary questions;
- adapter/runtime permissions;
- ambiguous instructions;
- stale or missing capsules.

### Stop-and-ask

Stop if the needed context exceeds budget or authority.

Required when:

- private context is requested without approval;
- model capability is insufficient;
- token budget is exceeded without justification;
- routing choice is uncertain and risk is high;
- the adapter cannot report enough evidence.

## Capability is not authorization

A model may be technically able to do a task and still lack authorization.

Konoha separates:

```text
capability -> what a model can do
authorization -> what the Mission Charter and policies allow it to do
sufficiency -> whether the result is good enough
```

A lower-tier model may perform a higher-tier task only when:

- the task is narrowed;
- the prompt is reinforced;
- the context capsule is validated;
- the output is propose-only or dry-run;
- reviewer checks are defined;
- escalation triggers are explicit.

## Escalation triggers

Escalate to a higher tier when:

- the model asks for broad source loading;
- the model cannot cite evidence;
- output contains unsupported claims;
- retries exceed the expected budget;
- the action touches private context;
- the action affects safety, permissions, Git, release, runtime, or doctrine;
- the model contradicts the Mission Charter;
- the reviewer finds repeated defects.

## Downgrade rules

A task may be downgraded to a lower tier only when there is evidence that the lower tier is sufficient.

Evidence may include:

- prior successful evals;
- prior successful missions;
- stable context capsule;
- narrow prompt;
- clear checklist;
- low-risk output;
- reviewer pass history.

Downgrade must not be based only on cost pressure.

## Token budget dimensions

A mission budget should separate:

- intake budget;
- reasoning/work budget;
- output budget;
- review budget;
- retry budget.

A cheap first pass is not successful if it creates expensive review and retry cycles.

## Token usage review

After each significant mission, record:

- planned model tier;
- actual model tier;
- context mode;
- files or capsules loaded;
- full-source reads;
- estimated or actual token usage;
- retries;
- reviewer effort;
- result quality;
- overage reason;
- whether the overage was justified;
- recommended routing next time.

## Over-budget handling

If expected usage exceeds budget:

1. reduce scope;
2. switch to capsule-first if safe;
3. split mission into smaller parts;
4. ask user for approval to continue;
5. escalate only when quality or safety requires it.

Do not silently consume excessive context.

## Reviewer role

A reviewer may decide that:

- the model was sufficient;
- the model was underpowered;
- the prompt was too broad;
- the context intake was excessive;
- the task should be split;
- a capsule should be created;
- the task may be downgraded next time.

A model must not self-certify that it is sufficient for future work.

## Relationship to evals

Model routing should be informed by evals.

Eval cases should test:

- whether lower-tier models follow stop conditions;
- whether they preserve privacy;
- whether they can use capsules correctly;
- whether they escalate when needed;
- whether they avoid unsupported authority claims;
- whether token savings are achieved without quality loss.

## Relationship to runtime

Before runtime implementation, Konoha should know:

- which model tier can produce runtime plans;
- which tier can review runtime plans;
- which tier can create dry-run records;
- which tier can never execute commands;
- which tier requires human approval.

Runtime planning remains non-executing until runtime readiness is approved.
