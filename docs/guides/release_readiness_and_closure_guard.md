# Release Readiness and Closure Guard

## Purpose

The guard detects incomplete release states without mutating Git or GitHub.

It checks:

- clean working tree;
- canonical tests bound to current `HEAD`;
- synchronized release branch;
- local tag target;
- remote branch and tag target;
- GitHub Release existence;
- stable and Latest status.

## Status codes

```text
RELEASE_CLOSED
NEEDS_TAG_CREATION
NEEDS_NETWORK_VERIFICATION
NEEDS_TAG_PUBLICATION
NEEDS_RELEASE_PUBLICATION
NEEDS_LATEST_PROMOTION

BLOCKED_DIRTY_WORKTREE
BLOCKED_BRANCH_MISMATCH
BLOCKED_BRANCH_NOT_SYNCED
BLOCKED_REMOTE_BRANCH_MISMATCH
BLOCKED_TEST_GATE_FAILED
BLOCKED_TEST_EVIDENCE_STALE
BLOCKED_LOCAL_TAG_TARGET_MISMATCH
BLOCKED_REMOTE_TAG_TARGET_MISMATCH
BLOCKED_GH_CLI_MISSING
BLOCKED_GH_AUTH
BLOCKED_RELEASE_DRAFT
BLOCKED_RELEASE_PRERELEASE
```

## First readiness run

Run after the release commit is pushed and the tree is clean:

```bash
python tools/release_closure/check_release_closure.py \
  --repo-root "." \
  --target-version "v3.1.4" \
  --expected-branch "main" \
  --remote "origin" \
  --github-repo "EddieRiq/konoha-agentic-academy" \
  --run-tests \
  --output "./sandbox/reports/v3-1-4-release-readiness.json" \
  --force
```

Before tag creation, expected:

```text
NEEDS_TAG_CREATION
```

## Reuse tested-commit evidence

```bash
python tools/release_closure/check_release_closure.py \
  --repo-root "." \
  --target-version "v3.1.4" \
  --expected-branch "main" \
  --remote "origin" \
  --github-repo "EddieRiq/konoha-agentic-academy" \
  --test-evidence "./sandbox/reports/v3-1-4-release-readiness.json" \
  --allow-network \
  --output "./sandbox/reports/v3-1-4-release-closure.json" \
  --force
```

Reused evidence is rejected if `HEAD` changed.

## Network boundary

Without `--allow-network`, the guard does not run remote commands.

With explicit approval it uses only:

```text
git ls-remote
gh auth status
gh release list
```

It never creates or edits tags or releases.

## Exit codes

```text
0  RELEASE_CLOSED
1  incomplete or blocked release
2  configuration or safety error
```

A report is evidence only. Git and GitHub mutations remain separate human-approved operations.
