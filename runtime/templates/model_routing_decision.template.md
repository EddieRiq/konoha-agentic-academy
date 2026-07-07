# Model Routing Decision

Status: draft.

Use this template before assigning a model or tier to a mission.

## Mission

- Mission ID:
- Mission title:
- Mission Charter exists: yes/no
- Mission type:
- Risk level: low / standard / high / sensitive
- Private context involved: no / yes / unclear

## Proposed model routing

- Proposed tier:
- Proposed adapter/model:
- Reason for selection:
- Expected capability:
- Expected limitation:
- Proposed reviewer tier:
- Execution mode: read-only / propose-only / dry-run / execution not allowed

## Context mode

- Context mode: capsule-first / source-on-demand / full-source required / stop-and-ask
- Required capsules:
- Required source files:
- Full-source triggers:
- Stale capsule risk:

## Token budget

- Intake budget:
- Work budget:
- Output budget:
- Review budget:
- Retry budget:
- Expected total:
- Hard stop threshold:

## Capability evidence

- Relevant evals:
- Similar prior missions:
- Known failure modes:
- Required prompt reinforcement:
- Checklist or rubric:

## Escalation triggers

Escalate if:

- [ ] output lacks evidence;
- [ ] model requests broad context;
- [ ] private context appears;
- [ ] safety or permission conflict appears;
- [ ] retry budget is exceeded;
- [ ] reviewer rejects output;
- [ ] user asks for execution beyond scope.

## Decision

- Approved tier:
- Approved context mode:
- Approved reviewer:
- Approved by:
- Date:

## Notes

