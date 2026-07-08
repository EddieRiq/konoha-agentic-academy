# Human-in-the-loop Agent Runtime Review Scroll

Use this Scroll to review Human-in-the-loop Agent Runtime runs.

## Review checklist

Confirm:

- Mission Workspace exists.
- Mission Charter is present.
- Runtime report exists under mission reports.
- Runtime report exists under sandbox reports.
- Planner loop was previewed or confirmed through the Real Model Invocation Gate.
- Controlled tool execution was previewed or confirmed through the Controlled Tool Execution Gate.
- Exact approval token evidence is present only as token name, not token value.
- No private context was accessed.
- No repository apply occurred.
- No Git operation occurred.
- No adapter invocation occurred.
- No autonomous closure occurred.

## Non-authority rules

The reviewer must preserve these rules:

```text
Model output is evidence only.
Model inference is never permission.
Controlled tool output is evidence only.
A plan proposal is not permission to execute.
Agent runtime output is not permission to apply, stage, commit, push, access private context, or close a mission.
```

## Required human decision

After reviewing the runtime report, the human reviewer may record an approval or rejection through the Human Approval Console.

The report itself does not approve anything.
