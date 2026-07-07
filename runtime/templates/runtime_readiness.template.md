# Runtime Readiness Template

Status: readiness review template.

Use this template before implementing executable runtime behavior.

## Readiness identity

- Runtime component:
- Reviewer:
- Date:
- Status: not ready / partially ready / ready for implementation proposal
- Related runtime plan:
- Related adapter contracts:
- Related eval cases:

## Doctrine readiness

- [ ] Mission Charter requirement is preserved.
- [ ] Approval policy is preserved.
- [ ] Safety policy is preserved.
- [ ] Review policy is preserved.
- [ ] Teachback policy is preserved.
- [ ] Public/private boundary is preserved.
- [ ] Technical capability is not treated as authority.

## Adapter readiness

- [ ] Adapter manifest exists.
- [ ] Adapter capability declaration exists.
- [ ] Adapter permission matrix exists.
- [ ] Invocation request/result templates exist.
- [ ] Dry-run behavior is defined.
- [ ] Execution gate behavior is defined.
- [ ] Evidence requirements are defined.
- [ ] Runtime boundary is defined.

## Execution readiness

- [ ] Mutating actions require explicit approval.
- [ ] Commands are scoped and reviewable.
- [ ] Filesystem changes are bounded.
- [ ] Git operations are blocked by default.
- [ ] Release operations are blocked by default.
- [ ] Private context access is blocked by default.
- [ ] Rollback expectations are documented.
- [ ] Post-execution evidence is required.

## Evaluation readiness

- [ ] Behavior evals exist.
- [ ] Safety evals exist.
- [ ] Adapter evals exist.
- [ ] Eval result templates exist.
- [ ] Eval runner boundary is respected.
- [ ] Required evals are listed.
- [ ] Failure handling is defined.

## Privacy readiness

- [ ] No local Village content is required by default.
- [ ] No private literature is required by default.
- [ ] No secrets or credentials are required.
- [ ] Local paths are generic unless explicitly approved.
- [ ] Outputs are safe for public review unless marked local.

## Stop conditions

Implementation must not proceed if:

- any required control is missing;
- runtime can act without a Mission Charter;
- runtime can mutate files without approval;
- private context is accessible by default;
- Git or release operations are automatic;
- eval coverage is missing;
- evidence requirements are unclear;
- rollback expectations are missing.

## Verdict

- [ ] Not ready.
- [ ] Partially ready.
- [ ] Ready for implementation proposal.

Reviewer notes:
