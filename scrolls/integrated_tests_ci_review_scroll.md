# Integrated Tests and CI Review Scroll

Status: review Scroll / pre-release.

## Purpose

Review the integrated smoke-test runner, CI workflow, report schema, tests, and examples before release.

## Required evidence

- Unit tests pass.
- Integrated smoke test passes locally.
- CI workflow uses no secrets.
- CI workflow performs no Git write operations.
- Security grep shows no dangerous command execution patterns.
- Public/private boundary grep shows no private content leakage.

## Review checklist

### Runner boundary

Confirm that `tools/integration/run_integrated_smoke_tests.py`:

- uses allowlisted internal Python tools;
- does not use `shell=True`;
- does not accept arbitrary executable paths;
- writes only integration reports under sandbox;
- preserves delegated tool exit codes;
- stops on first failed step.

### CI boundary

Confirm that `.github/workflows/konoha-ci.yml`:

- runs tests;
- runs the integrated smoke test;
- does not use repository secrets;
- does not push, commit, tag, release, clean, reset, or rewrite history;
- does not upload private artifacts.

### Report boundary

Confirm that the integrated test report records:

- run ID;
- step outcomes;
- failed steps;
- safety boundary fields;
- report path.

### Stop conditions

Block release if:

- the runner executes arbitrary shell commands;
- CI performs Git write operations;
- any test fails;
- any smoke test fails;
- private content appears in public examples;
- the integrated report claims to authorize runtime actions.

## Non-authority rule

Passing integrated tests does not authorize mission execution, adapter execution, Git writes, private context access, releases, or doctrine changes.
