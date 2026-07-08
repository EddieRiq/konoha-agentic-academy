# Local Web UI Alpha

Local Web UI Alpha adds a local browser interface for operating Konoha without adding new runtime authority.

The UI exposes existing mission, approval, report, and safety concepts through a local-only server-rendered interface.

## Purpose

The UI helps a human operator:

- see workspace and sandbox status;
- list Mission Workspaces;
- create Mission Workspaces under an explicit workspace root;
- inspect Mission Charters and manifests;
- inspect plans, reports, evidence, and approval logs;
- record human approval or rejection evidence with an exact approval token;
- view system safety boundaries;
- copy equivalent CLI commands.

## Non-authority rule

The UI is not an agent and not an authority layer.

The UI may display and record evidence. It may not grant permission that the underlying gates do not already grant.

## Allowed in v1.7 alpha

- Read Mission Workspaces.
- Read mission manifests.
- Read Mission Charters.
- Read mission-local plans, reports, evidence, and approvals.
- Create Mission Workspaces under an explicit workspace root.
- Record approval/rejection evidence with exact token `APPROVE_MISSION_TRANSITION`.
- Write local UI session reports under sandbox reports.
- Display safety boundaries.
- Display equivalent CLI commands.

## Blocked in v1.7 alpha

- Autonomous mission execution.
- Real model invocation from UI.
- Adapter invocation from UI.
- Repository apply from UI.
- Git stage from UI.
- Git commit from UI.
- Git push from UI.
- Arbitrary shell execution.
- Free-form path access.
- Private Village context access.
- Network access beyond localhost serving.
- Background agents.
- Token storage.
- Token autofill.

## Server boundary

Default startup must bind only to localhost:

```powershell
python .\tools\ui_server\run_konoha_ui.py `
  --repo-root "." `
  --workspace-root ".\sandbox\workspace" `
  --sandbox-root ".\sandbox" `
  --host "127.0.0.1" `
  --port 8765
```

Binding to a non-localhost address requires explicit human approval and the `--allow-non-localhost` flag.

## Stack

- FastAPI
- Jinja2 templates
- Uvicorn
- Filesystem-first storage
- Minimal CSS and JavaScript

## Dependency installation

The UI uses third-party packages. Install them in the local virtual environment:

```powershell
python -m pip install fastapi uvicorn jinja2
```

Unit tests for UI services do not require the server dependencies.

## Approval handling

The UI does not store or autofill approval tokens.

Human approvals recorded through the UI require the exact token:

```text
APPROVE_MISSION_TRANSITION
```

Recording an approval event is evidence only. It does not execute any mission step.

## Model handling

In v1.7 alpha, real model invocation remains blocked from the UI.

The UI may show model-related reports and planner evidence, but model calls remain controlled by the existing Model Invocation Gate and planner CLI.

## v2.0 Alignment Review Gate

Before v2.0.0, Konoha must pause for an alignment conversation to verify that the project still matches the original intent, autonomy level, safety boundaries, local-first principles, and human-in-the-loop model.
