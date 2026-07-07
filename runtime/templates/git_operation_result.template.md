# Git Operation Result

Status: template.

Use this template to record the result of a Git operation.

## Result metadata

- Request ID:
- Date:
- Operator/runtime:
- Repository path:
- Branch before:
- Branch after:
- Remote:
- Operation type:
- Approved by:

## Command or action executed

```text
<exact command or API action>
```

## Execution status

- [ ] Completed
- [ ] Completed with warnings
- [ ] Failed
- [ ] Blocked before execution
- [ ] Partially completed

Exit code:

```text
<exit code>
```

## Output summary

```text
<safe output summary>
```

Do not paste secrets, credentials, tokens, private data, or large logs.

## Git evidence after operation

```text
git status
git log --oneline --decorate -5
git tag -n
```

If relevant:

```text
git diff --stat
git diff --cached --stat
```

## Objects created or changed

Commits:

```text
<commit hashes>
```

Tags:

```text
<tag names>
```

Branches:

```text
<branch names>
```

Remote changes:

```text
<remote changes>
```

## Files affected

```text
<files>
```

## Private-boundary verification

```text
git ls-files alliance/<village>
git check-ignore -v alliance/<village>/test.md
```

Result:

```text
<summary>
```

## Unexpected behavior

- Unexpected files:
- Unexpected output:
- Unexpected remote state:
- Unexpected warnings:
- Private-boundary concern:

## Follow-up actions

- [ ] None
- [ ] Additional review needed
- [ ] Rollback needed
- [ ] Release notes needed
- [ ] Tag/release validation needed
- [ ] Security/privacy review needed

## Final status

- [ ] Accepted
- [ ] Accepted with notes
- [ ] Needs follow-up
- [ ] Rolled back
- [ ] Blocked

Reviewer:

Date:

Notes:
