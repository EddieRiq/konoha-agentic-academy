# Model Router and Token Economy

v2.7.0 adds the model routing and token economy layer for Konoha.

This guide defines how Konoha profiles the local runtime, recommends local or remote model use, records routing decisions, prepares local model download plans, records token usage, and summarizes token efficiency.

## Core rules

```text
Model routing is evidence only.
Model choice is not permission.
Token estimates are not truth.
Usage reports do not authorize execution.
Local model download plans do not download models.
```

## What v2.7 does

v2.7 can:

- build a safe model runtime profile;
- detect common local tool presence with read-only PATH inspection;
- classify tasks by type, risk, and privacy level;
- recommend local, remote, or mixed model strategies;
- record model routing decisions;
- prepare local model download plans;
- record actual token usage when providers report it;
- estimate token usage when providers do not report it;
- build a token usage ledger;
- summarize token economy and suggest optimization directions.

## What v2.7 does not do

v2.7 does not:

- invoke models;
- download models;
- run shell commands;
- use network access;
- call provider APIs;
- access private context by default;
- apply repository changes;
- stage files;
- commit files;
- push changes;
- authorize mission execution;
- close missions.

## Token accounting

Providers may report usage differently.

Konoha records usage as:

```text
actual     -> provider or CLI reported token usage
estimated  -> local heuristic, currently characters / 4
```

Estimated tokens must be marked as estimated. Summaries are operational evidence, not truth.

## Calibration

When actual and estimated records exist, Konoha can begin calibrating estimation error. Calibration is gradual and should be reviewed over multiple missions.

## Local model download planning

Local model download plans produce command proposals such as:

```text
ollama pull qwen2.5-coder:7b-instruct
```

The plan does not execute the command. A future execution workbench or command gate must request explicit approval before running it.

## v3.0 relevance

v2.7 prepares the economy layer required for v3.0 beta missions. In a real supervised task, Konoha should explain which model it wants to use, why, what it expects the token cost to be, and how well that choice performed afterward.
