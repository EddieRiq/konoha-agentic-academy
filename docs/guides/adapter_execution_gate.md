# Adapter Execution Gate

Status: public baseline.

This guide defines when an adapter invocation may move from planning, dry-run, or propose-only behavior into real execution.

The Execution Gate does not grant authority by itself. It is a review boundary that checks whether authority has already been granted by Konoha doctrine, the Mission Charter, the adapter permission matrix, and explicit user approval.

## Purpose

Adapters may have technical capabilities that are broader than their approved authority.

The Execution Gate prevents this failure mode:

```text
technical capability -> accidental action
```

Konoha requires this flow instead:

```text
Mission Charter
  -> adapter contract
  -> permission matrix
  -> invocation request
  -> dry-run or proposal
  -> execution gate review
  -> explicit approval
  -> execution
  -> result report
```

## Core rule

No adapter may execute a side-effecting action merely because it can.

Execution requires:

- an approved Mission Charter;
- a declared adapter profile;
- a permission matrix that allows the requested level;
- a concrete invocation request;
- explicit scope;
- explicit stop conditions;
- evidence from dry-run or proposal when applicable;
- explicit user approval for the action.

## Execution levels

### EG-0: Read-only

The adapter may inspect approved public files or approved local files.

It may not modify files, run commands with side effects, access private context, stage Git changes, push, tag, or publish.

### EG-1: Propose-only

The adapter may propose changes, commands, plans, checklists, or patches in text.

It may not apply changes.

### EG-2: Patch-authorized

The adapter may create or modify files only inside approved paths.

This level requires explicit file scope and a rollback plan.

### EG-3: Dry-run command-authorized

The adapter may run commands that are expected to be read-only or preview-only.

Examples include status checks, diff checks, validation commands, and dry-run commands.

### EG-4: Command-authorized

The adapter may run side-effecting commands only when each command has been explicitly authorized.

Commands must be listed in the invocation request or approved one by one.

### EG-5: Git-authorized

The adapter may stage, commit, push, tag, or otherwise mutate Git state only when the Mission Charter explicitly allows it.

Git authorization is separate from file edit authorization.

### EG-6: Release-authorized

The adapter may help prepare release notes, tags, or release checklists.

Publishing a release requires explicit user approval after final audit evidence.

### EG-7: Private-context-authorized

The adapter may access local private context only when the Mission Charter names the private path or source and explains why access is required.

Private-context authorization never implies publication permission.

## Gate inputs

An Execution Gate review must have:

```text
adapter profile
adapter permission matrix
Mission Charter or equivalent user-approved scope
invocation request
requested execution level
allowed paths
blocked paths
allowed commands
blocked commands
dry-run evidence when applicable
rollback plan
approval requirement
```

## Required checks

Before execution, verify:

- the requested level is not higher than the adapter permission matrix allows;
- the action is inside the approved Mission Charter;
- private context is excluded unless explicitly authorized;
- generated outputs do not include secrets or private content;
- Git actions are separately authorized;
- release actions are separately authorized;
- dry-run evidence has been reviewed when available;
- the user can understand what will happen before it happens.

## Stop conditions

Stop before execution if:

- the scope is ambiguous;
- the adapter asks for a higher level than approved;
- the action touches private context without explicit permission;
- the command could delete, overwrite, publish, push, tag, release, or expose data;
- the rollback plan is missing for side-effecting actions;
- the adapter output contains secrets, credentials, private data, or unapproved source content;
- the user has not approved the specific action.

## Approval language

Approval should be specific.

Weak approval:

```text
Looks good.
```

Strong approval:

```text
Approve EG-2 patch-authorized execution for these files only:
- docs/guides/example.md
- scrolls/example_scroll.md
No Git push. Stop on unexpected diff.
```

## Result reporting

After execution, the adapter result must report:

- what was executed;
- which files or commands were affected;
- what evidence was produced;
- whether stop conditions were triggered;
- whether any scope was skipped;
- current Git status when relevant;
- next recommended step.

## Non-goals

This guide does not implement an adapter runtime.

It does not define API calls, CLI wrappers, daemon processes, or automation.

It defines the public safety contract that executable integrations must satisfy later.
