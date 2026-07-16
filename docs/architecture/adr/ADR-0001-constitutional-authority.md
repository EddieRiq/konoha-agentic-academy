# ADR-0001: Constitutional authority

## Status

Accepted for v3.6.0 constitutional baseline.

## Context

Konoha already contained foundational laws, conduct rules, protocols and role
policies, but authority precedence was implicit and partially ambiguous.

## Decision

`core/laws/KONOHA_LAWS.md` is the supreme repository doctrine.

External law, safety obligations and explicit human authority remain binding.
Lower repository layers may restrict behavior but may not expand authority.

## Consequences

- Mission Charters cannot override the Constitution.
- Memory and model output remain evidence only.
- Conflicts must stop and escalate.
