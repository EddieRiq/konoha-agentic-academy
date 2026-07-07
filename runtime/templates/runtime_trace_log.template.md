# Runtime Trace Log Template

## Metadata

```yaml
mission_id:
trace_log_id:
created_at:
updated_at:
runtime_mode: dry_run_only
owner_role:
reviewer_role:
status: draft
```

## Scope

```text
Mission Charter reference:
Runtime package reference:
Validation report reference:
Evidence package reference:
```

## Boundaries

Confirm before adding trace events:

```text
Shell execution allowed: no
Filesystem mutation allowed: no
Git operations allowed: no
Automatic adapter invocation allowed: no
Automatic private context access allowed: no
Autonomous approval allowed: no
```

## Trace summary

```text
Total trace events:
Open blockers:
Hard stops reached:
User approvals recorded:
User approvals missing:
Context capsules used:
Context capsules blocked:
Model tier changes:
Token budget warnings:
```

## Trace events

### Trace event 001

```yaml
trace_id:
timestamp:
mission_id:
phase:
event_type:
actor_role:
artifact_reference:
input_reference:
decision_or_observation:
evidence:
boundary_check:
status:
next_required_action:
review_required:
```

#### Boundary check

```text
Dry-run only:
No shell execution:
No file mutation:
No Git operation:
No private context without approval:
Model routing documented:
Token budget respected:
Evidence attached or marked missing:
Approval required:
Approval present:
```

#### Notes

```text
Reviewer notes:
Supersedes trace_id:
Superseded by trace_id:
```

## Open blockers

```text
- blocker_id:
  related_trace_id:
  blocker_type:
  description:
  required_resolution:
  owner_role:
```

## Revision history

```text
- timestamp:
  changed_by_role:
  change_summary:
  reason:
```

## Closure readiness

```text
Trace log complete:
Validation report complete:
Evidence requirements complete:
Open blockers resolved:
User approval captured where required:
Teachback required:
Teachback completed:
Ready for review:
Ready for closure:
```

## Final reviewer decision

```text
Decision: approved_for_review | needs_revision | blocked
Reviewer:
Date:
Reason:
Required next action:
```
