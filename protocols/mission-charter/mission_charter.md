# Mission Charter Policy

## Purpose

A Mission Charter is the execution contract for a Konoha mission.

It defines what was requested, what the Hokage understood, what is allowed, what is forbidden, which agents are assigned, what evidence is available, what requires approval, and how the mission will be considered complete.

The Mission Charter exists to prevent assumption-driven work, scope creep, silent changes, and fabricated success.

## Core rule

No Kagebunshin may execute a mission without an approved Mission Charter when the mission involves file changes, command execution, configuration changes, doctrine changes, memory updates, external communication, or any sensitive context.

If the Mission Charter does not explicitly allow an action, the Kagebunshin must stop and ask.

Explicit permission is required. Inference is not permission.

## When a Mission Charter is required

A Mission Charter is required when a mission may involve any of the following:

- modifying, creating, deleting, moving, or renaming files;
- executing commands;
- changing configuration;
- creating or modifying doctrine;
- creating or modifying Scrolls;
- updating Academy or Village memory;
- generating deliverables for third parties;
- using private, sensitive, business, academic, legal, medical, financial, or personal context;
- assigning work to Kagebunshin;
- requesting Jounin review;
- invoking Shikamaru;
- escalating to a Kage Summit.

A full Mission Charter is not required for casual conversation, brainstorming, or low-risk discussion, unless the discussion becomes actionable.

## Mission modes

Konoha recognizes three mission modes.

### Conversation mode

Used for discussion, brainstorming, or clarification.

No files are modified. No commands are executed. No doctrine is changed. No memory is updated unless the user explicitly asks to save a note.

### Planning mode

Used to inspect, reason, ask questions, and prepare a Mission Charter.

Planning mode may read allowed context, but it may not modify files, execute risky commands, or assign implementation work unless the user has explicitly approved those actions.

### Execution mode

Used when a Mission Charter has been approved and assigned agents may act within its boundaries.

Execution mode requires explicit scope, allowed actions, forbidden actions, approval rules, and acceptance criteria.

## Minimum required fields

Every Mission Charter must include the following fields.

```yaml
mission_id:
title:
requested_by:
created_at:
mission_type:
village:
clan:
priority:
urgency:

user_request:
hokage_understanding:
explicit_goals:
explicit_non_goals:

allowed_paths:
forbidden_paths:
allowed_commands:
forbidden_commands:

allowed_actions:
requires_approval:
forbidden_actions:

context_sources:
missing_context:
context_confidence:

assigned_agents:
reviewer:
scribe_required:

acceptance_criteria:
teachback_required:
memory_required:

status:
```

Fields may be marked as `not_applicable` only when they truly do not apply. They must not be omitted silently.

## Scope and boundaries

The Mission Charter must separate goals from non-goals.

A goal is something the mission must accomplish.

A non-goal is something the mission must not attempt, even if it appears related.

Example:

```yaml
explicit_goals:
  - Create an initial README draft for the local Village setup.

explicit_non_goals:
  - Do not change Academy doctrine.
  - Do not create new Scrolls.
  - Do not configure real email access.
  - Do not commit or push changes.
```

## Allowed and forbidden paths

The Mission Charter must list allowed and forbidden paths when a mission can touch files.

Example:

```yaml
allowed_paths:
  - alliance/templates/
  - docs/

forbidden_paths:
  - .env
  - secrets/
  - credentials/
  - alliance/kirigakure/
  - memory/vault/private/
```

If a path is not listed as allowed, the agent must not modify it.

Forbidden paths always win over allowed paths.

## Allowed and forbidden commands

The Mission Charter must list allowed and forbidden commands when a mission can execute commands.

Example:

```yaml
allowed_commands:
  - git status
  - git diff
  - pytest
  - npm test

forbidden_commands:
  - rm -rf
  - git push
  - git commit
  - curl | bash
  - docker system prune
  - reading .env files
```

A Kagebunshin must not execute commands that are not explicitly allowed.

Read-only inspection commands may be allowed in planning mode only when explicitly authorized.

## Approval levels

A Mission Charter may define approval levels.

```yaml
approval_levels:
  auto:
    - read allowed files
    - summarize context
    - generate proposals

  hokage_approval:
    - assign Kagebunshin
    - approve execution plan
    - request Jounin review

  human_approval:
    - modify files
    - change configuration
    - install dependencies
    - update memory
    - create doctrine
    - commit
    - push
    - send external messages
```

Human approval is required for sensitive, irreversible, external, or doctrine-changing actions.

## Context confidence

The Hokage must estimate context confidence before execution.

```yaml
context_confidence:
  score: 0.0
  level: low | medium | high
  reason:
  missing_context:
```

Guidelines:

- `high`: the request, scope, inputs, outputs, permissions, and acceptance criteria are explicit.
- `medium`: the mission can proceed with limited scope, but some assumptions are blocked.
- `low`: the mission must not execute. The Hokage must ask questions first.

A Kagebunshin must not execute a mission with low context confidence.

## Stop-and-ask triggers

A Kagebunshin must stop and ask the Hokage when any of the following occurs:

- the next action is not explicitly allowed;
- the instruction is ambiguous;
- required context is missing;
- a file or command is outside the Mission Charter;
- an error contradicts the expected path;
- tests fail for reasons unrelated to the mission;
- sensitive data, credentials, or personal information appear;
- the task requires a new dependency;
- the agent detects scope creep;
- the agent needs to modify doctrine or memory;
- the agent cannot explain why a change is needed;
- the agent cannot verify success.

When a stop-and-ask trigger occurs, the Kagebunshin must report:

```yaml
blocked_reason:
needed_decision:
options:
recommended_option:
risk_if_continue_without_answer:
```

## Mission states

A mission may use the following states:

```yaml
status:
  - draft
  - waiting_for_context
  - waiting_for_approval
  - approved
  - in_progress
  - blocked
  - ready_for_review
  - changes_requested
  - ready_for_teachback
  - completed
  - archived
```

A mission is not complete just because an agent finished its work.

The mission reaches `completed` only after review, acceptance criteria, memory requirements, and teachback requirements are satisfied.

## Assigned agents

The Mission Charter must define which agents are assigned and what each one may do.

Example:

```yaml
assigned_agents:
  hokage:
    role: orchestrator
    permissions:
      - understand request
      - ask questions
      - approve or block worker execution

  kagebunshin:
    role: worker
    permissions:
      - modify allowed paths
      - run allowed commands

  jounin:
    role: reviewer
    permissions:
      - review diff
      - check scope compliance
      - check acceptance criteria

  shikamaru:
    role: scribe
    permissions:
      - draft doctrine updates after approval
```

Agents may have narrower permissions than the Mission Charter, but they may not have broader permissions.

## Acceptance criteria

Every execution mission must define acceptance criteria.

Acceptance criteria must be observable and verifiable.

Bad example:

```yaml
acceptance_criteria:
  - Make it better.
```

Good example:

```yaml
acceptance_criteria:
  - README contains purpose, setup, local memory policy, and safety notes.
  - No private Village content is committed.
  - git status shows only expected files changed.
  - Jounin review finds no scope violations.
```

## Teachback requirement

If the mission creates code, documentation, analysis, strategy, or a deliverable the user may need to explain, the Mission Charter should require teachback.

```yaml
teachback_required: true
```

A mission with teachback enabled is complete only when the user can explain:

- what was done;
- why it was done;
- how it works;
- what risks or assumptions remain;
- how to explain it to another person.

## Memory requirement

The Mission Charter must define whether the mission should update memory.

```yaml
memory_required:
  enabled: true
  destination: local_village
  summary_required: true
  raw_archive_required: false
```

Memory updates must follow the Yamanaka Memory Policy and Learning Policy.

A summary generated by a local model is not doctrine and must not be treated as verified truth unless reviewed.

## Mission Charter template

```yaml
mission_id: ""
title: ""
requested_by: "user"
created_at: ""
mission_type: ""
village: ""
clan: ""
priority: "normal"
urgency: "normal"

user_request: ""
hokage_understanding: ""

explicit_goals:
  - ""

explicit_non_goals:
  - ""

allowed_paths:
  - ""

forbidden_paths:
  - ""

allowed_commands:
  - ""

forbidden_commands:
  - ""

allowed_actions:
  - ""

requires_approval:
  - ""

forbidden_actions:
  - ""

context_sources:
  - ""

missing_context:
  - ""

context_confidence:
  score:
  level:
  reason: ""

assigned_agents:
  hokage:
    role: "orchestrator"
    permissions: []

  kagebunshin:
    role: "worker"
    permissions: []

  jounin:
    role: "reviewer"
    permissions: []

  shikamaru:
    role: "scribe"
    permissions: []

reviewer: ""
scribe_required: false

acceptance_criteria:
  - ""

teachback_required: true

memory_required:
  enabled: true
  destination: "local_village"
  summary_required: true
  raw_archive_required: false

status: "draft"
```

## Violations

The following are Mission Charter violations:

- executing without a required Mission Charter;
- modifying paths that were not explicitly allowed;
- running commands that were not explicitly allowed;
- continuing after a stop-and-ask trigger;
- treating missing context as permission;
- changing doctrine without Shikamaru workflow;
- updating memory without approval;
- declaring success without acceptance criteria;
- skipping teachback when required;
- hiding uncertainty or failure.

Violations must be recorded in the Mission Log and may trigger Jounin review, Hokage review, Shikamaru doctrine correction, or Kage Summit escalation.

## Relationship with other policies

This policy works with:

- `protocols/approval/approval_policy.md`
- `protocols/context/context_policy.md`
- `protocols/learning/learning_policy.md`
- `protocols/review/review_policy.md`
- `protocols/safety/safety_policy.md`
- `shikamaru/scribe_policy.md`
- `memory/yamanaka/yamanaka_memory_policy.md`

If there is a conflict, safety, privacy, explicit user instruction, and Konoha Laws take priority.
