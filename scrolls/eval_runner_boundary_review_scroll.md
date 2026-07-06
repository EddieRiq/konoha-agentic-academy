# Eval Runner Boundary Review Scroll

Status: public Scroll.

Use this Scroll to review any proposal that introduces, changes, or expands an executable eval runner.

## Purpose

This Scroll protects Konoha from accidentally turning eval documentation into uncontrolled execution.

The review checks whether a runner proposal respects:

- Mission Charter requirements;
- public/private boundaries;
- adapter boundaries;
- Git boundaries;
- evidence requirements;
- fail-closed behavior;
- human approval.

## Inputs

Required inputs:

- runner proposal;
- Mission Charter;
- eval runner readiness template;
- affected eval cases;
- expected output format;
- allowed paths;
- blocked paths;
- execution mode;
- evidence plan.

Optional inputs:

- adapter invocation contract;
- execution gate;
- dry-run result;
- prior eval run reports;
- security review notes.

## Review steps

### 1. Classify runner phase

Classify the proposal:

- Phase 0: manual only;
- Phase 1: dry-run parser;
- Phase 2: local non-mutating runner;
- Phase 3: adapter-backed evals;
- Phase 4: release-gated evals.

If the phase is unclear, stop.

### 2. Check Mission Charter authorization

Confirm the Mission Charter explicitly allows:

- runner design;
- runner implementation;
- runner execution;
- input paths;
- output paths;
- adapter usage, if any;
- file mutation, if any.

If not explicit, stop.

### 3. Check mutation boundary

Identify whether the runner may:

- create files;
- edit files;
- delete files;
- stage changes;
- commit;
- push;
- create tags;
- publish releases.

Any mutation requires explicit approval.

Git operations require separate explicit approval.

### 4. Check private context boundary

Confirm the runner does not access private context by default.

Blocked unless explicitly approved:

- local Villages;
- private libraries;
- private memory;
- local virtual environments;
- local model outputs;
- secrets;
- credentials;
- `.env` files.

If private context is involved, the runner must remain local and ignored unless a public-safe design is approved.

### 5. Check adapter boundary

If the runner invokes adapters, verify compliance with:

- Adapter Contracts;
- Adapter Permission Matrix;
- Adapter Invocation Contract;
- Adapter Execution Gate;
- Adapter Evidence Pack;
- Adapter Dry-Run Protocol;
- Adapter Runtime Boundary.

If adapter invocation bypasses any required contract, block.

### 6. Check evidence requirements

The proposal must define:

- pre-run evidence;
- post-run evidence;
- inputs used;
- observed behavior;
- verdict logic;
- stop conditions;
- reviewer notes.

If evidence is missing or not reproducible, block or defer.

### 7. Check failure behavior

The runner must fail closed when:

- inputs are missing;
- scope is unclear;
- expected behavior is undefined;
- private context risk exists;
- output path is unsafe;
- evidence cannot be recorded;
- adapter authorization is unclear.

If the runner fails open, reject.

### 8. Check output safety

Runner outputs must not include:

- secrets;
- credentials;
- personal data;
- private source text;
- private literature excerpts;
- unapproved memory;
- local-only context.

Outputs should include concise references and evidence summaries.

## Verdicts

### Approved for manual use

The proposal supports manual review only.

No executable runner is approved.

### Approved for dry-run parser prototype

The proposal may validate eval file structure without executing prompts, commands, adapters, or mutations.

### Approved for local non-mutating prototype

The proposal may run approved evals without mutation and without private context unless explicitly authorized.

### Needs changes

The proposal is promising but missing required boundaries, evidence, or stop conditions.

### Blocked

The proposal would violate safety, privacy, adapter, Git, or Mission Charter boundaries.

### Rejected

The proposal is incompatible with Konoha doctrine.

## Required output

The review must produce:

- runner phase;
- approved scope;
- blocked scope;
- evidence requirements;
- stop conditions;
- verdict;
- reviewer notes;
- approval status.

## Stop conditions

Stop the review if:

- there is no Mission Charter;
- the runner can mutate files without approval;
- private context access is ambiguous;
- adapter invocation is uncontrolled;
- Git operations are possible without approval;
- evidence cannot be recorded safely;
- the user cannot explain what the runner will do.

## Completion

This Scroll is complete only when the reviewer can state:

- what the runner may do;
- what it may not do;
- what evidence it must produce;
- what stops it;
- whether implementation is approved, blocked, or deferred.
