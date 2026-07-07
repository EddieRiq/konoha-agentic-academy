# Runtime Planning Baseline

Status: public planning baseline.

This guide defines how Konoha discusses and reviews future runtime work before any executable runtime exists.

## Summary

Konoha runtime work must be planned in layers.

The runtime is not the agent. It is not the Hokage. It is not a free executor.

A future runtime is a controlled coordination layer that may eventually help route approved requests through adapter contracts, permission matrices, dry-runs, execution gates, evidence packs, and eval checks.

## Non-goals

This baseline does not introduce:

- executable runtime code;
- command execution;
- filesystem mutation;
- adapter automation;
- Git automation;
- release automation;
- private Village access;
- memory writes;
- background jobs;
- tool orchestration.

## Runtime responsibilities

A future runtime may eventually coordinate:

- Mission Charter validation;
- adapter selection;
- adapter invocation envelopes;
- dry-run request and result handling;
- permission checks;
- execution gate checks;
- evidence pack creation;
- post-execution reporting;
- rollback notes;
- eval result recording.

Each responsibility must remain bounded by explicit authorization.

## Runtime must not become authority

The runtime may not decide that work is allowed merely because it can perform it.

Allowed execution requires:

1. a Mission Charter;
2. explicit scope;
3. declared adapter contract;
4. permission matrix match;
5. dry-run or equivalent pre-execution evidence;
6. execution gate approval;
7. privacy and safety checks;
8. user approval when required;
9. post-action evidence;
10. teachback-ready reporting.

## Planning layers

### Layer 1: Doctrine and policy

Existing Konoha laws, conduct, approval, safety, review, teachback, and Mission Charter policies remain upstream authority.

### Layer 2: Adapter contracts

Adapters declare capabilities, limits, permissions, invocation format, dry-run behavior, evidence requirements, and runtime boundary.

### Layer 3: Runtime plan

A runtime plan describes a future workflow without implementing it.

It must state:

- intended purpose;
- non-goals;
- allowed inputs;
- allowed outputs;
- required approvals;
- forbidden actions;
- stop conditions;
- rollback expectations;
- evidence requirements;
- eval coverage.

### Layer 4: Readiness review

Runtime readiness must be reviewed before implementation.

Readiness requires enough eval cases, templates, review Scrolls, and public/private boundaries to reduce accidental autonomy.

### Layer 5: Implementation proposal

Only after readiness review may implementation be proposed.

Implementation still requires user approval and should begin with non-mutating or dry-run behavior.

## Public/private boundary

Runtime planning may reference local Villages generically.

It must not include:

- real local Village content;
- private literature;
- private memory;
- local dependency locks;
- local virtual environments;
- credentials;
- project-specific data;
- user secrets;
- internal paths beyond generic examples.

## Minimal future runtime lifecycle

A future runtime lifecycle should follow this shape:

```text
mission request
→ Mission Charter validation
→ adapter candidate selection
→ permission matrix check
→ invocation request
→ dry-run
→ evidence review
→ execution gate
→ user approval if required
→ bounded execution
→ post-execution evidence
→ review
→ teachback report
```

This lifecycle is descriptive only. It does not authorize implementation.

## Stop conditions

Stop runtime planning if:

- the plan grants autonomy without approval;
- the runtime can execute without a Mission Charter;
- private context may be accessed by default;
- Git or release operations are automatic;
- dry-run is optional for mutating actions;
- evidence is not recorded;
- rollback expectations are missing;
- eval coverage is absent;
- the plan weakens existing Konoha laws.

## Release status

Runtime planning is documentation-first.

Any future runtime implementation belongs to a later milestone and must be explicitly reviewed before code is added.
