# Local Model Bootstrap, Repo Audit and Patch Flow

v3.0.1 adds the first beta patch flow after Konoha v3.0.0.

The purpose is to let Konoha:

1. profile the local computer from WSL or Linux;
2. recommend an Ollama local model;
3. create an Ollama install plan if Ollama is missing;
4. download a local model only with explicit approval;
5. use the local model to summarize the repository and compare README/index documentation against the actual repository structure;
6. produce a repo consistency audit;
7. propose safe documentation patches;
8. apply approved documentation patches;
9. hand off Git add/commit/push to the existing v3 beta Git gate.

## Authority

Local computer profiles are evidence only.

Local model recommendations are not permission.

Local model download plans do not download models.

Local model output is evidence only.

Patch plans are not permission.

Git operations are not handled by this tool. Use the existing Konoha Beta Git gate.

## Approval tokens

```text
PROFILE_LOCAL_COMPUTER
RECOMMEND_LOCAL_MODEL
PLAN_OLLAMA_INSTALL
DOWNLOAD_LOCAL_MODEL
RUN_LOCAL_MODEL_AUDIT
APPLY_LOCAL_MODEL_DOC_PATCH
```

## Main commands

```bash
python tools/local_model_audit/manage_local_model_audit.py profile --json
python tools/local_model_audit/manage_local_model_audit.py recommend ...
python tools/local_model_audit/manage_local_model_audit.py install-plan ...
python tools/local_model_audit/manage_local_model_audit.py pull-model ...
python tools/local_model_audit/manage_local_model_audit.py audit-repo ...
python tools/local_model_audit/manage_local_model_audit.py apply-doc-patch ...
```

## Ollama

The tool can prepare the official Linux install plan, but it does not execute the install command.

Model pull is executed only through:

```bash
ollama pull <model>
```

and only when the user passes `--allow-network`, `--confirm-download`, and `--approval-token DOWNLOAD_LOCAL_MODEL`.

Repository audit uses the local Ollama API at `http://localhost:11434/api/generate` only when `--use-ollama`, `--allow-localhost`, and `RUN_LOCAL_MODEL_AUDIT` are provided.

## Test strategy

The test suite uses `--mock-local-model` so CI does not require Ollama, network, or a downloaded local model.

Real beta validation should run the same audit with `--use-ollama`.
