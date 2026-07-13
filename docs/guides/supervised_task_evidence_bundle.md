# Supervised Task Evidence Bundle

## Purpose

v3.2.1 adds a deterministic evidence bundle for a validated v3.2.0 supervised task contract.

The bundle answers:

```text
What evidence is recorded for each declared evidence requirement?
```

It does not answer:

```text
Is the mission approved, complete, or authorized to execute?
```

A `complete` evidence bundle is only ready for human review.

## Validate an example

```bash
python tools/task_evidence/validate_supervised_task_evidence.py \
  --repo-root "." \
  --bundle "examples/task_evidence/supervised_task_evidence_bundle.example.json" \
  --output "./sandbox/reports/supervised-task-evidence-validation.json" \
  --force \
  --json
```

Exit codes:

```text
0  evidence_state = complete and no blockers
1  incomplete, contradicted, or structurally blocked
2  invalid invocation, unreadable JSON, private path, or unsafe output path
```

## Contract reference

The bundle records:

```json
{
  "contract_reference": {
    "path": "examples/task_contract/supervised_task_contract.example.json",
    "sha256": "<64 lowercase hex>"
  }
}
```

The validator:

1. resolves the path under the repository root;
2. blocks private-context prefixes;
3. verifies the SHA-256 digest;
4. loads the referenced `supervised_task_contract`;
5. checks contract and mission identity.

A matching hash proves which bytes were reviewed. It does not prove that the content is true.

## Evidence coverage

Every entry in the contract's `evidence_requirements` must have exactly one evidence item.

Each evidence item includes:

- stable evidence ID;
- requirement index;
- exact requirement text;
- status;
- source references;
- related acceptance criteria;
- related declared operations;
- human-readable summary.

Statuses:

```text
satisfied
missing
contradicted
unresolved
```

Derived states:

```text
complete      every requirement is satisfied
incomplete    one or more requirements are missing or unresolved
contradicted  one or more requirements are contradicted
```

## Source references

Source paths must:

- remain inside the repository root;
- exist as files;
- avoid blocked private-context prefixes;
- include a matching SHA-256 digest.

Permitted source types:

```text
file
report
command_result
observation
```

The validator reads and hashes files. It does not run commands or collect evidence.

## Claims, findings and unresolved items

Claims are explicit statements with status:

```text
supported
unsupported
contradicted
```

A supported claim may reference only satisfied evidence.

Findings are separate observations with levels:

```text
info
warning
error
```

An incomplete bundle must explain missing or unresolved requirements in `unresolved`.

## Public/private boundary

Blocked evidence paths include:

```text
.env
alliance/kirigakure/
alliance/private-library/
memory/local/
vault/
```

Local evidence under `sandbox/` is allowed because it is ignored and remains inside the repository boundary. It must still be anonymized before use when it may include personal, company, or client information.

## Authority

The bundle and validation report explicitly state:

```text
bundle is evidence only
complete is not permission
hashes verify bytes, not truth
human review is required
mission state does not authorize execution
```

Execution, models, patch apply, Git, network, private memory and mission closure remain behind separate gates.
