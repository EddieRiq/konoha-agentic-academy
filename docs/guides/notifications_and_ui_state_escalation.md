# Notifications and UI State Escalation

v2.1.0 defines the first formal notification state layer for Konoha missions.

The goal is simple:

```text
No input, no progress.
```

If Konoha needs clarification, approval, review, teachback, or human action, the mission state must say so explicitly.

## Supported states

```text
created
running
waiting_user_input
waiting_approval
blocked
ready_for_review
ready_for_teachback
closed
```

## Supported severities

```text
info
attention
blocked
urgent
```

## State authority

Notification state is evidence only.

A notification state update may:

- record that a mission is waiting;
- record what the human must do next;
- make UI state visible;
- write a mission-local notification log;
- write a mission-local state report.

A notification state update may not:

- execute mission actions;
- invoke model providers;
- invoke adapters;
- apply repository changes;
- stage files;
- create commits;
- push changes;
- access private context;
- close a mission.

## CLI

Preview only:

```powershell
python .\tools\notifications\manage_notification_state.py set `
  --workspace-root ".\sandbox\workspace" `
  --mission-id "example-mission" `
  --state "waiting_approval" `
  --reason "Human approval is required."
```

Confirmed state update:

```powershell
python .\tools\notifications\manage_notification_state.py set `
  --workspace-root ".\sandbox\workspace" `
  --mission-id "example-mission" `
  --event-id "example-waiting-approval" `
  --state "waiting_approval" `
  --severity "attention" `
  --reason "Human approval is required." `
  --required-human-action "Review the plan proposal." `
  --confirm-state-update `
  --approval-token "UPDATE_NOTIFICATION_STATE" `
  --force
```

## UI relationship

The Local Web UI Alpha should read:

```text
missions/<mission_id>/mission_notification_state.json
missions/<mission_id>/notifications/notification_log.md
missions/<mission_id>/reports/*_mission_notification_state_report.json
```

The UI may display mission state, severity, required human action, and notification history. It must not convert a notification state into permission.

## v2.0 alignment

This release preserves the v2.0 alignment decision:

- local-first;
- human-in-the-loop;
- no hidden authority;
- evidence before action;
- explicit approval before sensitive transitions;
- no autonomous mission closure.
