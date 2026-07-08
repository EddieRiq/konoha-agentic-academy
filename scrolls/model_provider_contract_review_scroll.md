# Model Provider Contract Review Scroll

Use this Scroll when reviewing model provider contract changes or model request plans.

## Review questions

1. Is the provider explicitly allowlisted?
2. Is real model invocation still blocked?
3. Is network access still blocked?
4. Are context sources explicit?
5. Are private context sources blocked?
6. Are token and cost limits present?
7. Is redaction required?
8. Is logging required?
9. Is human review required before future invocation?
10. Are prompts free of secrets and private data?

## Required evidence

- Contract JSON.
- Request plan JSON.
- Validation report.
- Token and cost limits.
- Context-source allowlist.
- Blocked context-source list.
- Human review note when preparing future real invocation.

## Non-authority rule

A valid model request plan is not permission to call a model.

Model inference is never permission.

Only a later, explicit, human-approved Real Model Invocation Gate may authorize real provider calls.
