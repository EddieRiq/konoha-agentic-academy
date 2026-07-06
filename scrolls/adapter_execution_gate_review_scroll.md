# Adapter Execution Gate Review Scroll

Status: public Scroll.

Use this Scroll to review whether an adapter invocation may move from read-only, dry-run, or propose-only mode into execution.

## Purpose

The Scroll protects Konoha from accidental execution.

Adapters can be useful, but they must not turn technical capability into authority.

## Required inputs

Before using this Scroll, collect:

- Mission Charter or explicit user-approved scope;
- adapter manifest;
- adapter permission matrix;
- adapter invocation request;
- requested execution level;
- dry-run or proposal evidence when applicable;
- rollback plan for side-effecting actions.

## Review sequence

### 1. Confirm adapter identity

Verify:

- adapter name;
- adapter profile;
- declared capabilities;
- declared permission limits;
- blocked actions.

Stop if the adapter identity is unclear.

### 2. Confirm mission authority

Verify that the Mission Charter allows the action.

Stop if the request is outside mission scope.

### 3. Confirm execution level

Map the request to one level:

```text
EG-0 read-only
EG-1 propose-only
EG-2 patch-authorized
EG-3 dry-run command-authorized
EG-4 command-authorized
EG-5 git-authorized
EG-6 release-authorized
EG-7 private-context-authorized
```

Stop if the requested level exceeds the permission matrix.

### 4. Confirm paths and commands

List:

- approved paths;
- blocked paths;
- approved commands;
- blocked commands.

Stop if paths or commands are ambiguous.

### 5. Confirm private-context boundary

Private context must be excluded unless explicitly authorized.

Stop if the adapter might access, summarize, copy, or publish private content without approval.

### 6. Confirm Git and release boundary

Git and release actions require separate explicit approval.

Stop if the adapter may stage, commit, push, tag, publish, or create releases without specific approval.

### 7. Review dry-run evidence

When available, dry-run evidence should show expected changes or no side effects.

Stop if dry-run evidence is missing for a risky action.

### 8. Decide

Allowed decisions:

- deny;
- request clarification;
- approve with restrictions;
- approve exactly as requested.

The decision must include an explicit approval statement.

## Output

The review output must include:

- requested execution level;
- approved scope;
- blocked scope;
- risks;
- stop conditions;
- decision;
- approval statement;
- next action.

## Stop conditions

Stop immediately if:

- the adapter tries to expand scope;
- private context appears unexpectedly;
- a command could delete, overwrite, publish, push, tag, or release without approval;
- a path is not explicitly allowed;
- validation evidence conflicts with the request;
- the user cannot understand what will happen next.

## Completion

The Scroll is complete only when the reviewer can state:

```text
This adapter invocation is denied, needs clarification, or is approved under an explicit execution level and scope.
```
