# Token Budget Enforcement

Status: documentation-first baseline.

Konoha optimizes for safe, sufficient intelligence, not maximum intelligence by default.

This guide defines how token budgets are planned, monitored, enforced, exceeded, reviewed, and improved before runtime execution exists.

It does not implement token metering, billing integration, adapter quota queries, or automated enforcement.

## Purpose

Token governance exists to prevent Konoha from becoming too expensive or too context-heavy for continuous use.

A mission should not spend excessive tokens reading repeated instructions when a smaller validated context intake would be sufficient.

## Core principles

- Safety is not optional.
- Cost awareness is required.
- Context should be loaded by relevance, not by habit.
- Summaries reduce intake but do not replace source authority.
- A cheaper model is useful only if it is sufficiently capable.
- A token overage may be acceptable only when justified by mission risk, ambiguity, or evidence needs.
- Token savings must never bypass Mission Charter, approval, privacy, review, or stop conditions.

## Budget types

### Soft budget

A soft budget is the expected token range for a mission.

Crossing it does not automatically stop the mission, but it requires explanation.

### Hard budget

A hard budget is the maximum allowed range for a mission without explicit approval.

Crossing it requires stopping, reporting, and asking for continuation approval.

### Intake budget

The maximum intended context load before work begins.

Includes doctrine, guides, Scrolls, adapters, templates, local context, and capsules.

### Work budget

The expected token range for reasoning, drafting, review, or iteration.

### Output budget

The expected token range for user-facing results or generated artifacts.

### Review budget

The expected token range for review, validation, audit, or Jounin assessment.

## Budget modes

### Minimal

Use when the mission is simple, low risk, and well-scoped.

Expected behavior:

- load Tier 0 laws;
- load only one or two directly relevant references;
- use capsule-first when approved;
- avoid broad repo scans.

### Standard

Use for ordinary documentation, planning, review, or template work.

Expected behavior:

- load Tier 0 laws;
- load role-specific doctrine;
- load mission-specific Scrolls;
- use source-on-demand for detailed references.

### Expanded

Use for repo audits, release checkpoints, safety checks, adapter review, or runtime boundary work.

Expected behavior:

- load required source documents;
- use checklists;
- gather evidence;
- justify larger intake.

### Full-source required

Use for doctrine changes, safety boundaries, privacy decisions, approval policy, runtime authority, releases, or disputed interpretations.

Expected behavior:

- do not rely only on capsules;
- read authoritative source files;
- produce evidence;
- expect higher token usage.

## Enforcement rules

### Before mission work

A mission should define:

- task type;
- risk level;
- model tier;
- context mode;
- soft budget;
- hard budget;
- expected source files;
- expected capsules;
- escalation triggers.

### During mission work

Stop and ask when:

- hard budget is likely to be exceeded;
- the task requires more full-source reading than planned;
- repeated retries suggest the selected model is insufficient;
- the agent needs private context not authorized by the Mission Charter;
- the budget pressure would require skipping safety checks.

### After mission work

The mission closure should report:

- estimated or measured token usage;
- intake sources;
- capsules used;
- full files opened;
- retries;
- reviewer involvement;
- overage reason;
- whether the selected model tier was sufficient;
- suggested budget improvement.

## Overage classification

### Justified overage

An overage may be justified when:

- safety review required full-source reading;
- release audit required broad verification;
- private boundary validation required extra checks;
- previous summaries were stale;
- the selected model needed escalation and review.

### Questionable overage

An overage is questionable when:

- the agent loaded unrelated files;
- the agent reread stable doctrine unnecessarily;
- the model produced repeated failed attempts;
- the task could have used a capsule;
- the mission lacked scope discipline.

### Unacceptable overage

An overage is unacceptable when:

- safety checks were skipped to save tokens;
- private context was accessed without authorization;
- the agent continued after a hard budget stop;
- the agent used a high-cost model without routing rationale;
- the overage was hidden from the mission report.

## Model interaction

Token budget enforcement is connected to model routing.

A lower tier model may be selected when:

- the task is bounded;
- a validated capsule exists;
- expected output is structured;
- failure risk is low;
- a reviewer can validate the result.

A higher tier model is required when:

- ambiguity is high;
- safety or privacy risk is high;
- doctrine interpretation is required;
- adapter/runtime authority is involved;
- previous attempts failed.

## Capsule interaction

Capsules may reduce repeated context intake, but they must include:

- source paths;
- source hashes;
- generated date;
- approval status;
- stale detection;
- limitations;
- full-source fallback conditions.

A stale capsule must not be used for authority-sensitive work.

## Session resource probe interaction

If an adapter can expose token/quota/resource state, the mission may use a Session Resource Probe.

If no reliable resource signal exists, Konoha must not invent one.

Allowed confidence levels:

- measured;
- adapter-reported;
- user-provided;
- estimated;
- unavailable.

## Stop conditions

Stop and ask when:

- the hard budget is reached or likely to be reached;
- continuing requires private context not authorized;
- continuing requires a higher-risk model tier;
- the budget can only be met by skipping required review;
- the adapter cannot provide requested resource data and the mission depends on it;
- cost pressure conflicts with safety.

## Non-goals

This baseline does not provide:

- real token metering;
- billing integration;
- vendor-specific quota parsing;
- automatic throttling;
- executable runtime enforcement;
- automatic model switching;
- private usage logs.

## Required review

Token budget enforcement should be reviewed before:

- runtime implementation;
- adapter implementation;
- context capsule automation;
- automated eval runner work;
- local private context integration;
- repeated high-cost mission workflows.

## Completion criteria

A mission using this guide is complete only when:

- budget mode is documented;
- model tier is documented;
- context intake is documented;
- overages are classified;
- safety was not weakened;
- improvement notes are captured.
