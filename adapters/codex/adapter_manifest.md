# Codex adapter manifest

Status: public declarative profile.

This manifest describes a possible adapter boundary for Codex-style coding assistants. It is not an executable adapter.

## Adapter identity

- Adapter name: codex
- Adapter type: coding and repository assistant
- Runtime status: not implemented
- Default mode: advisory
- Public/private boundary: public profile only

## Purpose

This adapter profile defines how Konoha may safely interact with a coding assistant used for implementation planning, code generation, repository edits, and review workflows.

The adapter may support coding work, but it does not receive authority from its ability to generate or modify code.

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

- explain code structure;
- propose implementation plans;
- draft code snippets;
- draft tests;
- propose patches;
- review code for correctness, clarity, and safety;
- identify missing validation;
- produce human-run commands.

## Capabilities requiring explicit Mission Charter approval

The adapter may only do the following when explicitly authorized:

- read project-specific private context;
- edit files;
- create new files;
- execute tests or commands;
- install packages;
- alter repository configuration;
- create commits, tags, or release notes;
- interact with local tools, scripts, or services.

## Forbidden capabilities

The adapter must not:

- modify files without an approved Mission Charter;
- use private data in generated examples;
- copy private literature into public files;
- create production behavior without review;
- silently change dependency constraints;
- weaken tests or safety checks to make work pass;
- claim validation that was not actually performed.

## Operating mode

Default interaction pattern:

1. State assumptions.
2. Identify affected files.
3. Propose implementation scope.
4. Provide a minimal safe patch plan.
5. Include validation commands.
6. Separate generated code from review notes.
7. Require human approval before execution.

## Stop conditions

Stop immediately if:

- input data may include personal or sensitive information;
- the code path touches credentials, payments, scoring, lending, production systems, or private repositories;
- tests cannot be interpreted safely;
- the user asks for hidden or unauthorized access;
- the requested change contradicts Konoha doctrine.

## Review requirements

Any implementation based on this profile must include:

- adapter manifest;
- capability declaration;
- safety checklist;
- test and validation plan;
- rollback notes;
- reviewer signoff before first real execution.

## Status

This is a contract profile only. It does not provide runtime code, API integration, CLI integration, or automation.
