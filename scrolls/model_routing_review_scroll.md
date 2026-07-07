# Model Routing Review Scroll

Status: documentation-first Scroll.

Use this Scroll to review whether a proposed model tier, adapter, context mode, and token budget are appropriate for a mission.

## Purpose

This Scroll prevents overusing expensive models, underusing capable low-tier models, or assigning unsafe work to models that cannot handle it.

## Inputs

- Mission Charter;
- model routing decision;
- context budget;
- relevant eval history;
- adapter permission matrix if applicable;
- token usage report from similar prior missions if available.

## Review questions

### Mission fit

- Is the mission type clear?
- Is risk level correctly classified?
- Is private context involved?
- Is execution authority excluded unless explicitly granted?

### Model fit

- Is the proposed tier sufficient?
- Is the proposed tier excessive?
- Is there evidence from evals or prior missions?
- Are known failure modes listed?
- Is reviewer coverage appropriate?

### Context fit

- Is capsule-first safe?
- Are full-source triggers defined?
- Are stale capsules handled?
- Is excluded context clearly listed?
- Is private context protected?

### Token budget

- Is intake budget reasonable?
- Is review budget included?
- Is retry budget included?
- Is the hard stop threshold clear?
- Are over-budget actions defined?

### Escalation

- Are escalation triggers explicit?
- Is a higher tier available if needed?
- Is downgrade justified by evidence, not cost pressure alone?

## Verdicts

### Pass

Routing is appropriate.

### Pass with notes

Routing is acceptable but should be monitored.

### Needs changes

Routing needs changes before mission start.

### Blocked

Routing is unsafe, under-specified, or violates policy.

## Required output

A review must state:

- verdict;
- approved tier;
- approved context mode;
- approved reviewer;
- token budget status;
- escalation triggers;
- unresolved risks.

## Stop conditions

Stop if:

- the Mission Charter is missing;
- private context is implied but not authorized;
- model tier is insufficient for risk;
- routing grants execution by implication;
- token budget is absent for a high-intake task;
- downgrade lacks evidence.
