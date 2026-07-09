# Human-approved Apply Plan

Status: prototype baseline.

The Human-approved Apply Plan prototype is the first controlled bridge from sandbox proposals to allowlisted repository files.

It is not a mission executor. It is not a version-control automation tool. It does not execute shell commands, invoke adapters, access private Village context, or perform repository version-control operations.

## Purpose

The apply plan tool reads a sandbox `apply_plan.json` and either:

- previews what would be copied from `proposed_outputs/` to allowlisted repository paths; or
- copies those files only when explicit human approval is provided.

This turns sandbox proposals into a controlled, auditable apply step.

## Inputs

Required inputs:

- `--sandbox-root`
- `--run-id`
- `--repo-root`

For real application, the caller must also provide:

- `--confirm-apply`
- `--approval-token APPLY_SANDBOX_PLAN`

Without explicit approval, the tool runs in preview mode.

## Allowed destinations

The prototype only allows destination paths under public, controlled repository areas:

- `docs/`
- `examples/`
- `runtime/templates/`
- `schemas/runtime/`
- `scrolls/`
- `alliance/templates/`
- `sandbox/tmp/`

The prototype only allows `.md`, `.json`, and `.txt` outputs.

## Blocked destinations

The tool blocks private or unsafe path segments, including:

- `.git`
- `.github`
- `kirigakure`
- `private-library`
- `private`
- `vault`
- `secrets`
- `credentials`
- `memory`
- `.env`

Path traversal and absolute paths are blocked.

## Outputs

The tool writes `human_approved_apply_report.json` inside the sandbox run unless `--no-report` is used.

The report records:

- run id;
- plan id;
- preview or applied status;
- changed paths;
- source checksums;
- approval mode;
- safety boundaries.

## Safety boundary

The tool may:

- read a sandbox apply plan;
- read sandbox proposed artifacts;
- preview planned repository changes;
- copy allowlisted files when explicitly approved;
- write an apply report inside the sandbox run.

The tool may not:

- execute mission actions;
- execute shell commands;
- perform repository version-control operations;
- invoke adapters;
- access private Village context;
- write outside allowlisted repository paths;
- authorize runtime actions.

## Stop conditions

Stop immediately when:

- the run id is unsafe;
- `apply_plan.json` is missing or invalid;
- a planned source artifact escapes `proposed_outputs/`;
- a destination path escapes the repo root;
- a destination path is outside the allowlist;
- a destination path contains private or unsafe segments;
- a destination already exists and overwrite is not explicitly allowed;
- `--confirm-apply` is used without the exact approval token.

## Relationship to previous releases

This prototype depends on:

- the local sandbox boundary;
- the dry-run runtime runner;
- the controlled sandbox artifact writer;
- the sandbox apply plan schema.

It prepares the ground for future apply gates, but it does not automate repository version-control operations.
