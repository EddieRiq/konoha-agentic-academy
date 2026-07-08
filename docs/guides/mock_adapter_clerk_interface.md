# Mock Adapter / Clerk Interface

Status: pre-release / mock-adapter alpha.

## Purpose

The Mock Adapter / Clerk Interface provides a deterministic local adapter for testing Konoha workflows without invoking real models, APIs, adapters, or private context.

It exists to let Konoha practice adapter-shaped workflows while preserving the safety boundary.

## What it does

The mock adapter may:

- read an existing sandbox run manifest;
- create deterministic Markdown output under `sandbox/runs/<run_id>/adapter_outputs/`;
- write `mock_adapter_invocation_report.json` inside the same sandbox run;
- support simple modes such as `draft_summary`, `checklist`, and `template_note`;
- preserve non-execution, no-network, no-Git, and no-private-context boundaries.

## What it does not do

The mock adapter may not:

- call external APIs;
- run local model inference;
- invoke real adapters;
- execute shell commands;
- access private Village context;
- apply repository changes;
- perform Git operations;
- authorize runtime actions.

## Clerk boundary

A Clerk is a low-authority helper. It can draft, summarize, list, and format. It cannot approve, authorize, execute, or override gates.

Mock adapter output is always review-required.

## Required sandbox state

The target sandbox run must already exist and contain:

```text
sandbox/runs/<run_id>/sandbox_run_manifest.json
```

If the run does not exist, the mock adapter must fail.

## Example

```powershell
python .\tools\mock_adapter\run_mock_adapter.py `
  --sandbox-root ".\sandbox" `
  --run-id "example-run" `
  --task "Draft a public dry-run checklist" `
  --mode "checklist" `
  --force
```

## Output

```text
sandbox/runs/<run_id>/adapter_outputs/mock_adapter_output.md
sandbox/runs/<run_id>/mock_adapter_invocation_report.json
```

## Review rule

Mock output is never truth and never permission. It is a proposed artifact for review.
