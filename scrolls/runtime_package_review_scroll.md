# Runtime Package Review Scroll

## Status

Review Scroll.

Use this Scroll to review a dry-run runtime package before it is considered ready for human review or any future execution gate.

## Purpose

The Runtime Package Review Scroll checks whether a package is complete, coherent, traceable, and safe.

It does not authorize execution.

## Required inputs

The reviewer should inspect:

- Runtime Package Manifest.
- Runtime Package Index.
- Mission Charter or mission scope reference.
- Mission intake object.
- Dry-run execution plan.
- Adapter invocation stubs.
- Evidence collection stubs.
- Runtime state record.
- Runtime validation checklist.
- Runtime validation report.
- Runtime trace log.
- Runtime trace events.
- Model routing decision, if applicable.
- Context budget, if applicable.
- Token usage report, if applicable.
- Capability review, if applicable.
- Context capsule manifest or refresh report, if applicable.
- Runtime package closure report.

## Review principles

- Complete does not mean authorized.
- Validated does not mean executable.
- Traced does not mean true.
- Capsule summaries do not replace source doctrine.
- Model capability does not authorize action.
- Runtime package review does not replace human approval.

## Step 1: Authority boundary review

Confirm that the package explicitly says it is dry-run only.

Block the package if it claims or implies authority to:

- execute shell commands;
- mutate files;
- run Git operations;
- invoke adapters for real;
- access private context automatically;
- publish releases;
- change doctrine;
- expand mission scope autonomously.

Outcome:

- `pass`
- `revision_required`
- `blocked`

Reviewer notes:

```text

```

## Step 2: Mission binding review

Confirm that the package is tied to an approved mission scope.

Check:

- Mission Charter reference exists.
- Scope is clear.
- Non-goals are stated.
- Ambiguities are documented.
- Required approvals are listed.
- Package does not infer missing permission.

Outcome:

- `pass`
- `revision_required`
- `blocked`

Reviewer notes:

```text

```

## Step 3: Artifact completeness review

Confirm required artifacts are present or explicitly marked not applicable.

Required artifacts:

- manifest;
- index;
- mission intake;
- dry-run execution plan;
- runtime state;
- validation checklist;
- validation report;
- trace log;
- review output;
- closure report.

Conditional artifacts must be present when relevant.

Outcome:

- `pass`
- `revision_required`
- `blocked`

Reviewer notes:

```text

```

## Step 4: Plan coherence review

Confirm the dry-run plan is coherent.

Check:

- steps are ordered;
- inputs and outputs are clear;
- stop conditions are explicit;
- adapter stubs are non-executing;
- evidence stubs are non-executing;
- rollback considerations are documented when relevant;
- no real commands are embedded as execution instructions.

Outcome:

- `pass`
- `revision_required`
- `blocked`

Reviewer notes:

```text

```

## Step 5: Governance review

Check model, context, token, and capsule governance.

Review:

- model tier assignment;
- routing decision;
- context budget;
- token budget;
- token overage records;
- capability review;
- capsule status;
- stale capsule handling;
- full-source fallback triggers.

Block if a lower tier model is treated as self-certifying.

Block if token overage is hidden or unjustified.

Outcome:

- `pass`
- `revision_required`
- `blocked`

Reviewer notes:

```text

```

## Step 6: Evidence review

Check whether evidence references are sufficient.

Evidence should support:

- package completeness;
- scope alignment;
- validation status;
- trace events;
- public/private boundary checks;
- model and token decisions;
- unresolved blockers.

Block if evidence is missing for a material decision.

Outcome:

- `pass`
- `revision_required`
- `blocked`

Reviewer notes:

```text

```

## Step 7: Trace review

Confirm the trace log is append-only and useful.

Check:

- material decisions are traced;
- blockers are recorded;
- supersession is explicit;
- unresolved issues are not hidden;
- timestamps or sequence IDs are present;
- trace entries point to evidence or artifacts.

Outcome:

- `pass`
- `revision_required`
- `blocked`

Reviewer notes:

```text

```

## Step 8: Privacy and public/private boundary review

Confirm the package does not expose private village content, local secrets, private literature, credentials, or local-only paths unless explicitly approved and intended for local-only use.

Public packages must not include:

- private village content;
- local virtual environment details;
- credentials;
- private source material;
- private memory;
- sensitive paths;
- user or client data.

Outcome:

- `pass`
- `revision_required`
- `blocked`

Reviewer notes:

```text

```

## Step 9: Closure review

Confirm closure is clear.

Check:

- final status is declared;
- teachback status is documented;
- unresolved blockers are listed;
- future gate requirements are documented;
- no execution is implied.

Outcome:

- `pass`
- `revision_required`
- `blocked`

Reviewer notes:

```text

```

## Final review decision

Choose one:

- `approved_for_review_only`
- `revision_required`
- `blocked`

## Final reviewer summary

```text

```

## Final boundary statement

This Scroll does not authorize execution, model escalation, token overage, private context access, Git operations, filesystem mutation, adapter execution, releases, or doctrine changes.

It only reviews whether a dry-run runtime package is coherent enough for review.
