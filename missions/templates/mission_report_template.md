# Mission report template

Use this template after a mission is executed, reviewed, or stopped.

A Mission Report records what happened. It is evidence, not a substitute for review, approval, or teachback.

## Metadata

```yaml
mission_id: "MISSION-YYYYMMDD-001"
title: ""
status: "completed" # completed | stopped | blocked | failed | partially_completed
mode: "execution"
report_author: ""
reviewer: ""
created_at: "YYYY-MM-DD"
completed_at: "YYYY-MM-DD"
```

## 1. Mission summary

```text
What was requested:
What was delivered:
Current status:
```

## 2. Approved scope reference

```text
Mission Charter:
Approved write paths:
Approved commands:
Required review level:
```

## 3. Work performed

List only actions that were actually performed.

```text
1.
2.
3.
```

Do not include planned actions that were not executed.

## 4. Files changed

```text
Created:
- 

Modified:
- 

Deleted:
- 
```

If no files changed, write:

```text
No files changed.
```

## 5. Commands executed

```bash
# Command
# Result
```

Do not include secrets, tokens, private paths, or sensitive output.

## 6. Validation performed

```text
Validation checks:
- 

Results:
- 
```

If validation was not run, explain why.

```text
Validation not run because:
```

## 7. Evidence

Attach or summarize evidence.

```text
git status:
git diff summary:
test output:
manual checks:
```

Evidence must be specific. Do not use vague claims like "looks good" or "works as expected" without proof.

## 8. Deviations from the charter

```text
Deviations:
- none
```

If any deviation occurred, include:

```text
What deviated:
Why it happened:
Who approved it:
Impact:
```

Unapproved deviations must be treated as violations.

## 9. Risks and limitations

```text
Known risks:
- 

Known limitations:
- 

Open questions:
- 
```

## 10. Review result

```text
Review required: true
Review level:
Reviewer:
Review result: pending # pending | approved | changes_requested | blocked
Review notes:
```

The mission is not complete until required review is done.

## 11. Teachback result

```text
Teachback required: true
Teachback status: pending # pending | completed | not_required
User can explain:
- what changed:
- why it changed:
- how to use it:
- how to validate it:
- remaining risks:
```

## 12. Memory and learning

```text
Memory written: false
Memory path:
Learning proposal created: false
Learning proposal path:
```

Learning proposals may suggest doctrine changes, but they do not modify doctrine by themselves.

## 13. Final status

```text
Final status:
Closure approved by:
Closure date:
```

Allowed closure states:

```text
completed
stopped
blocked
failed
partially_completed
```

## 14. Follow-up actions

```text
Recommended follow-up:
- 
```

Do not create follow-up work unless it is explicitly approved as a new mission.
