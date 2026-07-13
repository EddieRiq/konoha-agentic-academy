# Structured Teachback Protocol Gate

## Purpose

Teachback is human completion evidence. It is not a confirmation phrase and it
is not generated automatically by Mission Closure.

The canonical tool is:

```bash
python tools/teachback/manage_teachback.py --help
```

The canonical CLI surface is:

```bash
python tools/konoha_cli.py mission teachback --help
```

## Mission policy

Every mission manifest must declare or inherit:

```json
{
  "teachback": {
    "required": true,
    "required_level": 2,
    "skip_allowed": false
  }
}
```

When the manifest does not contain an explicit Teachback object, the runtime
uses a conservative risk-based default:

```text
low       level 1
medium    level 2
high      level 3
critical  level 4
```

## Record

A Teachback record contains:

```text
mission_id
teachback_id
required
required_level
achieved_level
result
completed_by_user
summary
gaps
next_explanation_needed
human_actor
human_evidence
source_execution
source_review
skip_reason
recorded_at
non_authority
```

Valid results:

```text
passed
needs_clarification
failed
skipped
```

## Passed

`passed` requires:

```text
completed_by_user = true
achieved_level >= required_level
gaps = []
summary >= 20 characters
human_evidence is not empty
source_execution exists under mission workspace
source_review exists under mission workspace
```

A model explanation cannot replace `human_evidence`.

## Needs clarification

`needs_clarification` is valid evidence, but it does not permit mission
closure. It requires at least one gap and an explicit next explanation.

## Failed

`failed` records the current state without closing the mission. It requires at
least one gap and `completed_by_user=false`.

## Skipped

`skipped` is allowed only when:

```text
manifest teachback.required = false
manifest teachback.skip_allowed = true
risk level is not high or critical
skip reason is explicit
```

## Record command

```bash
python tools/konoha_cli.py mission teachback \
  --workspace-root "./sandbox/konoha-beta-workspace" \
  --mission-id "example" \
  --teachback-id "example-teachback" \
  --result "passed" \
  --achieved-level 2 \
  --completed-by-user \
  --summary "I can explain what ran, why, how it was validated, and the limitations." \
  --human-evidence "The user explained operation, validation, failures and recovery in their own words." \
  --source-execution "evidence/command_results/execution.json" \
  --source-review "reports/human-review_konoha_human_review_record.json" \
  --human-actor "human" \
  --confirm-record \
  --approval-token "RECORD_TEACHBACK_EVIDENCE"
```

## Reentry

The same record may be submitted again. Identical evidence returns an
idempotent success without rewriting the file.

Different evidence for the same `teachback_id` returns:

```text
BLOCKED_TEACHBACK_CONFLICT
```

There is no force override for contradictory human evidence.

## Boundary

Teachback evidence does not authorize:

- execution;
- repository mutation;
- Git operations;
- model invocation;
- network access;
- mission closure.

Mission Closure remains a separate explicit gate.
