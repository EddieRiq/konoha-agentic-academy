# Token Budget Enforcement Review Scroll

Status: public Scroll.

Use this Scroll to review token budget plans, overage reports, context intake choices, and model routing decisions.

## Purpose

This Scroll prevents Konoha from becoming too expensive, too context-heavy, or too dependent on maximum-intelligence models for routine work.

## Required sources

Reviewers should inspect:

- `docs/guides/model_routing_and_token_governance.md`
- `docs/guides/context_capsules.md`
- `docs/guides/context_capsule_lifecycle.md`
- `docs/guides/session_resource_probe.md`
- `docs/guides/token_budget_enforcement.md`
- `docs/guides/model_tier_matrix.md`
- relevant Mission Charter
- relevant model routing decision
- relevant context budget
- relevant token usage report

## Review questions

### Budget clarity

- Is the mission budget mode explicit?
- Are soft and hard budgets defined?
- Is context intake separated from output and review?
- Are escalation triggers clear?

### Context discipline

- Are only relevant sources loaded?
- Are capsules used where safe?
- Are full sources required only when justified?
- Are stale capsules blocked?

### Model sufficiency

- Is the selected model tier justified?
- Is the cheapest capable model considered?
- Are reviewer requirements clear?
- Are escalation and demotion rules documented?

### Overage handling

- Was the overage detected?
- Was it classified?
- Was continuation approved if hard budget was reached?
- Was safety preserved?

### Efficiency learning

- Does the report propose future improvements?
- Should a capsule be created or refreshed?
- Should model routing be updated?
- Should an eval case be added?

## Pass criteria

A token budget plan passes when:

- budget mode is clear;
- model tier is justified;
- context intake is scoped;
- hard stops are defined;
- safety is not weakened;
- overage handling is documented.

## Needs changes

Mark as needs changes when:

- budget is vague;
- model tier is unjustified;
- context intake is too broad;
- hard stop is missing;
- overage handling is missing;
- capsule authority is overstated.

## Block conditions

Block the mission or workflow when:

- cost savings would skip required safety checks;
- private context is used without authorization;
- the hard budget was exceeded without approval;
- a lower-tier model is allowed to self-certify sufficiency;
- token usage or overage is hidden;
- a capsule is treated as authority for sensitive decisions.

## Reviewer output

Return:

- verdict: Pass / Pass with notes / Needs changes / Blocked;
- budget risk;
- model routing risk;
- context intake risk;
- overage risk;
- required changes;
- recommended future efficiency improvements.

## Non-authority

This Scroll does not authorize execution, model escalation, private context access, Git operations, releases, or doctrine changes.
