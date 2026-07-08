# Hokage Planner Loop Review Scroll

Use this Scroll when reviewing a Hokage Planner Loop run.

## Required evidence

- Mission Charter exists.
- Mission manifest exists.
- Planner loop report exists.
- Delegated dry-run runtime step passed.
- Delegated model invocation gate step passed or previewed.
- Plan proposal is marked `review_required`.
- Model output is treated as evidence only.

## Review questions

1. Does the plan stay inside the Mission Charter scope?
2. Does the report preserve execution blockers?
3. Does the plan avoid treating model output as authority?
4. Are private context, network, Git, and repository apply boundaries preserved?
5. Is a Human Approval Console event required before any downstream transition?

## Blockers

Block the planner loop if:

- the Mission Charter is missing or empty;
- the workspace structure is incomplete;
- the model gate failed;
- the output implies automatic execution;
- the plan attempts to authorize apply/stage/commit/push/closure;
- private context appears in the prompt, output, or report.
