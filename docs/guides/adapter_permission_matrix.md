# Adapter permission matrix

Status: public baseline.

This guide defines permission levels for Konoha adapters before any executable adapter runtime exists.

Adapters are bridges between Konoha doctrine and external tools. They do not own authority. They can only act inside an approved Mission Charter, with the minimum permission level needed for the mission.

## Core rule

An adapter may expose capabilities, but it may not grant itself permission.

Permission comes from:

1. Konoha laws.
2. The Mission Charter.
3. Approval policy.
4. Safety policy.
5. Public/private boundary policy.
6. Adapter contract review.

If any of these conflict, the stricter rule wins.

## Permission levels

| Level | Name | Purpose | Can modify files? | Can run commands? | Can access private local context? | Can publish/release? |
|---:|---|---|---|---|---|---|
| 0 | Disabled | Adapter is known but inactive | No | No | No | No |
| 1 | Read-only | Inspect public files and report findings | No | No | No | No |
| 2 | Propose-only | Propose changes, diffs, commands, or plans | No | No | No | No |
| 3 | Patch-authorized | Edit approved public files inside scope | Yes, scoped | No | No | No |
| 4 | Command-authorized | Run approved non-destructive commands | Scoped | Yes, scoped | No | No |
| 5 | Local-private-authorized | Work inside an approved ignored local Village | Scoped | Scoped | Yes, scoped | No |
| 6 | Release-authorized | Prepare release artifacts after review | Scoped | Scoped | No, unless separately approved | Yes, scoped |

Level numbers are not a ladder of trust. A mission should use the lowest level that satisfies the task.

## Level 0: Disabled

Use when an adapter is experimental, deprecated, unsafe, unknown, or not yet reviewed.

Allowed:

- document its existence;
- review its manifest;
- propose questions for evaluation.

Not allowed:

- reading project files;
- modifying files;
- running commands;
- using private context;
- publishing anything.

## Level 1: Read-only

Use for audits, repository inspection, documentation review, and context gathering.

Allowed:

- read approved public repository files;
- summarize findings;
- identify risks;
- recommend next steps.

Not allowed:

- modify files;
- run commands;
- inspect ignored local Villages;
- access secrets;
- publish or push changes.

## Level 2: Propose-only

Use when an adapter can design changes but should not make them.

Allowed:

- propose file changes;
- propose commands;
- draft diffs;
- produce review notes;
- prepare Mission Charter updates.

Not allowed:

- write files;
- execute proposed commands;
- stage, commit, push, tag, or release;
- read private local context unless separately authorized.

## Level 3: Patch-authorized

Use when the user approves file edits within a clear scope.

Allowed:

- create, edit, move, or delete files explicitly listed in the Mission Charter;
- generate public documentation artifacts;
- update templates and scrolls within scope;
- report diffs.

Not allowed:

- run shell commands unless separately authorized;
- edit files outside scope;
- touch ignored private folders;
- modify secrets or credentials;
- stage, commit, push, tag, or release unless separately authorized.

## Level 4: Command-authorized

Use when the adapter may run approved commands, usually for validation.

Allowed:

- run explicitly approved non-destructive commands;
- run tests, linters, formatters, status checks, or read-only Git commands;
- report command output and failures.

Not allowed by default:

- destructive commands;
- network calls;
- credentialed operations;
- dependency installation;
- shell scripts from untrusted sources;
- `git add`, `git commit`, `git push`, `git tag`, or release publication;
- operations outside the Mission Charter.

Potentially destructive or sensitive commands require explicit approval even at this level.

## Level 5: Local-private-authorized

Use for ignored Allied Villages and private local workflows.

Allowed only when the Mission Charter names the local Village and scope:

- read approved local Village files;
- create local notes, local memory, local source cards, local principle cards, or local reports;
- use local venvs and local requirements;
- work with private sources under approved boundaries.

Not allowed:

- copying private local content into the public repository;
- quoting long copyrighted excerpts;
- committing ignored Village files;
- leaking local paths, secrets, client data, private literature, or personal data;
- promoting local learning without approval.

This level does not imply release authority.

## Level 6: Release-authorized

Use for final release preparation after review.

Allowed:

- update release notes;
- verify changelog;
- create or propose tags;
- prepare GitHub release text;
- run final release checks.

Not allowed:

- bypassing publication safety review;
- releasing private content;
- creating a release from a dirty working tree;
- publishing without explicit user approval.

## Permission matrix by action

| Action | L0 | L1 | L2 | L3 | L4 | L5 | L6 |
|---|---|---|---|---|---|---|---|
| Read public docs | No | Yes | Yes | Yes | Yes | Yes | Yes |
| Summarize findings | No | Yes | Yes | Yes | Yes | Yes | Yes |
| Propose changes | No | No | Yes | Yes | Yes | Yes | Yes |
| Write approved public files | No | No | No | Yes | Scoped | No by default | Scoped |
| Run read-only commands | No | No | No | No | Yes | Scoped | Yes |
| Run tests or linters | No | No | No | No | Yes | Scoped | Yes |
| Install dependencies | No | No | No | No | Explicit approval | Local only with approval | No by default |
| Read ignored local Village files | No | No | No | No | No | Scoped | No by default |
| Write ignored local Village files | No | No | No | No | No | Scoped | No by default |
| Read secrets or credentials | No | No | No | No | No | No | No |
| Commit public changes | No | No | No | No | Explicit approval | No | Explicit approval |
| Push to remote | No | No | No | No | Explicit approval | No | Explicit approval |
| Create tag | No | No | No | No | No by default | No | Explicit approval |
| Publish release | No | No | No | No | No | No | Explicit approval |

## Adapter manifest requirement

Every executable adapter proposal must declare:

- requested maximum permission level;
- default permission level;
- supported actions;
- prohibited actions;
- command execution model;
- file access model;
- network access model;
- private context policy;
- logging policy;
- stop conditions;
- rollback plan.

A missing permission declaration means Level 0.

## Escalation

Escalate to Kage Summit when:

- an adapter asks for command execution and file writing together;
- an adapter needs local private context;
- an adapter needs network or credentialed access;
- an adapter proposes release authority;
- the capability boundary is ambiguous;
- the adapter could modify doctrine, safety rules, approval rules, memory policy, or release process.

## Stop conditions

Stop immediately if:

- the adapter requests permissions not approved by the Mission Charter;
- the adapter attempts to infer permission from available tools;
- private context may leak;
- secrets, tokens, credentials, or personal data appear;
- a command is destructive, credentialed, networked, or outside scope;
- the user cannot explain the intended action;
- the working tree is dirty before release actions;
- the adapter output contradicts Konoha laws.

## Review outcome

A permission review may return:

- approved at requested level;
- approved at lower level;
- approved with constraints;
- blocked pending clarification;
- rejected.

Approvals should be recorded in the mission report or adapter review notes.
