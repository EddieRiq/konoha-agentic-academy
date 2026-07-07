# Rollback Boundary

Status: planning baseline.

This guide defines the safety boundary for any future runtime behavior that may require rollback.

Konoha does not currently implement rollback automation. This document defines what must be known, approved, and recorded before runtime work may perform changes that could require reversal.

## Purpose

Rollback planning exists to prevent irreversible or poorly understood changes.

A runtime action must not proceed merely because it is technically possible. It must have:

- explicit Mission Charter scope;
- known affected files or systems;
- expected mutation list;
- dry-run evidence when available;
- recovery path;
- user approval;
- post-action verification;
- clear stop conditions.

## Scope

This boundary applies to future work involving:

- file creation, editing, overwriting, movement, renaming, or deletion;
- command execution with side effects;
- Git operations;
- generated artifacts;
- dependency changes;
- runtime state changes;
- adapter-triggered changes;
- local private Village changes when explicitly authorized.

## Current boundary

Konoha currently allows rollback planning only.

Konoha does not currently include:

- automatic rollback execution;
- autonomous revert;
- autonomous Git reset;
- autonomous deletion recovery;
- automatic restore from backups;
- automatic release rollback;
- automatic runtime state repair.

## Required rollback plan

Before any future runtime action with side effects, a rollback plan must define:

- what may change;
- where the change may occur;
- what evidence exists before the change;
- how to detect success;
- how to detect failure;
- how to reverse or mitigate the change;
- which rollback commands or manual steps would be used;
- which actions are irreversible;
- who must approve rollback execution.

## Irreversible actions

If an action cannot be safely reversed, the request must say so explicitly.

Irreversible actions require stricter review and may be blocked even if the user requested them.

Examples include:

- deleting files without backup;
- rewriting Git history;
- force pushing;
- publishing releases;
- removing local memory or private sources;
- changing generated outputs without preserving prior state;
- modifying secrets, credentials, or deployment state.

## Evidence requirements

A rollback-ready action should include:

- pre-action `git status` when relevant;
- file list before mutation;
- planned diff or dry-run output;
- expected output paths;
- backup path or restore strategy;
- post-action verification command;
- failure signals;
- rollback owner or approver.

## Approval rule

Rollback planning does not authorize execution.

Execution requires explicit approval through the Mission Charter, adapter execution gate, command runner boundary, filesystem mutation boundary, Git operation boundary, or a future approved runtime policy.

## Stop conditions

Stop before action if:

- no rollback plan exists;
- affected files or systems are unclear;
- success criteria are unclear;
- irreversible action is requested without explicit acknowledgement;
- private context may be exposed;
- Git state is dirty and not accounted for;
- backup or restore strategy is missing for destructive changes;
- the Mission Charter does not authorize mutation;
- rollback would require commands outside approved scope.

## Review question

A safe runtime plan must answer:

> If this goes wrong, can the user understand what happened, what changed, and how to recover?

If not, the action remains blocked.
