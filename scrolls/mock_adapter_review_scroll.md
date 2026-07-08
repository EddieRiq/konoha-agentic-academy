# Mock Adapter Review Scroll

Status: pre-release / review scroll.

## Purpose

Review mock adapter behavior before relying on mock-generated outputs in a dry-run workflow.

## Required checks

- Confirm the adapter is deterministic and local-only.
- Confirm no external API, model server, network, or real adapter is invoked.
- Confirm outputs are written only inside `sandbox/runs/<run_id>/adapter_outputs/`.
- Confirm `mock_adapter_invocation_report.json` is written inside the same sandbox run.
- Confirm output is marked review-required.
- Confirm the tool rejects path traversal and unsafe output names.
- Confirm the tool does not perform Git operations.
- Confirm the tool does not access private Village context.
- Confirm the tool does not authorize runtime actions.

## Stop conditions

Stop if:

- the adapter attempts network access;
- the adapter accepts arbitrary script paths;
- the adapter writes outside the sandbox run;
- the adapter reads ignored/private paths;
- the adapter performs Git operations;
- the adapter claims approval authority;
- the adapter output is treated as final truth.

## Review outcome

Allowed outcomes:

- `approved_for_mock_dry_run_use`
- `revision_required`
- `blocked`

Approval for mock dry-run use does not authorize real adapter invocation.
