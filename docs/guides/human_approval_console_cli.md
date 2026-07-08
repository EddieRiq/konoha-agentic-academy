# Human Approval Console CLI

The Human Approval Console CLI records human approval and rejection evidence
inside a formal Konoha Mission Workspace.

It is a product-facing approval layer, not an execution layer.

## Purpose

The console makes mission state easier to review before sensitive transitions:

- mission status;
- mission inspection;
- human approval events;
- human rejection events;
- approval event listing;
- evidence listing;
- report listing.

## Commands

```powershell
python .\tools\approval_console\manage_mission_approval.py status `
  --workspace-root ".\sandbox\workspace" `
  --mission-id "example-mission"

python .\tools\approval_console\manage_mission_approval.py approve `
  --workspace-root ".\sandbox\workspace" `
  --mission-id "example-mission" `
  --transition "apply_plan_preview" `
  --decision "approved_for_preview" `
  --reason "Evidence reviewed by human." `
  --approval-token "APPROVE_MISSION_TRANSITION"

python .\tools\approval_console\manage_mission_approval.py reject `
  --workspace-root ".\sandbox\workspace" `
  --mission-id "example-mission" `
  --transition "mission_close" `
  --decision "rejected" `
  --reason "Teachback was incomplete." `
  --approval-token "REJECT_MISSION_TRANSITION"
```

## Approval tokens

The console uses exact tokens for explicit human intent:

- `APPROVE_MISSION_TRANSITION`
- `REJECT_MISSION_TRANSITION`

These tokens are not secrets. They are friction and evidence markers. They do not
grant broad runtime authority.

## Files written

The console may write only mission-local approval artifacts:

```text
missions/<mission_id>/approvals/approval_events.jsonl
missions/<mission_id>/approvals/approval_log.md
missions/<mission_id>/reports/mission_approval_console_report.json
```

## Safety boundaries

The Human Approval Console CLI may:

- inspect a mission workspace;
- read public mission metadata;
- list mission-local evidence and reports;
- record human approval events;
- record human rejection events;
- write mission-local approval reports.

The Human Approval Console CLI may not:

- execute mission actions;
- call model providers;
- invoke real adapters;
- use network access;
- access private Village context;
- apply files to the repository;
- stage files;
- create commits;
- push changes;
- clean or reset files;
- authorize runtime actions by itself.

## UI gate

No UI implementation is included in this release.

The CLI defines the approval semantics that a future UI may display. Before any UI
implementation, Konoha must present a draft covering UI goals, screens,
navigation, stack, permission model, approval boundaries, and files to be
created. UI files should only be generated after explicit human approval.
