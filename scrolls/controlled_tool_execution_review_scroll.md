# Controlled Tool Execution Review Scroll

Use this Scroll before approving controlled tool execution.

## Review checklist

- Is the action in the allowlist?
- Is the execution plan public and mission-scoped?
- Is `requires_human_approval` true?
- Is the exact token `EXECUTE_CONTROLLED_TOOL` required for confirmed execution?
- Are private context, network access, Git operations, repository apply, real model invocation, arbitrary shell, and background agents blocked?
- Does the action map to a fixed internal Konoha tool?
- Are output reports written under sandbox?
- Is the result treated as evidence only?

## Stop conditions

Stop if:

- the plan requests arbitrary shell;
- the plan requests network access;
- the plan requests private context;
- the plan requests Git operations;
- the plan requests repository apply;
- the plan requests real model invocation;
- the action is not allowlisted;
- the user cannot explain why the tool is being run.

## Closure

A controlled tool execution report does not close a mission. Human review remains required.
