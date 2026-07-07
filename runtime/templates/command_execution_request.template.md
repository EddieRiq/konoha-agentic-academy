# Command Execution Request

Status: template.

Use this template before any future command runner executes a command.

## Mission

- Mission ID:
- Mission Charter path:
- Request owner:
- Requested by:
- Date:

## Command summary

- Command category:
  - [ ] read-only
  - [ ] file mutation
  - [ ] package/environment
  - [ ] Git
  - [ ] release
  - [ ] network
  - [ ] destructive
  - [ ] other:
- Purpose:
- Expected effect:
- Expected output:

## Exact command

```text
<exact command here>
```

## Working directory

```text
<path>
```

## Scope

Allowed paths:

```text
<paths>
```

Blocked paths:

```text
<paths>
```

Private context involved?

- [ ] No
- [ ] Yes, local-private authorization attached
- [ ] Unclear, stop and review

## Risk level

- [ ] Low
- [ ] Medium
- [ ] High
- [ ] Critical

Risk notes:

```text
<notes>
```

## Preconditions

- [ ] Mission Charter authorizes command execution.
- [ ] Adapter permission matrix allows this category.
- [ ] Invocation contract allows this action.
- [ ] Dry-run completed or not required.
- [ ] Execution gate approved.
- [ ] Target paths are explicit.
- [ ] Rollback/recovery notes are present when needed.
- [ ] Output sensitivity was reviewed.

## Dry-run evidence

- Dry-run required:
  - [ ] Yes
  - [ ] No
- Dry-run result path:
- Evidence pack path:

## Rollback or recovery

Required?

- [ ] No
- [ ] Yes

Plan:

```text
<rollback or recovery notes>
```

## Approval

- Approved by:
- Approval timestamp:
- Approval scope:
- Expiration or limits:

## Stop conditions

Stop if:

- command differs from this request;
- working directory differs;
- target paths differ;
- private context appears unexpectedly;
- output includes secrets;
- command asks for elevated permissions;
- command requires network access not approved;
- command mutates files not listed in scope.

## Result location

Expected command result file:

```text
<path to command_execution_result>
```
