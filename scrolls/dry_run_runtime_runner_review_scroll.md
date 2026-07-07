# Dry-run Runtime Runner Review Scroll

Status: v0.14.0 baseline.

Use this Scroll to review the Dry-run Runtime Runner before release or before trusting its output.

## Review objective

Confirm that the runner only orchestrates safe dry-run tooling:

```text
prepare sandbox
build package
validate package
inspect package
write reports inside sandbox
```

The runner must not execute mission actions.

## Required artifacts

Review these files:

- `tools/runtime_runner/run_dry_run_runtime.py`
- `tests/runtime_runner/test_run_dry_run_runtime.py`
- `schemas/runtime/runtime_run_summary.schema.json`
- `examples/sandbox_runs/runtime_run_summary.example.json`
- `docs/guides/dry_run_runtime_runner.md`

## Safety checks

Verify that the runner does not use:

- shell execution;
- subprocess execution;
- network requests;
- adapter invocation;
- Git operations;
- private context access;
- writes outside the sandbox root.

A textual mention of blocked Git operations is acceptable when it documents a boundary. It is not acceptable if it invokes Git.

## Path checks

The reviewer must confirm:

- `run_id` is validated as a single safe path segment;
- path traversal such as `../escape` fails;
- generated paths are checked against the sandbox root;
- reports are written only under `sandbox/runs/<run_id>/`;
- existing artifacts require `--force` to overwrite.

## Functional checks

Run:

```powershell
python .\tools\runtime_runner\run_dry_run_runtime.py `
  --title "v0.14 review smoke test" `
  --scope "Generate, validate, and inspect a public dry-run package." `
  --run-id "v0-14-review-smoke" `
  --sandbox-root ".\sandbox" `
  --force
```

Then verify:

- `sandbox_run_manifest.json` exists;
- `runtime_package.json` exists;
- `validation_report.json` exists;
- `inspection_report.json` exists;
- `runtime_run_summary.json` exists;
- output says `DRY-RUN RUNTIME PASSED`;
- output says execution is blocked.

## Test checks

Run:

```powershell
python -m unittest discover -s .\tests\runtime_runner -p "test_*.py"
```

Expected:

```text
Ran 5 tests
OK
```

## Stop conditions

Block release if:

- any code path executes shell commands;
- any code path performs Git operations;
- any code path invokes adapters;
- any code path accesses private Village context;
- any generated file can escape the sandbox root;
- path traversal is not rejected;
- validation or inspection can be bypassed silently;
- tests fail.

## Review outcome

Acceptable outcomes:

- `approved_for_release`;
- `revision_required`;
- `blocked`.

This Scroll does not authorize mission execution. It only reviews dry-run orchestration.
