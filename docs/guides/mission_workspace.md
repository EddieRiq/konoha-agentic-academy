# Mission Workspace

The Mission Workspace defines the file-system structure for real Konoha missions.

It is the bridge between the v1.1 product bootstrap and later approval consoles, model-provider contracts, planning loops, and UI work.

## Purpose

A Mission Workspace gives each mission a stable local home:

```text
missions/
  <mission_id>/
    charter.md
    mission_manifest.json
    README.md
    inputs/
    context/
    plans/
    outputs/
    reports/
    approvals/
      approval_log.md
    evidence/
```

The workspace is evidence and organization. It is not authority.

## Commands

Create a workspace:

```powershell
python .\tools\mission_workspace\manage_mission_workspace.py create `
  --workspace-root ".\sandbox\workspace" `
  --mission-id "example-mission" `
  --title "Example mission" `
  --scope "Create a safe local mission workspace." `
  --force
```

Validate:

```powershell
python .\tools\mission_workspace\manage_mission_workspace.py validate `
  --workspace-root ".\sandbox\workspace" `
  --mission-id "example-mission"
```

Inspect:

```powershell
python .\tools\mission_workspace\manage_mission_workspace.py inspect `
  --workspace-root ".\sandbox\workspace" `
  --mission-id "example-mission" `
  --json
```

List:

```powershell
python .\tools\mission_workspace\manage_mission_workspace.py list `
  --workspace-root ".\sandbox\workspace"
```

## Safety boundary

The Mission Workspace tool may:

- create directories under an explicit workspace root;
- create a Mission Charter draft;
- create a mission manifest;
- create approval and report files inside the mission workspace;
- validate required workspace structure;
- inspect public mission metadata;
- list mission workspaces under the explicit workspace root.

The Mission Workspace tool may not:

- execute mission actions;
- invoke real adapters;
- call model providers;
- use network access;
- access private Village context;
- apply files to the repository;
- stage files;
- create commits;
- push changes;
- clean or reset files;
- authorize runtime actions.

## Mission ID policy

Mission IDs must be explicit and path-safe.

Allowed:

```text
example-mission
risk_review_001
mission.v1
```

Blocked:

```text
../escape
nested/path
..\escape
```

## Relationship to v1.1

v1.1 introduced product bootstrap commands. v1.2 formalizes the mission workspace as a stable contract that later layers can consume.

## Relationship to UI work

No UI implementation is included here.

UI remains gated. Before creating any UI files, Konoha must present a draft with screens, stack, permissions, approval boundaries, and file plan for explicit human approval.
