# Runtime Trace Review Scroll

Status: documentation-first review Scroll.

## Purpose

This Scroll reviews whether a Runtime Trace Log is complete, coherent, dry-run-only, and suitable for audit.

It helps reviewers verify that runtime planning steps were recorded without converting trace records into execution authority.

## This Scroll reviews

- trace completeness;
- chronological coherence;
- Mission Charter linkage;
- dry-run-only boundary;
- model routing references;
- context budget references;
- token budget references;
- validation report references;
- evidence references;
- blocker visibility;
- user approval records;
- stop conditions;
- closure readiness.

## This Scroll does not authorize

- command execution;
- filesystem mutation;
- Git operations;
- automatic adapter invocation;
- private context access;
- model escalation;
- release publication;
- mission closure by itself.

## Required inputs

Before review, collect:

```text
Mission Intake:
Dry-Run Execution Plan:
Adapter Invocation Stub:
Evidence Collection Stub:
Runtime State:
Runtime Validation Checklist:
Runtime Validation Report:
Runtime Trace Log:
Model Routing Decision:
Context Budget:
Token Budget Enforcement record:
Evidence package or evidence stub:
```

If a required input is missing, mark the trace review as blocked or conditional.

## Review checklist

### 1. Trace identity

```text
[ ] Trace log has a mission_id.
[ ] Trace log has a trace_log_id.
[ ] Runtime mode is dry_run_only.
[ ] Owner role is declared.
[ ] Reviewer role is declared.
[ ] Status is declared.
```

### 2. Chronology

```text
[ ] Events are ordered.
[ ] Event timestamps are present.
[ ] Event IDs are unique.
[ ] Superseded events are not silently deleted.
[ ] Corrections are recorded as new trace entries.
```

### 3. Mission linkage

```text
[ ] Trace log references the Mission Charter or Mission Intake.
[ ] Trace events remain within mission scope.
[ ] Scope changes are recorded.
[ ] Missing approvals are visible.
```

### 4. Dry-run boundary

```text
[ ] No trace event claims shell execution occurred.
[ ] No trace event claims filesystem mutation occurred.
[ ] No trace event claims Git mutation occurred.
[ ] No trace event claims adapter execution occurred beyond stub planning.
[ ] No trace event implies autonomous approval.
```

### 5. Context and privacy

```text
[ ] Context sources are recorded.
[ ] Context capsules are identified where used.
[ ] Stale or blocked capsules are recorded.
[ ] Private context is not accessed automatically.
[ ] Sensitive data is avoided, anonymized, or explicitly blocked.
```

### 6. Model routing and token governance

```text
[ ] Model tier proposals are traceable.
[ ] Capability concerns are recorded.
[ ] Escalation or demotion is justified.
[ ] Token budget warnings are visible.
[ ] Hard stops are recorded.
[ ] Overage justifications are linked when applicable.
```

### 7. Evidence

```text
[ ] Material claims have evidence references.
[ ] Missing evidence is marked explicitly.
[ ] Evidence stubs do not pretend evidence was collected.
[ ] Evidence references point to reviewable artifacts.
```

### 8. Blockers and stop conditions

```text
[ ] Blockers have IDs.
[ ] Blockers reference trace events.
[ ] Required resolutions are clear.
[ ] Stop conditions are not hidden in notes.
[ ] Blocked missions are not marked ready for closure.
```

### 9. Closure readiness

```text
[ ] Runtime validation is complete or explicitly pending.
[ ] Review outcome is documented.
[ ] Open blockers are resolved or accepted as blockers.
[ ] User approval is recorded where required.
[ ] Teachback is marked if required.
```

## Review outcomes

Use one of:

```text
approved_for_review
needs_revision
blocked
```

### approved_for_review

Use only when the trace is coherent, dry-run-only, supported by evidence, and ready for downstream review.

### needs_revision

Use when the trace is mostly usable but has fixable gaps, such as missing references, unclear timestamps, or incomplete blocker descriptions.

### blocked

Use when the trace suggests unauthorized execution, missing approval, private context leakage, stale unsupported context, missing Mission Charter, or unresolved stop conditions.

## Reviewer notes template

```text
Decision:
Reason:
Required revisions:
Blocked items:
Evidence gaps:
Approval gaps:
Recommended next action:
```

## Final rule

A clean trace log improves auditability.

It does not grant permission to act.
