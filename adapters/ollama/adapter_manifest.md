# Ollama adapter manifest

Status: public declarative profile.

This manifest describes a possible adapter boundary for local model runners such as Ollama. It is not an executable adapter.

## Adapter identity

- Adapter name: ollama
- Adapter type: local model runner
- Runtime status: not implemented
- Default mode: advisory
- Public/private boundary: public profile only

## Purpose

This adapter profile defines how Konoha may safely use a local model runner for low-risk local tasks such as summarization support, classification drafts, rewrite suggestions, and offline exploratory assistance.

A local model may be useful, but local execution does not automatically make a task safe.

## Required doctrine

Before using this adapter profile, the operator must apply:

- `AGENTS.md`
- `core/laws/KONOHA_LAWS.md`
- `core/conduct/AGENT_CONDUCT.md`
- `protocols/mission-charter/mission_charter.md`
- `protocols/context/context_policy.md`
- `protocols/approval/approval_policy.md`
- `protocols/safety/safety_policy.md`
- `memory/yamanaka/yamanaka_memory_policy.md`
- `docs/guides/adapter_contracts.md`

## Allowed capabilities by default

The adapter may:

- process explicitly approved local text;
- draft summaries of approved non-sensitive content;
- propose classifications;
- propose rewrites;
- support local brainstorming;
- generate local notes for human review.

## Capabilities requiring explicit Mission Charter approval

The adapter may only do the following when explicitly authorized:

- read Allied Village content;
- process private literature;
- process local memory;
- process project-specific files;
- write outputs;
- call tools;
- generate structured files;
- feed outputs into another agent or workflow.

## Forbidden capabilities

The adapter must not:

- assume local files are safe to read;
- treat summaries as truth;
- create memory automatically;
- publish local outputs;
- process secrets, credentials, personal data, or client data without explicit anonymization and approval;
- act as final reviewer for high-risk work;
- bypass Code Jounin, Kage Summit, or user approval.

## Operating mode

Default interaction pattern:

1. Confirm the input is approved for local processing.
2. Confirm whether output may be saved.
3. Use short, bounded prompts.
4. Mark outputs as draft.
5. Require human review before use.
6. Never promote local output to doctrine without approval.

## Stop conditions

Stop immediately if:

- the input source is unclear;
- the content may include secrets, credentials, personal data, client data, or private project context;
- the output could be mistaken for validated truth;
- the Mission Charter does not permit model processing;
- the requested action would write memory automatically.

## Review requirements

Any implementation based on this profile must include:

- adapter manifest;
- local model selection notes;
- capability declaration;
- privacy checklist;
- output retention policy;
- user approval before processing private sources;
- clear marking of generated output as draft.

## Status

This is a contract profile only. It does not provide runtime code, CLI integration, model configuration, or automation.
