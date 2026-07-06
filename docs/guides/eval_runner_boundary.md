# Eval Runner Boundary

Status: public guidance.

This document defines the boundary between Konoha's current documentation-first evaluation baseline and any future executable eval runner.

Konoha may define eval cases, result templates, review Scrolls, and expected behavior before it has an automated runner.

An eval case is not a runner.

A result template is not execution.

A future runner must not be implemented or treated as available until the runtime boundary, privacy boundary, evidence requirements, and approval gates are explicitly satisfied.

## Purpose

The Eval Runner Boundary prevents evaluation infrastructure from becoming an uncontrolled execution path.

A runner could eventually read files, execute prompts, call adapters, compare outputs, write reports, or interact with local context.

Those actions require explicit limits before implementation.

## Current release boundary

The current evaluation layer is declarative and manual.

Allowed now:

- define eval case templates;
- define behavior, safety, and adapter eval cases;
- define expected pass, fail, and blocked behavior;
- record manual eval results;
- review eval results;
- propose improvements.

Not available now:

- executable eval runner;
- automatic adapter invocation;
- automatic file mutation;
- automatic command execution;
- automatic scoring that overrides human review;
- automatic promotion of results into doctrine;
- automatic access to local Villages or private context.

## Core rule

A future eval runner may test behavior, but it may not become an authorization system.

Passing an eval does not grant permission to execute.

Failing an eval does not justify bypassing the Mission Charter.

Eval results are evidence, not authority.

## Minimum readiness requirements

Before implementing any eval runner, the proposal must define:

- runner scope;
- supported eval case format;
- allowed input paths;
- blocked input paths;
- output paths;
- mutation policy;
- adapter invocation policy;
- dry-run behavior;
- evidence requirements;
- privacy controls;
- logging boundaries;
- failure behavior;
- rollback or cleanup behavior;
- review owner;
- approval owner.

## Required boundaries

### Mission Charter boundary

The runner must operate only inside an approved Mission Charter.

The Mission Charter must state:

- why the runner is needed;
- which eval cases may run;
- which files may be read;
- whether any files may be written;
- whether adapters may be invoked;
- what output is expected;
- what stop conditions apply.

If the Mission Charter does not explicitly allow runner execution, the runner must not run.

### Non-mutating default

The default runner mode must be non-mutating.

Default allowed behavior:

- read approved public eval files;
- produce a proposed result;
- write only to an explicitly approved output path if allowed.

Default blocked behavior:

- modifying doctrine;
- modifying source files;
- staging Git changes;
- committing;
- pushing;
- deleting files;
- reading ignored local Villages;
- reading private libraries;
- invoking adapters with execution permissions.

### Private context boundary

A runner must not access private context by default.

Blocked unless explicitly approved:

- `alliance/<village>/`;
- private memory;
- private libraries;
- local virtual environments;
- local dependency locks;
- local model outputs;
- private assets;
- secrets;
- credentials;
- `.env` files.

If private context is required for a local eval, that eval must remain local and ignored by Git.

### Adapter boundary

An eval runner must not invoke adapters as a shortcut around adapter contracts.

Any adapter-backed eval must comply with:

- Adapter Contracts;
- Adapter Permission Matrix;
- Adapter Invocation Contract;
- Adapter Execution Gate;
- Adapter Evidence Pack;
- Adapter Dry-Run Protocol;
- Adapter Runtime Boundary.

### Git boundary

A runner must not perform Git operations by default.

Blocked unless separately approved:

- `git add`;
- `git commit`;
- `git push`;
- tag creation;
- release creation;
- branch deletion;
- history rewriting.

A runner may report Git status only if explicitly allowed.

### Output boundary

Runner outputs must not include:

- secrets;
- credentials;
- private source content;
- private literature excerpts;
- personal data;
- unapproved local memory;
- copyrighted source text beyond safe short references.

Outputs should include:

- eval case id;
- runner mode;
- input references;
- expected behavior;
- observed behavior;
- verdict;
- evidence summary;
- stop conditions triggered;
- reviewer notes.

## Failure behavior

A future runner must fail closed.

It must stop when:

- the Mission Charter is missing;
- input paths are ambiguous;
- private context might be exposed;
- adapter permissions are unclear;
- expected behavior is undefined;
- output path is not approved;
- evidence cannot be recorded safely;
- the runner would need mutation not explicitly authorized.

## Acceptable future phases

### Phase 0: manual only

Current state.

Human reviews eval cases and records results with templates.

### Phase 1: dry-run parser

A script may validate eval case structure without executing prompts or adapters.

Allowed:

- schema checks;
- missing-field detection;
- static consistency checks;
- non-sensitive report generation.

### Phase 2: local non-mutating runner

A runner may execute approved public eval cases in non-mutating mode.

Still blocked:

- private context access;
- adapter execution;
- Git operations;
- doctrine mutation.

### Phase 3: adapter-backed evals

A runner may invoke adapters only through approved invocation contracts, dry-run protocol, execution gates, and evidence packs.

### Phase 4: release-gated evals

Eval results may become part of release readiness only after review, but may not automatically approve a release.

## Required review

Any proposal for a runner must pass Eval Runner Boundary review before implementation.

The review must answer:

- Does this runner execute anything?
- Does it mutate files?
- Does it read private context?
- Does it invoke adapters?
- Does it write outputs?
- Does it interact with Git?
- Does it fail closed?
- Does it preserve the public/private boundary?
- Does it produce reviewable evidence?

## Stop conditions

Stop and ask for approval if:

- runner scope is unclear;
- a path points to a local Village;
- a path is ignored by Git;
- a file may contain private context;
- output could include sensitive content;
- an adapter would be invoked;
- a command would run;
- Git state would change;
- eval results would be promoted to doctrine;
- the user cannot explain what the runner will do.

## Completion criteria

An Eval Runner Boundary review is complete only when:

- runner mode is identified;
- allowed and blocked actions are explicit;
- evidence requirements are defined;
- private context is protected;
- Git boundaries are protected;
- adapter boundaries are protected;
- stop conditions are documented;
- implementation is either approved, rejected, or deferred.
