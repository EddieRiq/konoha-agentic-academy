# Review Policy

## Purpose

This policy defines how Konoha Agentic Academy reviews mission outputs before they are considered complete.

Review is not only a final check for correctness. It verifies that the mission stayed inside its approved scope, followed safety rules, used the required context, produced an understandable result, and is ready for user teachback and memory recording.

## Core rule

No mission may be marked as completed without the review level required by its risk, scope, and confidence.

A mission may skip review only when its Mission Charter explicitly classifies it as conversation-only, low-risk, and no-review-required.

## Review levels

Konoha uses review levels to avoid wasting strong models on simple checks while still protecting risky work.

### Level 0: no review

Level 0 may be used only for simple conversation or exploratory discussion with no persistent deliverable, no file changes, no external action, no memory update, and no technical or sensitive decision.

Examples:

- casual explanation;
- brainstorming without execution;
- informal clarification;
- conversation-only guidance.

Level 0 must not be used when the mission creates reusable output, modifies files, changes memory, handles sensitive context, or produces work intended for another person.

### Level 1: Clerk review

A Clerk may review low-risk structure, formatting, and completeness, but may not approve technical correctness, safety-sensitive changes, doctrine changes, or mission closure when risk is medium or high.

Clerk review is suitable for:

- Markdown formatting;
- spelling and grammar checks;
- required-field validation;
- basic checklist verification;
- simple summary comparison against the Mission Charter;
- detection of obvious placeholders or unfinished sections;
- detection of obvious secrets, `.env` files, credentials, or large unintended files.

Clerk review is not sufficient for:

- code correctness;
- architecture decisions;
- security-sensitive work;
- doctrine changes;
- Scroll behavior changes;
- sensitive communications;
- data handling decisions;
- production changes;
- changes involving dependencies, Docker, CI/CD, models, pipelines, or external systems.

If a Clerk is uncertain, finds missing context, detects a scope issue, or sees anything outside low-risk validation, it must escalate to Jounin review.

### Level 2: Jounin review

Jounin review is required for medium-risk or high-risk work.

Jounin review is required when a mission involves:

- code changes;
- multi-file changes;
- technical decisions;
- doctrine Markdown;
- Scroll behavior;
- promoted memory;
- sensitive context;
- work outputs for third parties;
- data processing;
- security;
- dependencies;
- Docker;
- Git operations;
- CI/CD;
- machine learning models;
- data engineering pipelines;
- production or production-like workflows.

A Jounin verifies both mission compliance and quality.

### Level 3: Kage Summit review

Kage Summit review is required when the mission involves strategic, ambiguous, high-impact, or cross-domain decisions.

Kage Summit review may be required for:

- new Clan creation;
- new Academy-level doctrine;
- changes to safety, approval, context, learning, or review policies;
- promotion of local Village learning to Academy doctrine;
- unresolved conflict between rules;
- unclear risk ownership;
- decisions that require extended user discussion;
- decisions that require web research or external expert review;
- work that could materially affect business, security, data privacy, or production systems.

A Kage Summit produces a Council Verdict. Shikamaru may then draft doctrine or structure changes based on that verdict.

## Review dimensions

Every review checks the dimensions required by the mission risk level.

### Mission compliance

The reviewer verifies whether the output matches the approved Mission Charter.

Questions:

- Did the Kagebunshin do exactly what was requested?
- Did it avoid explicit non-goals?
- Did it stay within allowed paths, commands, and actions?
- Did it avoid forbidden paths, commands, and actions?
- Did it stop when required?

### Technical quality

The reviewer verifies whether the output is maintainable, understandable, and appropriate for its purpose.

Questions:

- Is the solution clear and minimal?
- Is the implementation consistent with the surrounding project?
- Are naming, structure, and style appropriate?
- Are edge cases handled when required?
- Are errors explicit rather than silent?
- Are tests or validations included when required?
- Are assumptions documented as assumptions?

### Safety

The reviewer verifies that the Safety Policy was followed.

Questions:

- Were secrets, credentials, private data, or sensitive context avoided?
- Were dangerous commands avoided or explicitly approved?
- Were external actions avoided unless approved?
- Were copyrighted or franchise-specific public assets avoided?
- Was local Village context kept local?
- Was data minimization followed?

Safety issues override all other review outcomes.

### Scope control

The reviewer verifies that the mission did not grow beyond its approved scope.

Questions:

- Were unrelated files changed?
- Were unrelated refactors introduced?
- Were new dependencies added without approval?
- Were new folders, Scrolls, Clans, or doctrine files created without approval?
- Did the worker solve the requested problem rather than a larger imagined problem?

### Completion readiness

The reviewer verifies whether the mission is ready for final user-facing closure.

Questions:

- Is the output ready for teachback?
- Are there open questions?
- Is memory recording required?
- Is a Learning Proposal required?
- Is Shikamaru drafting required?
- Are there follow-up tasks that must be separated from this mission?

## Review assignment

The Hokage assigns the required review level in the Mission Charter.

The Mission Charter should include:

```yaml
review_required: true
review_level: none | clerk | jounin | kage_summit
review_reason: ""
confidence_threshold: 0.0
assigned_reviewer: ""
escalation_allowed: true
```

The assigned review level is a minimum. Review may always escalate when new risk, missing context, or uncertainty is discovered.

## Review outcomes

A review must return one of these outcomes:

```yaml
review_outcome: approved | approved_with_notes | changes_requested | blocked | escalate_to_hokage | escalate_to_kage_summit
```

### approved

The output satisfies the Mission Charter, meets the required quality bar, follows safety rules, and is ready for teachback or closure.

### approved_with_notes

The output is acceptable, but the reviewer found minor notes that do not block completion.

Notes must be recorded.

### changes_requested

The output has fixable issues that must be addressed before completion.

The reviewer must list specific required changes.

### blocked

The output cannot proceed because of a safety issue, missing approval, missing context, failed validation, or violation of the Mission Charter.

A blocked review requires Hokage attention.

### escalate_to_hokage

The reviewer cannot decide because the issue requires orchestration, clarification, or scope control.

### escalate_to_kage_summit

The reviewer cannot decide because the issue is strategic, ambiguous, cross-domain, or high-impact.

## Clerk escalation triggers

A Clerk must escalate to Jounin when any of these occur:

- confidence is below the threshold defined in the Mission Charter;
- the task involves code;
- the task involves sensitive context;
- the task involves doctrine;
- the task involves memory promotion;
- the task involves external actions;
- the task involves technical correctness;
- required fields are missing;
- the Mission Charter is incomplete;
- instructions conflict;
- the Clerk detects a possible secret, credential, or private data;
- the Clerk detects changes outside scope;
- the Clerk is unsure.

A Clerk must not hide uncertainty.

## Jounin escalation triggers

A Jounin must escalate to the Hokage or Kage Summit when any of these occur:

- the Mission Charter is unclear or contradictory;
- the work requires user approval that was not granted;
- the work changes mission scope;
- the work changes doctrine or Scroll behavior;
- the work affects safety policy, approval policy, context policy, learning policy, or review policy;
- the work requires business, legal, security, privacy, or production judgement;
- the work requires extended discussion with the user;
- the reviewer cannot determine correctness from available evidence.

## Evidence requirements

A review must be based on evidence, not impression.

Valid evidence includes:

- approved Mission Charter;
- attached Context Pack;
- observed files;
- test results;
- command output;
- git diff;
- logs;
- user instruction;
- approved local Village rules;
- relevant Academy doctrine;
- Council Verdict.

Model inference is not evidence.

## Review report template

```yaml
review_id: ""
mission_id: ""
review_level: none | clerk | jounin | kage_summit
reviewer: ""
reviewed_at: ""
review_outcome: approved | approved_with_notes | changes_requested | blocked | escalate_to_hokage | escalate_to_kage_summit

mission_compliance:
  status: pass | warning | fail | not_applicable
  notes: []

technical_quality:
  status: pass | warning | fail | not_applicable
  notes: []

safety:
  status: pass | warning | fail | not_applicable
  notes: []

scope_control:
  status: pass | warning | fail | not_applicable
  notes: []

completion_readiness:
  status: pass | warning | fail | not_applicable
  notes: []

required_changes: []
open_questions: []
learning_proposal_recommended: false
shikamaru_required: false
teachback_ready: true
memory_update_required: false
```

## Relationship with Teachback

Review completion does not mean the mission is fully complete.

A mission may be technically approved but still not completed until the user understands the result when Teachback is required.

Konoha separates:

```text
done_by_agent != completed_by_user
```

If the Mission Charter requires teachback, the mission remains pending until the user can explain what was done, why it was done, and how to defend or maintain it.

## Relationship with Shikamaru

If review identifies a doctrine issue, Scroll improvement, structure change, or repeated learning pattern, the reviewer may recommend a Learning Proposal.

The reviewer may not modify doctrine directly.

Shikamaru is required when approved changes affect doctrine Markdown, protocol structure, Scroll documentation, Clan structure, or Academy-level knowledge.

## Violations

A review violation occurs when:

- a mission is marked completed without the required review level;
- a Clerk approves work beyond low-risk validation;
- a Jounin ignores safety issues;
- a reviewer approves work without evidence;
- a reviewer hides uncertainty;
- a reviewer fails to escalate when required;
- a reviewer treats model inference as evidence;
- a reviewer approves scope creep without Hokage or human approval.

Violations must be recorded in the Mission Log and may trigger a Learning Proposal.
