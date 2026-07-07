# Runtime Trace Event Template

## Trace event

```yaml
trace_id:
timestamp:
mission_id:
runtime_mode: dry_run_only
phase:
event_type:
actor_role:
model_tier_if_applicable:
artifact_reference:
input_reference:
```

## Observation or decision

```text
What happened:
Why it matters:
What evidence supports it:
What remains unknown:
```

## Boundary check

```text
Dry-run only:
Shell execution avoided:
Filesystem mutation avoided:
Git operation avoided:
Adapter invocation avoided unless stub-only:
Private context avoided unless approved:
Sensitive data avoided or anonymized:
Model routing documented:
Context budget respected:
Token budget respected:
```

## Approval check

```text
Approval required:
Approval source:
Approval present:
Approval missing:
```

## Evidence

```text
Evidence reference:
Evidence type:
Evidence sufficient:
Evidence gap:
```

## Status

```text
Status: recorded | proposed | validated | needs_revision | blocked | approved_by_user | rejected | superseded
Next required action:
Reviewer required:
```

## Supersession

```text
Supersedes trace_id:
Superseded by trace_id:
Reason:
```
