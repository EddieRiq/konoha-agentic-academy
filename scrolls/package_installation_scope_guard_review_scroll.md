# Package Installation Scope Guard Review Scroll

## Package integrity

```bash
sha256sum -c \
  sandbox/tmp/v3-2-5-package/SHA256SUMS
```

## Focused tests

```bash
python -S -m unittest discover \
  -s tests/package_installation \
  -p "test_*.py"
```

Expected:

```text
12 tests
0 failures
0 errors
```

## Preview

```bash
python -S tools/package_installation/run_supervised_package_installation.py \
  --repo-root "." \
  --manifest "examples/package_installation/supervised_package_installation_manifest.example.json" \
  --output "./sandbox/reports/v3-2-5-install-preview.json" \
  --force
```

Expected:

```text
READY_FOR_HELPER_APPLY
direct paths = 10
helper paths = 7
public scope = 10
```

## Apply

```bash
python -S tools/package_installation/run_supervised_package_installation.py \
  --repo-root "." \
  --manifest "examples/package_installation/supervised_package_installation_manifest.example.json" \
  --output "./sandbox/reports/v3-2-5-installed.json" \
  --apply \
  --approval-token "APPLY_SUPERVISED_PACKAGE_INSTALLATION" \
  --force
```

Expected:

```text
INSTALLED
direct paths = 10
helper paths = 7
public scope = 17
direct hashes preserved = true
```

## Reentry

Repeat the apply command.

Expected:

```text
INSTALLED
helper = null
```

## Static review

Confirm the installer:

- uses `shell=False`;
- runs only Git read commands;
- invokes the fixed helper path with fixed argv;
- contains no stage, commit, push, tag, release or network command;
- blocks sandbox in public path lists;
- writes reports only under sandbox.

## Stop conditions

Stop if:

- actual direct scope differs from the manifest;
- direct/helper sets overlap;
- the public union is not exact;
- helper changes a direct path;
- staged or private paths appear;
- focused or canonical counts differ;
- release plan scope differs from 17 paths.
