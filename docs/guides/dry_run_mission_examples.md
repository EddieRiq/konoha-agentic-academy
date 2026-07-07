# Dry-run Mission Examples

Status: documentation-first baseline.

## Purpose

This guide defines public, generic examples of dry-run runtime packages for Konoha Agentic Academy.

The examples show how a Mission Charter can be represented as a reviewable package without executing shell commands, mutating files, invoking adapters, accessing private context, or performing Git operations.

## Scope

The examples cover:

- mission intake;
- dry-run execution planning;
- adapter invocation stubs;
- evidence collection stubs;
- runtime state;
- validation outcome;
- trace logging;
- package manifest;
- package index;
- package closure.

## Non-goals

These examples do not provide:

- executable runtime code;
- real adapter calls;
- real filesystem mutation;
- real Git operations;
- private Village content;
- local context access;
- secrets, credentials, or environment details.

## Example set

The initial example set contains three public-safe dry-run packages:

| Example | Intent | Risk level | Expected outcome |
| --- | --- | --- | --- |
| Documentation update dry-run | Plan a small public documentation update | Low | Valid for review |
| Adapter contract review dry-run | Plan a review of adapter contract documentation | Medium | Conditional revision required |
| Context capsule refresh dry-run | Plan a capsule refresh based on source-hash mismatch | Medium | Blocked until full source review |

## Required properties

Every example must be:

- synthetic or generic;
- safe for a public repository;
- free of private project paths;
- free of copyrighted source text;
- free of secrets or credentials;
- explicit about dry-run boundaries;
- clear about what evidence would be needed before any future execution.

## Package structure

A complete dry-run example should include these sections:

```text
Mission Intake
Dry-Run Execution Plan
Adapter Invocation Stub
Evidence Collection Stub
Runtime State
Runtime Validation Report
Runtime Trace Log
Runtime Package Manifest
Runtime Package Index
Runtime Package Closure
Teachback Notes
```

The sections may appear in a single Markdown file for readability.

## Authority boundary

A dry-run example is not authorization.

It may show a plan, expected evidence, blockers, review outcomes, and closure state, but it must not claim that execution is approved.

Execution requires a separate Mission Charter, approval gate, applicable runtime boundary, evidence review, and user authorization.

## Review requirements

Before adding or changing examples, reviewers must verify:

- no private content is present;
- no real credentials, tokens, local paths, or user-specific information are present;
- the example does not imply autonomous execution;
- all planned actions are described as dry-run only;
- blockers and stop conditions are explicit;
- evidence is referenced as expected evidence, not as already collected proof unless the example says it is synthetic.

## Relationship to runtime package assembly

Runtime package assembly defines how artifacts are organized.

Dry-run mission examples demonstrate what a completed synthetic package can look like.

The examples are teaching artifacts. They are not runtime outputs and do not authorize future execution.
