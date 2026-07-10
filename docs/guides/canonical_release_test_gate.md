# Canonical Release Test Gate

## Purpose

Konoha contains many independent `tests/*` suite directories. Most are not
Python packages, so root-level `unittest discover` does not reliably recurse
into all of them.

The canonical gate discovers each immediate suite directory containing
`test_*.py`, runs it independently, continues after failures, and returns an
aggregate result.

## Canonical command

```bash
python tools/release_testing/run_release_tests.py
```

## Exit codes

```text
0  all selected suites passed
1  one or more suites failed or timed out
2  configuration or safety blocker
```

## Useful commands

```bash
python tools/release_testing/run_release_tests.py --list

python tools/release_testing/run_release_tests.py \
  --suite hokage_shell \
  --suite local_model_audit \
  --suite beta_runtime

python tools/release_testing/run_release_tests.py \
  --output "./sandbox/reports/canonical-release-tests.json" \
  --force
```

## Safety

The gate does not invoke models, use network access, perform Git operations,
read private context, or mutate repository source files. Optional reports are
restricted to `sandbox/`.

A passed report is evidence only.
