# Ollama adapter permission matrix

Status: public declarative profile.

This file defines the default permission posture for an Ollama-style local model adapter.

It does not implement an adapter. It does not grant runtime authority by itself.

## Adapter identity

- Adapter family: Ollama-style local model execution
- Primary use: local drafting, classification, summarization, rough review, offline assistance
- Default authority: local propose-only
- Execution status: not implemented

## Permission posture

| Permission area | Default level | Notes |
|---|---|---|
| Read public repository files | Allowed with Mission Charter | Use only approved files. |
| Read ignored or private files | Blocked by default | Requires local-private authorization. |
| Process local private text | Blocked by default | Requires explicit local-private scope. |
| Generate summaries | Allowed only within approved scope | Summaries are not truth. |
| Generate code | Allowed with Mission Charter | Must be reviewed by stronger process. |
| Modify files directly | Blocked by default | Requires patch-authorized mission. |
| Run shell commands | Blocked by default | Requires command authorization. |
| Install or pull models | Blocked by default | Requires local environment approval. |
| Access network | Blocked by default | Local adapter should not imply network access. |
| Git add/commit/push/tag | Blocked by default | Requires explicit Git authorization. |
| Create or update memory | Blocked by default | Requires memory capture approval. |
| Publish outputs | Blocked by default | Requires publication safety review. |

## Allowed modes

### Local drafting mode

Ollama-style adapters may draft local notes, outlines, summaries, and rough proposals when the Mission Charter authorizes the source material.

The output must be reviewed before use.

### Local classification mode

Ollama-style adapters may classify local material into user-approved categories.

Classification is advisory and must not trigger action by itself.

### Local summarization mode

Summaries may support navigation and understanding.

They must not replace source review, approval, or evidence.

## Model quality rules

Local models can vary significantly in quality.

Reports should include:

- model name, when known;
- prompt or task summary;
- source scope;
- limitations;
- confidence level;
- reviewer notes.

Low confidence requires escalation to a stronger reviewer or human decision.

## Private context rules

Ollama-style adapters may be useful for private local work, but private access is still not automatic.

A local model running on the user's machine does not remove the need for:

- Mission Charter scope;
- approval;
- boundary checks;
- memory policy;
- publication safety.

Private input must not be transformed into public doctrine without an approved promotion process.

## Model and dependency rules

Pulling models, changing model settings, installing packages, or writing local caches requires explicit local environment approval.

Large model files and caches must stay ignored by Git.

## Git and release rules

Ollama-style adapters must not stage, commit, push, tag, or publish releases.

They may propose wording or analysis only.

## Stop conditions

Stop and ask if:

- model output is being treated as truth;
- the model would read private or ignored paths without authorization;
- the output could leak private context;
- the model requires installation, network, or local system changes;
- the task needs high factual accuracy or current information;
- the output will be used for public release;
- the model suggests actions outside the Mission Charter.

## Evidence requirements

An Ollama-style adapter report should include:

- model identity, when available;
- files or sources used;
- whether private context was included;
- summary of output;
- uncertainty notes;
- recommended human review.

## Default verdict

Ollama-style adapters are local assistants.

They are not authorities, reviewers of record, release managers, or memory governors.
