# Model Tier Matrix

Status: planning baseline.

This guide defines how Konoha classifies model tiers for safe, sufficient, cost-aware intelligence.

Konoha does not optimize for the strongest model by default. Konoha optimizes for the cheapest sufficiently capable model, with evidence, evals, review, and escalation.

This document does not implement routing automation. It defines policy and review expectations.

## Core principle

Use the cheapest capable model, but prove capability through:

- clear task scope;
- context budget discipline;
- relevant context capsules;
- prior eval results;
- evidence packs;
- reviewer feedback;
- escalation triggers;
- post-mission token and quality review.

A cheaper model may be used only when the mission can remain safe, bounded, and reviewable.

## Technical capability is not authorization

A model tier may be technically capable of generating a command, code patch, release note, or review.

That does not authorize the action.

Authorization still comes from:

- Mission Charter;
- role policy;
- adapter permission matrix;
- context budget;
- execution gate;
- review policy;
- explicit user approval.

## Tier overview

| Tier | Name | Typical use | Default authority |
|---:|---|---|---|
| 0 | Clerk | extraction, classification, summaries, checklists | read/propose only |
| 1 | Draft Worker | drafts, templates, simple documentation changes | propose only unless chartered |
| 2 | Specialist Worker | scoped code/docs/design work with clear rules | scoped propose or patch-authorized |
| 3 | Reviewer / Jounin | review, safety check, correctness check, capability review | review and block, not execute |
| 4 | Orchestrator / Hokage | planning, delegation, escalation, strategy | orchestrate, not execute |

## Tier 0: Clerk

Tier 0 models are low-cost workers for narrow, mechanical tasks.

Allowed by default:

- classify a mission type;
- summarize non-sensitive public docs;
- extract headings;
- create checklists;
- compare templates;
- prepare draft context capsules;
- detect missing fields;
- estimate whether a task is simple or complex.

Not allowed by default:

- authorize actions;
- execute commands;
- mutate files;
- perform Git operations;
- access private context;
- approve doctrine changes;
- certify its own sufficiency.

Escalate when:

- ambiguity affects safety;
- private context is involved;
- source conflict appears;
- output would drive code/runtime/Git action;
- the task requires judgment beyond a checklist.

## Tier 1: Draft Worker

Tier 1 models are suitable for low-risk drafting under clear prompts.

Allowed by default:

- draft documentation;
- create non-sensitive templates;
- propose README updates;
- rewrite public text;
- generate structured reports;
- fill eval result templates from provided evidence.

Not allowed by default:

- make final safety decisions;
- approve releases;
- modify doctrine without review;
- operate on private context without explicit charter;
- decide model demotion/promotion alone.

Escalate when:

- output changes policy meaning;
- action affects safety boundary;
- release language could misrepresent capability;
- code behavior is involved;
- model repeats uncertainty or needs retries.

## Tier 2: Specialist Worker

Tier 2 models can handle scoped technical work when the mission has clear boundaries.

Allowed when chartered:

- propose code patches;
- propose refactors;
- analyze specific modules;
- draft tests;
- inspect structured evidence;
- propose adapter/runtime designs;
- work from validated context capsules.

Not allowed without additional approval:

- execute shell commands;
- perform Git operations;
- access private Village content;
- change safety doctrine;
- approve its own work;
- bypass review.

Escalate when:

- task requires architecture decisions;
- security/privacy implications exist;
- rollback is unclear;
- output touches runtime execution;
- evals or tests are absent.

## Tier 3: Reviewer / Jounin

Tier 3 models review the sufficiency, safety, and correctness of lower-tier work.

Allowed:

- review proposed outputs;
- identify missing evidence;
- challenge model tier choice;
- block unsafe work;
- recommend escalation;
- review eval results;
- evaluate whether a lower tier can own future similar tasks.

Not allowed by default:

- execute the work being reviewed;
- silently expand mission scope;
- approve itself as final authority;
- replace user approval for sensitive actions.

Reviewer rule:

A reviewer can block or recommend. It cannot create permission where none exists.

## Tier 4: Orchestrator / Hokage

Tier 4 models coordinate complex missions and decide delegation strategy.

Allowed:

- classify mission risk;
- select candidate model tier;
- define reading plan;
- define context budget;
- assign workers;
- decide escalation;
- prepare user-facing plan;
- coordinate reviewers.

Not allowed:

- execute directly when policy says the role only orchestrates;
- bypass Mission Charter;
- authorize private access without user approval;
- treat strategic confidence as evidence.

Hokage rule:

The orchestrator protects the system from overuse and under-review.

## Task risk classes

### Low risk

Examples:

- formatting public docs;
- generating non-sensitive templates;
- listing missing files;
- drafting release notes from provided changelog.

Preferred tiers:

- Tier 0 for extraction/checking;
- Tier 1 for drafting;
- Tier 3 only for release-sensitive wording.

### Medium risk

Examples:

- updating doctrine references;
- creating eval cases;
- reviewing adapter manifests;
- proposing scoped code.

Preferred tiers:

- Tier 1 or Tier 2 for work;
- Tier 3 for review.

### High risk

Examples:

- runtime execution design;
- Git operations;
- private context access;
- security-sensitive changes;
- release publication;
- doctrine policy changes.

Preferred tiers:

- Tier 4 planning;
- Tier 2 scoped drafting;
- Tier 3 review;
- explicit user approval.

High-risk work must not be delegated solely to Tier 0 or Tier 1.

## Demotion rule

A task may be demoted to a cheaper tier only when:

- the task has a stable template or capsule;
- previous similar outputs passed review;
- failure impact is low or reversible;
- stop conditions are explicit;
- reviewer coverage remains available;
- token savings are meaningful.

Demotion is not permanent. It must be revisited after failures, drift, or policy changes.

## Escalation rule

Escalate to a higher tier when:

- the model asks for repeated clarification;
- output conflicts with doctrine;
- private context appears;
- code/runtime/Git/release impact appears;
- token usage exceeds budget without clear value;
- reviewer finds material defects;
- the task has not been evaluated before.

## Prompt reinforcement

A lower tier may be used for a higher-tier-looking task only when the prompt removes ambiguity.

Reinforcement may include:

- exact scope;
- allowed files;
- blocked actions;
- required output schema;
- evidence checklist;
- stop conditions;
- examples of pass/fail;
- context capsule references.

Prompt reinforcement does not grant new authority.

## Context capsule dependency

Lower tiers should rely on context capsules rather than full doctrine loads when:

- the capsule is current;
- source hashes are valid;
- task is not safety-critical;
- required stop conditions are included;
- sources are available for review.

Full sources are required for:

- doctrine changes;
- safety boundary changes;
- release claims;
- permission changes;
- private context decisions;
- runtime execution proposals.

## Token governance relationship

Model tier choice must be recorded with:

- expected intake tokens;
- expected working/output tokens;
- selected context mode;
- source loading plan;
- expected review cost;
- escalation triggers;
- post-mission actual or estimated usage.

Token efficiency is judged by total accepted mission cost, not only model price.

## Capability review

After repeated successful runs, Konoha may update routing guidance.

Evidence should include:

- number of similar missions;
- pass/fail history;
- reviewer notes;
- token usage trend;
- failure modes;
- recommended prompt reinforcement;
- recommended tier.

Capability learning is a proposal, not automatic doctrine.

## Stop conditions

Stop and escalate if:

- model tier is not justified;
- budget is missing;
- private context is requested without approval;
- safety docs would be summarized but not source-checked;
- lower-tier output would be accepted without review;
- token overage is unexplained;
- task risk is higher than expected.

## Completion criteria

A mission using this matrix is complete only when:

- model tier choice was recorded;
- context budget was recorded;
- actual or estimated token usage was reported;
- quality outcome was reviewed;
- escalation/demotion recommendation was documented;
- user can understand why the chosen model was sufficient.
