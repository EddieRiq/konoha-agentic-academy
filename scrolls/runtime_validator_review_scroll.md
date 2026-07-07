# Runtime Validator Review Scroll

Status: documentation-first alpha.

Use this Scroll to review the Runtime Contract and Dry-run Validator MVP.

## Purpose

Confirm that the first executable runtime component is safe, read-only, deterministic, and aligned with Konoha's dry-run boundary.

## Required inputs

- Runtime package schemas.
- Validator CLI implementation.
- Valid package fixture.
- Invalid package fixture.
- Unit tests.
- Guide explaining the execution boundary.

## Review checklist

### Contract coverage

Confirm that schemas exist for:

- Mission Intake;
- Dry-run Execution Plan;
- Adapter Invocation Stub;
- Evidence Collection Stub;
- Runtime State;
- Runtime Validation Report;
- Runtime Trace Event;
- Runtime Package Manifest;
- Runtime Package Index;
- Runtime Package root object.

### Read-only boundary

Confirm that the validator:

- reads JSON input only;
- does not execute shell commands;
- does not mutate repository files;
- does not call Git;
- does not invoke adapters;
- does not read private context by default;
- does not make network calls.

### Safety flags

Confirm that validation fails if any of these are true:

- shell execution;
- filesystem mutation;
- Git operations;
- adapter execution;
- private context access;
- autonomous execution.

### Fixture behavior

Confirm that:

- valid dry-run fixture passes;
- invalid execution-enabled fixture fails;
- CLI exit codes are meaningful;
- test command succeeds without secrets or network access.

## Required reviewer outcome

Choose one:

- `approved_for_release`;
- `revision_required`;
- `blocked`.

## Stop conditions

Block the release if:

- validation success could be interpreted as execution approval;
- the validator mutates files;
- the validator performs shell/Git/network operations;
- private or local Village paths are referenced as defaults;
- fixtures contain real project data or credentials.

## Closure note

Passing this Scroll does not authorize runtime execution. It only approves a read-only validator artifact for release.
