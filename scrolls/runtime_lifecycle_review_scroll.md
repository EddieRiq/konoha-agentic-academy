# Runtime Lifecycle Review Scroll

Status: public Scroll.

This Scroll reviews proposed runtime lifecycle work before implementation, dry-run, execution, or closure.

It does not authorize execution.

## Purpose

Use this Scroll to check whether a runtime lifecycle is safe, scoped, evidenced, reversible where needed, and aligned with Konoha doctrine.

## Inputs

A review should include:

- Mission Charter;
- runtime lifecycle template;
- runtime plan;
- boundary checks;
- dry-run evidence, if available;
- approval evidence, if execution is requested;
- rollback readiness;
- closure criteria.

## Required doctrine

Reviewers must check consistency with:

- Mission Charter;
- approval policy;
- safety policy;
- review policy;
- teachback policy;
- adapter invocation contract;
- adapter execution gate;
- command runner boundary;
- filesystem mutation boundary;
- Git operation boundary;
- rollback boundary.

## Review checklist

### Mission Charter

- [ ] Mission Charter exists.
- [ ] Goal is explicit.
- [ ] Allowed scope is explicit.
- [ ] Disallowed scope is explicit.
- [ ] Stop conditions are explicit.
- [ ] Required approvals are explicit.

### Runtime plan

- [ ] Proposed steps are clear.
- [ ] Affected paths are listed.
- [ ] Commands are listed or explicitly absent.
- [ ] File mutations are listed or explicitly absent.
- [ ] Git operations are listed or explicitly absent.
- [ ] Private context access is listed or explicitly absent.

### Boundary checks

- [ ] Command runner boundary satisfied.
- [ ] Filesystem mutation boundary satisfied.
- [ ] Git operation boundary satisfied.
- [ ] Adapter permission matrix satisfied.
- [ ] Adapter invocation contract satisfied.
- [ ] Adapter execution gate satisfied.
- [ ] Rollback boundary satisfied.
- [ ] Private context boundary satisfied.

### Dry-run

- [ ] Dry-run was performed when required.
- [ ] Dry-run did not mutate files.
- [ ] Dry-run did not perform unauthorized commands.
- [ ] Dry-run produced actionable evidence.
- [ ] Dry-run identified approvals still required.

### Approval gate

- [ ] Approval is explicit.
- [ ] Approval is scoped.
- [ ] Approval is current.
- [ ] Approval does not rely on inferred permission.

### Evidence

- [ ] Pre-state is documented.
- [ ] Actions are documented.
- [ ] Outputs are documented.
- [ ] Errors are documented.
- [ ] Git state is documented.
- [ ] Privacy checks are documented.
- [ ] Evidence avoids sensitive leakage.

### Rollback

- [ ] Rollback readiness is documented.
- [ ] Recovery method is feasible.
- [ ] Residual risk is documented.
- [ ] Non-reversible changes are identified before execution.

### Closure

- [ ] Validation is complete.
- [ ] Evidence is sufficient.
- [ ] User-facing explanation is clear.
- [ ] Teachback is possible.
- [ ] No hidden follow-up work remains.

## Verdicts

### Pass

The lifecycle is acceptable for the requested non-executing stage or explicitly approved execution stage.

### Pass with notes

The lifecycle may proceed, but minor gaps should be addressed.

### Needs changes

The lifecycle should be revised before proceeding.

### Blocked

The lifecycle must not proceed.

Blocking conditions include:

- missing Mission Charter;
- unclear scope;
- missing approval;
- private context exposure risk;
- planned mutation outside scope;
- planned Git operation outside scope;
- missing rollback readiness for risky changes;
- insufficient evidence;
- ambiguous closure criteria.

## Reviewer note

Runtime lifecycle review is not execution approval.

Execution approval must still come through the proper approval gate.
