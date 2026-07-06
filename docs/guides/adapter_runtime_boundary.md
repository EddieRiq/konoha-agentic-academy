# Adapter Runtime Boundary

Status: public baseline.

Konoha may define adapters before it implements any executable runtime. This document defines the boundary between declarative adapter design and real execution.

## Purpose

The Adapter Runtime Boundary prevents a future adapter from gaining authority merely because it has technical capability.

An adapter runtime may only execute work when all required doctrine, permissions, invocation contracts, execution gates, evidence requirements, and user approvals are satisfied.

## Current state

Konoha currently supports public adapter doctrine and templates.

It does not currently provide:

- executable adapter runtime;
- autonomous shell execution;
- autonomous Git operations;
- autonomous release publishing;
- autonomous private-context access;
- background agents;
- production CI runners;
- model-routing implementation;
- tool-calling runtime.

Any claim that the current repository can execute adapters must be treated as false unless an explicit runtime implementation is added, reviewed, and approved.

## Boundary rule

A runtime implementation is not allowed to infer permission from:

- adapter profiles;
- capability declarations;
- model confidence;
- dry-run results;
- local filesystem access;
- user-uploaded context;
- previous successful missions;
- available credentials;
- available command-line tools.

Permission must come from an approved Mission Charter, applicable adapter permission matrix, execution gate, and explicit user approval.

## Minimum runtime prerequisites

Before executable runtime implementation is allowed, Konoha must have:

- adapter contract baseline;
- adapter permission matrix;
- adapter profile permissions;
- adapter invocation contract;
- adapter execution gate;
- adapter evidence pack;
- adapter dry-run protocol;
- runtime boundary documentation;
- runtime readiness review;
- safety review;
- Git and release safety review;
- private-context boundary review;
- rollback and recovery plan;
- logging and evidence policy;
- user approval for the specific runtime scope.

## Runtime classes

### Class 0: Declarative only

The adapter is documented but cannot run commands, edit files, call tools, access private context, commit, push, or release.

This is the default state.

### Class 1: Dry-run only

The adapter may simulate work, produce plans, list proposed commands, describe diffs, and identify risks.

It must not mutate files or execute commands.

### Class 2: Patch proposal

The adapter may produce patch text or suggested edits.

It must not apply changes unless a separate execution gate approves mutation.

### Class 3: Controlled local execution

The adapter may execute explicitly approved local commands within a narrow scope.

This requires an approved execution gate, evidence pack, rollback notes, and user approval.

### Class 4: Git operation execution

The adapter may run approved Git operations such as add, commit, tag, or push.

This requires explicit Git scope, clean status checks, diff review, and user approval.

### Class 5: Release operation execution

The adapter may support release actions only when the release scope, tag, notes, branch, privacy scan, and publication target are explicitly approved.

This requires a release-specific Mission Charter and review.

### Class 6: Private-context execution

The adapter may access or process private Village content only when the Mission Charter explicitly grants that access.

Private-context execution must remain local unless explicit publication approval exists.

## Runtime implementation stop conditions

Stop before implementation or execution if:

- no Mission Charter exists;
- runtime scope is vague;
- command scope is vague;
- file paths are broad or ambiguous;
- private context could be exposed;
- Git status is unknown;
- rollback is unclear;
- evidence cannot be recorded safely;
- credentials or secrets may be exposed;
- execution would depend on inferred permission;
- the adapter profile lacks a permission matrix;
- the user has not explicitly approved execution.

## Required runtime evidence

Any runtime invocation must record:

- Mission Charter reference;
- adapter name and version;
- permission level;
- invocation request;
- dry-run result;
- execution gate decision;
- commands approved;
- paths in scope;
- files changed;
- Git status before and after;
- tests or validation performed;
- errors encountered;
- rollback notes;
- private-context check;
- final verdict.

## Public/private boundary

Runtime implementation must not weaken the public/private boundary.

Public runtime code and docs must not include:

- private Village content;
- local books or converted literature;
- local dependency locks;
- local virtual environments;
- credentials;
- local memory;
- project-specific private paths;
- copied user files.

## Implementation rule

Runtime code must be introduced incrementally.

The first executable runtime should start with the safest possible scope:

- read-only inspection;
- no private context;
- no shell execution;
- no Git mutation;
- explicit evidence output;
- dry-run-first behavior;
- manual approval before mutation.

## Review rule

A runtime implementation is not ready merely because it works.

It is ready only when it can be explained, reviewed, audited, tested, and stopped safely.
