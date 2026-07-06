# Adapter invocation result

Status: template.

Use this template to report the result of a bounded adapter invocation.

## Request reference

```text
request_id:
mission_id:
adapter_id:
adapter_profile:
mode_requested:
mode_used:
```

## Result status

Select one:

- [ ] Completed
- [ ] Completed with notes
- [ ] Stopped
- [ ] Blocked
- [ ] Failed validation

## Actions taken

```text
Describe only actions actually taken.
```

## Files read

```text
- path/to/file.md
```

## Files modified

```text
- path/to/file.md
```

If no files were modified, write:

```text
None.
```

## Commands run

```text
None.
```

If commands were run, list exact commands and working directory.

| Command | Working directory | Result |
|---|---|---|
| | | |

## Evidence

Include concrete validation evidence.

```text
git status:
diff summary:
tests:
checks:
other:
```

## Permission check

- [ ] Stayed within invocation mode.
- [ ] Stayed within allowed paths.
- [ ] Ran only approved commands.
- [ ] Did not access private context unless explicitly approved.
- [ ] Did not expose secrets, credentials, or private data.
- [ ] Did not perform Git or release actions without approval.

## Risks found

```text
List risks found, or write None.
```

## Stop conditions triggered

```text
List triggered stop conditions, or write None.
```

## Deviations

```text
Describe deviations from the request, or write None.
```

## Next approval needed

```text
Describe any required approval before continuing.
```

## Teachback summary

```text
Explain what was done, why, and how the user can validate it.
```
