# Adapter Invocation Gate Disabled by Default

Status: pre-release / adapter-gate alpha.

## Purpose

The Adapter Invocation Gate introduces a controlled boundary for adapter-shaped workflows while keeping real adapter execution disabled by default.

This release exists to prove the gate shape before any real adapter integration.

## Core rule

Real adapter invocation is blocked in this baseline.

Mock adapter invocation is allowed only when all of the following are true:

- an existing sandbox run is present;
- `--confirm-invocation` is provided;
- the exact approval token `INVOKE_ADAPTER_GATE` is provided;
- `--enable-mock-adapter` is provided;
- outputs remain inside `sandbox/runs/<run_id>/adapter_outputs/`.

## Allowed behavior

The gate may:

- read an existing sandbox run manifest;
- preview an adapter invocation request;
- write deterministic mock adapter output inside the sandbox run;
- write `adapter_invocation_gate_report.json` inside the sandbox run;
- reject real adapter requests;
- reject unsafe run IDs and missing manifests;
- emit text or JSON reports.

## Blocked behavior

The gate may not:

- call real adapters;
- call external APIs;
- run local model inference;
- use network access;
- execute shell commands;
- apply files to the repository;
- perform Git operations;
- access private Village context;
- authorize runtime actions.

## Output contract

A confirmed mock invocation writes:

```text
sandbox/runs/<run_id>/adapter_outputs/adapter_gate_mock_output.md
sandbox/runs/<run_id>/adapter_invocation_gate_report.json
```

Outputs are review-required. They are not doctrine, authority, approval, or evidence of real adapter capability.

## Relationship to mock adapter

The previous mock adapter proved deterministic sandbox-only adapter-shaped output.

This gate adds an explicit approval boundary around that idea. It is intentionally conservative before any future real adapter invocation gate.

## Stop conditions

Stop if:

- the run ID is unsafe;
- the sandbox run manifest is missing;
- real adapter invocation is requested;
- approval token is missing or incorrect;
- `--enable-mock-adapter` is missing for confirmed mock invocation;
- outputs already exist and `--force` is not provided;
- any output would leave the sandbox run.
