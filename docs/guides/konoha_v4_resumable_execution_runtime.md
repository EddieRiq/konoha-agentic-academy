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
| `blocked` | The provider's own structured result declared `outcome` `blocked` or `changes_requested`, or the task's `mutation=true` was rejected before invocation. See "Outcome → runtime state mapping" and "Mutation (not yet supported)" below. | No. |
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

## Structured assignment result

Every assignment invocation must return exactly one JSON object with these
six keys - no more, no fewer - and nothing outside that JSON:

- `outcome`: `"completed"`, `"blocked"`, `"failed"`, or `"changes_requested"`.
- `objective_satisfied`: `true` only when `outcome == "completed"`, `false`
  for every other outcome.
- `summary`: non-empty string.
- `diagnostic`: string or `null` - the model's own free-text note. This
  field is evidence, never authority: the runtime never reads it to decide
  anything, and never substring-scans it (or `summary`) for words like
  "blocked". Only the structured `outcome`/`review_outcome` fields, checked
  against the deterministic rules below, decide the runtime's own
  diagnostic and state.
- `evidence`: array of `{source, observation}` pairs (both non-empty
  strings), possibly empty.
- `review_outcome`: `"approved"`, `"approved_with_notes"`,
  `"changes_requested"`, `"blocked"`, or `null` - see "Jounin review
  contract" below.

The schema lives at
`schemas/runtime/konoha_v4_assignment_result.schema.json` and is
deliberately portable (`type`/`required`/`enum`/`minLength`/
`additionalProperties: false` only, no `allOf`/`if`/`then`) - every
cross-field correlation is enforced in Python, not in the schema. Codex is
invoked with `--output-schema` pointing at this file (resolved from
Konoha's own installation, never from the target workspace being audited,
which may be an external repository with no `schemas/` directory of its
own). Claude and Ollama have no equivalent CLI-level enforcement, so they
are subject to the exact same Python validation as Codex - an unstructured
response from either fails closed identically.

Three distinct parse/validation failures, each with its own stable
diagnostic:

- **`invalid_result_json`**: the provider's output is not valid JSON.
- **`invalid_result_schema`**: valid JSON, but it doesn't match the six-key
  structural contract (missing/extra keys, wrong types, or an `outcome`/
  `review_outcome` outside its enum). Type is always checked before enum
  membership, so an unhashable value (a JSON array or object where a
  string was expected) fails closed as `invalid_result_schema` instead of
  raising `TypeError`.
- **`contradictory_result_fields`**: structurally valid, but the
  cross-field rules below (outcome/family/review_outcome correlation)
  aren't satisfied.

Each parse/validation failure produces `EvidenceRecord.status="failed"`
after provider invocation. Post-invoke Git failures and workspace
mismatches also produce failed evidence. A Git baseline failure occurs
before provider invocation and transitions the execution state directly to
`failed`; the legacy `execute_plan` path separately returns one failed
evidence record for that condition.

## Outcome → runtime state mapping

| `outcome` | `EvidenceRecord.status` | `ExecutionState.status` | `diagnostic` |
|---|---|---|---|
| `completed` (with `objective_satisfied=true`) | `completed` | advances normally (`in_progress` or `completed`) | `completed` |
| `blocked` | `blocked` | `blocked` | `blocked` |
| `changes_requested` | `blocked` | `blocked` | `changes_requested` |
| `failed` | `failed` | `failed` | `assignment_failed` |

`blocked` and `changes_requested` both stop the mission exactly like
`failed` does - `blocked` is a `NON_RESUMABLE_EXECUTION_STATUSES` member,
so no later assignment in the plan ever runs once one of these is reached.
The only difference between the two is the `diagnostic` string, which is
what a human reviewing the mission uses to tell "the provider itself
declared it can't proceed" (`blocked`) apart from "a review found
something that needs changes" (`changes_requested`).

`diagnostic` is always one of a fixed, code-owned set of reason codes -
never the model's own free-text `diagnostic`/`summary` fields. The failure
and stop reason codes used across this contract are: `invalid_result_json`,
`invalid_result_schema`, `contradictory_result_fields`, `process_error`
(the provider process itself failed to run), `assignment_failed`,
`git_status_timeout`, `git_status_failed`, `workspace_mutation_detected`,
`blocked`, `changes_requested`, `mutation_runtime_not_supported`.

## Jounin review contract

Assignments whose `family` is `jounin-review` carry an additional,
mandatory correlation between `review_outcome` and `outcome`/
`objective_satisfied`:

| `review_outcome` | required `outcome` | required `objective_satisfied` |
|---|---|---|
| `approved` or `approved_with_notes` | `completed` | `true` |
| `blocked` | `blocked` | `false` |
| `changes_requested` | `changes_requested` | `false` |

A `jounin-review` assignment with `review_outcome=null`, or with any other
mismatch between `review_outcome` and `outcome`/`objective_satisfied`,
fails as `contradictory_result_fields`.

For every other family, `review_outcome` must be `null` - a non-`null`
`review_outcome` on a non-`jounin-review` assignment is itself a
`contradictory_result_fields` failure.

## Mutation (not yet supported)

`AgentAssignment.mutation=true` is not runnable in this Patch - there is no
isolated worktree runtime yet, so nothing may write to the audited
workspace (including the primary checkout). This is enforced twice,
deterministically:

- **Before plan approval**: `hokage.validate_plan` rejects any
  `mutation=true` assignment unconditionally - not even declaring
  `"mutation"` in `approval_boundaries` allows it through. A plan
  containing one is never offered to a human for approval.
- **Before invocation, as defense in depth**: `execute_or_resume_plan`
  checks `current_task.mutation` before any gate/approval logic, before
  resolving the agent family, before the Git baseline, and before
  `invoke`. If true, the mission transitions straight to
  `ExecutionState.status="blocked"`,
  `diagnostic="mutation_runtime_not_supported"` - the provider is never
  invoked, `"executing"` is never persisted, and a supplied
  `separate_human_approval` is neither validated nor consumed (a mutating
  task never even reaches `waiting_for_approval`). The legacy
  `execute_plan` path applies the same rejection: it scans for the first
  `mutation=true` assignment before its normal preflight and, if found,
  persists exactly one `blocked` evidence record for it and stops - no
  `invoke` call, no evidence for any other task.

Supporting real mutation in the future requires an isolated worktree
(never the primary checkout) and a separate, explicit human approval to
apply the resulting diff back - not a relaxation of this gate.

## Git integrity gate

Git status verification belongs to the runtime, not to the provider - the
per-assignment prompt no longer asks the model to compare git status
before/after; it explicitly states that the before/after integrity check
is the runtime's responsibility. The provider must not reproduce that gate
with its own `git status` calls or model-selected timeouts. This does not
prohibit a read-only assignment from inspecting Git metadata when that
inspection is part of its explicit objective.

`_git_status` (`tools/konoha_v4/executor.py`):

- runs `git -c core.fsmonitor=false status --short --untracked-files=all`
  (untracked files count, not just tracked changes);
- with `GIT_OPTIONAL_LOCKS=0` set in the subprocess environment;
- under a configurable timeout whose runtime default is 120 seconds;
- fails closed on either a non-zero exit code or a timeout - it raises
  `GitStatusError` in both cases and can never return a string after
  either, so an empty result can never be misread as a clean tree.

The runtime captures a Git baseline **before** persisting `"executing"`,
and checks again after `invoke` returns:

- **Baseline failure** (before `"executing"` is ever persisted): the
  mission goes straight to `ExecutionState.status="failed"` with
  `diagnostic` set to `git_status_timeout` or `git_status_failed`. The
  provider is never invoked, `"executing"` is never persisted, and a
  supplied `separate_human_approval` is validated but never consumed.
  This never resolves to `recovery_required` - there is nothing to
  recover from, since nothing was ever persisted as in-flight.
- **Post-invoke failure**: `invoke` already ran; the second `_git_status`
  call raising is caught (not propagated) and produces a normal
  `EvidenceRecord.status="failed"` with `diagnostic` set to
  `git_status_timeout` or `git_status_failed`, going through the same
  evidence/state pipeline as any other post-invoke failure.
- **Post-invoke mismatch** (both calls succeed, but the output differs):
  `EvidenceRecord.status="failed"`,
  `diagnostic="workspace_mutation_detected"` - the workspace changed
  during what was supposed to be a read-only assignment, and this
  overrides whatever outcome the structured result itself claimed.

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
- **No mutation runtime yet**: `mutation=true` assignments are always
  rejected before invocation (see "Mutation (not yet supported)" below) -
  there is no isolated worktree, and this Patch does not add one.
- **Structured results are still model evidence, not authority**: the
  outcome/review_outcome contract narrows what a provider's own claim can
  mean, but the claim itself still comes from the model; the runtime
  never trusts free text, only the structured fields checked against
  fixed, deterministic rules.
- **No autonomous execution, daemon, or web server**: this Patch adds no
  new entry point beyond `execute_or_resume_plan`'s existing one-step-per-
  call contract, and no way to bypass `plan_approval` or
  `separate_human_approval` - every gate documented above still applies
  exactly as before.
