# Git Operation Runtime Readiness

Status: template.

Use this template before implementing any runtime behavior that can perform Git operations.

## Proposal

- Runtime/component name:
- Owner:
- Intended Git operations:
- Repository scope:
- Adapter integration:
- Mission Charter requirement:
- Current status:

## Supported operations

Mark only operations intended for implementation.

- [ ] Read-only Git inspection
- [ ] Stage files
- [ ] Commit
- [ ] Push
- [ ] Tag
- [ ] Push tag
- [ ] Release preparation
- [ ] Release publication
- [ ] Branch creation
- [ ] Branch deletion
- [ ] History-changing operation

## Explicitly unsupported operations

```text
<unsupported operations>
```

## Safety controls

- [ ] Mission Charter required.
- [ ] Exact command/action required.
- [ ] Dry-run required where applicable.
- [ ] Evidence pack required.
- [ ] Execution gate required.
- [ ] Private-boundary check required.
- [ ] Working tree state captured.
- [ ] Diff reviewed before staging/commit.
- [ ] Remote target confirmed.
- [ ] Rollback/recovery notes required.
- [ ] User approval recorded.

## Blocked command categories

- [ ] Force push blocked by default.
- [ ] Hard reset blocked by default.
- [ ] Destructive clean blocked by default.
- [ ] History rewrite blocked by default.
- [ ] Credential commands blocked by default.
- [ ] Global Git config mutation blocked by default.
- [ ] Branch/tag deletion blocked by default.

## Privacy controls

- [ ] Local Villages remain ignored.
- [ ] Private files cannot be staged.
- [ ] Credentials cannot be read, printed, or stored.
- [ ] Release packages cannot include local/private content.
- [ ] Logs redact sensitive content.

## Evidence and logging

- [ ] Pre-operation evidence recorded.
- [ ] Post-operation evidence recorded.
- [ ] Command output captured safely.
- [ ] Exit status recorded.
- [ ] Commit/tag hashes recorded.
- [ ] Remote state recorded where relevant.
- [ ] Failure modes recorded.

## Test/eval coverage

Required evals:

```text
<evals>
```

Required manual scenarios:

```text
<scenarios>
```

## Rollback/recovery

- Rollback strategy:
- Recovery owner:
- Known irreversible operations:
- Approval required for irreversible operations:

## Decision

- [ ] Ready for design only
- [ ] Ready for prototype
- [ ] Ready for limited local test
- [ ] Ready for broader runtime implementation
- [ ] Blocked

Reviewer:

Date:

Notes:
