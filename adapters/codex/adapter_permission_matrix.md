# Codex adapter permission matrix

Status: public declarative profile.

This file defines the default permission posture for a Codex-style coding assistant adapter.

It does not implement an adapter. It does not grant runtime authority by itself.

## Adapter identity

- Adapter family: Codex-style coding assistant
- Primary use: code generation, refactoring, tests, bug fixes, implementation drafts
- Default authority: propose-only
- Execution status: not implemented

## Permission posture

| Permission area | Default level | Notes |
|---|---|---|
| Read public repository files | Allowed with Mission Charter | Scope must be explicit. |
| Read ignored or private files | Blocked by default | Requires local-private authorization. |
| Generate code | Allowed with Mission Charter | Generated code must be reviewed. |
| Propose patches | Allowed with Mission Charter | Patches are not self-approved. |
| Modify files directly | Blocked by default | Requires patch-authorized mission. |
| Run tests | Blocked by default | Requires command-authorized mission. |
| Run shell commands | Blocked by default | Requires explicit command authorization. |
| Install dependencies | Blocked by default | Requires dependency review. |
| Access network | Blocked by default | Requires explicit approval. |
| Git add/commit/push/tag | Blocked by default | Requires Git authorization and review. |
| Access local Village context | Blocked by default | Requires local-private authorization. |
| Create or update memory | Blocked by default | Requires learning capture approval. |
| Publish outputs | Blocked by default | Requires publication safety review. |

## Allowed modes

### Code proposal mode

Codex-style adapters may propose:

- functions;
- modules;
- tests;
- refactors;
- bug fixes;
- migration plans;
- validation commands.

The user or reviewer must approve before adoption.

### Patch-authorized mode

Direct file changes require a Mission Charter that names:

- allowed paths;
- intended behavior;
- forbidden paths;
- validation expectations;
- rollback or restore strategy.

### Test-authorized mode

Tests or validation commands may be run only when command authority is granted.

The adapter must report:

- command;
- result;
- failure details;
- changed files, if any.

## Dependency rules

Codex-style adapters must not add dependencies casually.

Adding or updating dependencies requires:

- purpose;
- package name;
- version policy;
- security and license awareness;
- public/private boundary review;
- user approval.

For local Villages, dependencies should stay local unless the repo intentionally introduces public executable functionality.

## Private context rules

Codex-style adapters must not use private context to generate public code unless the Mission Charter explicitly permits a safe abstraction.

Do not copy local project details, proprietary logic, private data, logs, credentials, or literature excerpts into public files.

## Git and release rules

Codex-style adapters must not stage, commit, push, tag, or publish releases by default.

Git authority must be explicit and scoped.

Generated code is not merge approval.

## Stop conditions

Stop and ask if:

- the code change touches sensitive paths;
- tests require network, credentials, private services, or destructive state;
- the adapter would need private context;
- dependency changes are required but not authorized;
- generated code may encode private logic;
- validation cannot be reproduced;
- the requested implementation weakens safety or review rules.

## Evidence requirements

A Codex-style adapter report should include:

- requested behavior;
- proposed files;
- reasoning summary;
- validation plan;
- tests or checks run, if authorized;
- unresolved risks.

## Default verdict

Codex-style adapters are useful implementation assistants.

They are not merge authorities, release authorities, or private-context authorities.
