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
from .executor import execute_plan
from .hokage import approval_summary, validate_plan
from .planner import build_plan
from .registry import CapabilityRegistry
from .source_monitor import start_scan

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
    source_result: dict = {}
    start_scan(
        state_dir / "source_policy.json", state_dir,
        lambda result: source_result.update(result),
    )
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
        evidence = execute_plan(repo, plan, registry, state_dir)
        completed = sum(e.status == "completed" for e in evidence)
        failed = [e for e in evidence if e.status != "completed"]
        print(f"Codex: Ejecución terminada: {completed}/{len(plan.assignments)} tareas completadas.")
        for e in evidence:
            print(f"\n[{e.task_id} · {e.provider}/{e.model} · {e.status}]\n{e.output}")
        if failed:
            print("\nHokage: La misión quedó suspendida por evidencia fallida. No se improvisó.")
        if source_result.get("new_sources"):
            print(f"\nYamanaka: Detecté {len(source_result['new_sources'])} fuente(s) nuevas en rutas autorizadas.")
            print("Shikamaru puede proponer su procesamiento e incorporación a una familia, pero requiere aprobación.")
