# Runtime Package Index Template

## Status

Template.

Use this index to list package files in a stable, reviewable order.

## Package

- Package ID:
- Mission ID:
- Package title:
- Current status:
- Manifest reference:

## Recommended folder shape

```text
runtime-package/
  manifest.md
  index.md
  mission_intake.md
  dry_run_execution_plan.md
  adapter_invocation_stub.md
  evidence_collection_stub.md
  runtime_state.md
  validation_checklist.md
  validation_report.md
  trace_log.md
  trace_events/
    event_001.md
  governance/
    model_routing_decision.md
    context_budget.md
    token_usage_report.md
    capability_review.md
  closure.md
```

This folder shape is illustrative.

It does not require a runtime implementation, filesystem mutation, or automated package builder.

## Index

| Order | Artifact | Path or reference | Required | Status | Reviewer notes |
|---:|---|---|---:|---|---|
| 1 | Manifest |  | yes |  |  |
| 2 | Mission intake |  | yes |  |  |
| 3 | Dry-run execution plan |  | yes |  |  |
| 4 | Adapter invocation stub |  | conditional |  |  |
| 5 | Evidence collection stub |  | conditional |  |  |
| 6 | Runtime state |  | yes |  |  |
| 7 | Runtime validation checklist |  | yes |  |  |
| 8 | Runtime validation report |  | yes |  |  |
| 9 | Runtime trace log |  | yes |  |  |
| 10 | Trace events |  | conditional |  |  |
| 11 | Model routing decision |  | conditional |  |  |
| 12 | Context budget |  | conditional |  |  |
| 13 | Token usage report |  | conditional |  |  |
| 14 | Token budget enforcement |  | conditional |  |  |
| 15 | Capability review |  | conditional |  |  |
| 16 | Capsule manifest |  | conditional |  |  |
| 17 | Capsule refresh report |  | conditional |  |  |
| 18 | Review Scroll output |  | yes |  |  |
| 19 | Closure report |  | yes |  |  |

## Missing artifacts

| Artifact | Required reason | Impact | Owner | Due before review |
|---|---|---|---|---|
|  |  |  |  |  |

## Superseded artifacts

| Old artifact | Superseded by | Reason | Trace event |
|---|---|---|---|
|  |  |  |  |

## Review order

1. Confirm manifest authority boundary.
2. Confirm mission binding.
3. Review plan and stubs.
4. Review governance records.
5. Review validation outcome.
6. Review trace completeness.
7. Review closure report.
8. Decide whether the package is ready for review only.

## Final note

An index improves package navigation.

It does not create approval, execution rights, or runtime capability.
