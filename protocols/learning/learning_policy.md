# Learning Policy

Konoha Agentic Academy treats learning as a controlled process.

Agents may learn from missions, but they may not rewrite doctrine. Learning becomes doctrine only after review, approval, and Shikamaru drafting.

## Purpose

This policy defines how mission experience becomes reusable knowledge without allowing agents to silently change rules, protocols, Scrolls, configs, or local Village behavior.

The goal is to preserve improvement while avoiding drift, hallucinated rules, unsafe automation, and unapproved doctrine changes.

## Core principles

### 1. Experience is not doctrine

A Kagebunshin may report what happened during a mission.

It may not convert that experience into a rule by itself.

### 2. Evidence before learning

Every learning proposal must point to evidence.

Valid evidence includes:

- a mission log;
- a failing test;
- a repeated user clarification;
- a reviewed diff;
- a documented incident;
- a rejected assumption;
- a confirmed user correction;
- a Jounin review finding;
- a Kage Summit verdict.

If there is no evidence, the proposal remains an observation, not a learning candidate.

### 3. Local learning stays local by default

Learning from a Local Village belongs to that Village unless explicitly promoted.

A local lesson may become Academy doctrine only after review, sanitization, and human approval.

Sensitive, private, corporate, personal, credential-related, or project-specific context must never be promoted to the public Academy memory.

### 4. Summaries are not truth

Local models, Clerks, or cheap workers may summarize, tag, cluster, and prepare learning candidates.

Their output is not authoritative.

A summary may support a proposal, but it cannot approve a proposal.

### 5. No silent doctrine changes

No agent may silently modify:

- Konoha Laws;
- agent conduct;
- protocols;
- role policies;
- Scroll instructions;
- memory policies;
- approval rules;
- local Village doctrine;
- configuration that changes agent behavior.

Doctrine changes require Shikamaru and human approval.

## What counts as learning

A mission may produce a learning candidate when it reveals:

- a missing question that should have been asked earlier;
- a recurring ambiguity in user requests;
- a validation that prevented an error;
- a tactic that worked and should be reused;
- a tactic that failed and should be avoided;
- a repeated failure pattern;
- a safer approval boundary;
- a better Mission Charter field;
- a missing Scroll;
- a Scroll improvement;
- a new Clan candidate;
- a review checklist improvement;
- a documentation gap;
- a security risk;
- a token-saving pattern;
- a local model routing improvement;
- a Teachback issue where the user could not explain the result.

## Who may propose learning

The following roles may create a Learning Proposal:

- Hokage;
- Local Kage;
- Kagebunshin;
- Jounin;
- Shikamaru;
- Clerk;
- the user.

Only the user, or a user-approved governance flow, may approve doctrine changes.

## Learning Proposal format

Every Learning Proposal must use this structure:

```yaml
type: learning_proposal
id:
created_at:
reported_by:
source_mission:
scope: local | academy
village:
clan:
category: tactic | failure | correction | doctrine_change | scroll_improvement | protocol_improvement | security | model_routing | teachback
status: proposed
evidence:
  - type:
    reference:
summary:
problem_observed:
recommendation:
risk_if_ignored:
suggested_destination:
  path:
  reason:
requires_kage_summit: false
requires_human_approval: true
sensitive_context: false
```

## Learning flow

```text
Mission produces experience
        ↓
Agent creates Learning Proposal
        ↓
Hokage or Local Kage reviews relevance
        ↓
Jounin reviews risk and evidence when needed
        ↓
Kage Summit is called if the proposal is complex, strategic, risky, or cross-scope
        ↓
Shikamaru drafts the doctrine, Scroll, folder, or config change
        ↓
User reviews the proposed diff
        ↓
If approved, Shikamaru applies the change
        ↓
Jounin reviews consistency
        ↓
Yamanaka Memory records the outcome
```

## Approval levels

### Observation

A raw note from a mission.

No approval required.

It may be stored in memory but must not affect future behavior by itself.

### Learning Proposal

A structured recommendation.

Requires Hokage or Local Kage review.

### Accepted Learning

A proposal accepted as useful.

It may guide future missions locally, but it is still not doctrine unless drafted and approved.

### Doctrine Candidate

A proposal that would change rules, policies, protocols, Scrolls, or configs.

Requires Shikamaru drafting and human approval.

### Academy Doctrine

A promoted, approved, sanitized, public rule.

Requires:

- evidence;
- review;
- Shikamaru drafting;
- user approval;
- no sensitive local context;
- Jounin consistency review.

## Kage Summit triggers

A Learning Proposal must escalate to Kage Summit when it:

- changes a Konoha Law;
- creates a new Clan;
- changes approval boundaries;
- affects security;
- changes how agents use local or remote models;
- changes how sensitive context is handled;
- modifies Shikamaru authority;
- promotes local Village learning to Academy doctrine;
- affects multiple Clans;
- resolves conflicting protocols;
- requires external research;
- has unclear trade-offs.

## Shikamaru responsibilities

Shikamaru may:

- create doctrine files;
- edit doctrine files;
- create folders for new doctrine, Scrolls, Clans, protocols, or memory structures;
- draft changes from approved Learning Proposals;
- convert accepted learning into clear, maintainable Markdown;
- request Kagebunshin support for non-Markdown technical files.

Shikamaru may not:

- invent doctrine without evidence;
- bypass Hokage review;
- bypass human approval;
- promote local sensitive knowledge to public doctrine;
- silently change agent behavior.

## Clerk responsibilities

A Clerk may:

- summarize mission logs;
- extract candidate lessons;
- tag memory notes;
- cluster related events;
- prepare context packs;
- draft Learning Proposals for review.

A Clerk may not:

- approve learning;
- modify doctrine;
- close missions;
- escalate local context to Academy memory;
- decide that a lesson is generally valid.

## Storage

Academy-level learning should be stored under:

```text
memory/yamanaka/learning-proposals/
memory/yamanaka/accepted/
memory/yamanaka/rejected/
memory/yamanaka/promoted/
```

Local Village learning should be stored under:

```text
alliance/<village>/memory/yamanaka/learning-proposals/
alliance/<village>/memory/yamanaka/accepted/
alliance/<village>/memory/yamanaka/rejected/
alliance/<village>/memory/yamanaka/promoted/
```

Local Village memory is private by default and must be ignored by Git unless the user explicitly decides otherwise.

## Rejection reasons

A Learning Proposal may be rejected when:

- evidence is missing;
- the issue was caused by user-specific context;
- the recommendation is too broad;
- the proposal leaks sensitive context;
- the proposal duplicates existing doctrine;
- the tactic worked only by accident;
- the failure was not reproduced;
- the proposed rule would slow down normal missions unnecessarily;
- the proposal increases risk more than it reduces ambiguity.

Rejected proposals should remain stored with the rejection reason to prevent repeated discussion.

## Promotion rules

A local lesson may be promoted to Academy-level doctrine only when:

- it is sanitized;
- it is not tied to private data;
- it applies beyond one Village;
- it has clear evidence;
- it does not conflict with Konoha Laws;
- it improves safety, clarity, repeatability, or cost control;
- the user approves the promotion.

## Completion rule

A mission is not fully complete until learning has been handled.

At mission close, Hokage must decide one of the following:

```text
no_learning_detected
learning_proposal_created
learning_deferred
learning_rejected_with_reason
learning_escalated_to_kage_summit
```

This decision must be recorded in the Mission Log.
