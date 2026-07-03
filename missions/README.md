# Missions

Missions are the operational unit of Konoha Agentic Academy.

A Mission is a bounded task with a clear request, explicit scope, approved permissions, assigned agents, review requirements, memory requirements, and completion criteria.

Missions are not open-ended autonomy. A Mission exists to make agent work traceable, reviewable, teachable, and safe.

## Core rule

No execution happens without an approved Mission Charter.

If the Mission Charter does not explicitly allow an action, the agent must stop and ask.

Inference is never permission.

## What a Mission is

A Mission may be:

- a conversation or clarification session;
- a planning task;
- a coding task;
- a debugging task;
- a writing task;
- a research task;
- a review task;
- a memory curation task;
- a local Village setup task;
- a doctrine proposal;
- a Kage Summit escalation.

A Mission must have boundaries. If the work expands beyond those boundaries, the Hokage must update the Mission Charter or escalate.

## What a Mission is not

A Mission is not:

- permission to touch anything in the repository;
- permission to read private context;
- permission to execute arbitrary commands;
- permission to modify doctrine;
- permission to skip review;
- permission to declare success without evidence;
- permission to store sensitive content;
- permission to continue when context is missing.

## Mission modes

### Conversation mode

Used for discussion, brainstorming, explanation, and clarification.

Conversation mode may not modify files, run commands, create memory records, or execute workflows unless a Mission Charter is created and approved.

### Planning mode

Used to understand the request, inspect allowed context, ask questions, create a Mission Charter, and propose execution.

Planning mode may read allowed files and produce plans, but may not modify project state unless explicitly approved.

### Execution mode

Used when a Mission Charter has been approved and the assigned Kagebunshin may act inside the defined scope.

Execution mode requires:

- explicit goal;
- allowed paths;
- forbidden paths;
- allowed commands;
- forbidden commands;
- assigned agent;
- review level;
- acceptance criteria;
- stop-and-ask triggers.

### Review mode

Used when a Jounin, Clerk, or Kage Summit evaluates the Mission output.

Review mode does not expand scope. It verifies whether the work matches the Mission Charter, meets quality requirements, and is safe to move forward.

### Teachback mode

Used after review, when the user must understand the result.

A Mission is not complete until Teachback requirements are satisfied when required by the Mission Charter.

### Learning mode

Used after the Mission to capture Learning Proposals, approved tactics, failures, or memory summaries.

Learning mode may propose doctrine changes, but it may not apply them without Shikamaru drafting and user approval.

## Mission lifecycle

```text
request received
    ↓
Hokage understanding
    ↓
context check
    ↓
questions if needed
    ↓
Mission Charter drafted
    ↓
approval
    ↓
agent assignment
    ↓
execution inside scope
    ↓
report
    ↓
review
    ↓
teachback when required
    ↓
memory update when required
    ↓
learning proposal when useful
    ↓
completion
```

## Mission states

Recommended states:

```text
requested
clarifying
charter_drafted
waiting_approval
approved
assigned
in_progress
waiting_user_input
blocked
under_review
changes_requested
review_approved
teachback_pending
teachback_passed
memory_pending
learning_pending
completed
cancelled
failed
escalated
```

A Mission may be blocked at any point by Safety Policy, Context Policy, Approval Policy, Review Policy, or the Hokage.

## Mission identifiers

Mission IDs should be short, sortable, and traceable.

Recommended format:

```text
mission-YYYYMMDD-short-title
```

Examples:

```text
mission-20260702-init-kirigakure
mission-20260702-review-scroll-policy
mission-20260702-debug-docker-pipeline
```

For local Villages, the Village name may be included:

```text
kirigakure-20260702-init-local-config
```

## Mission folder structure

When Missions are persisted, use a folder per Mission:

```text
missions/
  mission-YYYYMMDD-short-title/
    mission_charter.md
    mission_report.md
    review_report.md
    teachback.md
    learning_proposal.md
```

Local Villages may keep private Mission records in their own ignored memory or mission folders.

Public Missions must not contain secrets, private data, local-only context, sensitive work material, proprietary code, or copyrighted assets.

## Mission Charter

Every executable Mission must have a Mission Charter.

The Mission Charter defines:

- what was requested;
- what the Hokage understood;
- explicit goals;
- explicit non-goals;
- allowed paths;
- forbidden paths;
- allowed commands;
- forbidden commands;
- required approvals;
- assigned agents;
- selected Scrolls;
- context sources;
- missing context;
- context confidence;
- review level;
- acceptance criteria;
- Teachback requirements;
- memory requirements;
- stop-and-ask triggers.

The Mission Charter is the contract. It does not remove the authority of Safety Policy or Konoha Laws.

## Agent assignment

The Hokage assigns agents according to mission risk, complexity, and cost.

Possible assignments:

```text
Clerk
```

Used for low-risk formatting, summarization, tagging, basic checks, and context pack preparation.

```text
Genin
```

Used for simple, bounded tasks with low risk.

```text
Chunin
```

Used for normal implementation, writing, debugging, or structured work inside an approved scope.

```text
Jounin
```

Used for review, complex work, technical judgment, or safety-sensitive inspection.

```text
Sage
```

Used for high-complexity reasoning, architecture, hard debugging, and ambiguous trade-offs.

```text
Shikamaru
```

Used for doctrine drafting, Markdown policy updates, structural proposals, and knowledge architecture.

```text
Kage Summit
```

Used when the Mission exceeds normal authority, confidence, or scope.

## Review requirements

A Mission must receive the review level required by its Mission Charter.

Review levels:

```text
none
clerk
jounin
kage_summit
```

No Mission may be marked completed if the required review has not happened.

Clerk review is allowed only for low-risk structure, formatting, and completeness checks.

Jounin review is required for technical correctness, safety-sensitive changes, doctrine, public assets, code, architecture, memory promotion, external integrations, and medium or high risk.

## Stop-and-ask triggers

The assigned agent must stop and ask when:

- context is missing;
- the Mission Charter is incomplete;
- an action is not explicitly allowed;
- a required file or command is unknown;
- allowed paths are unclear;
- a forbidden path is needed;
- a command may modify state;
- a secret or private file is encountered;
- the task requires external network access;
- scope expands;
- review level appears too low;
- the user request conflicts with policy;
- evidence contradicts the Mission Charter;
- the agent cannot verify success.

Stopping is not failure. Continuing without permission is failure.

## Mission reports

Every execution Mission should produce a Mission Report.

Minimum report fields:

```yaml
mission_id:
assigned_agent:
status:
actions_taken:
files_read:
files_modified:
commands_run:
evidence:
tests_or_checks:
deviations_from_charter:
blocked_items:
risks:
open_questions:
review_required:
memory_required:
learning_proposal_required:
```

The report must be specific. It must not use vague claims such as "done", "fixed", "improved", or "works" without evidence.

## Completion requirements

A Mission can be completed only when:

- the approved Mission Charter was followed;
- all required work was executed inside scope;
- required review is complete;
- required Teachback is complete;
- required memory updates are complete;
- any Learning Proposal was created or explicitly skipped;
- no unresolved safety issue remains;
- evidence is traceable;
- the Hokage confirms the Mission state;
- the user approves completion when required.

## done_by_agent is not completed_by_user

Agent work may be done before the Mission is complete.

The Mission is complete only when the user understands the result at the level required by the Mission and can explain what was done, why it was done, and how to use or defend it.

## Learning after Missions

A Mission may produce:

- no learning;
- a Learning Proposal;
- an approved tactic;
- a failure pattern;
- a doctrine change proposal;
- a Scroll improvement proposal;
- a Clan creation proposal;
- a local Village rule proposal.

Learning does not automatically modify doctrine.

Shikamaru is required for doctrine drafting.

User approval is required before doctrine changes are applied.

## Violations

Mission violations include:

- executing without a Mission Charter;
- assuming permission from inference;
- modifying files outside allowed paths;
- running commands outside allowed commands;
- skipping required review;
- skipping required Teachback;
- declaring success without evidence;
- storing sensitive context without permission;
- using local memory as permission;
- expanding scope silently;
- hiding uncertainty;
- fabricating results.

Violations must be reported to the Hokage.

Risky or repeated violations may block the agent, Scroll, tool, adapter, or workflow until review.
