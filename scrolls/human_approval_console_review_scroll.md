# Human Approval Console Review Scroll

Use this Scroll to review approval-console behavior before accepting a mission
transition.

## Review checklist

- Confirm the mission workspace exists.
- Confirm `mission_manifest.json` and `charter.md` exist.
- Confirm approval events are mission-local.
- Confirm approval token evidence is present.
- Confirm approval reason is specific.
- Confirm rejection reason is specific when applicable.
- Confirm evidence and reports are listed, not modified.
- Confirm no real adapter invocation occurred.
- Confirm no Git operation occurred.
- Confirm no repository apply occurred.
- Confirm no private context was accessed.
- Confirm UI implementation remains gated until a draft is approved.

## Required boundaries

```text
Execution: blocked
Repository apply: blocked
Git operations: blocked
Private context access: blocked
Real adapter execution: blocked
Network access: blocked
```

## Reviewer note

Approval events are evidence of human intent for a specific transition. They are
not broad authorization for autonomous execution.
