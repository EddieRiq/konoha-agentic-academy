# Mission charter template

Use this template before any execution mission.

A Mission Charter defines what an agent may do. It does not grant authority beyond the approved scope. If an action is not explicitly allowed here, the agent must stop and ask.

## Metadata

```yaml
mission_id: "MISSION-YYYYMMDD-001"
title: ""
status: "draft"
mode: "planning" # conversation | planning | execution | review | teachback | learning
requester: ""
hokage: ""
local_kage: ""
assigned_agents: []
review_required: true
review_level: "level_2_jounin" # level_0_none | level_1_clerk | level_2_jounin | level_3_kage_summit
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
```

## 1. Mission objective

Describe the mission in one or two sentences.

```text
Objective:
```

## 2. Background and source context

List the context that may be used for this mission.

```text
Approved context sources:
- 
```

Rules:

- Do not use private or local context unless it is listed here.
- Do not infer missing context from memory.
- If required context is missing, stop and ask.

## 3. Scope

### In scope

```text
The agent may:
- 
```

### Out of scope

```text
The agent may not:
- 
```

## 4. Allowed paths

List the files or folders the agent may read or modify.

```text
Read allowed:
- 

Write allowed:
- 
```

Rules:

- Empty write scope means read-only.
- Broad write scope must be approved explicitly.
- Local Village paths are private by default.

## 5. Allowed commands

List commands the agent may run.

```bash
# Examples
git status
git diff
```

Rules:

- Commands not listed here are not allowed.
- State-changing commands require explicit approval.
- Network access, dependency installation, destructive commands, and external uploads require explicit approval.

## 6. Forbidden actions

The following actions are forbidden unless explicitly approved in this charter:

```text
- Modify doctrine.
- Access private local Village context.
- Read secrets, credentials, tokens, .env files, or private keys.
- Run destructive filesystem commands.
- Install dependencies.
- Push, merge, deploy, publish, or upload externally.
- Rewrite Git history.
- Declare the mission complete without required review and teachback.
```

## 7. Agent assignment

```text
Hokage role:
- 

Kagebunshin role:
- 

Shikamaru role:
- 

Jounin reviewer role:
- 

Clerk role:
- 
```

Only include roles that are needed.

## 8. Execution plan

Write the planned steps before executing.

```text
1.
2.
3.
```

Each step must fit the approved scope.

## 9. Evidence requirements

Define what evidence must be produced.

```text
Required evidence:
- git status
- git diff summary
- files changed
- tests or validation output
- known limitations
```

## 10. Review requirements

```text
Required review level:
Reviewer:
Review criteria:
- 
```

The mission cannot close until the required review is complete.

## 11. Teachback requirement

Define what the user must be able to explain at the end.

```text
The user should be able to explain:
- what changed;
- why it changed;
- how to use it;
- how to validate it;
- what risks remain.
```

## 12. Memory and learning

```text
May write memory: false
May create learning proposal: false
Allowed memory path:
```

Rules:

- Memory does not authorize action.
- Learning proposals do not rewrite doctrine.
- Local lessons stay local unless promoted explicitly.

## 13. Approval

```text
Human approval:
- approved_by:
- approved_at:
- notes:

Hokage approval:
- approved_by:
- approved_at:
- notes:
```

No execution may begin before approval is recorded.

## 14. Stop conditions

The agent must stop and ask if:

```text
- the scope is unclear;
- required context is missing;
- a command is not listed as allowed;
- a file is outside the approved path;
- private data, secrets, or credentials appear;
- execution would change doctrine;
- execution would require network access;
- validation fails;
- the result differs from the expected outcome.
```
