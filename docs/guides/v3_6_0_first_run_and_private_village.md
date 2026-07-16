# v3.6.0 First Run and Private Village

## Purpose

This guide covers first use, private village initialization and reentry.

## First run

```bash
konoha
```

Konoha inspects providers and hardware before proposing any mission action.

If the default private village does not exist, the Hokage displays:

```text
APROBAR ALDEA PRIVADA kirigakure
```

The exact phrase is required. Creation is blocked unless
`alliance/kirigakure/` is ignored by Git.

## Private structure

The initializer creates only:

```text
state/
memory/
telemetry/
budgets/
handoffs/
reports/
evals/
```

It writes `state/village_manifest.json` as evidence. The manifest grants no
execution authority.

## Reentry

On later runs, Konoha reuses the same private state. It does not recreate or
overwrite the village.

## Safety

Before sharing diagnostics, remove personal, company and client information.
Never commit the private village.
