# Model Provider Contract

## Purpose

The Model Provider Contract defines how Konoha records and validates model-shaped requests before real model invocation exists.

v1.4.0 does not invoke model providers. It creates a safe public contract for providers, request plans, token budgets, cost limits, context-source allowlists, private-context blockers, redaction requirements, and logging requirements.

## Capability boundary

The contract validator may:

- read a public model provider contract JSON file;
- read a public model request plan JSON file;
- validate provider allowlists;
- validate context-source allowlists;
- validate token budgets;
- validate estimated cost limits;
- block network-required requests;
- block private-context requests;
- block secret-like prompt patterns;
- print text and JSON reports.

The contract validator may not:

- call model providers;
- call external APIs;
- use network access;
- execute tools;
- execute mission actions;
- access private Village context;
- read credentials;
- apply repository changes;
- stage files;
- create commits;
- push changes;
- authorize runtime actions.

## Required v1.4 defaults

```text
Invocation: blocked
Execution: blocked
Filesystem mutation: blocked
Git operations: blocked
Private context access: blocked
Real model invocation: blocked
Network access: blocked
Human review required: true
```

## Provider handling

The contract may list future providers such as `openai`, `anthropic`, and `ollama`, but v1.4 only validates plans. A request for a future real provider may be valid as a plan, but invocation remains blocked until a later Real Model Invocation Gate.

## Context policy

Allowed context sources should be explicit and public or mission-local:

- `mission_workspace`
- `sandbox`
- `public_repo`

Blocked context sources must remain blocked by default:

- `private_village`
- `env`
- `credentials`
- `secrets`

## Token and cost policy

The request plan must include:

- estimated prompt tokens;
- requested completion tokens;
- estimated cost;
- provider;
- model;
- purpose;
- context sources.

The validator fails if requested budgets exceed contract limits.

## Secret handling

Prompts must not include credentials or secret-like patterns. The validator performs lightweight guard checks, but this does not replace human review.

## UI gate

No UI implementation is included in this release.

Before any UI implementation, Konoha must present a draft covering UI goals, screens, navigation, stack, permission model, approval boundaries, and files to be created. UI files should only be generated after explicit human approval.
