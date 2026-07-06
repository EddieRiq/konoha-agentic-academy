# Adapter runtime readiness review

Status: template.

Use this template before implementing or enabling an executable adapter runtime.

## Runtime proposal

- Runtime name:
- Adapter profile:
- Runtime class:
- Proposed scope:
- Owner:
- Review date:

## Current state

- [ ] Declarative adapter profile exists.
- [ ] Adapter permission matrix exists.
- [ ] Invocation contract exists.
- [ ] Execution gate exists.
- [ ] Evidence pack exists.
- [ ] Dry-run protocol exists.
- [ ] Runtime boundary reviewed.

## Requested capability

Describe exactly what the runtime should be allowed to do.

Allowed actions:

- 

Blocked actions:

- 

## Scope

Allowed paths:

```text
<paths>
```

Blocked paths:

```text
<paths>
```

Allowed commands:

```text
<commands>
```

Blocked commands:

```text
<commands>
```

## Private-context access

- [ ] No private context access.
- [ ] Local private context access requested.

If private context access is requested, define:

- Village:
- Purpose:
- Files or folders:
- Output boundary:
- Publication risk:
- Required user approval:

## Git and release access

- [ ] No Git mutation.
- [ ] Git mutation requested.
- [ ] Release action requested.

If requested, define exact operations:

```text
<operations>
```

## Evidence plan

- [ ] Pre-execution evidence required.
- [ ] Dry-run result required.
- [ ] Execution gate decision required.
- [ ] Post-execution evidence required.
- [ ] Git status before and after required.
- [ ] Rollback notes required.

## Safety review

- [ ] No secrets exposed.
- [ ] No private content copied to public files.
- [ ] No broad filesystem access.
- [ ] No command wildcard risk.
- [ ] No implicit approval.
- [ ] Stop conditions documented.

## Runtime readiness verdict

- [ ] Not ready.
- [ ] Ready for dry-run only.
- [ ] Ready for patch proposal only.
- [ ] Ready for controlled local execution.
- [ ] Ready for Git operations.
- [ ] Ready for release operations.
- [ ] Ready for private-context execution.

## Approval

- Reviewer:
- Decision:
- Required changes:
- Approval status:
