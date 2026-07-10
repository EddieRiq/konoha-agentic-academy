# Canonical Release Test Gate Review Scroll

## Required evidence

```bash
python -m unittest discover \
  -s tests/release_testing \
  -p "test_*.py"

python tools/release_testing/run_release_tests.py --list
python tools/release_testing/run_release_tests.py

python tools/release_testing/run_release_tests.py \
  --suite hokage_shell \
  --suite local_model_audit \
  --suite beta_runtime

git diff --check
```

## Review questions

- Are non-package suites discovered?
- Does execution continue after failure?
- Does a failed suite make the final command fail?
- Are commands arrays executed with `shell=False`?
- Are report writes restricted to `sandbox/`?
- Are outputs bounded?
- Are Git, network, model and private-context operations blocked?
- Is success described as evidence only?

## Stop conditions

Stop before Git stage if any suite is silently skipped, a failure returns zero,
or report output escapes `sandbox/`.
