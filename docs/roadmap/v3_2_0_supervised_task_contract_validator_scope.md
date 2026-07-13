# v3.2.0 Supervised Task Contract Validator Scope

## Discovery result

The existing runtime schemas cover mission identity, state, path allowances, command allowances, evidence and stop/blocker concepts, but do not expose one complete normalized contract for:

- blocked paths;
- blocked commands/operations;
- acceptance criteria;
- operation-specific approvals;
- completion conditions;
- Teachback;
- required review.

v3.2.0 fills that policy gap without replacing existing runtime reports.

## Objective

Create a deterministic, declarative task policy contract that can be reviewed before any execution proposal.

## Included

- supervised task contract JSON schema;
- validation report schema;
- deterministic validator;
- normalized operation vocabulary;
- protected path rules;
- sensitive-operation approval declarations;
- risk/review rules;
- network and private-context policy checks;
- mandatory Teachback;
- explicit stop triggers;
- example, tests, guide and review Scroll.

## Excluded

- mission start;
- command proposal generation;
- command execution;
- model invocation;
- patch application;
- Git operations;
- network access;
- private-memory reads or writes;
- mission closure;
- automatic migration of existing manifests;
- Hokage Shell integration.

## Compatibility position

Existing contracts remain sources of operational evidence:

```text
beta_mission_manifest
mission_intake
mission_command_proposal
mission_approval_event
mission_closure_report
mission_workflow_report
human_in_loop_agent_state
controlled_tool_execution_plan
human_approved_apply_report
```

The new contract is a pre-execution policy profile. Future releases may map existing reports into it, but v3.2.0 performs no migration and no execution.

## Acceptance criteria

1. A complete read-only contract validates as `ready`.
2. Missing acceptance, evidence, completion, review or Teachback blocks readiness.
3. Protected/private paths cannot be allowed.
4. Traversal and absolute paths are blocked.
5. Sensitive allowed operations require specific approval declarations.
6. High and critical risks enforce stronger review.
7. `git_push` requires explicit network-approval policy.
8. `write_private_memory` requires explicit private-context policy.
9. Report output stays under sandbox.
10. Validation never authorizes execution.
11. Existing test suites remain green.
12. Canonical Release Test Gate passes.
