# Scrolls

Scrolls are reusable, activatable skills that guide agent behavior for a specific workflow.

A Scroll is not general doctrine. Doctrine defines what agents must always respect. A Scroll defines how an agent should perform a bounded task when that Scroll is selected by the Hokage and allowed by the Mission Charter.

## Core rule

A Scroll may guide execution, but it may not override KonoHA Laws, Safety Policy, Context Policy, Approval Policy, Mission Charter boundaries, or local Village rules.

If a Scroll conflicts with higher doctrine, the Scroll loses.

## What a Scroll is

A Scroll is a reusable workflow, capability, checklist, or operating pattern.

Examples:

- systematic debugging;
- repository exploration;
- diff review;
- humanized writing;
- scientific writing;
- Docker review;
- data pipeline validation;
- context pack generation;
- mission postmortem writing.

A Scroll should help an agent do one job clearly.

## What a Scroll is not

A Scroll is not:

- a law;
- a Mission Charter;
- a full project context;
- a memory entry;
- a personality file;
- a place to hide assumptions;
- permission to execute actions;
- proof that a task is complete.

## Scroll structure

Recommended structure:

```text
scrolls/
  <clan-or-domain>/
    <scroll-name>/
      SCROLL.md
      examples/
      tests/
      assets/
      scripts/
      README.md
```

Minimum viable Scroll:

```text
scrolls/
  <clan-or-domain>/
    <scroll-name>/
      SCROLL.md
```

## Required fields

Every `SCROLL.md` must define:

```yaml
name:
version:
status: draft | active | deprecated | archived
language:
clan:
purpose:
activation_triggers:
allowed_tasks:
forbidden_tasks:
required_inputs:
outputs:
risk_level: low | medium | high | critical
review_level: none | clerk | jounin | kage_summit
requires_hokage_approval: true | false
requires_human_approval: true | false
```

## Required sections

Every Scroll should include:

```text
# <Scroll name>

## Purpose
## Activation triggers
## When not to use this Scroll
## Required inputs
## Workflow
## Evidence requirements
## Stop-and-ask triggers
## Outputs
## Review requirements
## Examples
## Failure modes
## Related doctrine
```

## Activation

The Hokage selects Scrolls before assigning work.

A Kagebunshin may not silently select a Scroll unless the Mission Charter allows self-selection for that mission.

When a Scroll is selected, the assignment must state:

```yaml
selected_scrolls:
  - name:
    version:
    reason:
    scope:
```

## Progressive context

Scrolls must be loaded only when relevant.

Konoha should not load every Scroll into every mission. The Hokage should select the smallest useful Scroll set for the mission.

## Language policy

Core Scrolls are written in English.

Writing Scrolls may be written in their target language when language nuance matters.

Examples:

```text
scrolls/writing/humanize-en/SCROLL.md     # English
scrolls/writing/humanize-es/SCROLL.md     # Spanish
scrolls/writing/scientific-writing-es/    # Spanish
```

A writing Scroll should not be a literal translation of another writing Scroll when the language has different style risks, corporate habits, academic conventions, or AI-writing patterns.

## Scope

Each Scroll must have a narrow scope.

Good:

```text
systematic-debugging
repo-exploration
diff-review
humanize-es
docker-compose-review
```

Too broad:

```text
do-anything
be-a-good-agent
software-engineering
write-better
```

If a Scroll keeps growing across unrelated use cases, Shikamaru should propose either:

- splitting it;
- moving domain rules into a Clan;
- turning repeated behavior into doctrine;
- archiving the Scroll.

## Evidence requirements

A Scroll must define what evidence is required before the agent can claim success.

Examples:

```text
systematic-debugging:
- error reproduced or clearly explained;
- root cause identified;
- fix applied within scope;
- validation command executed or blocked with reason.

diff-review:
- changed files listed;
- out-of-scope changes checked;
- tests or validation reviewed;
- risks reported.

humanize-es:
- tone adjusted;
- inflated phrasing removed;
- meaning preserved;
- language matches target audience.
```

## Stop-and-ask triggers

Every Scroll must define when the agent must stop and ask.

Common triggers:

- required input is missing;
- task scope changed;
- context conflicts with Mission Charter;
- a sensitive file or secret appears;
- a command is not allowed;
- output would affect an external party;
- the Scroll is not enough for the task;
- confidence is below the required threshold.

## Review

A Scroll must declare the minimum review level.

Low-risk formatting Scrolls may allow Clerk review.

Technical, safety-sensitive, doctrine, architecture, data, model, or external communication Scrolls require Jounin review or higher.

A Scroll cannot lower the review level required by the Mission Charter.

## Scroll lifecycle

```text
draft
  ↓
tested
  ↓
active
  ↓
revised
  ↓
deprecated
  ↓
archived
```

## Draft

A draft Scroll can be explored, but should not control production work.

## Tested

A tested Scroll has examples, expected outputs, and at least one real or synthetic scenario showing how it behaves.

## Active

An active Scroll can be selected by the Hokage during missions.

## Revised

A revised Scroll must record what changed, why it changed, and what evidence supports the change.

## Deprecated

A deprecated Scroll should not be selected for new missions unless explicitly approved.

## Archived

An archived Scroll is kept for traceability only.

## Creating a new Scroll

A new Scroll may be proposed by:

- Hokage;
- Kagebunshin;
- Jounin;
- Shikamaru;
- Clerk;
- user;
- Kage Summit.

Only Shikamaru may create or modify official Scroll Markdown.

For non-Markdown technical assets, scripts, tests, or examples, Shikamaru may prepare the structure and assign implementation to a Kagebunshin.

## Creation workflow

```text
1. Learning Proposal or user request identifies repeated need.
2. Hokage decides whether a Scroll is appropriate.
3. If the need is complex or cross-domain, Kage Summit reviews it.
4. Shikamaru drafts the Scroll.
5. User approves the proposed doctrine or Scroll behavior.
6. Jounin reviews consistency and safety.
7. Scroll becomes draft or active depending on evidence.
```

## Importing external Scrolls

External Scrolls are untrusted by default.

Before importing an external Scroll, Konoha must record:

```yaml
source:
license:
version:
commit_or_hash:
review_status:
reviewed_by:
import_reason:
known_risks:
```

Imported Scrolls must be reviewed for:

- hidden assumptions;
- unsafe commands;
- excessive permissions;
- vague success criteria;
- prompt injection risk;
- incompatible doctrine;
- privacy risks;
- unclear licensing.

## Public vs local Scrolls

Public Academy Scrolls must be generic and safe.

Local Village Scrolls may include project-specific context, corporate tone, local paths, private workflows, or sensitive rules.

Local Scrolls must stay local by default.

A local Scroll may only be promoted to the Academy after review, sanitization, Shikamaru drafting, and user approval.

## Scrolls and memory

A memory entry may suggest a Scroll improvement, but memory does not modify Scrolls.

A Learning Proposal may request a new Scroll or Scroll revision.

An approved tactic may become a Scroll only after Shikamaru drafts it and review confirms it is reusable.

## Scrolls and Mission Charter

The Mission Charter controls the mission.

A Scroll may define a workflow, but it cannot add permissions not present in the Mission Charter.

If the Scroll recommends an action outside the Mission Charter, the Kagebunshin must stop and ask.

## Violations

Violations include:

- using a Scroll outside its scope;
- treating a Scroll as permission;
- hiding assumptions inside a Scroll;
- modifying Scroll doctrine without Shikamaru;
- importing external Scrolls without review;
- claiming a Scroll succeeded without evidence;
- lowering review requirements through a Scroll;
- storing sensitive local context in a public Scroll.

## Completion checklist for a Scroll

A Scroll is ready for active use only when:

```text
- purpose is clear;
- activation triggers are explicit;
- required inputs are listed;
- forbidden tasks are listed;
- workflow is actionable;
- evidence requirements are defined;
- stop-and-ask triggers are defined;
- review level is defined;
- examples exist or are intentionally deferred;
- related doctrine is referenced;
- Shikamaru drafted or approved the Markdown;
- user approved the behavior if it affects doctrine.
```
