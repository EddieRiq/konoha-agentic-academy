# Claude adapter manifest

Status: public declarative profile.

This manifest describes a possible adapter boundary for Claude-style coding assistants. It is not an executable adapter.

## Adapter identity

- Adapter name: claude
- Adapter type: interactive coding assistant
- Runtime status: not implemented
- Default mode: advisory
- Public/private boundary: public profile only

## Purpose

This adapter profile defines how Konoha may safely interact with a coding assistant that can read instructions, reason about repositories, propose changes, review code, and explain implementation plans.

The adapter must not infer permission from model capability.

## Required doctrine

Before using this adapter profile, the operator must apply:

- `AGENTS.md`
- `core/laws/KONOHA_LAWS.md`
- `core/conduct/AGENT_CONDUCT.md`
- `protocols/mission-charter/mission_charter.md`
- `protocols/approval/approval_policy.md`
- `protocols/safety/safety_policy.md`
- `protocols/review/review_policy.md`
- `docs/guides/adapter_contracts.md`

## Allowed capabilities by default

The adapter may:

- read public repository instructions;
- explain repository structure;
- propose a Mission Charter;
- propose file changes;
- draft diffs for review;
- review staged or provided changes;
- identify safety and privacy risks;
- produce commands for a human operator to run.

## Capabilities requiring explicit Mission Charter approval

The adapter may only do the following when explicitly authorized:

- inspect local private folders;
- inspect Allied Village content;
- create or edit files;
- run shell commands;
- install dependencies;
- move or delete files;
- run tests;
- create commits;
- push branches or tags;
- prepare release notes.

## Forbidden capabilities

The adapter must not:

- treat tool access as permission;
- bypass user approval;
- publish private Village content;
- commit secrets, credentials, PDFs, converted books, local memory, local venvs, or local lock files;
- rewrite doctrine without approved doctrine-update flow;
- mark a mission complete without teachback or user confirmation.

## Operating mode

Default interaction pattern:

1. Read applicable doctrine.
2. Ask for or draft a Mission Charter.
3. Identify scope, files, and stop conditions.
4. Propose changes before execution.
5. Preserve public/private boundaries.
6. Provide verification commands.
7. Request review before closure.

## Stop conditions

Stop immediately if:

- the user request is ambiguous;
- private context may be exposed;
- a command would modify files without authorization;
- the adapter sees secrets or credentials;
- the Mission Charter does not cover the requested action;
- the action would publish local Village content.

## Review requirements

Any implementation based on this profile must include:

- adapter manifest;
- adapter capability declaration;
- adapter safety checklist;
- dry-run mode;
- audit log plan;
- review by Jounin or equivalent reviewer;
- explicit user approval before first real execution.

## Status

This is a contract profile only. It does not provide runtime code, API integration, CLI integration, or automation.
