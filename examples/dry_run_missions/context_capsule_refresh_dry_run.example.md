# Example: Context Capsule Refresh Dry-run Package

Status: synthetic example.

## Runtime Package Manifest

Package ID: `example-capsule-refresh-001`

Package type: dry-run runtime package.

Mission type: context capsule refresh.

Risk level: medium.

Execution status: not authorized.

Private context required: no.

Adapters invoked: none.

Filesystem mutation performed: no.

Git operation performed: no.

## Mission Intake

### Mission Charter summary

Plan a context capsule refresh when a source hash mismatch indicates the capsule may be stale.

### User objective

Prevent stale summarized context from being treated as current doctrine.

### Allowed scope

- compare recorded source hashes against current source hashes conceptually;
- mark capsule as stale in the dry-run package;
- require full-source review before reuse;
- propose refresh evidence.

### Disallowed scope

- reading private sources;
- publishing private context;
- rewriting doctrine from a capsule alone;
- approving capsule use without source review.

## Dry-Run Execution Plan

### Step 1: Detect stale capsule condition

Planned action: compare stored hash and current hash.

Execution: dry-run only.

Expected evidence:

- capsule identifier;
- recorded source hash;
- current source hash;
- mismatch status.

Synthetic result:

```text
recorded_source_hash = sha256:example-old
current_source_hash = sha256:example-new
status = mismatch_detected
```

### Step 2: Block capsule-first use

Planned action: mark the capsule as stale and require full-source review.

Execution: dry-run only.

Expected evidence:

- stale status;
- reviewer note;
- full-source fallback requirement.

### Step 3: Plan refresh

Planned action: define evidence needed for a reviewed capsule refresh.

Execution: dry-run only.

Expected evidence:

- source list;
- refreshed summary;
- reviewer approval;
- new manifest;
- supersession note.

## Adapter Invocation Stub

No adapter invocation is planned.

Reason: the mission concerns context governance, not adapter execution.

## Evidence Collection Stub

Evidence required before future capsule approval:

- source file list;
- source hashes;
- refresh rationale;
- summary diff;
- reviewer approval;
- stale capsule supersession record.

Evidence not collected in this dry-run example:

- actual source text;
- private documents;
- local paths;
- real hash values.

## Runtime State

Current state: `blocked`.

Blocked: yes.

Blocker:

```text
Capsule hash mismatch. Full-source review required before capsule-first use.
```

Execution authorized: no.

## Runtime Validation Report

Outcome: `blocked`.

Rationale:

- stale capsule condition detected;
- capsule cannot replace source doctrine;
- full-source review is required;
- no private context may be loaded automatically.

## Runtime Trace Log

| Event ID | Phase | Event | Result |
| --- | --- | --- | --- |
| `trace-001` | intake | Capsule refresh mission represented as dry-run package | accepted |
| `trace-002` | planning | Hash mismatch condition documented | accepted |
| `trace-003` | validation | Capsule-first use blocked | blocked |
| `trace-004` | closure | Package closed with stale capsule blocker | closed_without_execution |

## Runtime Package Index

| Artifact | Status |
| --- | --- |
| Mission Intake | present |
| Dry-Run Execution Plan | present |
| Adapter Invocation Stub | not applicable |
| Evidence Collection Stub | present |
| Runtime State | blocked |
| Validation Report | blocked |
| Trace Log | present |
| Package Closure | present |

## Runtime Package Closure

Closure status: closed without execution.

Reviewer action required: full-source review and capsule refresh.

User approval required before source access: yes.

## Teachback Notes

This example demonstrates that summaries are not truth.

A stale context capsule can support triage, but it cannot authorize action or replace source review.
