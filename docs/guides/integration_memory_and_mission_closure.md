# Integration, Memory and Evidence-Bound Mission Closure

## Current contract

Mission closure is a composition of four distinct evidentiary states:

```text
successful execution evidence
    ↓
approved human review evidence
    ↓
closure-eligible structured Teachback evidence
    ↓
explicit human closure approval
```

The canonical tool is:

```bash
python tools/mission_closure/close_mission.py --help
```

The canonical CLI surface is:

```bash
python tools/konoha_cli.py mission close --help
```

## Required evidence

The closure command requires three mission-local JSON sources:

```text
--execution-evidence
--review-evidence
--teachback-record
```

All paths must remain under:

```text
<workspace-root>/missions/<mission-id>/
```

### Execution

Execution evidence must report a completed successful state, such as:

```text
status = passed | completed | success | closed
```

or:

```text
exit_code = 0
```

### Review

Review evidence must contain an approved human decision and identify the human
reviewer.

A review display, self-review suggestion or model assessment is not approval.

### Teachback

The Teachback record must:

- match the same mission;
- match the same execution and review source paths;
- be valid against the mission manifest;
- have result `passed`, or an explicitly allowed `skipped`;
- satisfy required and achieved levels;
- contain human evidence when passed.

## Closure approval

After all evidence validates:

```bash
python tools/konoha_cli.py mission close \
  --workspace-root "./sandbox/konoha-beta-workspace" \
  --mission-id "example" \
  --memory-root "alliance/kirigakure/memory/obsidian" \
  --closure-id "example-closure" \
  --execution-evidence "evidence/command_results/execution.json" \
  --review-evidence "reports/human-review_konoha_human_review_record.json" \
  --teachback-record "reports/example-teachback_teachback_record.json" \
  --closure-reason "Execution, review and Teachback evidence are complete." \
  --human-actor "human" \
  --confirm-close \
  --approval-token "CLOSE_MISSION_WITH_TEACHBACK"
```

## Reentry and conflict

The gate hashes:

```text
mission and closure ids
human actor and closure reason
execution path and SHA-256
review path and SHA-256
Teachback path and SHA-256
```

An identical closure is idempotent and performs no new writes.

A different fingerprint for an existing closure returns a conflict. The
compatibility `--force` flag cannot overwrite contradictory closure evidence.

## Outputs

Mission-local:

```text
reports/<closure-id>_mission_closure_report.json
reports/<closure-id>_notification_state.json
mission_status.json
```

Explicit private/local memory root:

```text
10-missions/<mission-id>.md
20-decisions/<mission-id>_closure_decision.md
60-context-packs/<mission-id>_context_pack.md
```

Memory supports action but does not authorize action.

## Non-authority

Closure does not authorize:

- new execution;
- repository apply;
- Git stage, commit or push;
- model or adapter invocation;
- private context discovery;
- network access;
- doctrine rewrite.
