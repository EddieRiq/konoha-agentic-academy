# First Runtime Skeleton

Status: documentation-first baseline.

## Purpose

The First Runtime Skeleton defines the minimum structure required for Konoha to turn a Mission Charter into a dry-run plan without executing commands, changing files, invoking Git operations, loading private context automatically, or selecting models autonomously.

This guide exists to make runtime behavior reviewable before any executable runtime is implemented.

## Core principle

The first runtime skeleton plans. It does not act.

A valid runtime skeleton may:

- receive a Mission Charter reference;
- normalize mission intake into a structured object;
- identify required context and evidence;
- propose dry-run steps;
- propose adapter calls as stubs;
- declare expected outputs;
- declare risks and stop conditions;
- produce a reviewable runtime state record.

It may not:

- execute shell commands;
- mutate the filesystem;
- run Git operations;
- access private Village content automatically;
- invoke external tools without explicit authorization;
- escalate model tier by itself;
- treat memory, context capsules, or summaries as authorization;
- mark a mission complete without review and Teachback.

## Required inputs

A First Runtime Skeleton run requires:

1. Mission Charter identifier or pasted Mission Charter content.
2. Mission objective.
3. Scope boundary.
4. Approved context sources.
5. Requested output type.
6. Risk level.
7. Model routing decision, if applicable.
8. Context budget, if applicable.
9. User approval for the dry-run planning step.

If any of these are missing, the runtime skeleton must produce a blocked intake record instead of a plan.

## Runtime phases

### 1. Intake

The runtime records what the user asked for and maps it to an approved Mission Charter.

The intake phase must distinguish:

- explicit user instruction;
- inferred objective;
- missing information;
- prohibited action;
- private or sensitive context request;
- required review.

Inference may support planning, but inference is not permission.

### 2. Context plan

The runtime declares what context is needed and why.

The context plan must identify:

- public repository files;
- templates;
- Scrolls;
- approved context capsules;
- private/local sources, if explicitly approved;
- sources that must not be loaded.

Context capsules may reduce repeated intake, but they do not replace source doctrine for high-risk decisions.

### 3. Dry-run execution plan

The runtime produces a proposed sequence of steps.

Each step must include:

- step identifier;
- proposed actor or role;
- action description;
- inputs;
- expected output;
- evidence required;
- stop conditions;
- permissions required before real execution.

The plan is descriptive until explicitly approved.

### 4. Adapter invocation stubs

The runtime may describe potential adapter calls.

A stub is not an invocation. It must not execute anything.

The stub must state:

- target adapter;
- intended purpose;
- requested mode;
- permissions required;
- expected evidence;
- rollback or non-mutation guarantee.

### 5. Evidence collection plan

The runtime declares what evidence would be collected if the plan were executed.

Evidence may include:

- diff summaries;
- validation commands;
- test output;
- file lists;
- review checklists;
- token usage report;
- capability review;
- user confirmation.

### 6. Runtime state

The runtime records the current state of the dry-run.

Allowed states:

- `draft_intake`;
- `blocked_intake`;
- `dry_run_plan_created`;
- `awaiting_review`;
- `changes_requested`;
- `approved_for_next_step`;
- `rejected`;
- `closed_without_execution`.

The state does not authorize execution by itself.

## Stop conditions

The runtime skeleton must stop when:

- no Mission Charter exists for scoped work;
- requested action is outside scope;
- private context is requested without explicit approval;
- a command, file mutation, or Git action would be required;
- model tier sufficiency is unclear;
- context budget is exceeded or undefined for a high-risk mission;
- required evidence cannot be produced;
- user approval is missing.

## Relationship to existing doctrine

The First Runtime Skeleton depends on:

- Mission Charter policy;
- adapter invocation contract;
- adapter execution gate;
- dry-run protocol;
- evidence pack;
- runtime planning baseline;
- command runner boundary;
- filesystem mutation boundary;
- Git operation boundary;
- rollback boundary;
- model routing and token governance;
- token budget enforcement;
- evaluation baseline.

It does not replace any of those documents.

## Review requirements

Before a runtime skeleton output can be used as the basis for implementation, it must be reviewed for:

- scope match;
- safety boundary compliance;
- no hidden execution;
- no private context leakage;
- no autonomous Git or command behavior;
- evidence completeness;
- token/context discipline;
- teachability to the user.

## Output requirement

A valid First Runtime Skeleton output must include:

1. Mission intake record.
2. Context plan.
3. Dry-run execution plan.
4. Adapter invocation stubs, if any.
5. Evidence collection plan.
6. Runtime state record.
7. Review decision.
8. Open questions or blocked items.

If the output cannot be reviewed by a human, it is not valid.
