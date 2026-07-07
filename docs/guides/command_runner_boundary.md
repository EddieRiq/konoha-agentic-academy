# Command Runner Boundary

Status: planning-only baseline.

This guide defines the boundary for any future component that may request command execution.

Konoha Agentic Academy does not currently include an executable command runner. This guide is a planning artifact for future runtime work.

## Purpose

A command runner is any runtime component that can execute shell commands, scripts, tests, package operations, Git operations, release commands, or other system-level actions.

The command runner boundary exists to prevent a future runtime from turning adapter suggestions into unsupervised execution.

## Core rule

Technical ability to run a command is not permission to run it.

A command may be executed only when all of the following are true:

- a Mission Charter explicitly allows command execution;
- the adapter invocation contract allows the command category;
- the adapter permission matrix allows the requested level;
- dry-run evidence has been reviewed when required;
- the execution gate approves the action;
- the command scope is explicit;
- rollback or recovery notes exist when state may change;
- the user or authorized reviewer approves the execution.

## Non-goals

This guide does not implement:

- a shell runner;
- a task runner;
- automatic command execution;
- CI execution;
- Git automation;
- release automation;
- credential management;
- sandbox isolation;
- permission enforcement code.

## Command categories

### Read-only commands

Examples:

```text
git status
git diff --stat
tree
Get-Content
Select-String
python --version
```

Read-only commands may still expose private paths, environment details, credentials, or local context. They require scope.

### Mutating file commands

Examples:

```text
Set-Content
Move-Item
Remove-Item
New-Item
python script_that_writes_files.py
```

These require explicit write authorization and evidence of target paths.

### Package and environment commands

Examples:

```text
pip install
npm install
uv add
python -m venv
```

These may affect local environments, dependency locks, or supply-chain exposure. They require environment scope and package review.

### Git commands

Examples:

```text
git add
git commit
git tag
git push
git clean
git reset
```

Git commands require explicit Git authorization. Destructive Git commands require extra confirmation.

### Release commands

Examples:

```text
gh release create
npm publish
twine upload
docker push
```

Release commands require release authorization and final safety audit.

### Network commands

Examples:

```text
curl
wget
Invoke-WebRequest
pip install from URL
git clone external repository
```

Network commands require source review and clear destination.

### Destructive commands

Examples:

```text
Remove-Item -Recurse
rm -rf
git clean -fdx
git reset --hard
drop database
truncate table
```

Destructive commands are blocked by default and require explicit, high-confidence approval.

## Required command request fields

A future command runner must receive a structured request containing:

- mission identifier;
- command category;
- exact command;
- working directory;
- target files or directories;
- expected effect;
- expected output;
- risk level;
- rollback or recovery plan;
- dry-run evidence when applicable;
- approval record;
- stop conditions.

Free-form command execution requests are not sufficient.

## Working directory rule

A command must declare its working directory.

The runner must not infer a working directory from context unless the Mission Charter explicitly allows that inference.

## Path scope rule

Commands may access only paths explicitly allowed by the request.

Private Village paths require local-private authorization.

Public repository paths require public-repo authorization.

Cross-boundary movement from private to public paths is blocked unless explicitly reviewed and approved.

## Output boundary

Command output may contain sensitive content.

A runner must treat stdout, stderr, logs, tracebacks, file previews, environment variables, and absolute paths as potentially sensitive.

Outputs must be summarized safely when reporting publicly.

## Git boundary

A command runner must not perform Git operations unless explicitly authorized.

The following are blocked by default:

- staging all files without review;
- committing private or ignored content;
- force pushes;
- hard resets;
- destructive clean operations;
- tag creation;
- release creation;
- pushing tags;
- rewriting history.

## Environment boundary

A command runner must not assume that local environment dependencies are safe, current, or public.

Local virtual environments, local dependency locks, and private tools may exist inside ignored Villages.

They must not be promoted to public dependencies without review.

## Stop conditions

Stop before command execution if:

- the Mission Charter does not authorize commands;
- the command category is unclear;
- target paths are ambiguous;
- the command may touch private context;
- the command may mutate files outside scope;
- the command may perform Git, release, network, or destructive actions;
- rollback is missing for state-changing commands;
- expected output may reveal secrets;
- dry-run evidence is missing when required;
- approval is missing or stale.

## Minimum future implementation requirements

Before implementing any command runner, Konoha must have:

- command request template;
- command result template;
- command runner readiness template;
- execution gate integration;
- evidence pack integration;
- stop condition handling;
- private/public boundary checks;
- command logging policy;
- rollback expectations;
- user approval flow;
- eval cases for command safety.

## Status

Planning-only.

No command runner exists in Konoha at this stage.
