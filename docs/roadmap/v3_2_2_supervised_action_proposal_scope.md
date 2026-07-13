# v3.2.2 Supervised Action Proposal Scope

## Discovery decision

The repository already contains:

- mission command proposal sets;
- controlled tool execution plans;
- task workbench plans and command batches;
- Git operation plans;
- model request plans;
- apply plans;
- approval events;
- rollback doctrine.

v3.2.2 must not replace those formats.

It adds a normalized composition layer between the v3.2 contract/evidence sequence and future operation-specific execution plans.

## Objective

Validate whether a set of explicit actions is consistent with:

1. the supervised task contract;
2. the complete evidence bundle;
3. contract scope and allowed operations;
4. operation-specific approval requirements;
5. rollback doctrine;
6. non-authority boundaries.

## Included

- supervised action proposal schema;
- proposal validation report schema;
- deterministic read-only validator;
- contract and evidence reference hashes;
- identity and reference cross-checks;
- source evidence hash revalidation;
- action-to-evidence links;
- action-to-acceptance links;
- contract operation and path checks;
- argv command proposals as data;
- shell-composition blockers;
- approval requirement cross-checks;
- rollback planning;
- irreversible-action blockers;
- review and stop-trigger links;
- sandbox-only validation output;
- example, focused tests, guide and review Scroll.

## Excluded

- command execution;
- approval creation or consumption;
- patch generation or application;
- Git stage, commit, push or tag;
- model invocation;
- network access;
- private-memory access;
- automatic rollback;
- mission acceptance;
- mission closure;
- Hokage Shell integration;
- migration of existing plan schemas;
- automatic conversion to operation-specific plans.

## Compatibility

The proposal may later feed adapters for:

```text
mission_command_proposal
controlled_tool_execution_plan
sandbox_apply_plan
git_operation_plan
model_request_plan
```

v3.2.2 does not emit or execute those plans automatically.

## Acceptance criteria

1. The example validates as `proposed`.
2. Contract and evidence hashes match current bytes.
3. Evidence references the same contract path and digest.
4. All evidence requirements remain satisfied.
5. Unsupported claims, unresolved evidence and error findings block.
6. Actions cite existing satisfied evidence.
7. Operations are allowed and not blocked by contract.
8. Paths remain within allowed contract scope.
9. Private paths are blocked.
10. Command proposals use argv and block shell composition.
11. Sensitive operations require contract-declared approval tokens.
12. State-changing proposals require rollback planning.
13. Irreversible actions remain blocked.
14. Output stays under sandbox.
15. Production validator executes no subprocess.
16. Focused and canonical tests pass.
17. `proposed` grants no authority.
