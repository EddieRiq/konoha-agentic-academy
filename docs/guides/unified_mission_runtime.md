# Unified Mission Runtime

v2.6.0 introduces the Unified Mission Runtime.

The purpose is to stop operating Konoha as a collection of many isolated commands.
The runtime prepares one mission-level work surface with a charter, manifest, plan,
command proposals, notification state, evidence, reports, and optional memory note.

## Core rule

```text
Command proposals are not permission.
A runtime report is evidence only.
No command executes in v2.6.
```

## What v2.6 does

The runtime may:

- create a Mission Workspace under an explicit workspace root;
- write a mission charter;
- write a mission manifest;
- write a unified mission runtime plan;
- write command proposals;
- write notification state;
- write an evidence note;
- write a runtime report;
- optionally write a Yamanaka memory note with explicit approval.

## What v2.6 does not do

The runtime may not:

- execute arbitrary commands;
- invoke model providers;
- invoke adapters;
- access private context by default;
- use network access;
- apply files to the repository;
- stage files;
- create commits;
- push changes;
- run background agents;
- close missions.

## Approval tokens

Starting a confirmed runtime requires:

```text
START_UNIFIED_MISSION
```

Optional memory note recording requires:

```text
RECORD_YAMANAKA_MEMORY
```

These tokens authorize only the specific evidence-writing operation. They do not
authorize command execution or repository changes.

## Command proposal model

The runtime turns a task description into a set of proposed commands. Each command is:

- explicit;
- labeled with purpose;
- labeled with risk;
- marked as `proposed_only`;
- blocked until future explicit command or batch approval.

This release intentionally does not execute the command proposals. Execution belongs
to later gates.

## Why this matters

v2.6 is the first step toward a functional beta. It gives Konoha a single mission
runtime surface that later releases can extend with model routing, token economy,
general task execution, self-review, and Git operation gates.

## Expected v3.0 behavior

v3.0 should use this runtime as the main mission spine:

```text
mission intake
→ model/router decision
→ plan
→ command proposals
→ approved execution
→ evidence capture
→ verification
→ token/cost review
→ learning proposals
→ Git gate if approved
→ teachback and closure
```
