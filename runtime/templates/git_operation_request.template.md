# Git Operation Request

Status: template.

Use this template to request a Git operation from a future runtime or adapter.

This template does not grant permission by itself.

## Request metadata

- Request ID:
- Date:
- Requester:
- Mission Charter:
- Repository path:
- Current branch:
- Remote:
- Target branch:
- Adapter/runtime:
- Permission level requested:

## Operation type

Select one:

- [ ] Read-only Git inspection
- [ ] Stage files
- [ ] Unstage files
- [ ] Commit
- [ ] Push
- [ ] Tag
- [ ] Push tag
- [ ] Release preparation
- [ ] Release publication
- [ ] Branch creation
- [ ] Branch deletion
- [ ] History-changing operation
- [ ] Other:

## Exact operation

Command or API action requested:

```text
<exact command or action>
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

Files expected to change:

```text
<files>
```

Files expected to be staged:

```text
<files>
```

## Evidence before operation

Attach or summarize:

```text
git status
git diff --stat
git diff --cached --stat
git branch --show-current
git log --oneline --decorate -5
```

Private-boundary checks:

```text
git ls-files alliance/<village>
git check-ignore -v alliance/<village>/test.md
```

## Risk review

- Could this publish private content?
- Could this trigger CI/CD?
- Could this modify remote state?
- Could this create a public tag or release?
- Could this alter history?
- Could this affect other collaborators?
- Could this be hard to roll back?

## Approval requirements

- User approval required:
- Reviewer approval required:
- Release approval required:
- Security/privacy approval required:
- Approval evidence:

## Rollback or recovery plan

Describe how to recover if the operation is wrong:

```text
<rollback notes>
```

## Stop conditions

Stop if:

- exact command differs from this request;
- unexpected files appear;
- private-boundary checks fail;
- working tree is not as expected;
- remote target differs;
- user approval is missing;
- release status is unclear;
- rollback plan is inadequate.

## Decision

- [ ] Approved for dry-run only
- [ ] Approved for execution
- [ ] Needs changes
- [ ] Blocked

Reviewer:

Date:

Notes:
