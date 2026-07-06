# Adapter safety checklist template

Status: public template.

Use this checklist before an adapter is allowed to execute or generate changes.

This checklist does not replace the Mission Charter.

## Mission boundary

- [ ] Mission Charter exists.
- [ ] Objective is explicit.
- [ ] Adapter role is explicit.
- [ ] Allowed inputs are listed.
- [ ] Allowed outputs are listed.
- [ ] Allowed paths are listed.
- [ ] Forbidden paths are listed.
- [ ] Stop conditions are listed.
- [ ] Required approvals are listed.

## Public/private boundary

- [ ] No private Village content will be committed.
- [ ] No private source material will be copied into public files.
- [ ] No local memory will be published.
- [ ] No credentials, tokens, or `.env` files will be read or printed.
- [ ] No personal data or client data will be included in outputs.
- [ ] Local-only files remain ignored by Git.

## Execution safety

- [ ] Commands are non-destructive or explicitly approved.
- [ ] Writes are limited to approved paths.
- [ ] Dependency installation is approved if needed.
- [ ] Network access is disabled or explicitly approved.
- [ ] Generated files are reviewed before commit.
- [ ] Rollback or cleanup path is known.

## Git safety

- [ ] `git status` was checked before action.
- [ ] Adapter will not stage ignored private files.
- [ ] Adapter will not commit without explicit approval.
- [ ] Adapter will not push without explicit approval.
- [ ] Tags or releases require explicit approval.
- [ ] Public diffs were reviewed before commit.

## Memory and learning safety

- [ ] Adapter will not update memory unless authorized.
- [ ] Learning proposals are separated from approved doctrine.
- [ ] Literature is treated as evidence, not doctrine.
- [ ] Local notes are not promoted without approval.

## Review safety

- [ ] Jounin review is required for code, tools, adapters, or commands.
- [ ] Security review is required for credentials, network, shell execution, or publishing.
- [ ] Hokage or Local Kage approval is required when authority is unclear.
- [ ] Kage Summit escalation is required for conflicts between safety, scope, or doctrine.

## Validation evidence

Attach or describe validation evidence.

```text
<validation-evidence>
```

## Final decision

- [ ] Proceed
- [ ] Proceed with limits
- [ ] Needs changes
- [ ] Blocked

Reason:

```text
<reason>
```

Approver:

```text
<name-or-role>
```

Date:

```text
<YYYY-MM-DD>
```
