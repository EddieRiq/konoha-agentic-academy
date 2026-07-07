# Adapter Invocation Stub

Status: template.

## Stub metadata

- Stub ID:
- Related Mission Intake ID:
- Related Dry-Run Plan ID:
- Date:
- Target adapter:
- Adapter profile reference:
- Adapter permission matrix reference:
- Reviewer:

## Boundary

This is a stub, not an invocation.

It does not authorize:

- adapter execution;
- shell commands;
- file changes;
- Git operations;
- network calls;
- private context access;
- model escalation;
- mission closure.

## Intended purpose

```text
Describe why an adapter might be invoked later.
```

## Proposed mode

Choose one:

- `read_only_review`
- `dry_run_plan_review`
- `diff_review`
- `evidence_review`
- `capability_review`
- `other`

## Proposed input package

| Input | Required? | Approved? | Notes |
|---|---:|---:|---|
| Mission Charter |  |  |  |
| Mission Intake |  |  |  |
| Dry-Run Plan |  |  |  |
| Evidence Pack |  |  |  |
| Context Capsule |  |  |  |
| Public source files |  |  |  |
| Private source files |  |  |  |

## Permissions required before real invocation

| Permission | Required? | Granted? | Evidence |
|---|---:|---:|---|
| Read repository files |  |  |  |
| Read private Village files |  |  |  |
| Execute commands |  |  |  |
| Mutate files |  |  |  |
| Run Git operation |  |  |  |
| Access external network |  |  |  |

## Expected output

- 

## Expected evidence

- 

## Stop conditions

- Missing adapter profile.
- Missing permission matrix.
- Requested mode exceeds adapter permissions.
- Private context included without approval.
- Invocation would mutate state.
- Invocation result would be treated as authorization.

## Stub decision

Choose one:

- `stub_ready_for_review`
- `stub_needs_permissions`
- `stub_needs_context_reduction`
- `stub_blocked`
- `stub_rejected`

## Reviewer notes

- 
