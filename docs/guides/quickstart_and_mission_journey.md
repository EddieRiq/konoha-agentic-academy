# Quickstart and Mission Journey

## Initialize

```bash
konoha quickstart \
  --human-actor Eduardo \
  --persona calm_mentor \
  --confirm-quickstart \
  --approval-token START_KONOHA_QUICKSTART
```

Repeated execution with the same actor and persona is idempotent. A conflicting
actor or persona blocks instead of rewriting human setup state.

## Inspect the next transition

```bash
konoha next
```

Possible product states include:

```text
QUICKSTART_REQUIRED
READY_FOR_FIRST_MISSION
READY_FOR_EXECUTION_OR_PLAN
READY_FOR_REVIEW
REVIEW_CHANGES_REQUESTED
READY_FOR_TEACHBACK
TEACHBACK_NEEDS_WORK
READY_FOR_MISSION_CLOSE
MISSION_CLOSED
```

The command inspects only local public workspace evidence. It does not execute
the recommended command.

## Complete a mission

```bash
konoha mission start --help
konoha mission plan --help
konoha mission review --help
konoha mission teachback-prepare --help
konoha mission teachback --help
konoha mission close --help
```

Execution remains available only through explicit bounded gates. Model output,
status, summaries and memory remain evidence only.
