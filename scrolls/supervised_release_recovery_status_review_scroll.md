# Supervised Release Recovery and Status Review Scroll

## Focused tests

```bash
python -m unittest discover \
  -s tests/release_workflow \
  -p "test_*.py"
```

Expected:

```text
24 tests
0 failures
0 errors
```

## Local-only status

```bash
python tools/release_workflow/run_supervised_release.py \
  --repo-root "." \
  --plan "examples/release_workflow/supervised_release_workflow_plan.example.json" \
  --output "./sandbox/reports/v3-2-4-status-local.json" \
  --status \
  --force
```

Review:

- no token arguments;
- no `--allow-network`;
- no fetch;
- no Git or release mutation;
- report under sandbox.

Before Git delivery, expected state:

```text
NEEDS_GIT_DELIVERY
```

## Remote read-only status

```bash
python tools/release_workflow/run_supervised_release.py \
  --repo-root "." \
  --plan "examples/release_workflow/supervised_release_workflow_plan.example.json" \
  --output "./sandbox/reports/v3-2-4-status-remote.json" \
  --status \
  --allow-network \
  --force
```

After closure, expected state:

```text
RELEASE_CLOSED
```

## Static command review

Inspect every command in `inspect_release_status`.

Allowed remote commands:

```text
git ls-remote
gh release view
gh release list
```

Blocked:

```text
git fetch
git add
git commit
git push
git tag
gh release create
gh release edit
gh release delete
```

These commands remain allowed only in the existing token-gated execution workflow, not in status mode.

## Evidence recovery

Corrupt the copied status-test fixture, not production evidence:

```text
invalid JSON → corrupt
valid report for another HEAD → stale
matching report → valid
missing report → absent
```

No stale or corrupt evidence may produce `reusable=true`.

## Reentry check

After release closure:

```bash
python tools/release_workflow/run_supervised_release.py \
  --repo-root "." \
  --plan "examples/release_workflow/supervised_release_workflow_plan.example.json" \
  --output "./sandbox/reports/v3-2-4-status-after-close.json" \
  --status \
  --allow-network \
  --force
```

Confirm:

```text
status_code = RELEASE_CLOSED
release_closed = true
safe_to_resume = true
working tree remains clean
tracking remains 0/0
```

## Stop conditions

Stop if:

- status mode fetches or mutates refs;
- local-only status accesses network;
- tokens are required for status;
- status output escapes sandbox;
- exact scope is misclassified;
- divergence is classified as resumable;
- stale/corrupt evidence is reusable;
- remote inspection failure is hidden;
- closed release is not recognized;
- canonical counts differ from 49/371.
