# Konoha v4: Resumable Execution Runtime

`execute_or_resume_plan` (`tools/konoha_v4/executor.py`) is the crash-safe
orchestrator behind mission execution. `conversation.run()` and
`konoha --resume MISSION_ID` are both terminal front ends for the same
runtime - neither is a separate execution path, and neither is a daemon,
background thread, or server. Each call to `execute_or_resume_plan`
resolves at most one approval gate or runs at most one assignment; the
terminal loop (`_run_resumable_execution` in `conversation.py`) hides that
one-step-per-call mechanic from the operator by calling it repeatedly until
the mission reaches a pause point or a terminal status.

## Terminal command

A normal interactive session (`konoha --repo .`) already drives a mission
through this runtime automatically once its plan is approved - nothing
extra to type. To reconnect to a mission that is paused, was interrupted
(process killed, machine restarted), or whose plan-level approval is still
pending, resume it directly by `mission_id` without opening a new
conversation:

```text
konoha --repo . --resume mission-x
```

This calls `resume_mission()`, which loads the mission's persisted plan
and execution state from disk (`KONOHA_STATE_ROOT`, or the default state
root) and continues from exactly where it left off.

## `plan_approval` flow

A task gated `plan_approval` is authorized once the mission's own plan is
approved - the same approval already required before `run()` starts
executing anything. On each call, `execute_or_resume_plan` re-reads
`plan.json` from disk and checks `plan.approval.status` fresh; it never
trusts an in-memory flag from a previous call.

If that status is not yet `"approved"` when a `plan_approval`-gated task is
reached, the runtime does **not** fail or block the mission - it returns
`diagnostic="plan_approval_not_satisfied"` and leaves the persisted
execution state completely untouched (nothing is written to disk, no
provider is invoked). The terminal loop responds by walking the operator
through the same plan-approval prompt (`approval_summary` + sí/no) used
everywhere else in Konoha, persists the decision through the normal
`plan.json` write path, and then continues automatically - a mission whose
plan is still pending approval can be approved and completed entirely from
`--resume`, with no manual `plan.json` editing required.

## `separate_human_approval` flow

A task gated `separate_human_approval` requires a distinct, single-use
authorization beyond the plan-level approval. The first time the runtime
reaches such a task, it generates a fresh nonce, persists a
`waiting_for_approval` state, and returns without invoking any provider.
The terminal loop then prints the exact command required:

```text
Hokage: Tarea t1 requiere aprobación humana explícita (gate=separate_human_approval).
Hokage: Pegá exactamente este comando para autorizarla, o escribí "salir" para pausar:
:aprobar-assignment mission-x t1 separate_human_approval <plan_identity> <nonce>
```

`<plan_identity>` and `<nonce>` are the real, full values printed on
screen for that specific pending task - they are not shortened in the
actual prompt. The match required from the operator is **exact**:
byte-for-byte, exactly one space between each of the five arguments, no
leading/trailing whitespace, no case changes. Anything else (empty input,
a partial paste, an extra space, a different case) is rejected without
creating an approval, without mutating persisted state, and without
invoking anything; the terminal reprints the same command so the operator
can retry, or accepts `salir` to pause without executing anything.

Approvals are single-use. A consumed approval never authorizes another
invocation. A terminal mission may be rejected first as
`non_resumable_status:<status>` before approval validation is even
reached - once a mission has moved on to `completed` (or any other
terminal status), a replayed approval for an earlier task is rejected by
that check, not by approval validation itself.

## Pause and resume example

A two-task mission (`t1` gated `separate_human_approval`, `t2` gated
`plan_approval`) from a fresh terminal session:

```text
$ konoha --repo .
Vos> Inspeccionar el módulo de facturación y proponer un resumen.
...
Vos> sí                       # plan-level approval
Hokage: Tarea t1 requiere aprobación humana explícita (gate=separate_human_approval).
Hokage: Pegá exactamente este comando para autorizarla, o escribí "salir" para pausar:
:aprobar-assignment mission-x t1 separate_human_approval <plan_identity> <nonce>
Vos> salir
Konoha: Misión mission-x queda pausada en waiting_for_approval. Reanudá con --resume mission-x.
```

Later, from a new terminal session (even a new machine, if it shares the
same state root):

```text
$ konoha --repo . --resume mission-x
Konoha: Reanudando la misión mission-x sin abrir una nueva conversación.
Hokage: Tarea t1 requiere aprobación humana explícita (gate=separate_human_approval).
Hokage: Pegá exactamente este comando para autorizarla, o escribí "salir" para pausar:
:aprobar-assignment mission-x t1 separate_human_approval <plan_identity> <nonce>
Vos> :aprobar-assignment mission-x t1 separate_human_approval <plan_identity> <nonce>
[t1 · codex/codex · completed]
...
Codex: Misión mission-x completada: 2 tarea(s).
```

`t2` (gated `plan_approval`) runs automatically right after `t1` completes,
with no further prompt, since the mission's plan approval already covers
it.

## Terminal states

| `state.status` | Meaning | Resumes automatically? |
|---|---|---|
| `in_progress` | Between tasks, or a `plan_approval` gate still pending (`plan_approval_not_satisfied`). | Yes, on the next call. |
| `waiting_for_approval` | Paused on a `separate_human_approval` gate. | Only once the exact matching approval is supplied. |
| `executing` | A task is, or was, actively running. | Never re-invoked automatically. On the next call, the runtime attempts to transition an inherited `executing` state to `recovery_required`. |
| `completed` | Every assignment finished successfully. | No. |
| `failed` | The current task's evidence was not `completed` (e.g. `workspace_mutation_detected`, a provider error). | No. |
| `blocked` | Reserved for a future explicit operator-pause capability; not produced by this runtime today. | No. |
| `recovery_required` | See below. | No. |

## `recovery_required`

The runtime attempts to set `recovery_required` - and stop touching that
mission automatically - whenever it cannot safely trust the persisted
state enough to keep going on its own:

- **Inherited `executing`**: the previous process persisted "about to run
  this task" and then never persisted the next transition (crash, kill, or
  a persistence failure right after `invoke`). The task may or may not
  have actually run; the runtime never guesses, so it never re-invokes. On
  the next call, the runtime attempts to transition that inherited
  `executing` state to `recovery_required`. If that persistence itself
  fails, it returns `recovery_persist_failed` instead and still does not
  invoke the task.
- **Corrupt or missing evidence**: a completed task's evidence file is
  missing, unreadable, or its hash doesn't match its recorded output.
- **Plan drift**: the persisted plan's identity no longer matches what's
  in `plan.json` (something about the plan changed since the mission was
  paused).
- **Structural corruption**: an internally inconsistent cursor/status
  combination that couldn't have come from this runtime's own transitions.

In all of these cases the same rule applies: the runtime tries to persist
`recovery_required`; if that write fails, the diagnostic is
`recovery_persist_failed` rather than `recovery_required`, and the task is
still never invoked or re-invoked.

Recovery from `recovery_required` is manual: inspect
`<state_dir>/missions/<mission_id>/execution_state.json` and
`.../evidence/*.json` directly, determine what actually happened, and
decide by hand whether/how to continue. Once `recovery_required` is
durably persisted, `execute_or_resume_plan` keeps reporting
`non_resumable_status:recovery_required` on every subsequent call rather
than guess.

## Persistence-failure diagnostics

Every write to `execution_state.json` or to an evidence file can fail
(disk full, permission error). Each failure point has its own stable
diagnostic and its own precise "what actually happened" - they are not
interchangeable:

- **`waiting_persist_failed`**: about to enter `waiting_for_approval`.
  `invoke` did not run. The `waiting` transition itself was never
  persisted - disk still holds whatever state existed before this call.
- **`executing_persist_failed`**: about to enter `executing`, before
  running anything. `invoke` did not run. The `executing` transition
  itself was never persisted - disk still holds whatever state existed
  before this call.
- **`evidence_persist_failed`**: `invoke` already ran and returned, but
  writing the resulting evidence file failed. `executing` **is** durably
  persisted on disk (it was written successfully before `invoke` ran) -
  the evidence itself is not written anywhere.
- **`final_transition_persist_failed`**: `invoke` already ran, and this
  time the evidence file **was** written successfully - but persisting the
  resulting final state (`completed` or `failed`) then failed. Both
  `executing` and the evidence file are durably on disk; only the final
  state transition is missing.
- **`recovery_persist_failed`**: the runtime decided the mission needs
  `recovery_required` (plan drift, corrupt evidence, inherited `executing`,
  or structural corruption) but could not make that decision durable.
- **`failed_before_execution_persist_failed`**: the runtime decided the
  current task must be marked `failed` before ever invoking anything, but
  could not persist that `failed` state. This has two distinct underlying
  cases:
  - **unknown agent family**: reached only after `executing` was already
    durably persisted for this task. `invoke` did not run. If persisting
    `failed` fails, disk is left at `executing`, and the next call does
    not re-invoke - it treats the inherited `executing` state the same as
    any other interrupted run.
  - **unrecognized execution gate**: reached before any `executing`
    transition was attempted for this task. `invoke` did not run. Disk is
    left exactly as it was before this call (whatever durable state
    existed previously, if any).
- **`lock_release_error`**: the mission-level result above was already
  computed - and, if applicable, already persisted - correctly; only
  releasing `execution.lock` afterwards failed. `state` and `evidence` are
  preserved; the reported diagnostic becomes `lock_release_error`,
  replacing whatever diagnostic the underlying operation would otherwise
  have reported for this call.

In every one of these cases, and regardless of what `state.status` says,
the terminal loop stops immediately: it never calls
`execute_or_resume_plan` again, never prompts for input, and never reports
the mission as completed. The next *separate* call (a fresh `--resume`)
re-reads disk from scratch and reacts to whatever was actually durably
persisted - never to anything held only in the previous process's memory.

## Known limitations

- **Evidence missing after `evidence_persist_failed`**: `invoke` ran but
  its evidence was never written anywhere; there is nothing to reconcile
  from disk, only provider-side logs/cost records outside Konoha, if any.
- **Evidence possibly orphaned after `final_transition_persist_failed`**:
  a real, hash-valid evidence file exists on disk but
  `execution_state.json` was never updated to reference it (it still says
  `executing`). Konoha does not automatically discover and reconcile this
  orphaned evidence - an operator must inspect `.../evidence/*.json` by
  hand.
- **No automatic recovery of a stale `execution.lock`** left behind by a
  crashed process; this was already a known limitation of `_MissionLock`
  before this runtime existed.
- **`recovery_required` always requires manual reconciliation** - there is
  no automated repair path, by design: the runtime would rather stop than
  guess.
- `blocked` is not produced by `execute_or_resume_plan` today - it remains
  reserved for a possible future explicit pause capability.
