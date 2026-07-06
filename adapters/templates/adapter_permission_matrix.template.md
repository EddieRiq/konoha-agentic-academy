# Adapter permission matrix template

Status: template.

Use this template when proposing or reviewing permissions for a specific adapter.

## Adapter

- Adapter name:
- Adapter path:
- Adapter type:
- Owner:
- Status:
- Review date:

## Requested permission

- Requested maximum level:
- Default level:
- Reason for requested level:
- Minimum viable level:
- Mission or use case:

## Capability declaration

| Capability | Requested? | Required for mission? | Notes |
|---|---|---|---|
| Read public repository files |  |  |  |
| Propose changes |  |  |  |
| Write public files |  |  |  |
| Run read-only commands |  |  |  |
| Run tests or linters |  |  |  |
| Install dependencies |  |  |  |
| Read ignored local Village files |  |  |  |
| Write ignored local Village files |  |  |  |
| Network access |  |  |  |
| Credentialed access |  |  |  |
| Git commit |  |  |  |
| Git push |  |  |  |
| Tag creation |  |  |  |
| Release publication |  |  |  |

## File access scope

Allowed paths:

```text
<path>
```

Denied paths:

```text
<path>
```

Ignored/private paths:

```text
<path>
```

## Command scope

Allowed commands:

```text
<command>
```

Denied commands:

```text
<command>
```

Commands requiring explicit approval:

```text
<command>
```

## Private context policy

- May access ignored local Village files: no
- May access private literature: no
- May access local memory: no
- May access secrets or credentials: never
- May copy local content into public repo: no

If any answer above changes, escalation is required.

## Logging policy

- Log command names:
- Log full command output:
- Redact paths:
- Redact environment variables:
- Redact secrets:
- Store logs where:

## Stop conditions

The adapter must stop if:

- permission is ambiguous;
- requested action exceeds approved level;
- private content may leak;
- a command is destructive or credentialed;
- the working tree is dirty before release actions;
- approval is missing;
- outputs cannot be explained to the user.

## Review decision

- [ ] Approved at requested level
- [ ] Approved at lower level
- [ ] Approved with constraints
- [ ] Blocked pending clarification
- [ ] Rejected

Approved level:

Constraints:

Reviewer:

Date:
