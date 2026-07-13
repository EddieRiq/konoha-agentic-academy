# Supervised Task Contract Validator

## Purpose

v3.2.0 adds a normalized declarative contract for supervised tasks and a deterministic validator.

The validator answers:

```text
Is the task policy complete enough to review?
```

It does not answer:

```text
May the task execute now?
```

A `ready` contract is evidence only. Execution, models, patches, Git, network, private memory and closure still require their separate gates.

## Contract command

```bash
python tools/task_contract/validate_supervised_task_contract.py \
  --repo-root "." \
  --contract "examples/task_contract/supervised_task_contract.example.json" \
  --output "./sandbox/reports/supervised-task-contract-validation.json" \
  --force \
  --json
```

Exit codes:

```text
0  contract readiness = ready
1  contract readiness = blocked
2  invalid invocation, unreadable JSON, or unsafe output path
```

## Required policy categories

The normalized contract contains:

- objective and explicit non-goals;
- risk level;
- allowed and blocked public paths;
- allowed and blocked operations;
- network policy;
- private-context policy;
- acceptance criteria;
- evidence requirements;
- operation-specific approval requirements;
- completion conditions;
- review requirements;
- mandatory Teachback;
- stop triggers;
- explicit authority flags.

## Operation vocabulary

```text
inspect_repository
read_public_files
run_deterministic_checks
propose_command
record_external_result
invoke_local_model
execute_command
apply_patch
git_stage
git_commit
git_push
write_private_memory
close_mission
```

Operations not listed as allowed or blocked produce warnings.

Sensitive allowed operations require an operation-specific approval declaration:

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

The declaration records which future gate is required. It does not consume or validate approval for execution.

## Path policy

Allowed paths must be repository-relative. Absolute paths and traversal are blocked.

The following protected prefixes cannot appear in `allowed_paths`:

```text
.env
alliance/kirigakure
alliance/private-library
memory/local
vault
sandbox
```

They may appear in `blocked_paths`.

## Risk and review

```text
low/medium   standard, strict or critical review
high         strict or critical review
critical     critical review
```

Human review is always required.

## Network and private context

`git_push` can only be declared allowed when:

```json
"network_policy": "explicit_approval_required"
```

`write_private_memory` can only be declared allowed when:

```json
"private_context_policy": "explicit_approval_required"
```

These policies still do not authorize network or private-context access.

## Teachback

`teachback_required` must be `true` for every contract.

Mission closure also requires:

- `close_mission` in allowed operations;
- an operation-specific approval requirement;
- a separate closure gate.

## Output boundary

The optional validation report may only be written under:

```text
<repo-root>/sandbox/
```

The contract and public repository are never mutated.
