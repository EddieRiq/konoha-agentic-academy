# Model Tier Assignment

Status: draft.

Use this template before assigning a model or agent tier to a mission.

## Mission reference

- Mission ID:
- Mission title:
- Mission Charter path:
- Requested by:
- Date:

## Task classification

- Task type:
- Risk class:
  - [ ] Low
  - [ ] Medium
  - [ ] High
- Sensitive/private context involved:
  - [ ] No
  - [ ] Yes
- Runtime / command / filesystem / Git impact:
  - [ ] No
  - [ ] Yes
- Release or public claim impact:
  - [ ] No
  - [ ] Yes

## Proposed model tier

- Proposed tier:
  - [ ] Tier 0 - Clerk
  - [ ] Tier 1 - Draft Worker
  - [ ] Tier 2 - Specialist Worker
  - [ ] Tier 3 - Reviewer / Jounin
  - [ ] Tier 4 - Orchestrator / Hokage
- Proposed model or adapter:
- Reason for tier choice:

## Capability rationale

Why is this tier sufficient?

- Scope is narrow:
  - [ ] Yes
  - [ ] No
- Output schema is clear:
  - [ ] Yes
  - [ ] No
- Context capsule is available:
  - [ ] Yes
  - [ ] No
- Prior similar evals passed:
  - [ ] Yes
  - [ ] No
  - [ ] Not available
- Reviewer will check output:
  - [ ] Yes
  - [ ] No

## Context plan

- Context mode:
  - [ ] Capsule-first
  - [ ] Source-on-demand
  - [ ] Full-source required
  - [ ] Stop-and-ask
- Required capsules:
- Required full sources:
- Sources explicitly blocked:

## Budget

- Expected input/context tokens:
- Expected output tokens:
- Expected review tokens:
- Total target range:
- Hard stop threshold:
- Token measurement source:
  - [ ] Adapter-provided
  - [ ] User-provided
  - [ ] Estimated
  - [ ] Unavailable

## Prompt reinforcement

Required prompt constraints:

- Allowed actions:
- Blocked actions:
- Required evidence:
- Required output format:
- Stop conditions:

## Escalation triggers

Escalate if:

- [ ] output conflicts with doctrine;
- [ ] private context appears;
- [ ] task risk increases;
- [ ] token budget is exceeded;
- [ ] model produces low-confidence output;
- [ ] reviewer blocks result;
- [ ] user requests higher assurance.

## Approval

- Assigned by:
- Reviewer required:
  - [ ] No
  - [ ] Yes
- User approval required:
  - [ ] No
  - [ ] Yes
- Approval status:
  - [ ] Draft
  - [ ] Approved
  - [ ] Blocked
