# Runtime State

Status: template.

## State metadata

- Runtime State ID:
- Related Mission Intake ID:
- Related Dry-Run Plan ID:
- Date:
- Runtime mode: `dry-run only`
- Current state:
- Previous state:
- State owner:
- Reviewer:

## Allowed states

Choose one:

- `draft_intake`
- `blocked_intake`
- `dry_run_plan_created`
- `awaiting_review`
- `changes_requested`
- `approved_for_next_step`
- `rejected`
- `closed_without_execution`

## State boundary

A runtime state record is evidence of workflow status.

It does not authorize:

- command execution;
- filesystem mutation;
- Git operations;
- adapter execution;
- model escalation;
- private context access;
- release publication;
- mission closure.

## State transition

| From | To | Reason | Evidence | Approved by |
|---|---|---|---|---|
|  |  |  |  |  |

## Current artifacts

| Artifact | Path or reference | Status | Notes |
|---|---|---|---|
| Mission Intake |  |  |  |
| Dry-Run Plan |  |  |  |
| Adapter Invocation Stub |  |  |  |
| Evidence Collection Stub |  |  |  |
| Model Routing Decision |  |  |  |
| Context Budget |  |  |  |
| Token Usage Report |  |  |  |

## Open risks

| Risk | Severity | Owner | Resolution |
|---|---|---|---|
|  |  |  |  |

## Open decisions

| Decision | Required by | Owner | Status |
|---|---|---|---|
|  |  |  |  |

## Review checklist

| Check | Passed? | Evidence |
|---|---:|---|
| Mission Charter referenced |  |  |
| Scope boundary clear |  |  |
| Dry-run only |  |  |
| No command execution |  |  |
| No file mutation |  |  |
| No Git operation |  |  |
| No private context leak |  |  |
| Model routing documented |  |  |
| Context budget documented |  |  |
| Evidence plan present |  |  |
| Stop conditions documented |  |  |

## Next allowed action

Choose one:

- `ask_user_for_clarification`
- `revise_dry_run_plan`
- `submit_for_review`
- `prepare_separate_execution_request`
- `close_without_execution`
- `block`

## Notes

- 
