# Conversational Hokage Lifecycle

## Slice 3

Slice 3 completes a supervised mission through the `Mission>` conversation:

```text
natural-language request
→ Mission Charter
→ bounded actions
→ deterministic execution validation
→ human review
→ human Teachback
→ explicit mission closure
→ private Obsidian memory
```

## Review

After every action is completed or rejected, Hokage validates the persisted
runtime evidence and proposes a review:

```text
APROBAR REVIEW-...
CAMBIOS REVIEW-...
```

The generated review summary is a proposal. Only the exact human approval
records an approved review in the beta runtime.

## Teachback

After review, the user must explain the mission in their own words:

```text
TEACHBACK: <human explanation>
```

Generated text does not count as Teachback. The explanation is recorded through
the existing structured Teachback gate and remains evidence only.

## Closure

After passed Teachback, Hokage proposes:

```text
APROBAR CIERRE-...
```

The closure gate validates matching execution, review and Teachback sources.
Closure writes mission status plus private Obsidian mission, decision and
context-pack notes. It does not authorize new work.

## Reentry

After closure, runtime continuity retains:

- last mission;
- closure report;
- last closed timestamp;
- no active mission.

A new `konoha` session greets the user as returning and references the last
mission without loading the complete Obsidian vault.
