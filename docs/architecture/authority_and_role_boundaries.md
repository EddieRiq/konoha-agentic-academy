# Authority and role boundaries

## Status

Normative architecture derived from
`core/laws/KONOHA_LAWS.md`.

This document explains authority. It does not supersede the Constitution.

## Authority graph

```text
External law, safety obligations and explicit human authority
                              |
                              v
          Konoha Constitution and Foundational Laws
                              |
                              v
                       Agent Conduct
                              |
                              v
                 Cross-cutting protocols
                              |
                              v
                    Role-specific policies
                              |
                              v
                 Approved Mission Charter
                              |
                              v
        Scrolls, workflows and approved local configuration
                              |
                              v
              Memory, summaries and model output
                         evidence only
```

A lower layer may restrict behavior further but may not expand authority.

## Role matrix

| Role | Decides | Executes | Reviews | Proposes doctrine | Approves doctrine |
|---|---|---|---|---|---|
| Human user | Final authority | Optional | Yes | Yes | Yes |
| Hokage | Within approved bounds | No | Evaluates evidence | May request | Not unilaterally |
| Shikamaru | No operational mission authority | Drafting only | Not own proposal | Yes | No |
| Jounin | No mission strategy | No reviewed work | Yes | May recommend | No |
| Kagebunshin worker | No | One bounded assignment | Not own work | Observations only | No |
| Kage Summit | Recommends | No | Deliberates | May recommend | No |
| Yamanaka memory | No | Records and retrieves | Does not validate truth | Evidence only | No |
| Provider adapter | No | Invokes bounded provider capability | No | No | No |
| Provider model | No | Produces model output | No | No | No |

## Universal boundary contract

Every role must have:

1. explicit responsibility;
2. explicit authority;
3. explicit tools;
4. explicit context;
5. explicit budget;
6. explicit escalation path.

No role may silently substitute for another role, approve its own work, expand
its own authority or modify its own governing constraints.

Boundary violations require STOP, evidence capture and escalation.

## Mission Charter constraint

A Mission Charter may narrow authority for a mission. It may not override the
Constitution, safety obligations, approval gates or human authority.

## Provider neutrality

Providers are replaceable executors. They do not own Konoha roles and do not
decide routing, strategy, acceptance or authorization.

## Memory constraint

Memory supports continuity and context. It never grants permission and never
replaces current evidence.

## Machine-readable constitutional contract

The deterministic registry is
[`core/laws/CONSTITUTIONAL_REGISTRY.json`](../../core/laws/CONSTITUTIONAL_REGISTRY.json).

Its schema is
[`schemas/doctrine/constitutional_metadata.schema.json`](../../schemas/doctrine/constitutional_metadata.schema.json).

Architecture decisions are recorded under [`adr/`](adr/).
