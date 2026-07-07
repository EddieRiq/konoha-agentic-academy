# Command Execution Result

Status: template.

Use this template after any future command runner executes or blocks a command.

## Request reference

- Mission ID:
- Command request path:
- Executed by:
- Execution timestamp:
- Working directory:

## Final status

- [ ] Completed
- [ ] Completed with warnings
- [ ] Blocked before execution
- [ ] Failed during execution
- [ ] Partially completed
- [ ] Rolled back

## Command executed

```text
<exact command executed>
```

If no command was executed, explain why:

```text
<reason>
```

## Output summary

Do not paste sensitive logs.

```text
<safe summary>
```

## Exit status

- Exit code:
- Duration:
- stdout captured:
  - [ ] no
  - [ ] yes, sanitized
- stderr captured:
  - [ ] no
  - [ ] yes, sanitized

## Files or state changed

```text
<paths changed or "none">
```

## Git status evidence

Before command:

```text
<summary or path to evidence>
```

After command:

```text
<summary or path to evidence>
```

## Privacy and safety review

- [ ] No secrets exposed.
- [ ] No private context exposed.
- [ ] No ignored files staged.
- [ ] No out-of-scope paths touched.
- [ ] No unauthorized network access.
- [ ] No unauthorized Git operation.
- [ ] No unauthorized release operation.

Issues found:

```text
<issues or none>
```

## Rollback

- Rollback required:
  - [ ] No
  - [ ] Yes
- Rollback performed:
  - [ ] No
  - [ ] Yes
  - [ ] Not applicable

Rollback notes:

```text
<notes>
```

## Evidence links

- Command request:
- Dry-run result:
- Evidence pack:
- Execution gate:
- Logs, if safe:

## Reviewer verdict

- [ ] Accept result
- [ ] Accept with notes
- [ ] Needs follow-up
- [ ] Blocked
- [ ] Rollback required

Reviewer notes:

```text
<notes>
```
