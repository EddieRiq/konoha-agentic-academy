# General Task Execution Workbench Review Scroll

Use this Scroll to review v2.8 task workbench outputs.

## Review questions

1. Is the task stated clearly?
2. Is the target environment explicit?
3. Are command proposals separated from permission?
4. Are dangerous actions blocked?
5. Are private context and credentials protected?
6. Is there a verification checklist?
7. Are rollback notes present?
8. Are command results recorded as evidence only?
9. Is the workbench ready for a future v3.0 supervised execution run?

## Required non-authority language

The review must preserve:

```text
Command proposals are not permission.
Recorded command results are evidence only.
A workbench report does not authorize execution.
v2.8 does not execute arbitrary commands.
```

## Stop conditions

Stop review if:

- arbitrary execution is introduced;
- network use is introduced without a separate gate;
- private context is requested by default;
- credentials are requested or stored;
- repository apply is implied;
- Git operations are implied;
- mission closure is implied.
