# Adapter Dry-Run Protocol

Status: public baseline.

This guide defines how Konoha adapters simulate a requested action before any real execution is allowed.

Dry-run is not execution. Dry-run is a safety and planning layer used to expose intended scope, commands, file changes, assumptions, risks, rollback notes, and required approvals.

## Purpose

The Adapter Dry-Run Protocol exists to prevent uncontrolled execution.

It helps reviewers answer:

- What would the adapter do?
- Which files, commands, tools, or paths would be touched?
- What evidence supports the action?
- What could go wrong?
- What approval is required before execution?
- What rollback or recovery path exists?

## Core rule

An adapter must not treat a dry-run approval as execution approval.

A dry-run result may support a later execution request, but it does not authorize execution by itself.

## Required inputs

A dry-run request must define:

- mission identifier;
- adapter name;
- requested mode;
- allowed repository scope;
- allowed local/private scope, if any;
- expected outputs;
- proposed commands, if commands are relevant;
- files expected to be read;
- files expected to be changed;
- privacy constraints;
- stop conditions;
- reviewer or approver.

If any of these are unclear, the dry-run must stop before proposing execution.

## Dry-run modes

### Read-only dry-run

The adapter may inspect explicitly allowed files and produce analysis.

It must not create, modify, delete, move, stage, commit, push, install dependencies, run commands with side effects, or access private context unless explicitly allowed.

### Patch-planning dry-run

The adapter may propose file changes as text, patch notes, or diff-like plans.

It must not apply the patch.

### Command-planning dry-run

The adapter may list proposed commands and explain expected effects.

It must not execute the commands.

### Release-planning dry-run

The adapter may plan tagging, release notes, changelog checks, and publication readiness.

It must not create tags, push tags, publish releases, or modify release state.

### Local-private dry-run

The adapter may work with local/private context only if the Mission Charter explicitly allows it.

Private context remains local. The adapter must not copy private content into public outputs.

## Required dry-run output

A dry-run result must include:

- summary of proposed action;
- files to read;
- files to create;
- files to modify;
- files to delete;
- commands to run;
- expected Git status before and after;
- private-context exposure assessment;
- dependency changes;
- evidence required before execution;
- rollback or recovery notes;
- explicit approval requirement;
- stop conditions;
- final verdict.

## Prohibited dry-run behavior

During dry-run, adapters must not:

- execute commands with side effects;
- modify files;
- stage or commit changes;
- push to remotes;
- create tags;
- publish releases;
- install dependencies;
- alter local environments;
- access ignored local villages unless explicitly allowed;
- copy private or copyrighted source content into public files;
- convert analysis into doctrine without approval.

## Evidence requirements

A dry-run should reference evidence, not guess.

Useful evidence includes:

- Mission Charter;
- adapter manifest;
- adapter permission matrix;
- invocation request;
- execution gate draft;
- repository status;
- file list;
- relevant guide or Scroll;
- safety checklist;
- previous dry-run result.

## Approval boundary

A valid dry-run result may recommend execution, but only the user or an explicitly authorized reviewer may approve execution.

The approval must be specific:

- adapter;
- mission;
- command or action;
- files or paths;
- permission level;
- time window;
- expected output.

Generic approval is not sufficient for sensitive execution.

## Stop conditions

Stop the dry-run if:

- the requested action is unclear;
- the adapter permission level is missing;
- the requested scope is broader than the Mission Charter;
- private context is involved but not explicitly allowed;
- commands have unknown side effects;
- rollback is unclear for a risky action;
- Git status is dirty and not explained;
- a requested step would publish private content;
- the result would weaken Konoha doctrine or safety rules.

## Relationship to execution gate

The dry-run result is an input to the Adapter Execution Gate.

The execution gate decides whether a proposed action may move from planning to execution.

A dry-run result must not bypass the execution gate.

## Relationship to evidence pack

Dry-run evidence should be included in the Adapter Evidence Pack.

The evidence pack should preserve:

- the dry-run request;
- the dry-run result;
- reviewer notes;
- approval decision;
- execution gate decision;
- post-execution evidence, if execution later occurs.

## Completion criteria

A dry-run is complete only when:

- proposed scope is explicit;
- side effects are clearly identified;
- sensitive context risk is reviewed;
- required approval is stated;
- stop conditions are documented;
- reviewer can decide whether to block, revise, or escalate.
