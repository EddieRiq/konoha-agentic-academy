# Sandbox Boundary Review Scroll

Status: review Scroll.

## Purpose

Review whether the Local Sandbox Boundary safely prepares dry-run sandbox space
without becoming an execution mechanism.

## Review inputs

Reviewers should inspect:

- `docs/guides/local_sandbox_boundary.md`;
- `schemas/runtime/sandbox_run_manifest.schema.json`;
- `tools/sandbox_boundary/sandbox_guard.py`;
- `tools/sandbox_boundary/prepare_sandbox_run.py`;
- `tests/sandbox_boundary/test_sandbox_boundary.py`;
- `examples/sandbox_runs/sandbox_run_manifest.example.json`.

## Required checks

### 1. Non-execution boundary

Confirm the tool does not:

- execute shell commands;
- perform Git operations;
- invoke adapters;
- use network access;
- access private context;
- execute missions.

### 2. Sandbox-only mutation

Confirm the only intended writes are:

- sandbox root directory creation;
- `tmp/` directory creation;
- `runs/` directory creation;
- `reports/` directory creation;
- `runs/<run_id>/sandbox_run_manifest.json`.

Any write outside the declared sandbox root is a blocker.

### 3. Path traversal rejection

Confirm path segments reject:

- `..`;
- slashes;
- backslashes;
- drive prefixes;
- URI separators;
- empty values;
- unsafe shell-like identifiers.

### 4. Manifest boundary

Confirm the manifest records:

- `mode = dry_run`;
- `execution = blocked`;
- `filesystem_mutation = sandbox_only`;
- `git_operations = blocked`;
- `adapter_execution = blocked`;
- `private_context_access = blocked`;
- `network_access = blocked`.

### 5. Tests

Confirm tests cover:

- safe identifier acceptance;
- traversal rejection;
- nested segment rejection;
- manifest creation under the sandbox root;
- refusal to overwrite without `--force`;
- valid CLI invocation.

## Stop conditions

Stop review and mark blocked if:

- subprocess, shell, Git, network, or adapter calls are present;
- the tool can write outside the sandbox root;
- run IDs can contain path traversal;
- the manifest implies execution permission;
- private context paths are read or referenced as inputs;
- tests are missing for boundary rejection.

## Review outcome

Use one of:

```text
approved_for_dry_run_sandbox_preparation
revision_required
blocked
```

Approval means the tool may prepare sandbox directories only.
Approval does not authorize runtime execution.
