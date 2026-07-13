# Supervised Action Proposal

## Purpose

v3.2.2 composes:

```text
validated supervised task contract
+
complete supervised task evidence bundle
+
explicit proposed actions
```

The result is a review artifact. It is not an execution plan, approval event, command runner request, patch application, Git operation or mission closure.

## Validate the example

```bash
python tools/action_proposal/validate_supervised_action_proposal.py \
  --repo-root "." \
  --proposal "examples/action_proposal/supervised_action_proposal.example.json" \
  --output "./sandbox/reports/supervised-action-proposal-validation.json" \
  --force \
  --json
```

Exit codes:

```text
0  proposal_state = proposed
1  proposal_state = blocked
2  invalid invocation, unreadable JSON, private path, or unsafe output
```

## References

The proposal hashes both prior artifacts:

```json
{
  "contract_reference": {
    "path": "examples/task_contract/supervised_task_contract.example.json",
    "sha256": "<64 lowercase hex>"
  },
  "evidence_bundle_reference": {
    "path": "examples/task_evidence/supervised_task_evidence_bundle.example.json",
    "sha256": "<64 lowercase hex>"
  }
}
```

The validator verifies:

1. both paths remain inside the repository;
2. private-context prefixes are blocked;
3. SHA-256 values match actual bytes;
4. report types and schema versions match;
5. contract, evidence and proposal identities align;
6. the evidence bundle references the same contract bytes.

Hashes identify reviewed bytes. They do not prove truth or grant authority.

## Proposed actions

Each action declares:

- action ID;
- contract operation;
- purpose;
- expected effect;
- risk level;
- affected paths;
- evidence IDs;
- acceptance-criterion links;
- optional command `argv`;
- working directory;
- approval requirement;
- destructive and irreversible flags;
- `execution_status = proposed_only`.

Every operation must be allowed by the contract. Every affected path must remain inside contract scope and outside blocked/private paths.

## Command proposals

Commands are arrays of arguments:

```json
{
  "command_argv": [
    "grep",
    "-n",
    "v3.2",
    "README.md",
    "CHANGELOG.md",
    "docs/roadmap.md"
  ]
}
```

The validator rejects shell-composition tokens such as:

```text
|
||
&&
;
>
>>
<
<<
$(
`
```

The validator never executes `command_argv`.

## Evidence gate

Before an action can be `proposed`:

- every contract evidence requirement must map exactly once;
- every evidence item must be `satisfied`;
- every source path and digest must still match;
- unresolved evidence must be empty;
- all claims must be `supported`;
- error-level findings must be absent;
- action evidence IDs must exist and remain satisfied.

A complete bundle still requires human interpretation.

## Approval requirements

Sensitive operations require an operation-specific approval declaration inherited from the contract.

```text
invoke_local_model
execute_command
apply_patch
git_stage
git_commit
git_push
write_private_memory
close_mission
```

The proposal repeats the required token for review. It does not create, consume or validate a human approval event.

## Rollback plan

Every proposal includes rollback planning. State-changing operations cannot use `mode = not_required`.

Modes:

```text
not_required
manual
command_proposal
irreversible
```

`irreversible` remains blocked in v3.2.2.

Rollback commands are data only. Rollback execution is outside scope.

## Proposal state

```text
proposed  internally consistent and ready for approval review
blocked   one or more policy, evidence, scope, approval or rollback blockers
```

`proposed` does not mean:

```text
approved
authorized
executable
accepted
complete
closed
```

## Public/private boundary

Blocked prefixes include:

```text
.env
alliance/kirigakure/
alliance/private-library/
memory/local/
vault/
```

Before recording evidence or actions, anonymize any personal, company or client information. Local private material remains outside the public repository.

## Authority

The proposal and validation report state:

```text
proposal is not permission
commands are data only
approvals are not consumed
evidence does not authorize action
human review is required
mission state does not authorize execution
```
