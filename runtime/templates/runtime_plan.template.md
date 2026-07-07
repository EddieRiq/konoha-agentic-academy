# Runtime Plan Template

Status: planning template.

Use this template to describe a proposed runtime workflow before implementation.

## Runtime plan identity

- Plan name:
- Plan owner:
- Date:
- Status: draft / reviewed / blocked / approved for proposal
- Related Mission Charter:
- Related adapters:
- Related eval cases:

## Purpose

Describe what the proposed runtime workflow is meant to coordinate.

## Non-goals

List what this runtime plan explicitly does not do.

Required defaults:

- no autonomous command execution;
- no autonomous file mutation;
- no autonomous Git operation;
- no autonomous release operation;
- no private Village access by default;
- no memory writes by default.

## Inputs

List allowed inputs.

Examples:

- Mission Charter;
- adapter invocation request;
- dry-run result;
- execution gate approval;
- eval result;
- user approval.

## Outputs

List allowed outputs.

Examples:

- runtime plan report;
- evidence pack;
- adapter invocation result;
- post-execution report;
- teachback summary.

## Required controls

- [ ] Mission Charter required.
- [ ] Approval policy checked.
- [ ] Safety policy checked.
- [ ] Adapter contract checked.
- [ ] Permission matrix checked.
- [ ] Dry-run required for mutating actions.
- [ ] Execution gate required for execution.
- [ ] Evidence pack required.
- [ ] Eval coverage identified.
- [ ] Teachback output required.

## Forbidden actions

List actions this runtime plan must never perform.

## Public/private boundary

Explain how local private Villages, local memory, private literature, secrets, credentials, and local artifacts remain protected.

## Execution modes

Allowed modes:

- [ ] read-only planning;
- [ ] dry-run only;
- [ ] propose-only;
- [ ] bounded execution after approval.

Do not select bounded execution unless a later implementation proposal is explicitly approved.

## Rollback expectations

Describe what must be reversible and what evidence is required before and after execution.

## Evidence requirements

List required evidence before, during, and after runtime activity.

## Eval coverage

List eval cases that should pass before implementation.

## Stop conditions

List conditions requiring stop and user clarification.

## Approval status

- [ ] Draft only.
- [ ] Reviewed.
- [ ] Blocked.
- [ ] Approved for implementation proposal.

Approver:

Date:
