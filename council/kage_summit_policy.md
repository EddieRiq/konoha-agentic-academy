# Kage Summit Policy

## Purpose

The Kage Summit is Konoha Agentic Academy's escalation protocol for decisions that exceed normal mission orchestration.

It exists to prevent rushed, under-specified, high-risk, or strategic decisions from being solved through shallow back-and-forth between the Hokage and a single user prompt.

The Kage Summit is used when a mission requires deeper discussion, external research, cross-domain judgment, architectural trade-offs, doctrine changes, or human-level strategic alignment.

## Core rules

```text
The Hokage may orchestrate missions, but must escalate decisions that exceed mission scope, confidence, authority, or safety boundaries.
```

```text
A Kage Summit produces a verdict, not an implementation.
```

```text
No Kage Summit decision becomes doctrine until Shikamaru drafts it and the user approves it.
```

```text
A Kage Summit must clarify uncertainty. It must not hide uncertainty behind confident language.
```

## What the Kage Summit is

A Kage Summit is a structured decision process.

It may involve:

- the user;
- the Konoha Hokage;
- a Local Kage;
- Shikamaru;
- Jounin reviewers;
- specialist agents;
- external research;
- a separate GPT or chat;
- human collaborators;
- domain experts.

The exact participants depend on the mission.

The important part is not the number of participants. The important part is that the decision is documented, reviewed, and returned as an explicit verdict.

## What the Kage Summit is not

The Kage Summit is not:

- a worker;
- a place to execute code;
- a shortcut around approvals;
- a replacement for user approval;
- a way for agents to create doctrine by themselves;
- a dumping ground for every unclear mission;
- a reason to send sensitive local context outside the Village by default.

## When to call a Kage Summit

The Hokage must call a Kage Summit when any of the following apply:

### Strategic decisions

- creating a new Clan;
- changing the Academy's core structure;
- changing the local Village architecture;
- selecting long-term memory strategy;
- selecting model routing strategy;
- creating or changing a major protocol;
- changing the public repository direction.

### Doctrine decisions

- modifying Konoha Laws;
- modifying Agent Conduct;
- modifying Shikamaru authority;
- changing Approval, Safety, Context, Review, Learning, or Teachback policies;
- promoting local learning into Academy doctrine;
- accepting behavior-changing Scrolls into the public repo.

### High-risk technical decisions

- changing architecture;
- changing security boundaries;
- modifying CI/CD;
- touching deployment, Docker, infrastructure, credentials, or permissions;
- making changes with difficult rollback;
- changing data pipelines, model production, scoring logic, or business-critical logic.

### Ambiguity and low confidence

- the Hokage cannot build a Mission Charter with enough confidence;
- the context is contradictory;
- the user request is broad, strategic, or under-specified;
- multiple valid approaches exist and trade-offs matter;
- the mission requires web research or comparison of external tools;
- the consequences of choosing wrong are significant.

### Human context

- the user needs to discuss options deeply;
- the task involves workplace communication, politics, or hierarchy;
- the decision must be defendable to leadership;
- the user must understand the reasoning before action.

### Resource and model routing

- the task may consume many tokens;
- local models may be sufficient but need evaluation;
- model selection affects cost, latency, privacy, or quality;
- the Hokage needs to decide whether to escalate from Clerks to stronger agents.

## When not to call a Kage Summit

A Kage Summit is not needed for:

- simple explanations;
- routine formatting;
- low-risk summaries;
- small Mission Charter clarifications;
- Clerks checking Markdown structure;
- Jounin reviewing a normal low or medium risk mission;
- routine local memory summaries;
- clearly scoped edits already approved by the Mission Charter.

The Hokage should not overuse the Kage Summit. Escalation is a safety and clarity tool, not a ritual.

## Participants

### Konoha Hokage

Responsibilities:

- detects that escalation is required;
- prepares the Council Brief;
- limits the context sent to the summit;
- protects local and sensitive information;
- receives the Council Verdict;
- decides the next mission step based on the verdict.

### Local Kage

Used when the mission belongs to a Local Village.

Responsibilities:

- represents local rules, private context, and constraints;
- confirms what can and cannot leave the Village;
- approves or blocks local execution after the verdict;
- protects local memory, assets, and sensitive data.

### Shikamaru

Responsibilities:

- converts approved verdicts into doctrine drafts when needed;
- creates folders and Markdown files when approved;
- prepares structured proposals;
- refuses to write doctrine without evidence and approval.

### Jounin

Responsibilities:

- reviews the logic, risks, trade-offs, and evidence;
- challenges weak reasoning;
- verifies whether the verdict answers the original question;
- flags missing review, testing, or safety requirements.

### Specialist agents

Specialist agents may be called when a decision requires domain knowledge.

Examples:

- data engineering;
- software engineering;
- machine learning;
- writing;
- research;
- security;
- DevOps;
- local model evaluation.

Specialist agents may advise, but they do not approve doctrine or high-risk actions alone.

### User

The user remains the final authority for actions that affect their repo, data, files, communications, machine, memory, or doctrine.

## Council Brief

A Kage Summit must start with a Council Brief.

The Council Brief is prepared by the Hokage or Local Kage.

It must be concise, sourced, and scoped.

### Required fields

```yaml
council_brief:
  summit_id:
  created_at:
  requested_by:
  village:
  mission_id:
  topic:
  urgency:
  risk_level:

  original_request:
  current_understanding:
  decision_needed:

  context_sources:
    - source:
      type:
      sensitivity:
      summary:

  known_facts:
    - fact:
      source:

  assumptions:
    - assumption:
      status: unconfirmed

  open_questions:
    - question:
      why_it_matters:

  options:
    - option:
      benefits:
      risks:
      cost:
      reversibility:

  constraints:
    - constraint:

  safety_notes:
    - note:

  token_budget_notes:
    - note:

  requested_output:
    - decision
    - recommendation
    - next_steps
    - doctrine_change_needed
```

## Council Verdict

A Kage Summit must end with a Council Verdict.

The verdict is not implementation. It is a decision artifact.

### Required fields

```yaml
council_verdict:
  summit_id:
  decided_at:
  decision:
  confidence:
  approved_scope:
  rejected_options:
  rationale:
  risks:
  unresolved_questions:
  required_approvals:
  next_actions:
  shikamaru_required:
  jounin_review_required:
  memory_update_required:
  doctrine_change_required:
  local_only:
```

## Output types

A Kage Summit may produce one or more of these outputs:

```text
decision
```

A clear choice between options.

```text
recommendation
```

A preferred direction, but not yet authorized for execution.

```text
mission charter input
```

Information needed to build or revise a Mission Charter.

```text
doctrine proposal
```

A recommendation for Shikamaru to draft doctrine changes.

```text
scroll proposal
```

A recommendation to create or modify a Scroll.

```text
clan proposal
```

A recommendation to create or modify a Clan.

```text
research summary
```

A sourced summary of external research.

```text
blocker
```

A finding that the mission should not continue until more context is provided.

## Context minimization

The Kage Summit must use the minimum context needed.

Local Village context must not be exported to the summit unless explicitly allowed.

Sensitive data must be summarized, anonymized, or omitted unless the Safety Policy and Approval Policy explicitly allow its use.

The Council Brief must mark context sensitivity.

Examples:

```yaml
sensitivity: public
sensitivity: internal
sensitivity: local_private
sensitivity: secret
```

Secret context should not be included in the brief.

## Local Village cooperation

For missions involving a Local Village:

```text
The Local Kage protects the Village.
The Konoha Hokage protects the Academy doctrine and process.
High-impact local decisions require cooperation between both.
```

Dual approval is required when:

- local doctrine changes;
- local security rules change;
- local memory is promoted to Academy memory;
- local assets or private context may leave the Village;
- local execution affects important files, infrastructure, or external systems.

## Model and token discipline

A Kage Summit should not be an excuse to waste tokens.

The Hokage should decide whether the summit needs:

- a Clerk for summarization;
- a local model for clustering or context packing;
- a Jounin for review;
- a Sage-level agent for deep reasoning;
- human discussion outside the agent runtime.

Large context must be compressed into a Council Brief before being sent to expensive or remote models.

Raw logs should not be sent when a sourced summary is enough.

## Research requirements

When external research is required:

- sources must be cited or recorded;
- uncertainty must be stated;
- current information must be verified when it may have changed;
- research outputs must distinguish fact from interpretation;
- no external claim becomes doctrine without Shikamaru drafting and user approval.

## Relationship with Shikamaru

A Council Verdict may require Shikamaru.

Shikamaru may:

- draft doctrine;
- create folders;
- create Markdown files;
- scaffold new Scroll or Clan documentation;
- prepare structured proposals.

Shikamaru may not:

- invent doctrine not present in the verdict;
- silently apply changes;
- modify non-Markdown technical files directly;
- bypass user approval.

## Relationship with Yamanaka Memory

The Kage Summit should create a memory entry when:

- a strategic decision was made;
- a doctrine change was proposed;
- a local-to-Academy promotion was considered;
- an important option was rejected;
- a risk was identified;
- a new Clan, Scroll, or protocol was proposed.

The memory entry must include:

- Council Brief reference;
- Council Verdict reference;
- date;
- participants;
- decision;
- rationale;
- unresolved questions;
- next action.

## Relationship with Teachback

If the summit produces a decision that the user must defend or explain, Teachback is required.

The mission cannot be completed until the user can explain:

- what was decided;
- why it was decided;
- what alternatives were rejected;
- what risks remain;
- what happens next.

## Stop-and-ask triggers

The Kage Summit must stop and ask when:

- the decision depends on missing context;
- the brief contains unverified assumptions;
- sensitive data would need to be exposed;
- the requested output is unclear;
- no option is safe enough;
- the user must choose between trade-offs;
- the summit is being used to bypass approval.

## Violations

Violations include:

- executing work during the summit without approval;
- producing a verdict without evidence;
- hiding uncertainty;
- promoting local memory to Academy doctrine without approval;
- exposing sensitive local context;
- skipping Shikamaru for doctrine changes;
- skipping user approval for high-impact decisions;
- using the summit to justify scope creep.

## Completion checklist

A Kage Summit is complete only when:

- the Council Brief exists;
- the Council Verdict exists;
- the decision, uncertainty, and risks are explicit;
- required approvals are listed;
- next actions are defined;
- Shikamaru requirements are identified;
- review requirements are identified;
- memory requirements are identified;
- local-only constraints are respected.
