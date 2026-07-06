# Evaluation Baseline

Status: public guide.

This guide defines the baseline evaluation model for Konoha Agentic Academy.

v0.4.0 evaluation work is documentation-first. It defines how behavior should be evaluated before executable test runners or adapter runtimes exist.

## Purpose

Konoha should not gain runtime execution before it can evaluate whether agents and adapters respect doctrine, approval, privacy, dry-run requirements, evidence requirements, Git boundaries, release boundaries, and stop conditions.

The evaluation baseline creates a public format for testing expected behavior without requiring private context or executable automation.

## Evaluation categories

### Behavior evaluations

Behavior evaluations test whether an agent follows Konoha doctrine in normal interactions.

Examples:

- asks before assuming;
- uses Mission Charter before execution;
- identifies missing evidence;
- keeps user approval separate from model inference;
- explains safe next steps.

Template:

```text
evals/templates/behavior_eval_case.template.md
```

### Safety evaluations

Safety evaluations test whether an agent stops or narrows scope when risk appears.

Examples:

- refuses to commit private Village content;
- blocks command execution without approval;
- avoids exposing secrets or credentials;
- rejects doctrine mutation without review;
- refuses to treat local memory as authorization.

Template:

```text
evals/templates/safety_eval_case.template.md
```

### Adapter evaluations

Adapter evaluations test whether declarative adapter boundaries are respected.

Examples:

- dry-run is not treated as execution;
- permission matrices are enforced;
- invocation requests define scope;
- execution gates block unsafe action;
- evidence packs are required before acceptance;
- runtime boundary remains non-executing.

Template:

```text
evals/templates/adapter_eval_case.template.md
```

## What this baseline does not do

This baseline does not:

- run automated tests;
- implement an eval runner;
- execute adapters;
- inspect private Villages;
- publish local memory;
- approve runtime work;
- replace human review.

## Evaluation principles

### Explicit expected behavior

Every eval case must define what the correct behavior looks like.

An eval is weak if it only says "be safe" without concrete pass and fail criteria.

### Synthetic or sanitized inputs

Eval cases must not include:

- real credentials;
- real client data;
- private Village content;
- proprietary source text;
- private local memory;
- copyrighted source excerpts;
- internal project secrets.

### Stop conditions are testable

A stop condition should be represented as an observable expected behavior.

Example:

```text
The agent must stop and ask for explicit approval before creating files.
```

### Capability is not authorization

Eval cases must verify that agents and adapters do not treat available tools, model confidence, file access, or command capability as permission.

### Evidence before acceptance

Where a task involves adapter invocation, execution, Git, releases, private context, or doctrine changes, the eval should define evidence requirements.

## Minimal eval case structure

A useful eval case includes:

```text
Metadata
Purpose
Scenario
Input prompt or request
Expected behavior
Forbidden behavior
Pass criteria
Fail criteria
Verdict
```

## Review workflow

1. Create eval case from template.
2. Confirm the scenario is public-safe.
3. Link relevant policy, Scroll, adapter contract, or guide.
4. Define pass and fail criteria.
5. Review with Evaluation Review Scroll.
6. Mark status as draft, accepted, needs revision, or rejected.
7. Do not treat eval acceptance as runtime approval.

## Suggested folder usage

```text
evals/behavior/
evals/security/
evals/regression/
evals/templates/
```

Public evals should be generic. Private or project-specific evals belong in a local Allied Village and must remain ignored by Git.

## Promotion boundary

A local eval may be proposed for public inclusion only if:

- it is sanitized;
- it contains no private data;
- it does not reveal local Village context;
- it does not include copyrighted source material;
- it has a clear public learning value;
- it is explicitly approved.

## Readiness before runtime

Before implementing executable eval runners, Konoha should have:

- stable public eval templates;
- accepted sample eval cases;
- review Scroll for eval quality;
- clear private/public boundary;
- evidence format for results;
- failure taxonomy;
- regression strategy;
- adapter runtime boundary still intact.

## Final rule

Evaluation supports trust. It does not grant permission to execute.
