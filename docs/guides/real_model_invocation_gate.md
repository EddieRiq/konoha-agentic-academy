# Real Model Invocation Gate

The Real Model Invocation Gate is the first Konoha boundary that can permit a real provider call under explicit human approval.

The gate is intentionally narrow.

A valid model request plan is not permission to call a model.

Model inference is never permission.

## Supported provider modes

- `mock`: deterministic local provider for test and dogfood evidence.
- `openai`: real provider call through an explicit gate.
- `anthropic`: real provider call through an explicit gate.
- `ollama`: local provider call through an explicit gate.

Real providers require:

- existing sandbox run;
- model provider contract;
- model request plan;
- provider allowlist;
- `real_model_invocation_enabled: true`;
- `requires_network: true`;
- `--confirm-invocation`;
- exact approval token `INVOKE_REAL_MODEL`;
- `--allow-network`;
- no private context;
- no secret-like prompt content;
- token and cost budgets within contract.

## Output boundary

The gate writes only inside:

```text
sandbox/runs/<run_id>/model_outputs/
sandbox/runs/<run_id>/model_invocation_gate_report.json
```

The model output is evidence only. It must be reviewed by a human before any apply, stage, commit, execution, or mission closure.

## Non-authority rules

The gate may not:

- execute mission actions;
- execute arbitrary shell commands;
- invoke tools from model output;
- access private Village context;
- apply files to the repository;
- stage files;
- create commits;
- push changes;
- clean or reset files;
- authorize runtime actions;
- close a mission.

## Credentials

Provider credentials must be supplied only through local environment variables.

Examples:

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
```

Never commit credentials, `.env` files, raw tokens, API responses containing secrets, or private context.
