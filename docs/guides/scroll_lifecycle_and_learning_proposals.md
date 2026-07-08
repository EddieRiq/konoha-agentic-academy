# Scroll Lifecycle and Learning Proposals

v2.4.0 adds a mission-local lifecycle for Scroll learning proposals.

The goal is to let Konoha learn from completed or ongoing missions without allowing agents to rewrite doctrine automatically.

## Core rule

```text
Agents may learn, but they may not rewrite doctrine.
Learning proposals are evidence only.
Review records do not rewrite doctrine.
Promotion plans are not permission to modify Scrolls.
```

## What this release adds

- A Scroll Lifecycle Manager CLI.
- Mission-local learning proposals.
- Mission-local lifecycle review records.
- Plan-only promotion records.
- Proposal indexing.
- Public schemas, examples, templates, tests, and review Scroll.

## Lifecycle states

```text
draft
review_required
approved_for_experiment
rejected
deferred
promotion_planned
```

## Review decisions

```text
approve_for_experiment
reject
defer
request_changes
plan_promotion
```

## Approval tokens

Recording a learning proposal requires:

```text
RECORD_LEARNING_PROPOSAL
```

Recording a lifecycle review requires:

```text
REVIEW_SCROLL_PROPOSAL
```

Planning promotion requires:

```text
PLAN_SCROLL_PROMOTION
```

These tokens authorize only their local evidence operation. They do not authorize doctrine rewrite, official Scroll modification, execution, model calls, adapter calls, repository apply, Git operations, private context access, or mission closure.

## Allowed actions

The Scroll Lifecycle Manager may:

- inspect an existing Mission Workspace;
- record a mission-local learning proposal;
- record a mission-local review decision;
- write proposal and review reports;
- build a mission-local proposal index;
- create a plan-only promotion record.

## Blocked actions

The Scroll Lifecycle Manager may not:

- rewrite doctrine;
- modify official Scroll definitions;
- execute mission actions;
- invoke models;
- invoke adapters;
- use network access;
- apply files to the repository;
- stage files;
- create commits;
- push changes;
- access private Village context by default;
- close missions.

## Shikamaru boundary

A proposal can become official doctrine only after a separate process:

```text
Learning Proposal
→ Hokage review
→ possible Kage Summit
→ Shikamaru drafting
→ Jounin review
→ explicit human approval
→ separate doctrine change
```

The v2.4 tool stops before doctrine modification.
