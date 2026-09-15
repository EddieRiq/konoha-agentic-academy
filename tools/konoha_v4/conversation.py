from __future__ import annotations
import json, os, secrets, subprocess, sys
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from .terminal_input import TerminalTurnReader
from .context_acquisition import acquire_context
from .continuity import (
 MissionContinuityStore,
 default_state_root,
 plan_payload,
)
from .executor import (
 execute_or_resume_plan,
 expected_approval_command,
 load_persisted_plan,
 plan_identity,
)
from .hokage import approval_summary, validate_plan
from .models import AssignmentApproval, MissionPlan
from .planner import build_plan
from .registry import CapabilityRegistry

APPROVE_WORDS = {"si", "sí", "s", "dale", "aprobar", "apruebo", "aprobado", "continuar", "proceed", "yes"}
REJECT_WORDS = {"no", "rechazar", "rechazo", "cancel", "cancelar", "stop", "detener"}
# protocols/approval/approval_policy.md: approval must be explicit and
# ambiguous responses are not approval - "ok" is explicitly listed as
# ambiguous there. It must neither approve nor be treated as free-form
# requested changes; it stays pending so Konoha asks again.
AMBIGUOUS_APPROVAL_WORDS = {"ok"}

# v4.0.2: stable machine-readable ExecutionAttempt.diagnostic prefixes for
# executor._readiness_diagnostic's operational readiness gate - never
# human-prose parsing, exact prefix matching only. Kept in one place so
# _run_resumable_execution's dispatch and any test can reference the same
# contract instead of duplicating the literal strings.
READINESS_DIAGNOSTIC_PREFIXES = ("provider_not_ready:", "model_not_ready:")

_TERMINAL_INPUT = TerminalTurnReader(sys.stdin, sys.stdout)


def _repo_state(repo: Path) -> dict:
    def run(*args: str) -> str:
        cp = subprocess.run(args, cwd=repo, text=True, capture_output=True, check=False)
        return cp.stdout.strip()
    return {
        "branch": run("git", "branch", "--show-current"),
        "head": run("git", "rev-parse", "HEAD"),
        "status": run("git", "status", "--short"),
    }


def _read_turn(prompt: str = "Vos> ") -> str | None:
    """Deterministic mission-turn capture. The first line only decides
    whether to exit or enter block mode - it is never treated as "probably
    the whole mission" based on timing. Any substantive first line always
    requires an explicit ':fin' to submit, however many lines, pastes or
    OS chunks it takes to arrive, so a paste can never be silently
    truncated and its tail can never leak into a later read. Uses the
    unstripped first_line for mission content and a separately normalized
    copy only for control-word matching, reusing the same canonical
    _EXIT_COMMANDS set every other prompt in this module uses - not a
    second, narrower exit-word set."""
    first_line = _TERMINAL_INPUT.read_exact_line(prompt)
    if first_line is None:
        return None

    control = first_line.strip().casefold()

    if not control:
        return ""

    if control in _EXIT_COMMANDS:
        return control

    print(
        "Konoha: Capturando la misión. "
        "Terminá con una línea exacta ':fin' o cancelá con ':cancelar'."
    )
    mission_text, cancelled = _TERMINAL_INPUT.read_block_until(
        prompt="...> ",
        continuation_prompt="...> ",
        first_line=first_line,
        terminator=":fin",
        cancel_token=":cancelar",
    )
    if cancelled:
        print(
            "Hokage: Captura de misión cancelada. "
            "No se envió ninguna misión."
        )
        return ""
    return mission_text or ""


def _read_decision(prompt: str = "Vos> ") -> str | None:
    """Read one simple decision line (a control word, not free-form
    content) through the single-owner terminal reader.

    Kept compatible with the existing approval protocol contract and
    tests.
    """
    return _TERMINAL_INPUT.read_line(prompt)


def classify_approval(text: str | None) -> str:
    if text is None or not text.strip():
        return "pending"
    normalized = text.strip().lower()
    if normalized in AMBIGUOUS_APPROVAL_WORDS:
        return "pending"
    if normalized in APPROVE_WORDS:
        return "approved"
    if normalized in REJECT_WORDS:
        return "rejected"
    return "changes_requested"

def _yes(text: str) -> bool:
    return classify_approval(text) == "approved"







_SESSION_EXIT = object()
_EXIT_COMMANDS = {
    "salir",
    "exit",
    "quit",
    "q",
    ":salir",
}




def _read_feedback_from_first_line(
    first_line: str,
) -> tuple[str | None, bool]:
    print(
        "Hokage: Capturando cambios. "
        "Terminá con una línea exacta ':fin' o cancelá con ':cancelar'."
    )
    return _TERMINAL_INPUT.read_block_until(
        prompt="...> ",
        continuation_prompt="...> ",
        first_line=first_line,
        terminator=":fin",
        cancel_token=":cancelar",
    )


def _read_approval_input(
    prompt: str = "Vos> ",
) -> tuple[str, str | None]:
    """Read a deterministic approval command or line-framed feedback.

    Uses read_exact_line (not read_line) so a first line that turns out to
    be free-form feedback content - falling through to
    _read_feedback_from_first_line below - is never pre-stripped before we
    even know it is content rather than a control word. Control words are
    matched against a separately normalized copy; the text passed onward
    as feedback content is never mutated."""
    text = _TERMINAL_INPUT.read_exact_line(prompt)
    if text is None or not text.strip():
        return "pending", None

    normalized = text.strip().casefold()

    if normalized in _EXIT_COMMANDS:
        return "exit", None

    if normalized in {"sí", "si", "no"}:
        return "decision", text.strip()

    if normalized == "cambios":
        feedback, cancelled = _read_feedback_block()
        if cancelled:
            return "cancelled", None
        if feedback is None:
            return "pending", None
        return "feedback", feedback

    if normalized.startswith("cambio:"):
        feedback = text.split(":", 1)[1].strip()
        if not feedback:
            return "pending", None
        return "feedback", feedback

    feedback, cancelled = _read_feedback_from_first_line(text)
    if cancelled:
        return "cancelled", None
    if feedback is None:
        return "pending", None
    return "feedback", feedback




def _read_feedback_block() -> tuple[str | None, bool]:
    print(
        "Hokage: Modo de cambios multilínea. "
        "Terminá con una línea exacta ':fin' o cancelá con ':cancelar'."
    )
    return _TERMINAL_INPUT.read_block_until(
        prompt="Cambios> ",
        continuation_prompt="...> ",
        terminator=":fin",
        cancel_token=":cancelar",
    )


def _confirm_feedback(feedback: str) -> bool:
    """Fresh-challenge confirmation. The nonce is generated only after the
    requested-change block has already been fully consumed through its
    exact ':fin' terminator, so bytes typed or pasted before that
    terminator - including any trailing content in the same paste - cannot
    satisfy a challenge that did not exist yet when they were produced.
    Only the exact freshly-generated command confirms; anything else
    (blank, EOF, "sí" alone, a stale command) leaves the plan pending,
    exactly like today's decline path."""
    print("Hokage: Interpreté este texto como cambios solicitados:")
    print("---")
    print(feedback)
    print("---")

    nonce = secrets.token_hex(16)
    expected = f":confirmar-cambios {nonce}"
    print("Hokage: Para confirmar este replanning pegá exactamente:")
    print(expected)
    response = _TERMINAL_INPUT.read_exact_line(
        "Vos> "
    )
    return response == expected


def _read_plan_challenge_grant(
    *, command_verb: str, grant_label: str, mission_id: str, plan,
) -> bool:
    """Fresh-challenge plan-authority grant, shared by every flow that
    grants authority over a specific plan revision: normal plan approval,
    plan-only acceptance, and resumed pending-plan approval. The challenge
    is generated only after the human's prior intention line (e.g. "sí")
    was already read - so pre-buffered/type-ahead bytes typed before this
    specific challenge existed can never satisfy it - and is bound to
    plan_identity(plan), the same canonical plan-drift identity
    executor.py already uses for assignment-approval binding, so a stale
    command for a previous plan revision can never authorize a replanned
    or reloaded one. command_verb/grant_label vary only the wording, never
    the mechanism, so plan-only acceptance can use wording that cannot be
    confused with execution approval."""
    expected = (
        f":{command_verb} {mission_id} {plan_identity(plan)} "
        f"{secrets.token_hex(16)}"
    )
    print(f"Hokage: Para {grant_label} pegá exactamente:")
    print(expected)
    return _TERMINAL_INPUT.read_exact_line("Vos> ") == expected


def _persist_plan(path: Path, plan) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(plan), ensure_ascii=False, indent=2), encoding="utf-8")


def _approval_loop(
    repo: Path,
    state_dir: Path,
    mission_text: str,
    plan,
    registry: CapabilityRegistry,
    *,
    provider_readiness: dict[str, dict] | None = None,
    plan_only: bool = False,
):
    continuity = MissionContinuityStore.create(
        state_dir,
        plan.mission_id,
        mission_text,
        _repo_state(repo),
    )
    continuity.record_plan(
        plan,
        reason="initial_pending_approval",
    )

    def render_current_plan() -> None:
        print("\nCodex:")
        print(approval_summary(plan))

    render_current_plan()

    while True:
        input_kind, decision_text = _read_approval_input("Vos> ")

        if input_kind == "exit":
            print(
                "Konoha: Solicitud de salida recibida. "
                "No se registró feedback ni se invocó ningún provider."
            )
            return _SESSION_EXIT

        if input_kind == "cancelled":
            print(
                "Hokage: Captura de cambios cancelada. "
                "El mismo plan continúa pendiente y no se invocó ningún provider."
            )
            continue

        if input_kind == "feedback":
            decision = "changes_requested"
        elif input_kind == "pending":
            decision = "pending"
        else:
            decision = classify_approval(decision_text)

        if decision == "pending":
            print(
                "Hokage: El plan sigue pendiente. "
                "No se ejecutó ninguna herramienta."
            )
            print(
                'Hokage: Respondé “sí”, “no”, “salir”, '
                '“cambio: <texto>” para una línea o pegá cambios '
                'terminados con una línea exacta “:fin”.'
            )
            continue

        if decision == "rejected":
            plan.approval.update(
                {
                    "status": "rejected",
                    "approved_by": None,
                    "approved_at": None,
                    "feedback": None,
                }
            )
            continuity.record_approval("rejected")
            print(
                "Hokage: Plan rechazado explícitamente. "
                "No se ejecutó ninguna herramienta."
            )
            return None

        if decision == "changes_requested":
            assert decision_text is not None
            if not _confirm_feedback(decision_text):
                print(
                    "Hokage: Replanning cancelado. "
                    "El mismo plan continúa pendiente y no se invocó ningún provider."
                )
                continue

            plan.approval.update(
                {
                    "status": "changes_requested",
                    "approved_by": None,
                    "approved_at": None,
                    "feedback": decision_text,
                }
            )
            continuity.record_requested_change(decision_text, plan)
            old_id = plan.plan_hash
            _persist_plan(
                state_dir
                / "missions"
                / plan.mission_id
                / f"plan-{old_id}-changes-requested.json",
                plan,
            )
            print(
                "Codex: Cambios confirmados. "
                "Replanificando; el nuevo plan requerirá aprobación."
            )
            # v4.1.1: human-requested replanning runs the SAME bounded
            # build/validate/deterministic-corrective-retry engine as
            # initial planning (_build_validated_plan). Invariants held here:
            #   - MAX_PLAN_ATTEMPTS stays the hard bound.
            #   - mission_authority_texts stays [original mission] + the
            #     confirmed requested_changes_history texts on every attempt;
            #     deterministic validator feedback is never added as
            #     authority (it only rides the requested_changes channel).
            #   - the confirmed human feedback seeds attempt 1.
            #   - continuity.validate_replanned_plan runs on every attempt.
            #   - each invalid candidate is recorded once as deterministic
            #     evidence and supplied only as ephemeral previous_plan
            #     context; it is never record_plan()'d.
            #   - only the final validated replan is record_plan()'d, with
            #     reason "human_requested_replan".
            #   - missing_context and attempt exhaustion fail closed.
            mission_authority_texts = [mission_text] + [
                item["text"]
                for item in continuity.state.requested_changes_history
            ]
            try:
                revised, problems, attempts = _build_validated_plan(
                    repo,
                    mission_text,
                    _repo_state(repo),
                    registry,
                    provider_readiness=provider_readiness,
                    mission_authority_texts=mission_authority_texts,
                    first_attempt_feedback=decision_text,
                    base_continuity=continuity.planner_context(),
                    extra_validate=continuity.validate_replanned_plan,
                    on_invalid_attempt=lambda invalid, findings: (
                        continuity.record_validator_findings(
                            findings, plan=invalid
                        )
                    ),
                )
            except Exception as exc:
                print(f"Konoha: No pude construir el plan revisado: {exc}")
                return None

            if problems:
                print("Hokage: El plan revisado fue detenido.")
                for problem in problems:
                    print(f"- {problem}")
                return None

            plan = revised
            if attempts > 1:
                print(
                    "Hokage: Codex corrigió el plan revisado tras una "
                    "validación determinística; no se ejecutó ninguna tarea."
                )
            continuity.record_plan(
                plan,
                reason="human_requested_replan",
            )
            render_current_plan()
            continue

        # decision == "approved": an explicit affirmative is intention
        # only, never authority by itself - see _read_plan_challenge_grant.
        # A pre-buffered/type-ahead "sí" typed before this specific,
        # freshly-generated, plan-identity-bound challenge existed can
        # never satisfy it, so it can never grant authority over a plan
        # the human had not actually seen yet.
        if plan_only:
            # v4.1.0 plan-only mode: an explicit affirmative here means
            # only "I accept this as the reviewed technical planning
            # artifact" - it must never mean "I approve execution". The
            # challenge wording ("aceptar-planificacion") never uses
            # execution-approval vocabulary. The plan's approval object is
            # left exactly as build_plan() produced it (status=pending,
            # approved_by=None, approved_at=None) and
            # continuity.record_approval is never called, so no execution
            # authority is ever granted or persisted. Caller (run()) is
            # responsible for the plan-only-specific acceptance message
            # and for never persisting plan.json or invoking execution in
            # this mode.
            if not _read_plan_challenge_grant(
                command_verb="aceptar-planificacion",
                grant_label=(
                    "aceptar esta planificación para revisión únicamente "
                    "(sin autoridad de ejecución)"
                ),
                mission_id=plan.mission_id,
                plan=plan,
            ):
                print(
                    "Hokage: La aceptación no se confirmó con el comando "
                    "exacto. El plan sigue pendiente."
                )
                continue
            return plan

        if not _read_plan_challenge_grant(
            command_verb="aprobar-plan",
            grant_label="aprobar este plan (autoridad de ejecución)",
            mission_id=plan.mission_id,
            plan=plan,
        ):
            print(
                "Hokage: La aprobación no se confirmó con el comando "
                "exacto. El plan sigue pendiente."
            )
            continue

        plan.approval.update(
            {
                "status": "approved",
                "approved_by": "human",
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "feedback": None,
            }
        )
        continuity.record_approval(
            "approved",
            approved_by="human",
            approved_at=plan.approval["approved_at"],
        )
        return plan


def _read_exact_command(prompt: str) -> str | None:
    """Unlike _read_decision, this never strips or normalizes (an
    unstripped logical line - see TerminalTurnReader.read_exact_line, not
    a literal byte-exact read: CRLF is still normalized and text is still
    decoded). An assignment approval command must match
    expected_approval_command exactly, so a stray leading/trailing space
    or a casing difference must not be silently forgiven. Reads through
    the single-owner terminal reader instead of raw input(), so it can
    never race a second stdin owner against bytes TerminalTurnReader
    already holds; the existing plan_identity + approval_nonce +
    expected_approval_command authority mechanism itself is unchanged."""
    return _TERMINAL_INPUT.read_exact_line(prompt)


def _resolve_pending_plan_approval(state_dir: Path, mission_id: str) -> str:
    """Reached only when execute_or_resume_plan reports
    diagnostic="plan_approval_not_satisfied" for a plan_approval-gated task.

    Reuses the exact approval-mutation shape _approval_loop already uses for
    a fresh plan (status/approved_by/approved_at/feedback) and the same
    _persist_plan write path, applied to the plan reloaded from disk - not a
    new approval mechanism, no continuity/replanning (neither applies to an
    already-persisted, in-progress mission).

    Returns one of "approved" / "paused" / "rejected" / "persist_failed" -
    never a bare bool, so the caller can tell a voluntary pause apart from
    an explicit rejection and from a failure to durably persist either
    decision. "rejected" is returned only after the rejection itself was
    durably persisted; a write failure at that point returns
    "persist_failed" instead, same as for an approval.

    _persist_plan's real, unwrapped failure surface is OSError (mkdir/
    write_text) - verified by reading its source, not assumed.
    """
    plan = load_persisted_plan(state_dir, mission_id)
    plan_path = state_dir / "missions" / mission_id / "plan.json"
    print("\nCodex:")
    print(approval_summary(plan))

    while True:
        text = _read_decision("Vos> ")
        if text is None or text.strip().casefold() in _EXIT_COMMANDS:
            print(
                f"Konoha: Aprobación de plan pendiente para {mission_id}. "
                f"Reanudá más tarde con --resume {mission_id}."
            )
            return "paused"

        decision = classify_approval(text)

        if decision == "pending":
            print("Hokage: El plan sigue pendiente. Respondé “sí”, “no” o “salir”.")
            continue

        if decision == "rejected":
            plan.approval.update(
                {"status": "rejected", "approved_by": None, "approved_at": None, "feedback": None},
            )
            try:
                _persist_plan(plan_path, plan)
            except OSError:
                print(f"Konoha: No se pudo persistir el rechazo del plan para {mission_id}.")
                return "persist_failed"
            print(f"Hokage: Plan rechazado explícitamente. La misión {mission_id} queda detenida.")
            return "rejected"

        if decision == "changes_requested":
            print(
                "Hokage: Los cambios de plan no están disponibles al reanudar una misión "
                "en ejecución; respondé “sí” o “no”."
            )
            continue

        # decision == "approved": intention only, same as in _approval_loop
        # - grants nothing until the fresh, plan-identity-bound challenge
        # is satisfied exactly, using the same shared helper.
        if not _read_plan_challenge_grant(
            command_verb="aprobar-plan",
            grant_label="aprobar este plan (autoridad de ejecución)",
            mission_id=mission_id,
            plan=plan,
        ):
            print(
                "Hokage: La aprobación no se confirmó con el comando "
                "exacto. El plan sigue pendiente."
            )
            continue

        plan.approval.update(
            {
                "status": "approved",
                "approved_by": "human",
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "feedback": None,
            }
        )
        try:
            _persist_plan(plan_path, plan)
        except OSError:
            print(f"Konoha: No se pudo persistir la aprobación del plan para {mission_id}.")
            return "persist_failed"
        print("Codex: Plan aprobado. Continuando la ejecución.")
        return "approved"


def _run_resumable_execution(
    repo: Path, state_dir: Path, mission_id: str, registry: CapabilityRegistry,
) -> str:
    """Drives execute_or_resume_plan to completion or to a pause point from
    an interactive terminal - no daemon, no background thread, no server.

    Each execute_or_resume_plan call resolves at most one gate or runs at
    most one assignment; this loop hides that mechanic from the operator by
    calling it repeatedly until a terminal status (completed/failed/
    blocked/recovery_required) or an unresolved pause
    (waiting_for_approval without input, or a plan pending approval) is
    reached.

    Returns exactly one of "completed" / "paused" / "failed" - never a bare
    int - so callers (run(), resume_mission()) can tell a voluntary pause
    apart from a real completion apart from a terminal/security failure,
    instead of collapsing all three into the same exit code.
    """
    print(f"Hokage: Ejecutando la misión {mission_id}; se detendrá ante cualquier desviación o gate pendiente.")
    pending_approval: AssignmentApproval | None = None

    while True:
        attempt = execute_or_resume_plan(repo, state_dir, mission_id, registry, approval=pending_approval)
        pending_approval = None

        if attempt.state is None:
            print(f"Konoha: No se pudo operar sobre la misión {mission_id} ({attempt.diagnostic}).")
            return "failed"

        if attempt.diagnostic == "lock_release_error" or attempt.diagnostic.endswith("_persist_failed"):
            # Security/durability diagnostics always win over whatever
            # state.status happens to say - never call execute_or_resume_plan
            # again, never prompt for input, never report success, no matter
            # if state.status looks like "completed", "in_progress" or
            # "waiting_for_approval".
            print(
                f"Hokage: Misión {mission_id} detenida por un fallo de persistencia u "
                f"operación ({attempt.diagnostic}). No se reintenta automáticamente."
            )
            return "failed"

        for record in attempt.evidence:
            print(f"\n[{record.task_id} · {record.provider}/{record.model} · {record.status}]\n{record.output}")

        state = attempt.state

        if attempt.diagnostic.startswith(READINESS_DIAGNOSTIC_PREFIXES):
            # v4.0.2: a fresh operational readiness check failed for the
            # exact pending assignment's provider/model. Persisted state is
            # guaranteed unchanged by executor._readiness_diagnostic's gate
            # (no invoke, no fallback, no approval consumed, no plan/model
            # substitution) regardless of whether the pending task is
            # plan_approval-gated (state.status=="in_progress") or
            # separate_human_approval-gated (state.status=="waiting_for_approval").
            # Stop after exactly this one attempt - never loop or re-prompt
            # here - so an unattended --resume can never busy-poll a
            # provider. The approved plan/mission remain fully resumable;
            # only an explicit later --resume (after the operator fixes the
            # environment) tries again.
            print(
                f"Hokage: Misión {mission_id} no puede continuar todavía "
                f"({attempt.diagnostic}). No se invocó ningún provider ni se "
                "realizó fallback automático."
            )
            print(
                f"Konoha: El plan aprobado de la misión {mission_id} sigue vigente "
                f"y la misión permanece resumible. Reanudá con --resume {mission_id} "
                "una vez que el entorno esté listo."
            )
            return "paused"

        if state.status == "in_progress":
            if attempt.diagnostic == "plan_approval_not_satisfied":
                result = _resolve_pending_plan_approval(state_dir, mission_id)
                if result == "approved":
                    continue
                if result == "paused":
                    return "paused"
                if result == "rejected":
                    return "failed"
                print(
                    f"Hokage: Misión {mission_id} detenida (plan_approval_persist_failed). "
                    "No se reintenta automáticamente."
                )
                return "failed"
            continue

        if state.status == "waiting_for_approval":
            if attempt.diagnostic != "waiting_for_approval":
                print(f"Hokage: Aprobación rechazada ({attempt.diagnostic}). Podés reintentar.")

            expected = expected_approval_command(
                mission_id, state.pending_task_id, state.plan_identity, state.approval_nonce,
            )
            print(
                f"Hokage: Tarea {state.pending_task_id} requiere aprobación humana explícita "
                f"(gate={state.pending_execution_gate})."
            )
            print("Hokage: Pegá exactamente este comando para autorizarla, o escribí “salir” para pausar:")
            print(expected)

            text = _read_exact_command("Vos> ")
            if text is None or text in _EXIT_COMMANDS:
                print(
                    f"Konoha: Misión {mission_id} queda pausada en waiting_for_approval. "
                    f"Reanudá con --resume {mission_id}."
                )
                return "paused"

            if text != expected:
                print(
                    "Hokage: Entrada rechazada: no coincide exactamente con el comando de "
                    "aprobación. No se ejecutó nada."
                )
                continue

            pending_approval = AssignmentApproval(
                mission_id=mission_id,
                task_id=state.pending_task_id,
                execution_gate="separate_human_approval",
                plan_identity=state.plan_identity,
                approval_nonce=state.approval_nonce,
                approval_text=text,
                approval_source="interactive_terminal",
                approved_at=datetime.now(timezone.utc).isoformat(),
            )
            continue

        if state.status == "completed":
            print(f"Codex: Misión {mission_id} completada: {len(state.completed_task_ids)} tarea(s).")
            return "completed"

        # failed, blocked, recovery_required: terminal or needs a human;
        # execute_or_resume_plan never retries these automatically.
        print(
            f"Hokage: Misión {mission_id} detenida en estado {state.status} "
            f"({attempt.diagnostic}). Requiere intervención manual; no se reintenta automáticamente."
        )
        return "failed"


def resume_mission(repo: Path, mission_id: str) -> int:
    """Terminal entrypoint for --resume MISSION_ID: continues an existing
    mission's execution without opening a new planning conversation."""
    state_dir = default_state_root()
    state_dir.mkdir(parents=True, exist_ok=True)
    registry = CapabilityRegistry(repo)
    print(f"Konoha: Reanudando la misión {mission_id} sin abrir una nueva conversación.")
    result = _run_resumable_execution(repo, state_dir, mission_id, registry)
    return 0 if result in ("completed", "paused") else 1






MAX_PLAN_ATTEMPTS = 3


def _corrective_planner_context(
    mission_text: str,
    base_continuity: dict | None,
    invalid_plan,
    finding_history: list[dict],
) -> dict:
    """Build the ephemeral planner context for the next deterministic
    corrective attempt, shared by initial planning and human-requested
    replanning.

    The invalid candidate rides back only as previous_plan context - it is
    never record_plan()'d - and the accumulated deterministic findings ride
    the validator_findings_history / requested_changes channel, which is
    evidence, never authority.

    For human-requested replanning, base_continuity is the live
    continuity.planner_context(): every one of its fields (schema_version,
    mission_id, original_request, repo_baseline, requested_changes_history,
    approval, execution, provider_sessions, ...) is carried through
    unchanged. Only the two ephemeral corrective parts are updated:
    previous_plan (the immediately preceding invalid candidate) and
    validator_findings_history (the context's existing history plus this
    bounded sequence's deterministic findings). It is never flattened into
    the reduced synthetic context used by initial planning.

    For initial planning, base_continuity is None and the historical inline
    synthetic shape is reproduced exactly.
    """
    if base_continuity is None:
        return {
            "schema_version": "1.0",
            "original_request": mission_text,
            "requested_changes_history": [],
            "validator_findings_history": list(finding_history),
            "previous_plan": plan_payload(invalid_plan),
            "approval": {"status": "pending"},
        }

    context = dict(base_continuity)
    context["previous_plan"] = plan_payload(invalid_plan)
    context["validator_findings_history"] = (
        list(base_continuity.get("validator_findings_history") or [])
        + list(finding_history)
    )
    return context


def _build_validated_plan(
    repo: Path,
    mission_text: str,
    state_summary: dict,
    registry: CapabilityRegistry,
    *,
    provider_readiness: dict[str, dict] | None = None,
    mission_authority_texts: list[str] | None = None,
    first_attempt_feedback: str | None = None,
    base_continuity: dict | None = None,
    extra_validate: Callable[[object], list[str]] | None = None,
    on_invalid_attempt: Callable[[object, list[str]], None] | None = None,
) -> tuple[MissionPlan, list[str], int]:
    """Bounded build -> validate -> deterministic corrective retry engine.

    The single engine for both initial planning and human-requested
    replanning. MAX_PLAN_ATTEMPTS is the hard bound in both modes.

    Keyword-only extension points, all defaulting to today's
    initial-planning behavior:

    - mission_authority_texts: fixed for the whole call. Defaults to
      [mission_text] (initial planning). Human replanning passes
      [original mission] + confirmed requested_changes_history texts. A
      corrective retry never promotes deterministic validator feedback to
      authority - that feedback only ever rides the requested_changes
      channel (the ``feedback`` argument to build_plan).
    - provider_readiness: the one acquired snapshot, passed unchanged into
      every attempt's validate_plan.
    - first_attempt_feedback: seeds attempt 1's requested_changes (the
      confirmed human requested change, for a human replan). Corrective
      retries replace it with the deterministic validator-feedback message.
    - base_continuity: continuity.planner_context() for a human replan;
      None for initial planning. Carried through unchanged except for the
      ephemeral corrective parts - see _corrective_planner_context.
    - extra_validate: e.g. continuity.validate_replanned_plan; runs on
      every attempt, before validate_plan.
    - on_invalid_attempt: records each invalid candidate exactly once as
      deterministic evidence (including the final failing attempt on
      exhaustion or missing_context). The invalid candidate itself is only
      ever ephemeral previous_plan context, never record_plan()'d.

    missing_context and MAX_PLAN_ATTEMPTS exhaustion both fail closed.
    """
    authority = (
        list(mission_authority_texts)
        if mission_authority_texts is not None
        else [mission_text]
    )
    feedback: str | None = first_attempt_feedback
    plan: MissionPlan | None = None
    problems: list[str] = []
    finding_history: list[dict] = []
    continuity_context: dict | None = base_continuity

    for attempt in range(1, MAX_PLAN_ATTEMPTS + 1):
        plan = build_plan(
            repo,
            mission_text,
            state_summary,
            registry,
            feedback=feedback,
            continuity=continuity_context,
        )
        problems = (
            list(extra_validate(plan)) if extra_validate is not None else []
        )
        problems += validate_plan(
            plan,
            registry,
            provider_readiness=provider_readiness,
            mission_authority_texts=authority,
        )

        if not problems:
            return plan, [], attempt

        if on_invalid_attempt is not None:
            on_invalid_attempt(plan, problems)

        # No pedirle al modelo que invente una decisión, fuente o permiso humano.
        if plan.missing_context:
            return plan, problems, attempt

        if attempt >= MAX_PLAN_ATTEMPTS:
            return plan, problems, attempt

        finding_history.append({
            "attempt": attempt,
            "findings": list(problems),
        })
        continuity_context = _corrective_planner_context(
            mission_text, base_continuity, plan, finding_history,
        )
        feedback = (
            "Hokage rechazó el plan por validación determinística. "
            "Conservá la misión y corregí exclusivamente estos problemas:\n"
            + "\n".join(f"- {problem}" for problem in problems)
        )

    if plan is None:
        raise RuntimeError("No se produjo ningún plan.")

    return plan, problems, MAX_PLAN_ATTEMPTS

def run(repo: Path, *, plan_only: bool = False) -> int:
    state_dir = default_state_root()
    state_dir.mkdir(parents=True, exist_ok=True)
    registry = CapabilityRegistry(repo)
    acquired = acquire_context(repo, registry)
    (state_dir / "context_acquisition.json").write_text(
        json.dumps(acquired.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ready = [p for p, info in acquired.provider_readiness.items() if info["available"]]
    print("Konoha: Bienvenido, Eduardo. Codex conduce la misión bajo autoridad constitucional de Hokage.")
    print("Konoha: Contexto público del workspace cargado; rutas privadas y externas permanecen excluidas.")
    print("Konoha: Providers verificados localmente: " + (", ".join(ready) if ready else "ninguno"))
    print(
        "Konoha: Escribí o pegá tu misión y terminá con una línea exacta "
        "':fin' (o cancelá con ':cancelar'). El contenido se captura "
        "completo, sin importar cuántas líneas o pegados incluya, recién "
        "hasta ':fin'."
    )
    if plan_only:
        print(
            "Konoha: Modo --plan-only activo: planificación técnica supervisada. "
            "No se otorga autoridad de ejecución ni se ejecuta ninguna tarea."
        )

    while True:
        text = _read_turn()
        if text is None or text.strip().casefold() in _EXIT_COMMANDS:
            print("Konoha: Sesión suspendida. La evidencia permanece local.")
            return 0
        if not text:
            continue
        try:
            print("Konoha: Adquiriendo doctrina, políticas, familias y readiness dentro del workspace autorizado...")
            plan, problems, attempts = _build_validated_plan(
                repo,
                text,
                _repo_state(repo),
                registry,
                provider_readiness=acquired.provider_readiness,
            )
        except Exception as exc:
            print(f"Konoha: No pude construir un plan verificable: {exc}")
            continue

        if attempts > 1:
            print(
                "Hokage: Codex corrigió el plan tras una validación "
                "determinística; no se ejecutó ninguna tarea."
            )

        if problems:
            print("Hokage: El plan fue detenido.")
            for problem in problems:
                print(f"- {problem}")
            print("Hokage: Solo se requiere intervención humana para contexto realmente ausente, contradictorio o no autorizado.")
            continue

        approval_result = _approval_loop(
            repo, state_dir, text, plan, registry,
            provider_readiness=acquired.provider_readiness,
            plan_only=plan_only,
        )
        if approval_result is _SESSION_EXIT:
            print("Konoha: Sesión suspendida. La evidencia permanece local.")
            return 0
        plan = approval_result
        if plan is None:
            continue
        if plan_only:
            # v4.1.0: review acceptance only - never execution approval.
            # No executable plan.json is persisted, execute_or_resume_plan/
            # _run_resumable_execution are never called, and plan.approval
            # remains exactly as _approval_loop returned it (pending).
            print(
                "Konoha: Plan técnico aceptado para revisión únicamente.\n"
                "No se autorizó ni ejecutó ninguna tarea."
            )
            continue
        mission_dir = state_dir / "missions" / plan.mission_id
        _persist_plan(mission_dir / "plan.json", plan)
        print("Hokage: Plan aprobado explícitamente. Ejecutando el grafo autorizado; se detendrá ante cualquier desviación.")
        execution_result = _run_resumable_execution(repo, state_dir, plan.mission_id, registry)

        if execution_result == "failed":
            print(
                f"Hokage: La misión {plan.mission_id} quedó detenida por un fallo. "
                "No se ofrecen fuentes nuevas para esta misión."
            )
            continue

        if execution_result == "paused":
            print(
                f"Konoha: La misión {plan.mission_id} quedó pausada; podés reanudarla con "
                f"--resume {plan.mission_id}."
            )
            continue
