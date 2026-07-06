# Adapter capabilities template

Status: public template.

This template records what an adapter can and cannot do.

Capabilities are descriptive. They do not authorize execution.

## Adapter

Adapter name: `<adapter-name>`

Manifest: `<path-to-manifest>`

## Capability summary

Briefly describe the adapter's practical capabilities.

```text
<summary>
```

## Capability matrix

| Capability | Supported | Requires approval | Evidence |
|---|---:|---:|---|
| Read repository files | `<yes/no>` | `<yes/no>` | `<how-known>` |
| Write repository files | `<yes/no>` | `<yes/no>` | `<how-known>` |
| Execute shell commands | `<yes/no>` | `<yes/no>` | `<how-known>` |
| Run tests | `<yes/no>` | `<yes/no>` | `<how-known>` |
| Access network | `<yes/no>` | `<yes/no>` | `<how-known>` |
| Use local private files | `<yes/no>` | `<yes/no>` | `<how-known>` |
| Use local memory | `<yes/no>` | `<yes/no>` | `<how-known>` |
| Update memory | `<yes/no>` | `<yes/no>` | `<how-known>` |
| Generate artifacts | `<yes/no>` | `<yes/no>` | `<how-known>` |
| Publish outputs | `<yes/no>` | `<yes/no>` | `<how-known>` |

## Allowed operations

List operations that are allowed when a Mission Charter explicitly grants them.

```text
<allowed-operations>
```

## Forbidden operations

The adapter must not:

- infer approval from capability;
- access private context without explicit permission;
- write outside approved paths;
- run destructive commands without explicit approval;
- install dependencies without explicit approval;
- commit or push changes without explicit approval;
- publish local Village content;
- update doctrine or memory without the proper approval flow.

Additional forbidden operations:

```text
<adapter-specific-forbidden-operations>
```

## Permission model

Default mode:

- [ ] read-only
- [ ] draft-only
- [ ] limited write
- [ ] execution allowed after approval
- [ ] other: `<describe>`

Permission source:

- Mission Charter;
- approval policy;
- safety policy;
- local Village rules;
- user approval.

Capability is never permission.

## Evidence requirements

Before using a capability, the operator must provide evidence that the adapter supports it safely.

Examples:

- dry-run output;
- help command;
- test run;
- sandbox execution;
- documentation reference;
- limited path validation;
- review note.

## Known failure modes

List known ways this adapter can fail or misbehave.

```text
<failure-modes>
```

## Stop conditions

Stop immediately if:

- scope is ambiguous;
- approval is missing;
- private context appears unexpectedly;
- a command would affect files outside approved paths;
- output may leak secrets or private content;
- validation fails;
- the adapter's behavior differs from this capability template.

## Review status

- [ ] Draft
- [ ] Reviewed
- [ ] Approved for limited use
- [ ] Rejected

Reviewer:

```text
<reviewer>
```

Date:

```text
<YYYY-MM-DD>
```
