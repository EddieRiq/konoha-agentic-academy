# Rollback request

Status: template.

Use this template when a proposed runtime action may require rollback.

## Request metadata

- Request ID:
- Date:
- Requester:
- Mission Charter:
- Related adapter invocation:
- Related execution gate:
- Related command request:
- Related filesystem mutation request:
- Related Git operation request:

## Proposed action

Describe the action that may need rollback.

## Affected scope

Allowed paths, systems, or artifacts:

```text
<allowed scope>
```

Out of scope:

```text
<out of scope>
```

## Expected changes

List expected changes before execution.

```text
<expected changes>
```

## Pre-action evidence

Required evidence:

- [ ] Current status captured.
- [ ] Relevant files listed.
- [ ] Planned diff or dry-run captured.
- [ ] Private boundary checked.
- [ ] Destructive action identified.
- [ ] Irreversible action identified.

Evidence notes:

```text
<evidence notes>
```

## Rollback strategy

Describe how to reverse or mitigate the change.

```text
<rollback strategy>
```

## Rollback commands or manual steps

```text
<commands or manual steps>
```

## Irreversible risk

- [ ] No known irreversible risk.
- [ ] Irreversible risk exists and is described below.

Description:

```text
<irreversible risk>
```

## Approval

- [ ] Rollback plan reviewed.
- [ ] User understands recovery path.
- [ ] Execution approval granted separately.
- [ ] Rollback execution approval required separately.

Approver:

```text
<approver>
```

## Stop conditions

Stop if:

- rollback plan is incomplete;
- affected scope expands;
- dry-run differs from expected result;
- private content may be exposed;
- Git state changes unexpectedly;
- user approval is missing.
