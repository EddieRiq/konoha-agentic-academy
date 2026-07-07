# Example: Documentation Update Dry-run Package

Status: synthetic example.

## Runtime Package Manifest

Package ID: `example-docs-update-001`

Package type: dry-run runtime package.

Mission type: public documentation update.

Risk level: low.

Execution status: not authorized.

Private context required: no.

Adapters invoked: none.

Filesystem mutation performed: no.

Git operation performed: no.

## Mission Intake

### Mission Charter summary

Plan a small documentation update that adds a short safety note to a public guide.

### User objective

Improve clarity for readers without changing doctrine, permissions, runtime behavior, or public/private boundaries.

### Allowed scope

- inspect existing public documentation structure;
- propose a documentation-only update;
- identify files that would be affected;
- describe expected validation.

### Disallowed scope

- modifying files;
- committing changes;
- changing doctrine;
- adding runtime code;
- accessing private Village context.

## Dry-Run Execution Plan

### Step 1: Identify target documentation

Planned action: review public guide index and select the correct target guide.

Execution: dry-run only.

Expected evidence:

- target file path;
- reason for choosing the file;
- confirmation that the change is documentation-only.

### Step 2: Draft proposed note

Planned action: draft a short public-safe note.

Execution: dry-run only.

Expected evidence:

- proposed text;
- scope explanation;
- no new authorization implied.

### Step 3: Validate boundary

Planned action: verify that the note does not imply autonomous execution or private context access.

Execution: dry-run only.

Expected evidence:

- boundary checklist;
- reviewer decision.

## Adapter Invocation Stub

No adapter invocation is planned.

Reason: the mission can be planned without external adapter execution.

## Evidence Collection Stub

Evidence to collect before any future execution:

- public file path;
- proposed diff;
- safety boundary review;
- user approval for actual mutation.

Evidence not collected in this dry-run example:

- real diff;
- Git status;
- commit hash.

## Runtime State

Current state: `planned`.

Blocked: no.

Ready for review: yes.

Execution authorized: no.

## Runtime Validation Report

Outcome: `valid_for_review`.

Rationale:

- scope is narrow;
- no private context is needed;
- no commands or file mutations are performed;
- expected evidence is clear;
- execution remains unauthorized.

## Runtime Trace Log

| Event ID | Phase | Event | Result |
| --- | --- | --- | --- |
| `trace-001` | intake | Mission converted to dry-run package | accepted |
| `trace-002` | planning | Documentation-only steps identified | accepted |
| `trace-003` | validation | Boundary check completed | valid_for_review |
| `trace-004` | closure | Package closed as dry-run example | closed_without_execution |

## Runtime Package Index

| Artifact | Status |
| --- | --- |
| Mission Intake | present |
| Dry-Run Execution Plan | present |
| Adapter Invocation Stub | not applicable |
| Evidence Collection Stub | present |
| Runtime State | present |
| Validation Report | present |
| Trace Log | present |
| Package Closure | present |

## Runtime Package Closure

Closure status: closed without execution.

Reviewer action required: optional review.

User approval required before execution: yes.

## Teachback Notes

This example demonstrates that even a low-risk documentation update should separate planning from action.

A valid dry-run package can be review-ready without being execution-ready.
