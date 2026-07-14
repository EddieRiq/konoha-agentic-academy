# Conversational Hokage Foundation

## Status

Development foundation for v3.5.0.

## Product entry

```bash
konoha
```

The primary interface is the `Mission>` conversation prompt. Technical
subcommands remain recovery, testing and maintainer surfaces.

## Slice 1

1. First-session or returning-session greeting.
2. Natural-language mission intake.
3. Deterministic intent contract.
4. Repository-scoped target validation.
5. Mission Charter generation.
6. Exact Charter approval or rejection phrase.
7. Compact private continuity state.
8. Human-readable Obsidian dashboard and handoff.
9. No tool, model, patch or Git execution.

The Charter is not permission. Charter approval does not authorize a skill.

## Recovery commands

```text
/help
/status
/pending
/details
/exit
```

## Private state

The shell prefers ignored Kirigakure paths:

```text
alliance/kirigakure/memory/runtime/
alliance/kirigakure/memory/obsidian/
```

Fallback:

```text
memory/local/runtime/
memory/local/obsidian/
```

Environment overrides are supported through `KONOHA_REPO_ROOT`,
`KONOHA_WORKSPACE_ROOT`, `KONOHA_STATE_ROOT` and `KONOHA_MEMORY_ROOT`.

## Next slice

Slice 2 adds a registered skill catalog, action proposals and exact per-action
approvals, connected to the existing bounded runtime.
