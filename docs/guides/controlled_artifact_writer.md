# Controlled Artifact Writer inside Sandbox

Status: validation-tool alpha.

The Controlled Artifact Writer creates proposed artifacts only inside an existing sandbox run.

It is not a mission executor. It does not apply files to the repository.

## Purpose

The writer allows a dry-run workflow to produce proposed outputs without mutating public doctrine, runtime files, Git state, adapters, or private Village context.

Allowed output location:

```text
sandbox/runs/<run_id>/proposed_outputs/
```

Metadata written inside the same run:

```text
sandbox/runs/<run_id>/apply_plan.json
sandbox/runs/<run_id>/artifact_write_report.json
```

## Safety boundary

The writer may:

- read the sandbox run manifest;
- create proposed artifact files inside `proposed_outputs/`;
- create or update an apply plan inside the same run;
- create an artifact write report inside the same run;
- reject unsafe paths and path traversal.

The writer may not:

- execute shell commands;
- perform Git operations;
- invoke adapters;
- access private Village context;
- read ignored local knowledge sources;
- write outside the configured sandbox run;
- apply proposed files to the repository;
- authorize runtime actions.

## Required existing run

The target run must already contain:

```text
sandbox/runs/<run_id>/sandbox_run_manifest.json
```

The manifest must keep these boundaries blocked:

```text
execution = blocked
git_operations = blocked
adapter_execution = blocked
private_context_access = blocked
```

## Allowed artifact extensions

Initial allowed extensions:

```text
.md
.json
.txt
```

Python, shell, JavaScript, TypeScript, binary, and executable artifacts are intentionally blocked at this stage.

## Apply plan boundary

`apply_plan.json` is a proposal record only.

It does not authorize copying, moving, committing, or pushing files.

A future release may define a human-approved apply gate. Until then, every planned change remains:

```text
apply_status = not_applied
requires_human_approval = true
```

## Example

```powershell
python .\tools\artifact_writer\write_sandbox_artifact.py `
  --sandbox-root ".\sandbox" `
  --run-id "demo-run" `
  --artifact-path "docs/proposed_note.md" `
  --content "# Proposed note" `
  --artifact-kind "markdown" `
  --intended-repo-path "docs/proposed_note.md" `
  --force
```

Expected boundary output:

```text
SANDBOX ARTIFACT WRITTEN
Execution: blocked
Filesystem mutation: sandbox only
Repository apply: blocked
Git operations: blocked
Private context access: blocked
Adapter execution: blocked
Network access: blocked
```

## Stop conditions

Stop if:

- the run manifest is missing;
- the run id is unsafe;
- artifact path escapes `proposed_outputs/`;
- artifact extension is not allowed;
- JSON artifact content is invalid;
- the target artifact already exists and `--force` was not provided;
- any boundary field implies execution, Git, adapters, or private context access.
