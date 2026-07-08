# Proposed Artifact Workflow Review Scroll

Status: review Scroll / pre-release alpha.

## Purpose

Review proposed artifact workflow runs before they are treated as valid evidence.

## Review inputs

Required inputs:

- workflow command or invocation record;
- sandbox run manifest;
- runtime package;
- artifact write report;
- apply plan;
- proposed artifact workflow report;
- apply report when confirmed apply was used.

## Checks

The reviewer must verify:

1. The workflow stayed inside `sandbox/runs/<run_id>/`.
2. The artifact path does not use traversal, absolute paths, or private/local-only paths.
3. The intended repository path is allowlisted by policy.
4. Apply mode is preview-only unless explicit human approval is documented.
5. Confirmed apply uses the exact approval token and delegated apply-plan gate.
6. No Git operation occurred.
7. No adapter invocation occurred.
8. No private Village context was accessed.
9. The workflow report includes all delegated steps and pass/fail status.

## Stop conditions

Stop review if:

- proposed outputs target private paths;
- the apply plan targets non-allowlisted destinations;
- apply occurred without explicit approval;
- Git operations are present;
- shell execution or network access is present;
- the report is missing or inconsistent with sandbox artifacts.

## Outcome

Allowed outcomes:

- `approved_for_review`: workflow evidence is coherent and bounded;
- `revision_required`: report or proposed artifact needs correction;
- `blocked`: safety boundary violation or missing approval evidence.

This Scroll does not authorize execution, adapter calls, Git operations, private context access, or repository changes.
