# General Task Execution Workbench

v2.8.0 introduces the General Task Execution Workbench.

This release is intentionally general. It is not an Airflow-specific, Docker-specific, server-specific, or data-pipeline-specific implementation.

The goal is to prepare Konoha for supervised real technical tasks by creating a reusable mission workbench that can decompose tasks, propose command batches, define verification checklists, record evidence, and prepare for v3.0 beta execution.

## Core rule

```text
Command proposals are not permission.
Recorded command results are evidence only.
A workbench report does not authorize execution.
v2.8 does not execute arbitrary commands.
```

## What the workbench does

The workbench may:

- initialize a general task mission;
- create a mission charter;
- create a mission manifest;
- infer a general playbook;
- propose command batches;
- create verification checklists;
- create rollback notes;
- record supervised or external command results as evidence;
- review readiness for v3.0 supervised execution.

## What the workbench does not do

The workbench may not:

- execute arbitrary commands;
- invoke model providers;
- invoke adapters;
- use network access;
- access private context by default;
- apply repository changes;
- perform Git operations;
- run background agents;
- close missions.

## Why v2.8 is general

The beta task may involve Docker, Airflow, JARs, a server, a repo refactor, a data pipeline, documentation, or another technical task.

The workbench should not assume the task type. It should follow this behavior:

```text
inspect
plan
ask
propose commands
wait for human approval
record externally supervised execution
verify
summarize
learn
```

## Command batch model

Command batches are proposed as evidence. They include:

- command id;
- purpose;
- proposed command;
- risk;
- approval requirement;
- execution mode.

A proposed command is never permission to execute the command.

## Evidence capture

v2.8 supports command result recording after a human-supervised or external execution.

Each result captures:

- command id;
- command text;
- execution context;
- executor;
- exit code;
- stdout summary;
- stderr summary;
- observation.

The result remains evidence only.

## Relationship to v3.0

v2.8 prepares the workbench surface.

v3.0 should integrate actual supervised command execution with explicit approval, live evidence capture, token tracking, model routing, self-review, memory updates, and Git gates.
