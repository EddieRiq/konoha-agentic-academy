# Model Tier Review Scroll

Status: baseline Scroll.

Use this Scroll to review model tier assignments, capability reviews, and routing recommendations.

## Purpose

The Model Tier Review Scroll ensures that Konoha uses safe, sufficient, cost-aware intelligence.

It prevents two failures:

- overusing expensive models for routine work;
- underusing capable models when safety or quality requires escalation.

## Inputs

Required inputs:

- Mission Charter;
- model tier assignment;
- context budget;
- relevant context capsules or source plan;
- risk classification;
- expected output;
- escalation triggers.

Optional inputs:

- token usage reports;
- prior eval results;
- capability review history;
- adapter permission matrix;
- reviewer notes.

## Review questions

### Mission fit

- Is the mission clearly scoped?
- Is the proposed tier appropriate for the risk?
- Is the model being asked to do only what it is allowed to do?
- Does the assignment confuse capability with authorization?

### Context fit

- Is the context intake plan minimal but sufficient?
- Are context capsules current and hash-validated?
- Are full sources required for this task?
- Is private context excluded unless explicitly approved?

### Cost fit

- Is there a planned token budget?
- Is the budget realistic for the task?
- Are expensive model calls reserved for judgment-heavy work?
- Is a cheaper tier possible with prompt reinforcement?

### Safety fit

- Are stop conditions explicit?
- Is review required for sensitive output?
- Are command, filesystem, Git, runtime, and release boundaries respected?
- Is the model forbidden from self-certifying sufficiency?

### Capability fit

- Is there evidence this tier can handle similar tasks?
- Are evals available?
- Are retries likely?
- Is a reviewer needed?
- Would a higher tier likely reduce total accepted mission cost?

## Verdicts

### Pass

The model tier assignment is appropriate.

### Pass with notes

The model tier assignment can proceed, but improvements are recommended.

### Needs changes

The assignment must be revised before work starts.

### Blocked

The assignment is unsafe, under-scoped, over-scoped, or lacks required approval.

## Required output

A review must include:

- reviewed tier;
- risk class;
- context mode;
- token budget status;
- approval status;
- escalation triggers;
- reviewer verdict;
- rationale.

## Stop conditions

Stop and escalate if:

- no Mission Charter exists;
- tier choice is not justified;
- private context is involved without approval;
- token budget is absent for a non-trivial mission;
- high-risk task is assigned to low tier without review;
- model is asked to approve its own capability;
- release/runtime/Git authority is implied but not granted.

## Completion criteria

This Scroll is complete when:

- tier assignment has a verdict;
- required changes are documented;
- reviewer is named if required;
- user can understand why the chosen tier is sufficient or why escalation is required.
