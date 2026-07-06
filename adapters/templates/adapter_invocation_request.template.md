# Adapter invocation request

Status: template.

Use this template to request bounded work from an adapter.

This file is not permission by itself. Permission comes from the Mission Charter, adapter permission matrix, and explicit approval.

## Request identity

```text
request_id:
mission_id:
created_at:
requested_by:
adapter_id:
adapter_profile:
```

## Invocation mode

Select one:

- [ ] Read-only
- [ ] Propose-only
- [ ] Patch-authorized
- [ ] Command-authorized
- [ ] Local-private
- [ ] Release-authorized

## Requested outcome

```text
Describe the exact outcome expected.
```

## Allowed inputs

```text
List files, folders, prompts, docs, templates, or context the adapter may read.
```

## Disallowed inputs

```text
List anything explicitly out of scope.
```

## Allowed paths

```text
- path/to/file.md
- path/to/folder/
```

## Allowed outputs

```text
List what the adapter may produce.
```

## Allowed commands

Leave empty unless command execution is explicitly authorized.

| Command | Working directory | Purpose | Approval |
|---|---|---|---|
| | | | |

## Private context scope

Default: denied.

```text
Private context allowed: no
Allowed private paths: none
Reason: none
```

If private context is allowed, name exact paths and reason.

## Git permissions

Select all that apply:

- [ ] No Git mutation allowed
- [ ] `git status` allowed
- [ ] `git diff` allowed
- [ ] `git add` allowed for named files only
- [ ] `git commit` allowed with exact message
- [ ] `git push` allowed
- [ ] tag creation allowed
- [ ] release publication allowed

## Approval state

```text
Approval required before action:
Approval already granted:
Approval source:
```

## Stop conditions

The adapter must stop if:

- [ ] requested action exceeds selected mode;
- [ ] scope is ambiguous;
- [ ] a file outside allowed paths is needed;
- [ ] a command not listed above is needed;
- [ ] private context may be exposed;
- [ ] credentials or secrets may be accessed;
- [ ] copyrighted source content may be copied;
- [ ] Git or release action is needed but not approved;
- [ ] validation cannot be performed.

## Evidence required

```text
List exact evidence expected from the adapter.
```

Examples:

- `git status`
- diff summary
- test output
- file list
- check-ignore output
- validation checklist

## Expected result format

The adapter must return:

```text
request_id:
adapter_id:
mode_used:
actions_taken:
files_read:
files_modified:
commands_run:
evidence:
risks_found:
stop_conditions_triggered:
next_approval_needed:
result_status:
```

## Reviewer notes

```text
Optional notes for Jounin or Kage review.
```
