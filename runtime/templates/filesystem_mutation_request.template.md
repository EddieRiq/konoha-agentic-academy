# Filesystem Mutation Request

Status: template.

Use this template before requesting any future component to create, modify, move, rename, overwrite, or delete files.

## Request metadata

- Request ID:
- Mission ID:
- Requester:
- Date:
- Adapter/runtime component:
- Mode requested:
  - [ ] read-only
  - [ ] propose-only
  - [ ] patch-prepared
  - [ ] mutation-authorized
  - [ ] local-private mutation-authorized
  - [ ] destructive mutation-authorized

## Mission Charter reference

- Mission Charter path:
- Mission Charter approved by:
- Mission Charter approval date:
- Does the Mission Charter explicitly allow filesystem mutation?
  - [ ] yes
  - [ ] no

If no, stop.

## Target scope

List exact paths.

```text
<path-1>
<path-2>
<path-3>
```

## Operation types

Select all requested operations.

- [ ] create file
- [ ] edit file
- [ ] append to file
- [ ] overwrite file
- [ ] move file
- [ ] rename file
- [ ] delete file
- [ ] create directory
- [ ] delete directory
- [ ] change permissions
- [ ] change encoding
- [ ] change line endings
- [ ] generate artifact
- [ ] other:

## Expected changes

Describe intended mutations.

```text
<short description>
```

## Files expected to be created

```text
<file-list>
```

## Files expected to be modified

```text
<file-list>
```

## Files expected to be deleted

```text
<file-list>
```

## Private-context check

- Does this request touch local private workspaces?
  - [ ] no
  - [ ] yes
- Does this request touch private sources, memory, credentials, secrets, client data, or local artifacts?
  - [ ] no
  - [ ] yes

If yes, describe the approved local boundary.

```text
<approved private boundary>
```

## Git impact

- Does this request require Git staging?
  - [ ] no
  - [ ] yes
- Does this request require commit?
  - [ ] no
  - [ ] yes
- Does this request require push?
  - [ ] no
  - [ ] yes
- Does this request require tag or release?
  - [ ] no
  - [ ] yes

Git operations require separate approval.

## Dry-run or preview

Provide one.

- [ ] proposed file list
- [ ] diff preview
- [ ] generated artifact preview
- [ ] command preview
- [ ] no-op dry-run
- [ ] not available

Evidence:

```text
<paste or reference preview evidence>
```

If dry-run is not available, explain why.

```text
<reason>
```

## Rollback or recovery plan

```text
<rollback notes>
```

## Approval

- Filesystem mutation approved?
  - [ ] yes
  - [ ] no
- Destructive action approved?
  - [ ] not applicable
  - [ ] yes
  - [ ] no

Approver:

Date:

## Stop conditions reviewed

- [ ] Mission Charter exists.
- [ ] Paths are explicit.
- [ ] Operations are explicit.
- [ ] Private context risk is reviewed.
- [ ] Git operations are not bundled without approval.
- [ ] Dry-run or preview is documented.
- [ ] Rollback or recovery notes exist.
