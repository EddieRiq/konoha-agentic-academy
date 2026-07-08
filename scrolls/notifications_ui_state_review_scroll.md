# Notifications and UI State Review Scroll

Use this Scroll to review notification-state updates and UI escalation behavior.

## Review checklist

- Is the mission state explicit?
- Is the required human action clear?
- Is the severity appropriate?
- Is the state written only inside the Mission Workspace?
- Is the notification log mission-local?
- Does the state update avoid authorizing execution?
- Does the UI preserve no-new-authority rules?
- Are private context, Git operations, model calls, adapter calls, network access, and repository apply still blocked?

## Required conclusion

A notification state update is valid only if it improves human visibility without creating new runtime authority.
