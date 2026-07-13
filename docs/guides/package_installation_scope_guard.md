# Package Installation Scope Guard

## Purpose

`v3.2.5` replaces package-specific recovery Bash with one supervised installer.

```text
ZIP extraction
    ↓
direct_repo_paths
    ↓
bounded helper
    ↓
helper_modified_paths
    ↓
exact expected_public_paths union
```

## Preview

```bash
python tools/package_installation/run_supervised_package_installation.py \
  --repo-root "." \
  --manifest "examples/package_installation/supervised_package_installation_manifest.example.json" \
  --output "./sandbox/reports/v3-2-5-install-preview.json" \
  --force
```

Expected state after extraction:

```text
READY_FOR_HELPER_APPLY
```

Preview performs no helper execution.

## Apply

```bash
python tools/package_installation/run_supervised_package_installation.py \
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
direct hashes preserved
exact public scope
no staged paths
```

## Manifest invariants

```text
direct_repo_paths ∩ helper_modified_paths = ∅
direct_repo_paths ∪ helper_modified_paths = expected_public_paths
```

All three lists are explicit. Counts alone are insufficient.

## Direct paths

Direct paths are written by ZIP extraction. They may be new or replace tracked files.

The installer records SHA-256 for every direct file before helper execution and verifies those hashes afterward.

## Helper paths

The helper lives under sandbox and is invoked with:

```text
python -S
--repo-root .
--apply
--approval-token <manifest helper token>
```

The installer does not accept helper commands from the manifest. Only the fixed helper script and arguments are used.

## Reentry

When the current public scope already equals `expected_public_paths`, apply returns:

```text
INSTALLED
helper = null
```

No helper runs again.

## Blocking conditions

- wrong branch, HEAD or tracking base;
- staged changes;
- extra or missing public paths;
- direct/helper overlap;
- incorrect public union;
- private path in manifest or actual scope;
- missing helper;
- missing installation token;
- helper failure;
- helper changes a direct package file;
- helper creates staged changes;
- output outside sandbox.

## Boundaries

The installer performs no stage, commit, push, tag, release, network, model or private-context operation.

Installation evidence does not authorize Git delivery. Delivery remains in the unified supervised release workflow.
