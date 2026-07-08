# Human-in-the-loop Agent Runtime

The Human-in-the-loop Agent Runtime coordinates already-gated Konoha capabilities into a mission-level loop.

It connects:

```text
Mission Workspace
→ Mission Workspace validation
→ Hokage Planner Loop
→ Real Model Invocation Gate
→ Hokage Plan Proposal
→ Controlled Tool Execution Gate
→ mission-local reports
→ sandbox reports
→ human review
```

## Core rule

```text
Model output is evidence only.
Model inference is never permission.
Controlled tool output is evidence only.
A plan proposal is not permission to execute.
Agent runtime output is not permission to apply, stage, commit, push, access private context, or close a mission.
```

## What the runtime may do

The runtime may:

- validate an existing Mission Workspace;
- run the Hokage Planner Loop in preview mode;
- run the Hokage Planner Loop in confirmed mode through the Real Model Invocation Gate;
- preview a controlled tool execution plan;
- execute a fixed allowlisted internal tool through the Controlled Tool Execution Gate;
- write agent runtime reports under mission reports;
- write agent runtime reports under sandbox reports;
- preserve delegated gate approval requirements.

## What the runtime may not do

The runtime may not:

- execute arbitrary shell commands;
- accept arbitrary executable paths;
- bypass approval tokens;
- bypass provider, network, budget, or private-context gates;
- bypass controlled tool execution allowlists;
- invoke adapters;
- access private Village context;
- apply repository changes;
- stage files;
- create commits;
- push changes;
- clean or reset files;
- run background autonomous agents;
- close missions automatically.

## Approval tokens

The runtime preserves delegated approval gates.

Planning confirmation requires:

```text
INVOKE_REAL_MODEL
```

Controlled tool execution requires:

```text
EXECUTE_CONTROLLED_TOOL
```

The runtime does not store tokens. Tokens must be entered for each confirmed run.

## Preview first

By default the runtime runs in preview mode.

Preview mode is the safe default because it produces evidence without invoking confirmed planning or confirmed tool execution.

## Confirmed mode

Confirmed mode is possible only when the user explicitly provides the relevant confirmation flags and exact approval tokens.

Confirmed mode still does not grant permission to apply, stage, commit, push, access private context, or close a mission.

## Relationship to UI

The Local Web UI Alpha may display runtime reports and prepare future runtime requests.

The UI must not add new authority. Any UI-triggered runtime action must still pass this runtime and its delegated gates.

## v2.0 Alignment Review Gate

Before v2.0.0, Konoha must pause for a formal alignment conversation.

That review must verify that Konoha still matches the original intent, local-first design, human-in-the-loop control, model-output non-authority, UI boundaries, controlled execution boundaries, and safety doctrine.
