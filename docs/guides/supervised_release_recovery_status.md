# Supervised Release Recovery and Status

## Purpose

`v3.2.4` adds a read-only inspection mode to the unified release workflow.

```bash
python tools/release_workflow/run_supervised_release.py \
  --repo-root "." \
  --plan "examples/release_workflow/supervised_release_workflow_plan.example.json" \
  --output "./sandbox/reports/v3-2-4-status.json" \
  --status \
  --force
```

This local-only command does not require release mutation tokens.

## Remote inspection

To distinguish remote tag, GitHub Release and Latest states:

```bash
python tools/release_workflow/run_supervised_release.py \
  --repo-root "." \
  --plan "examples/release_workflow/supervised_release_workflow_plan.example.json" \
  --output "./sandbox/reports/v3-2-4-status-remote.json" \
  --status \
  --allow-network \
  --force
```

Remote status uses read-only operations only:

```text
git ls-remote
gh release view
gh release list
```

Status mode never runs `git fetch`, stage, commit, push, tag creation, release publication or Latest promotion.

## Recovery states

Local preparation:

```text
NEEDS_PACKAGE_APPLY
NEEDS_GIT_DELIVERY
NEEDS_BRANCH_PUSH
```

Release continuation:

```text
NEEDS_REMOTE_INSPECTION
NEEDS_TAG_CREATION
NEEDS_TAG_PUBLICATION
NEEDS_RELEASE_PUBLICATION
NEEDS_LATEST_PROMOTION
RELEASE_CLOSED
```

Blocked divergence:

```text
BLOCKED_BRANCH_MISMATCH
BLOCKED_SCOPE_MISMATCH
BLOCKED_COMMIT_DIVERGENCE
BLOCKED_WORKING_TREE
BLOCKED_TRACKING_UNKNOWN
BLOCKED_BRANCH_DIVERGENCE
BLOCKED_REMOTE_BRANCH_DIVERGENCE
BLOCKED_LOCAL_TAG_DIVERGENCE
BLOCKED_REMOTE_TAG_DIVERGENCE
BLOCKED_RELEASE_DIVERGENCE
BLOCKED_REMOTE_INSPECTION
```

## Cached test evidence

Status inspects:

```text
sandbox/reports/<workflow-id>-closure-tests.json
```

Possible states:

```text
absent
valid
stale
corrupt
```

`valid` requires:

- canonical test counts match the plan;
- the guard reports a passed test gate;
- guard HEAD matches current HEAD;
- test `head_after` matches current HEAD.

Stale or corrupt evidence is not reusable. The next unified execution performs fresh tests.

## Safe-to-resume flag

`safe_to_resume=true` means the state machine recognizes a supported continuation. It does not grant permission.

The actual unified workflow still requires:

- the full explicit token set;
- `--confirm-run`;
- `--allow-network`;
- unchanged plan, scope, release notes and HEAD.

## Reinspection after closure

Running `--status --allow-network` after a closed release should return:

```text
status_code: RELEASE_CLOSED
release_closed: true
safe_to_resume: true
next_action: No release action is required.
```

Re-running the full unified workflow on the same aligned release remains idempotent. It reuses valid test evidence when possible and verifies closure directly.

## Minimal output

```text
version
status_code
head
tracking
test_evidence
remote_inspection
safe_to_resume
next_action
report
```

Detailed evidence remains in the JSON report under sandbox.

## Authority

```text
status is evidence only
status does not authorize resume
resume requires explicit tokens
no mutation was performed
```
