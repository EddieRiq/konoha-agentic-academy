# Integrated Tests and CI

Status: pre-release / integrated-test alpha.

## Purpose

This guide defines the integrated test and CI baseline for Konoha Agentic Academy.

The baseline connects the existing safe local-first tools into a repeatable smoke test. It verifies that the toolchain can validate config, run the dry-run runtime, validate and inspect the generated package, list sandbox runs, inspect the public repository, inspect Git readiness, and preview a proposed artifact workflow.

## Boundary

This baseline is not a mission executor.

It does not:

- execute mission actions;
- execute arbitrary shell commands;
- invoke adapters;
- access private Village context;
- perform Git write operations;
- apply repository changes;
- authorize runtime actions.

It may:

- run allowlisted internal Python tools;
- write integration reports under the configured sandbox root;
- run unit tests;
- run in CI;
- fail when any delegated tool fails.

## Integrated smoke-test runner

The runner is:

```text
tools/integration/run_integrated_smoke_tests.py
```

Recommended local command:

```powershell
python .\tools\integration\run_integrated_smoke_tests.py --repo-root "." --sandbox-root ".\sandbox" --run-id "local-integrated-smoke"
```

The runner writes:

```text
sandbox/reports/<run_id>_integrated_test_report.json
```

## CI workflow

The GitHub Actions workflow is:

```text
.github/workflows/konoha-ci.yml
```

The workflow installs Python, runs the test suite, and runs the integrated smoke-test runner.

## Review expectations

A reviewer should verify that:

- the runner uses `subprocess.run` only for allowlisted internal tools;
- `shell=True` is not used;
- outputs are limited to sandbox reports and delegated sandbox tools;
- Git write operations remain blocked;
- private context access remains blocked;
- CI does not require secrets;
- CI does not publish artifacts or mutate repository state.

## Stop conditions

Stop if:

- any integrated step fails;
- the runner attempts arbitrary command execution;
- the runner writes outside sandbox;
- the runner requires secrets;
- CI attempts Git write operations;
- private or ignored local paths are introduced into public fixtures.
