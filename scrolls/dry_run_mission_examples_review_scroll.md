# Dry-run Mission Examples Review Scroll

Status: documentation-first review Scroll.

## Purpose

This Scroll reviews public dry-run mission examples before they are added to the repository or referenced as valid teaching artifacts.

## Scope

Use this Scroll for examples that demonstrate:

- mission intake;
- dry-run execution planning;
- adapter invocation stubs;
- evidence collection stubs;
- runtime state;
- validation reports;
- trace logs;
- runtime package assembly;
- package closure;
- teachback notes.

## Non-authorization boundary

This Scroll does not authorize execution.

Passing this review means only that the example is acceptable as public documentation.

It does not authorize:

- shell execution;
- filesystem mutation;
- Git operations;
- adapter invocation;
- private context access;
- model routing decisions;
- token budget exceptions;
- doctrine changes.

## Review checklist

### 1. Public safety

Verify that the example contains no:

- secrets;
- credentials;
- tokens;
- private keys;
- real customer data;
- private project paths;
- local Village content;
- copyrighted source text;
- proprietary logs or stack traces.

Outcome:

```text
public_safety = pass | revise | block
```

### 2. Dry-run boundary

Verify that every action is described as planned, expected, synthetic, or dry-run only.

Block the example if it claims that commands, file mutations, adapter calls, or Git operations already happened unless the example is explicitly about synthetic evidence.

Outcome:

```text
dry_run_boundary = pass | revise | block
```

### 3. Runtime package completeness

Verify that the example includes or intentionally marks not applicable:

- Mission Intake;
- Dry-Run Execution Plan;
- Adapter Invocation Stub;
- Evidence Collection Stub;
- Runtime State;
- Validation Report;
- Trace Log;
- Package Manifest;
- Package Index;
- Package Closure.

Outcome:

```text
package_completeness = pass | revise | block
```

### 4. Governance consistency

Verify that the example is consistent with:

- Mission Charter before execution;
- no assumptions;
- evidence before action;
- capability does not imply authorization;
- summaries are not truth;
- private context stays private by default;
- user approval required for sensitive actions.

Outcome:

```text
governance_consistency = pass | revise | block
```

### 5. Teaching value

Verify that the example helps readers understand a real boundary or workflow.

The example should not be a decorative file. It should teach a practical pattern.

Outcome:

```text
teaching_value = pass | revise | block
```

## Reviewer decision

Allowed decisions:

```text
approved_as_example
revision_required
blocked
```

## Required reviewer notes

Reviewer notes must include:

- what the example teaches;
- why it is safe to publish;
- what remains non-authorized;
- any required revision;
- whether the example should be indexed.

## Stop conditions

Stop and block the example if:

- private content appears;
- execution is implied;
- authority boundaries are unclear;
- evidence is fabricated as real;
- sensitive source material is summarized too specifically;
- the example can be mistaken for a runtime output with authorization.

## Closure

A reviewed example may be merged only as documentation.

Any future executable runtime implementation must define separate tests and approval gates.
