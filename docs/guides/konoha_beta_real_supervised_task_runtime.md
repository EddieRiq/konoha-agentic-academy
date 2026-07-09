# Konoha Beta: Real Supervised Task Runtime

v3.0.0 is the first beta release intended for a supervised real technical task.

It is not autonomous. It is a supervised runtime that can:

- create a beta mission;
- classify the task;
- recommend a local/remote/model-agent strategy;
- prepare command proposals;
- call mock, Claude Code, Codex, or Ollama with explicit approval;
- capture token usage when available;
- estimate tokens when usage is not reported;
- execute exact approved commands with `shell=False`;
- record command evidence;
- self-review the mission;
- gate Git stage, commit, and push;
- close the mission only with teachback.

## External agent adapters

Supported provider names:

```text
mock
claude
codex
ollama
```

### Claude Code

The Claude adapter calls:

```text
claude -p "<prompt>"
```

The output is stored as evidence under the Mission Workspace. It is not treated as permission.

### Codex

The Codex adapter calls:

```text
codex exec --json --sandbox read-only "<prompt>"
```

Konoha parses Codex JSONL usage when available. When usage is not available, Konoha records an explicit estimate.

### Ollama

The Ollama adapter calls:

```text
ollama run <model> "<prompt>"
```

Local model invocation still requires explicit approval.

Local model download is separate:

```text
ollama pull <model>
```

Download requires both `DOWNLOAD_LOCAL_MODEL` and `--allow-network`.

## Approval tokens

```text
START_BETA_MISSION
PLAN_BETA_MISSION
INVOKE_EXTERNAL_AGENT
INVOKE_LOCAL_MODEL
PLAN_LOCAL_MODEL_DOWNLOAD
DOWNLOAD_LOCAL_MODEL
EXECUTE_APPROVED_COMMAND
RECORD_EXTERNAL_RESULT
RECORD_BETA_REVIEW
PLAN_BETA_GIT_OPERATION
APPROVE_BETA_GIT_STAGE
APPROVE_BETA_GIT_COMMIT
APPROVE_BETA_GIT_PUSH
CLOSE_BETA_MISSION
```

## Safety boundaries

Konoha Beta may not:

- run background autonomous agents;
- execute unapproved commands;
- use arbitrary shell;
- invoke external agents without token;
- invoke local models without token;
- download models without token and network allowance;
- access private context by default;
- stage forbidden paths;
- commit without explicit approval;
- push without explicit approval and `--allow-network`;
- close without teachback.

## Recommended first beta flow

```powershell
python .\tools\beta_runtime\run_konoha_beta.py doctor --json

python .\tools\beta_runtime\run_konoha_beta.py start `
  --workspace-root ".\sandbox\beta-workspace" `
  --mission-id "real-task-001" `
  --title "Real supervised task" `
  --task "Describe the task here." `
  --confirm-start `
  --approval-token "START_BETA_MISSION" `
  --force

python .\tools\beta_runtime\run_konoha_beta.py plan `
  --workspace-root ".\sandbox\beta-workspace" `
  --mission-id "real-task-001" `
  --plan-id "real-task-001-plan" `
  --confirm-plan `
  --approval-token "PLAN_BETA_MISSION" `
  --force
```

Then review:

```text
plans/<plan>_beta_runtime_plan.json
plans/<plan>_command_proposals.json
inputs/<plan>_agent_prompt.md
```

Invoke a model/agent only after review.

## Teachback

Closure requires:

```text
CLOSE_BETA_MISSION
I_CAN_EXPLAIN_AND_DEFEND_THIS_MISSION
```

A mission is not complete until the user can explain and defend what was done.
