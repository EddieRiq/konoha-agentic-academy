# Command Runner Readiness Review

Status: template.

Use this template before implementing any executable command runner.

## Proposal

- Runtime component name:
- Owner:
- Date:
- Related Mission Charter:
- Related runtime plan:

## Implementation status

- [ ] Planning only
- [ ] Prototype proposed
- [ ] Prototype implemented locally
- [ ] Public implementation proposed
- [ ] Public implementation ready for review

## Required doctrine references

- [ ] Mission Charter policy reviewed.
- [ ] Adapter Invocation Contract reviewed.
- [ ] Adapter Execution Gate reviewed.
- [ ] Adapter Evidence Pack reviewed.
- [ ] Adapter Dry-Run Protocol reviewed.
- [ ] Adapter Runtime Boundary reviewed.
- [ ] Command Runner Boundary reviewed.
- [ ] Safety policy reviewed.
- [ ] Public/private boundary reviewed.

## Supported command categories

- [ ] read-only
- [ ] file mutation
- [ ] package/environment
- [ ] Git
- [ ] release
- [ ] network
- [ ] destructive

For each checked category, attach permission logic and tests.

## Required controls

- [ ] Structured command requests only.
- [ ] Exact command logging.
- [ ] Working directory required.
- [ ] Path allowlist required.
- [ ] Private path handling.
- [ ] Public/private boundary checks.
- [ ] Dry-run support.
- [ ] Execution gate integration.
- [ ] Evidence pack integration.
- [ ] Approval validation.
- [ ] Stop condition enforcement.
- [ ] Output sanitization.
- [ ] Rollback/recovery notes.
- [ ] Eval coverage.

## Blockers

- [ ] Missing Mission Charter integration.
- [ ] Missing permission matrix integration.
- [ ] Missing execution gate.
- [ ] Missing evidence pack.
- [ ] Missing dry-run.
- [ ] Missing private boundary checks.
- [ ] Missing output sanitization.
- [ ] Missing command logs.
- [ ] Missing tests/evals.
- [ ] Unclear rollback behavior.
- [ ] Unclear user approval flow.

## Safety verdict

- [ ] Not ready
- [ ] Ready for design review
- [ ] Ready for local prototype only
- [ ] Ready for public prototype review
- [ ] Ready for limited implementation

## Reviewer notes

```text
<notes>
```
