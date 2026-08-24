# Konoha v4: Supervised Technical Planning (`--plan-only`)

`konoha --plan-only` is a native `tools/konoha_v4` CLI mode, added in v4.1.0,
that produces, deterministically validates, displays, and lets a human
review and iterate on a technical `MissionPlan` — **without ever granting
execution authority and without executing any assignment.**

This is native `tools/konoha_v4` functionality. It is unrelated to, does
not call, and does not modify the legacy `tools/hokage_orchestrator`
`run_technical_plan` skill — see "Relationship to the legacy
`run_technical_plan` skill" below.

## Command

```text
konoha --plan-only
```

`--plan-only` and `--resume` are mutually exclusive at the argument-parser
level. `--version` and `--repo` behave exactly as in every other mode.
Omitting both `--resume` and `--plan-only` keeps the current, unchanged
executable conversational runtime as the default.

## Architecture: the same runtime, one authority boundary earlier

`konoha --plan-only` reuses the existing v4 planning/approval machinery
(`conversation.run()`, `_build_validated_plan()`, `_approval_loop()`)
unchanged in every respect except one: the point at which the loop would
normally convert a human's explicit affirmative into **execution**
authority instead stops at **review acceptance**.

The normal runtime's boundary is approximately:

```text
validated MissionPlan
    -> _approval_loop
    -> approved MissionPlan (execution authority granted)
    -> plan.json persisted
    -> _run_resumable_execution / execute_or_resume_plan
```

`--plan-only` stops one step earlier:

```text
validated MissionPlan
    -> _approval_loop(plan_only=True)
    -> reviewed MissionPlan (still approval.status="pending")
    -> nothing else
```

`run(repo, plan_only=True)` and `_approval_loop(..., plan_only=True)` are the
only two call sites that know about this mode. No new runtime, no second
approval loop, no new persisted schema, and no broad refactor were
introduced to build it.

## Codex is planner/conductor evidence, not authority

`--plan-only` still invokes `build_plan()` (Codex) exactly as normal mode
does, including for replanning after a confirmed human requested change.
This is planning, not assignment execution: Codex proposes a mission-
specific graph as evidence, and that proposal carries no authority of its
own in either mode. The distinction this guide is about is a different one
— whether a *human's* explicit affirmative response converts that reviewed
proposal into standing authorization to invoke providers against real
assignments. In `--plan-only`, it never does.

## Deterministic Hokage validation

Every plan `--plan-only` displays — the initial one and every replanned one
— has already passed the same deterministic `hokage.validate_plan()` checks
required in normal mode: governance, workspace policy, budget arithmetic,
gate/family/model eligibility, and (for v4.0.1-format plans) the structured
`mission_constraints` manifest's shape, source-text provenance and match
against the plan. None of this validation is weakened, skipped, or
duplicated for plan-only mode — it is the exact same `validate_plan()` call.

## The human requested-change / replanning loop

`--plan-only` preserves the existing review loop rather than becoming a
one-shot print-only command:

1. `approval_summary(plan)` is displayed.
2. The human may respond with an explicit affirmative, an explicit
   rejection, or free-form requested changes (single line `cambio: ...` or a
   multi-line block terminated with `:fin`), using the exact same input
   protocol as normal mode.
3. A requested change is confirmed back to the human (`_confirm_feedback`)
   before anything happens — cancelling leaves the current plan pending
   with nothing invoked.
4. Once confirmed, the change is recorded as human continuity evidence via
   the existing `MissionContinuityStore.record_requested_change()` — this is
   the same private continuity state (`continuity.json`) normal mode
   already uses, not a new schema.
5. Codex is invoked again (`build_plan(feedback=...)`) for a corrected plan.
6. The corrected plan is validated the same way, with
   `mission_authority_texts` built exactly as in normal mode: the original
   mission text plus every *confirmed* requested-change text recorded in
   continuity — never the raw, unconfirmed feedback string, and never
   automatic corrective-replanning validator findings. This is the same
   `mission_constraints` human-source provenance rule v4.0.1 established;
   `--plan-only` does not relax or bypass it.
7. The corrected plan is displayed again, and the loop continues.

## Acceptance-as-planning-artifact semantics

When the human's response classifies as an explicit affirmative during
`--plan-only`, it means **only**:

> "I accept this as the reviewed technical planning artifact."

It does **not** mean "I approve execution." Concretely:

- `MissionPlan.approval` is left exactly as `build_plan()` produced it:
  `status="pending"`, `approved_by=None`, `approved_at=None`.
- `MissionContinuityStore.record_approval("approved", ...)` is never called
  — the continuity store's own `approval` field also stays
  `{"status": "pending", "approved_by": None, "approved_at": None}`.
- No `AssignmentApproval` is created or consumed.
- The terminal prints:

  ```text
  Konoha: Plan técnico aceptado para revisión únicamente.
  No se autorizó ni ejecutó ninguna tarea.
  ```

  — never the normal-mode "Plan aprobado explícitamente. Ejecutando..."
  wording, which is reserved for genuine execution approval.

An explicit rejection behaves exactly as it does in normal mode: the plan
is abandoned (`approval.status="rejected"`), nothing is invoked, and no
execution authority ever existed to withdraw.

## No assignment execution

In `--plan-only` mode, none of the following are ever reached:

- `execute_or_resume_plan()` / `_run_resumable_execution()`;
- a provider invocation for any assignment (`invoke()` in
  `provider_adapters.py`);
- a Git execution baseline capture;
- the v4.0.2 pre-invocation provider/model readiness gate (there is nothing
  pending to invoke, so it is never reached — this is not a weakening of
  that gate, it simply never applies here);
- fallback of any kind — `fallback` remains declarative-only data on
  `AgentAssignment` in every mode; nothing reads it to substitute a
  provider or model, in `--plan-only` or otherwise.

## No executable `plan.json` persistence

The canonical executable persisted-plan surface,
`<state_root>/missions/<mission_id>/plan.json`, is the file `--resume` /
`execute_or_resume_plan()` load and trust. `--plan-only` never writes it —
`run()` only calls `_persist_plan(mission_dir / "plan.json", plan)` in the
normal-mode branch. `execution_state.json` is likewise never created,
since it is only ever written from inside the execution path that
`--plan-only` never reaches.

Private Konoha continuity state (`continuity.json`) *is* still written,
because it is required for safe human-requested-change provenance and
replanning — this is the same file, and the same `MissionContinuityStore`,
normal mode already uses for the identical purpose. No new public schema
and no second executable-plan format were introduced.

## No `--resume` support for plan-only artifacts (v4.1.0)

A plan reviewed and accepted through `--plan-only` is **not** resumable
through `konoha --resume <mission_id>` in this release, precisely because
no `plan.json` was ever written for it. Making a plan-only artifact later
promotable to an executable, resumable mission is explicitly out of scope
for v4.1.0.

## `MissionPlan` / schema unchanged

`--plan-only` introduces no new fields, no new schema, and no change to
`plan_hash` or `plan_identity`. Every `MissionPlan` it produces is
byte-identical in shape to one produced by normal mode; the only difference
is which fields end up mutated (or not) by the human's decision, and
whether a `plan.json` is ever written. v4.0.0 legacy persisted-plan
compatibility and v4.0.1 `mission_constraints` compatibility are both
unaffected — `--plan-only` never loads a persisted plan at all; it only
ever works with in-memory plans freshly produced by `build_plan()`.

## Relationship to the legacy `run_technical_plan` skill

`tools/hokage_orchestrator`'s registered `run_technical_plan` skill is a
separate, older subsystem. It remains registered, provider-routed, and
**fails closed** exactly as before — it has no orchestrator implementation,
and `--plan-only` does not call, bridge, wrap, or otherwise implement it.
`--plan-only` is entirely native `tools/konoha_v4` functionality, built by
extending the existing `conversation.py` review loop.
