# Runtime lifecycle template

Status: template.

Use this template to document a proposed runtime lifecycle before any implementation or execution.

## Lifecycle ID

`runtime-lifecycle-<id>`

## Mission Charter reference

- Mission Charter:
- Owner:
- Date:
- Approval status:

## Scope

### Allowed

-

### Not allowed

-

## Runtime plan

### Goal

-

### Proposed steps

1.
2.
3.

### Expected affected paths

```text
<paths>
```

### Expected commands

```text
<commands or none>
```

### Expected file mutations

```text
<mutations or none>
```

### Expected Git operations

```text
<operations or none>
```

### Private context access

- [ ] None.
- [ ] Required and explicitly approved.
- Details:

## Boundary checks

- [ ] Command runner boundary checked.
- [ ] Filesystem mutation boundary checked.
- [ ] Git operation boundary checked.
- [ ] Adapter permission matrix checked.
- [ ] Adapter invocation contract checked.
- [ ] Adapter execution gate checked.
- [ ] Rollback boundary checked.
- [ ] Private context boundary checked.
- [ ] Eval runner boundary checked, if applicable.

## Dry-run

### Dry-run required?

- [ ] Yes.
- [ ] No, explain why:

### Dry-run evidence

-

### Dry-run result

- [ ] Pass.
- [ ] Pass with notes.
- [ ] Blocked.

## Approval gate

### Required approvals

-

### Approval evidence

-

### Execution authorization

- [ ] Not authorized.
- [ ] Authorized for exact scope only.

## Execution record

### Actions performed

-

### Commands run

```text
<commands or none>
```

### Files changed

```text
<files or none>
```

### Git state

```text
<git status summary>
```

## Evidence

-

## Validation

### Validation method

-

### Validation result

- [ ] Pass.
- [ ] Pass with notes.
- [ ] Failed.
- [ ] Blocked.

## Rollback readiness

### Rollback required?

- [ ] Yes.
- [ ] No.

### Rollback plan

-

### Residual risk

-

## Closure

- [ ] Evidence complete.
- [ ] Validation complete.
- [ ] Git state known.
- [ ] Private boundaries preserved.
- [ ] User-facing summary complete.
- [ ] Teachback possible.

## Final status

- [ ] Proposed only.
- [ ] Dry-run complete.
- [ ] Executed.
- [ ] Blocked.
- [ ] Closed.

## Notes

-
