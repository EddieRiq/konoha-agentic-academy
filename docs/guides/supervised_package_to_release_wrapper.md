# Supervised Package-to-Release Wrapper

## Purpose

`tools/release_delivery/run_supervised_package_release.py` composes the
existing package and release tools into one maintainer command.

```text
Package Installation Scope Guard
  ↓
Focused acceptance
  ↓
Clean terminal install smoke
  ↓
Unified Supervised Release Gate
  ↓
Read-only Release Status
```

The wrapper does not reimplement Git, tag, GitHub Release or canonical-test
authority.

## Command

```bash
python tools/release_delivery/run_supervised_package_release.py \
  --repo-root . \
  --plan examples/release_delivery/v3_3_0_supervised_package_release_plan.example.json \
  --output ./sandbox/reports/v3-3-0-package-release.json \
  --confirm-run \
  --delivery-token RUN_SUPERVISED_PACKAGE_RELEASE \
  --installation-token APPLY_SUPERVISED_PACKAGE_INSTALLATION \
  --workflow-token RUN_SUPERVISED_RELEASE_WORKFLOW \
  --git-plan-token PLAN_BETA_GIT_OPERATION \
  --git-stage-token APPROVE_BETA_GIT_STAGE \
  --git-commit-token APPROVE_BETA_GIT_COMMIT \
  --git-push-token APPROVE_BETA_GIT_PUSH \
  --tag-create-token APPROVE_SUPERVISED_RELEASE_TAG_CREATE \
  --tag-push-token APPROVE_SUPERVISED_RELEASE_TAG_PUSH \
  --release-publish-token APPROVE_SUPERVISED_RELEASE_PUBLISH \
  --latest-promotion-token APPROVE_SUPERVISED_RELEASE_LATEST \
  --allow-network \
  --force
```

## Alignment invariants

```text
delivery expected base
  = package installation expected base
  = release workflow expected base

package expected public paths
  = release workflow public paths

delivery target version
  = release workflow target version
```

## Resume behavior

On the expected base commit, the wrapper installs the package, runs focused
tests and executes the clean-install smoke.

On an exact aligned release commit, the wrapper asks the existing read-only
release status tool whether the release is safe to resume. It never reruns the
package helper on a committed release.

If the release is already closed, reentry returns `PACKAGE_RELEASE_CLOSED`
without another mutation.

## Boundaries

- every mutation token remains explicit;
- network remains explicit;
- no shell command strings;
- all detailed command logs stay under sandbox;
- test results remain evidence only;
- blocked or divergent release state stops the wrapper.
