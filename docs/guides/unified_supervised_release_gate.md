# Unified Supervised Release Gate

## Purpose

v3.2.3 turns the three release checkpoints into one supervised state machine:

```text
Acceptance invariant
    ↓
Git Delivery invariant
    ↓
Release Closure invariant
```

The checkpoints remain separate policy boundaries. The operator runs one command.

## Components reused

The workflow does not replace existing release infrastructure. It composes:

```text
tools/beta_runtime/run_konoha_beta.py
tools/release_testing/run_release_tests.py
tools/release_closure/check_release_closure.py
git
gh
```

The existing closure guard remains read-only. Git and GitHub mutations require explicit tokens.

## Command

```bash
python tools/release_workflow/run_supervised_release.py \
  --repo-root "." \
  --plan "examples/release_workflow/supervised_release_workflow_plan.example.json" \
  --output "./sandbox/reports/v3-2-3-unified-release.json" \
  --confirm-run \
  --workflow-token "RUN_SUPERVISED_RELEASE_WORKFLOW" \
  --git-plan-token "PLAN_BETA_GIT_OPERATION" \
  --git-stage-token "APPROVE_BETA_GIT_STAGE" \
  --git-commit-token "APPROVE_BETA_GIT_COMMIT" \
  --git-push-token "APPROVE_BETA_GIT_PUSH" \
  --tag-create-token "APPROVE_SUPERVISED_RELEASE_TAG_CREATE" \
  --tag-push-token "APPROVE_SUPERVISED_RELEASE_TAG_PUSH" \
  --release-publish-token "APPROVE_SUPERVISED_RELEASE_PUBLISH" \
  --latest-promotion-token "APPROVE_SUPERVISED_RELEASE_LATEST" \
  --allow-network \
  --force
```

Approval tokens are explicit command confirmations. They are not credentials and are not stored in the public plan.

## Transition model

The workflow accepts only these closure states:

```text
BLOCKED_BRANCH_NOT_SYNCED
    → push_main

NEEDS_TAG_CREATION
    → create_tag

NEEDS_TAG_PUBLICATION
    → push_tag

NEEDS_RELEASE_PUBLICATION
    → publish_release

NEEDS_LATEST_PROMOTION
    → promote_latest

RELEASE_CLOSED
    → complete
```

Any other state stops the workflow.

An expected nonzero return code is accepted only when the report contains the expected canonical state. A nonzero return code by itself never authorizes a transition.

## Test timing

The release commit is created locally before canonical tests.

The initial closure guard then runs the canonical test gate against that exact commit. Before the main branch is pushed, the expected state is:

```text
BLOCKED_BRANCH_NOT_SYNCED
```

This is an expected guard state, not a test failure.

After the commit is pushed, later closure checks reuse the prior guard report:

```text
--test-evidence <prior-guard-report>
```

Canonical tests are not repeated while:

- HEAD is unchanged;
- the prior guard test gate passed;
- the prior report identifies the same HEAD;
- the expected suite and test counts still match.

Invalid or stale local evidence causes fresh tests instead of an inferred pass.

## Exact public scope

Before staging, the workflow compares:

```text
git diff --name-only
+
git ls-files --others --exclude-standard
```

against the sorted `public_paths` in the plan.

Extra, missing, private or duplicated paths stop the workflow.

The same scope is verified after staging and after commit.

## Idempotent resume

The workflow accepts either:

1. the expected clean base plus the exact dirty public scope; or
2. an existing clean child commit whose parent, subject and changed paths exactly match the plan.

It does not accept arbitrary later commits.

Aligned existing local tags are reused. Divergent, lightweight or rewritten tags stop the workflow.

Aligned existing test evidence for the current HEAD is reused. Stale evidence is replaced by fresh tests.

## Direct final verification

`RELEASE_CLOSED` is necessary but not sufficient for the workflow report.

The workflow also verifies directly:

- local HEAD;
- remote main;
- local annotated tag object and target;
- remote tag object and target;
- exact GitHub Release tag and title;
- draft false;
- prerelease false;
- Latest true;
- tracking 0 behind / 0 ahead;
- clean working tree.

## Output

Default stdout is intentionally minimal:

```text
version
status_code
head
tag_target
release URL
suite/test counts
tracking
working tree
report path
```

Detailed command stdout and stderr are written under:

```text
sandbox/reports/
```

No command output is truncated before JSON parsing.

## Boundaries

The workflow blocks:

```text
arbitrary shell
force push
force tag
tag rewrite
release deletion
release overwrite
model invocation
private-context access
network without explicit allowance
```

The workflow does not repair divergence. It stops and reports evidence.

## Public/private boundary

The plan cannot contain paths under private or ignored areas such as:

```text
.env
alliance/kirigakure/
alliance/*/private-library/
alliance/*/memory/
memory/local/
vault/
sandbox/
```

The only plan field allowed to reference sandbox is `release_notes_path`.

Anonymize personal, company or client information before it enters public files.
