# Release Readiness and Closure Guard Review Scroll

## Focused tests

```bash
python -m unittest discover \
  -s tests/release_closure \
  -p "test_*.py"
```

## Canonical gate

```bash
python tools/release_testing/run_release_tests.py
```

## Readiness smoke

Run only after committing and pushing v3.1.4:

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

Expected before tag creation:

```text
NEEDS_TAG_CREATION
```

## Security questions

- Are subprocess commands arrays with `shell=False`?
- Are Git write commands absent?
- Are GitHub mutation commands absent?
- Does network require `--allow-network`?
- Are output and evidence paths restricted to `sandbox/`?
- Does stale test evidence block closure?
- Must local and remote tags point to tested `HEAD`?
- Is output described as evidence only?

## Stop conditions

Stop before Git stage if:

- any mutation command appears;
- a dirty tree can pass;
- stale test evidence can pass;
- remote checks run without network approval;
- reports can escape `sandbox/`;
- draft or prerelease state is treated as a closed stable release.
