# Example: Adapter Contract Review Dry-run Package

Status: synthetic example.

## Runtime Package Manifest

Package ID: `example-adapter-review-001`

Package type: dry-run runtime package.

Mission type: adapter documentation review.

Risk level: medium.

Execution status: not authorized.

Private context required: no.

Adapters invoked: none.

Filesystem mutation performed: no.

Git operation performed: no.

## Mission Intake

### Mission Charter summary

Plan a review of a public adapter contract to check whether capability claims, permission boundaries, and evidence requirements are coherent.

### User objective

Detect inconsistencies before adapter behavior is implemented.

### Allowed scope

- inspect public adapter manifest and permission matrix;
- compare claims against adapter contract guide;
- identify missing evidence requirements;
- produce review findings.

### Disallowed scope

- invoking the adapter;
- changing adapter permissions;
- approving execution;
- adding credentials;
- accessing private context.

## Dry-Run Execution Plan

### Step 1: Scope the adapter contract

Planned action: identify the manifest, capabilities, permission matrix, and invocation boundary that would be reviewed.

Execution: dry-run only.

Expected evidence:

- file list;
- declared adapter role;
- declared capability boundaries.

### Step 2: Compare permissions and capabilities

Planned action: check whether claimed capabilities are supported by the permission matrix.

Execution: dry-run only.

Expected evidence:

- capability-to-permission mapping;
- mismatches;
- missing stop conditions.

### Step 3: Review evidence requirements

Planned action: verify whether pre-execution and post-execution evidence expectations are explicit.

Execution: dry-run only.

Expected evidence:

- evidence checklist;
- missing records;
- required reviewer decision.

## Adapter Invocation Stub

Adapter target: synthetic adapter profile.

Invocation mode: none.

Reason: this package reviews documentation only.

Required before any future invocation:

- explicit Mission Charter;
- adapter execution gate;
- evidence pack;
- user approval.

## Evidence Collection Stub

Expected evidence before future execution:

- adapter manifest path;
- permission matrix path;
- invocation contract path;
- execution gate path;
- evidence pack path;
- reviewer notes.

Evidence not collected in this dry-run example:

- real adapter output;
- runtime logs;
- command output.

## Runtime State

Current state: `validation_pending`.

Blocked: no.

Ready for review: yes, with conditions.

Execution authorized: no.

## Runtime Validation Report

Outcome: `conditional_revision_required`.

Required revisions:

- document which capabilities are allowed only in dry-run;
- clarify that capability does not imply authorization;
- add missing escalation trigger for ambiguous adapter scope.

## Runtime Trace Log

| Event ID | Phase | Event | Result |
| --- | --- | --- | --- |
| `trace-001` | intake | Adapter review mission represented as dry-run package | accepted |
| `trace-002` | planning | Contract review steps identified | accepted |
| `trace-003` | validation | Missing escalation trigger found | conditional_revision_required |
| `trace-004` | closure | Package closed with required revisions | closed_without_execution |

## Runtime Package Index

| Artifact | Status |
| --- | --- |
| Mission Intake | present |
| Dry-Run Execution Plan | present |
| Adapter Invocation Stub | present |
| Evidence Collection Stub | present |
| Runtime State | present |
| Validation Report | present |
| Trace Log | present |
| Package Closure | present |

## Runtime Package Closure

Closure status: closed without execution.

Reviewer action required: revise and re-review.

User approval required before execution: yes.

## Teachback Notes

This example demonstrates that adapter capability, adapter invocation, and adapter authorization are separate concepts.

A model or adapter may be technically capable while still being blocked by governance.
