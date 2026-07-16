# ADR-0003: Provider neutrality

## Status

Accepted for v3.6.0 constitutional baseline.

## Context

Codex, Claude, Ollama and future providers expose different interfaces and may
change independently.

## Decision

Providers and adapters are replaceable bounded executors. They do not own
Konoha roles, decide routing, approve results, expand scope or authorize
actions.

## Consequences

- Hokage decisions are expressed as capability requirements.
- Adapters translate authorized requests to provider-specific contracts.
- Provider output is evidence only.
