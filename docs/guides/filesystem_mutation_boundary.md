# Filesystem Mutation Boundary

Status: planning baseline.

This guide defines the boundary for any future Konoha component that may create, modify, move, rename, or delete files.

Konoha does not currently include an executable filesystem mutation runtime.

## Purpose

Filesystem mutation is a high-impact capability. A future runtime must not treat file access as permission to mutate files.

This boundary exists to ensure that file changes remain explicit, scoped, reviewed, evidenced, and reversible.

## Core rule

A component may not mutate the filesystem unless all of the following are true:

- a Mission Charter explicitly authorizes the mutation;
- the requested paths are listed in scope;
- the operation type is listed in scope;
- the expected change is described before execution;
- a dry-run or preview is available when practical;
- an execution gate approves the action;
- evidence requirements are defined;
- rollback or recovery notes are documented.

Technical ability to write files is not authorization to write files.

## Mutation types

Filesystem mutation includes:

- creating files;
- editing files;
- appending to files;
- overwriting files;
- moving files;
- renaming files;
- deleting files;
- generating directories;
- changing permissions;
- changing line endings;
- changing encodings;
- replacing templates;
- writing logs, caches, outputs, reports, or artifacts.

## Default mode

The default mode is:

```text
read-only
```

A component may inspect allowed files and propose changes, but it must not modify files by default.

## Allowed mutation levels

### Read-only

The component may inspect approved files and report findings.

It may not write files.

### Propose-only

The component may describe proposed mutations.

It may not write files.

### Patch-prepared

The component may prepare a patch, diff, or instruction set for human review.

It may not apply the patch unless separately authorized.

### Mutation-authorized

The component may perform explicitly approved filesystem mutations within a bounded path and operation scope.

### Local-private mutation-authorized

The component may mutate files inside an explicitly approved local private workspace.

This still requires Mission Charter scope and must not publish private content.

### Destructive mutation-authorized

The component may delete or overwrite files only when a Mission Charter explicitly authorizes destructive actions and rollback/recovery is documented.

This mode should be rare.

## Required scope fields

A filesystem mutation request must specify:

- requester;
- mission ID;
- adapter or runtime component;
- target paths;
- operation types;
- files expected to be created;
- files expected to be modified;
- files expected to be deleted;
- private-context exposure risk;
- Git impact;
- dry-run evidence;
- approval status;
- rollback notes.

## Path rules

A filesystem mutation request must not use vague path scopes such as:

```text
the repo
all files
everything under this folder
wherever needed
```

Acceptable path scopes are explicit and bounded, for example:

```text
docs/guides/<file>.md
runtime/templates/<template>.md
scrolls/<scroll>.md
```

Directory-wide scopes require stronger justification and review.

## Private workspace rule

Mutation inside a local private workspace such as:

```text
alliance/<village>/
```

requires explicit local authorization.

A public mutation request must not expose private local paths, source content, credentials, client data, or internal project details.

## Git rule

Filesystem mutation and Git operations are separate authorities.

Permission to modify files does not imply permission to:

- stage files;
- commit files;
- push files;
- create tags;
- create releases;
- clean untracked files.

Git operations require separate authorization and evidence.

## Destructive action rule

Deletion, overwrite, permission changes, and bulk replacement are destructive or potentially destructive.

They require:

- explicit destructive-action approval;
- exact path list;
- reason;
- expected impact;
- rollback or recovery note;
- evidence before and after mutation.

## Dry-run requirement

Before mutation, the component should provide one of:

- proposed file list;
- diff preview;
- generated artifact preview;
- command preview;
- no-op dry-run;
- manual execution plan.

When dry-run is impossible, the reason must be documented.

## Evidence requirements

Before mutation:

- Mission Charter reference;
- approved scope;
- current Git status when applicable;
- path list;
- expected operations;
- risk notes.

After mutation:

- changed file list;
- summary of changes;
- validation output;
- Git status when applicable;
- rollback status;
- unresolved issues.

## Stop conditions

Stop before mutation if:

- the Mission Charter is missing;
- the path scope is vague;
- the operation type is not explicit;
- destructive action is implied but not approved;
- private context may be exposed;
- Git operation is being bundled into mutation without approval;
- dry-run evidence is missing without justification;
- rollback expectations are unclear;
- the user cannot explain what will change and why.

## Non-goals

This document does not implement:

- filesystem write runtime;
- command runner;
- adapter runtime;
- automatic patch application;
- autonomous cleanup;
- autonomous Git operations;
- release automation.

## Relationship to other documents

Filesystem mutation must respect:

- Konoha laws;
- Mission Charter;
- approval policy;
- adapter invocation contract;
- adapter execution gate;
- adapter evidence pack;
- command runner boundary;
- eval runner boundary;
- public/private boundary.

## Release status

This is a planning boundary.

It defines requirements before implementation, not executable behavior.
