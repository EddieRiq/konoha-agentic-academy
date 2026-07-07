# Session Resource Probe

Status: documentation-first baseline.

A Session Resource Probe is a safe, optional check performed at the beginning of a mission to understand available model, adapter, token, quota, or context resources.

It does not grant execution authority.

## Purpose

Some adapters may expose token usage, quota, context size, or session limits. Others may not.

Konoha should use this information when available, but it must not invent token availability when the adapter does not provide it.

## Core rule

```text
Measure when possible. Estimate when necessary. Never pretend an estimate is exact.
```

## Probe types

### Adapter-declared

The adapter reports:

- model name;
- context limit;
- available quota;
- token usage;
- rate limit;
- billing or quota warning.

Confidence: high if directly reported by the adapter.

### Command-based

A read-only command returns resource information.

Allowed only when the Mission Charter or user explicitly allows the command.

Confidence: medium to high depending on adapter reliability.

### User-provided

The user provides current usage or limits.

Confidence: medium unless independently verifiable.

### Estimated

Konoha estimates usage from text length, files loaded, or prior runs.

Confidence: low to medium.

### Unavailable

No reliable token or quota data is available.

Konoha must use conservative defaults.

## Probe output

A probe report should state:

```text
adapter:
model:
source:
confidence:
reported_context_limit:
reported_remaining_quota:
estimated_available_budget:
measurement_method:
commands_run:
private_data_accessed:
limitations:
recommended_context_mode:
recommended_model_tier:
escalation_trigger:
```

## Allowed behavior

A probe may:

- ask the user whether resource probing is allowed;
- run read-only commands if authorized;
- record unavailable data honestly;
- recommend a conservative budget;
- suggest capsule-first mode;
- suggest task splitting.

## Not allowed

A probe must not:

- run commands without authorization;
- inspect private context without approval;
- query credentials;
- infer secret quotas from private files;
- continue if probing requires unsafe access;
- treat unavailable data as unlimited budget.

## Session start prompt

A Konoha session may ask:

```text
Do you want to allow a read-only session resource probe for token/context/quota information?
```

The user may answer:

```text
yes
no
manual only
adapter reported only
```

If the answer is no, the system proceeds with conservative assumptions.

## Conservative defaults

When resource data is unavailable:

- prefer capsule-first;
- avoid loading broad source trees;
- split large tasks;
- ask before high-token operations;
- record usage as estimated;
- use lower-cost models only when risk allows;
- escalate when uncertainty affects safety or quality.

## Probe and privacy

Resource probing must not access:

- secrets;
- `.env`;
- credentials;
- private literature;
- local memory;
- private Village context;
- project-specific files.

Unless explicitly authorized by Mission Charter.

## Probe and model routing

The probe informs model routing, but it does not decide routing alone.

Routing still depends on:

- risk;
- mission type;
- available capsules;
- eval history;
- reviewer requirement;
- private-context exposure;
- expected complexity.

## Probe failure

If the probe fails:

- record failure;
- do not retry repeatedly without reason;
- do not escalate to unsafe commands;
- use conservative defaults;
- ask user if the missing information matters.

## Probe result status

Use one of:

- available;
- partially available;
- estimated;
- unavailable;
- blocked;
- failed.

## Relationship to token reports

The Session Resource Probe happens before work.

The Token Usage Report happens after or during work.

Together they answer:

```text
What resources did we expect?
What did we use?
Was the usage justified?
What should change next time?
```
