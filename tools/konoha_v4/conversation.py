from __future__ import annotations
import json, os, select, subprocess, sys
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
from .executor import execute_or_resume_plan, expected_approval_command, load_persisted_plan
from .hokage import approval_summary, validate_plan
from .models import AssignmentApproval
from .planner import build_plan
from .registry import CapabilityRegistry

APPROVE_WORDS = {"si", "sí", "s", "ok", "dale", "aprobar", "apruebo", "aprobado", "continuar", "proceed", "yes"}
REJECT_WORDS = {"no", "rechazar", "rechazo", "cancel", "cancelar", "stop", "detener"}

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
    return _TERMINAL_INPUT.read_turn(prompt)




def _read_decision(prompt: str = "Vos> ") -> str | None:
    """Read one simple decision line.

    Kept compatible with the existing approval protocol contract and tests.
    Fresh feedback confirmation uses _read_fresh_decision instead.
    """
    try:
        return input(prompt).strip()
    except EOFError:
        return None


def _read_fresh_decision(
    prompt: str,
) -> tuple[str | None, list[str]]:
    return _TERMINAL_INPUT.read_fresh_line(prompt)



def classify_approval(text: str | None) -> str:
    if text is None or not text.strip():
        return "pending"
    normalized = text.strip().lower()
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
    """Read a deterministic approval command or line-framed feedback."""
    text = _TERMINAL_INPUT.read_line(prompt)
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
    print("Hokage: Interpreté este texto como cambios solicitados:")
    print("---")
    print(feedback)
    print("---")

    confirmation, discarded = _read_fresh_decision(
        "¿Confirmás que querés replanificar? [sí/no]> "
    )
    if discarded:
        print(
            "Hokage: Ignoré "
            f"{len(discarded)} línea(s) residual(es); "
            "la confirmación debe ser una entrada nueva."
        )
    return classify_approval(confirmation) == "approved"




def _persist_plan(path: Path, plan) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(plan), ensure_ascii=False, indent=2), encoding="utf-8")


def _approval_loop(
    repo: Path,
    state_dir: Path,
    mission_text: str,
    plan,
    registry: CapabilityRegistry,
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
            try:
                plan = build_plan(
                    repo,
                    mission_text,
                    _repo_state(repo),
                    registry,
                    feedback=decision_text,
                    continuity=continuity.planner_context(),
                )
            except Exception as exc:
                print(f"Konoha: No pude construir el plan revisado: {exc}")
                return None

            problems = (
                continuity.validate_replanned_plan(plan)
                + validate_plan(plan, registry)
            )
            if problems:
                continuity.record_validator_findings(problems, plan=plan)
                print("Hokage: El plan revisado fue detenido.")
                for problem in problems:
                    print(f"- {problem}")
                return None

            continuity.record_plan(
                plan,
                reason="human_requested_replan",
            )
            render_current_plan()
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
    """Unlike _read_decision, this never strips or normalizes. An
    assignment approval command must match expected_approval_command
    byte-for-byte, so a stray leading/trailing space or a casing
    difference must not be silently forgiven."""
    try:
        return input(prompt)
    except EOFError:
        return None


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


def _build_validated_plan(
    repo: Path,
    mission_text: str,
    state_summary: dict,
    registry: CapabilityRegistry,
) -> tuple[MissionPlan, list[str], int]:
    feedback: str | None = None
    plan: MissionPlan | None = None
    problems: list[str] = []
    finding_history: list[dict] = []
    continuity_context: dict | None = None

    for attempt in range(1, MAX_PLAN_ATTEMPTS + 1):
        plan = build_plan(
            repo,
            mission_text,
            state_summary,
            registry,
            feedback=feedback,
         continuity=continuity_context,
        )
        problems = validate_plan(plan, registry)

        if not problems:
            return plan, [], attempt

        # No pedirle al modelo que invente una decisión, fuente o permiso humano.
        if plan.missing_context:
            return plan, problems, attempt

        if attempt >= MAX_PLAN_ATTEMPTS:
            return plan, problems, attempt

        finding_history.append({
         "attempt": attempt,
         "findings": list(problems),
        })
        continuity_context = {
         "schema_version": "1.0",
         "original_request": mission_text,
         "requested_changes_history": [],
         "validator_findings_history": list(finding_history),
         "previous_plan": plan_payload(plan),
         "approval": {"status": "pending"},
        }
        feedback = (
            "Hokage rechazó el plan por validación determinística. "
            "Conservá la misión y corregí exclusivamente estos problemas:\n"
            + "\n".join(f"- {problem}" for problem in problems)
        )

    if plan is None:
        raise RuntimeError("No se produjo ningún plan.")

    return plan, problems, MAX_PLAN_ATTEMPTS

def run(repo: Path) -> int:
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
    print("Konoha: Podés escribir o pegar la misión completa; el pegado multilínea se agrupa en un solo turno.")

    while True:
        text = _read_turn()
        if text is None or text.lower() in {"salir", "exit", "quit"}:
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

        approval_result = _approval_loop(repo, state_dir, text, plan, registry)
        if approval_result is _SESSION_EXIT:
            print("Konoha: Sesión suspendida. La evidencia permanece local.")
            return 0
        plan = approval_result
        if plan is None:
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
