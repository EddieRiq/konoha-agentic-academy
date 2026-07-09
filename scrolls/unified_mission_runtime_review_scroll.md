# Unified Mission Runtime Review Scroll

Use this Scroll to review v2.6 Unified Mission Runtime outputs.

## Review checklist

- The mission charter exists and matches the requested task.
- The manifest records safety boundaries.
- The runtime plan has clear phases.
- Command proposals are explicit and reviewable.
- Every command proposal is marked `proposed_only`.
- No command execution occurred.
- Notification state requires human review.
- Runtime report is evidence only.
- Optional memory note was written only with explicit approval.
- No Git operation occurred.
- No model invocation occurred.
- No adapter invocation occurred.
- No private context was accessed by default.

## Non-authority rule

```text
Command proposals are not permission.
Runtime reports are not permission.
Memory notes are not permission.
```

## Release readiness

Before release, confirm:

- tests pass;
- smoke preview writes no mission workspace;
- confirmed start writes expected mission files;
- wrong token is blocked;
- security grep has no dangerous command execution patterns.
