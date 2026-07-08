# v2.0.0 Integration, Memory and Mission Closure

v2.0.0 closes the loop that started in the v1.x runtime releases.

Konoha can now connect mission workspaces, planning, model-gated evidence, controlled tools, reports, human approval, teachback, minimal Yamanaka memory, notification state, and mission closure.

## Promise

```text
Konoha can run a local mission end-to-end with model evidence, planning, controlled tools, human review, teachback, memory notes, and safe closure.
```

## What this release adds

- Mission Closure Gate.
- Teachback Record.
- Minimal Yamanaka Memory layout.
- Mission Notification State.
- Context Pack generation.
- Mission-local closure report.
- Memory notes for missions, decisions, and context packs.

## Closure gate

A mission can close only when all of these are true:

```text
--confirm-close
--approval-token CLOSE_MISSION_WITH_TEACHBACK
--teachback-confirmation I_CAN_EXPLAIN_AND_DEFEND_THIS_MISSION
--teachback-summary "<human explanation>"
--closure-reason "<reason>"
```

## Non-authority

Mission closure records completion. It does not authorize:

- new mission execution;
- repository apply;
- Git staging;
- Git commit;
- Git push;
- real model calls;
- adapter calls;
- private context access;
- doctrine rewrite.

## Minimal Yamanaka memory

The closure gate writes Obsidian-compatible Markdown under an explicit memory root:

```text
10-missions/<mission_id>.md
20-decisions/<mission_id>_closure_decision.md
60-context-packs/<mission_id>_context_pack.md
```

Memory supports action, but memory never authorizes action.

## Notification state

v2.0.0 formalizes the mission state vocabulary:

```text
waiting_user_input
waiting_approval
blocked
ready_for_review
ready_for_teachback
closed
archived
reopened_by_human
```

The closure gate writes a mission-local notification state report when a mission closes.

## UI relationship

The Local Web UI can show closure reports, teachback records, notification state, and memory output paths through existing report browsing.

The UI still adds no new authority.
