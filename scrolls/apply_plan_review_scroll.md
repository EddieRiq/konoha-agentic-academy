# Apply Plan Review Scroll

Status: review baseline.

Use this Scroll to review human-approved apply plan previews and apply reports.

## Scope

This Scroll reviews:

- sandbox `apply_plan.json`;
- proposed artifacts under `proposed_outputs/`;
- allowlisted destination paths;
- human approval evidence;
- `human_approved_apply_report.json`;
- non-execution and non-version-control boundaries.

## Review questions

1. Does the apply plan belong to the expected run id?
2. Are all planned changes `propose_file` operations?
3. Does every planned change require human approval?
4. Are all source paths under `proposed_outputs/`?
5. Are all destination paths relative and allowlisted?
6. Are private paths, credentials, local Village paths, and memory paths blocked?
7. Was preview mode used before real application?
8. If `--confirm-apply` was used, is human approval explicit?
9. Does the report preserve `execution: blocked`?
10. Does the report preserve repository version-control operations as blocked?

## Required evidence

A review should include:

- command used;
- run id;
- apply plan path;
- report path;
- list of planned changes;
- preview result;
- apply result if applicable;
- reviewer decision.

## Allowed outcomes

- `approved_for_preview`: the plan can be previewed.
- `approved_for_human_apply`: the plan may be applied with explicit approval.
- `revision_required`: the plan must be fixed before apply.
- `blocked`: the plan must not be applied.

## Blockers

Block the apply plan when:

- any path escapes sandbox or repo boundaries;
- any destination touches private or ignored local context;
- any destination is outside the allowlist;
- any artifact has an unsupported extension;
- approval evidence is missing;
- the plan attempts mission execution, adapter execution, network access, or version-control operations.

## Non-authority boundary

This Scroll does not authorize mission execution, adapter execution, private context access, repository version-control operations, or autonomous apply. It only supports human review of a controlled apply plan.
