from __future__ import annotations
import json, os, select, subprocess, sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from .context_acquisition import acquire_context
from .executor import execute_plan
from .hokage import approval_summary, validate_plan
from .planner import build_plan
from .registry import CapabilityRegistry
from .source_monitor import start_scan

APPROVE_WORDS = {"si", "sí", "s", "ok", "dale", "aprobar", "apruebo", "aprobado", "continuar", "proceed", "yes"}
REJECT_WORDS = {"no", "rechazar", "rechazo", "cancel", "cancelar", "stop", "detener"}

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
    """Read one intentional turn; queued pasted lines belong to that same turn."""
    try:
        first = input(prompt)
    except EOFError:
        return None
    lines = [first]
    while True:
        ready, _, _ = select.select([sys.stdin], [], [], 0.10)
        if not ready:
            break
        nxt = sys.stdin.readline()
        if nxt == "":
            break
        lines.append(nxt.rstrip("\r\n"))
    return "\n".join(lines).strip()

def _read_decision(prompt: str = "Vos> ") -> str | None:
    """Approval input is a fresh line. Blank/whitespace remains pending."""
    try:
        return input(prompt).strip()
    except EOFError:
        return None

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

def _persist_plan(path: Path, plan) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(plan), ensure_ascii=False, indent=2), encoding="utf-8")

def _approval_loop(repo: Path, state_dir: Path, mission_text: str, plan,
                   registry: CapabilityRegistry):
    while True:
        print("\nCodex:")
        print(approval_summary(plan))
        decision_text = _read_decision("Vos> ")
        decision = classify_approval(decision_text)
        if decision == "pending":
            print('Hokage: El plan sigue pendiente. No se ejecutó ninguna herramienta.')
            print('Hokage: Respondé “sí”, “no” o indicá cambios.')
            continue
        if decision == "rejected":
            plan.approval.update({
                "status": "rejected", "approved_by": None,
                "approved_at": None, "feedback": None,
            })
            print("Hokage: Plan rechazado explícitamente. No se ejecutó ninguna herramienta.")
            return None
        if decision == "changes_requested":
            plan.approval.update({
                "status": "changes_requested", "approved_by": None,
                "approved_at": None, "feedback": decision_text,
            })
            old_id = plan.plan_hash
            _persist_plan(
                state_dir / "missions" / plan.mission_id / f"plan-{old_id}-changes-requested.json",
                plan,
            )
            print("Codex: Cambios recibidos. Replanificando; el nuevo plan requerirá aprobación.")
            try:
                plan = build_plan(repo, mission_text, _repo_state(repo), registry, feedback=decision_text)
            except Exception as exc:
                print(f"Konoha: No pude construir el plan revisado: {exc}")
                return None
            problems = validate_plan(plan, registry)
            if problems:
                print("Hokage: El plan revisado fue detenido.")
                for problem in problems:
                    print(f"- {problem}")
                return None
            continue
        plan.approval.update({
            "status": "approved", "approved_by": "human",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "feedback": None,
        })
        return plan

def run(repo: Path) -> int:
    state_dir = Path(os.environ.get("KONOHA_STATE_ROOT", repo / "alliance/kirigakure/memory/v4"))
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
            plan = build_plan(repo, text, _repo_state(repo), registry)
        except Exception as exc:
            print(f"Konoha: No pude construir un plan verificable: {exc}")
            continue
        problems = validate_plan(plan, registry)
        if problems:
            print("Hokage: El plan fue detenido.")
            for problem in problems:
                print(f"- {problem}")
            print("Hokage: Solo se requiere intervención humana para contexto realmente ausente, contradictorio o no autorizado.")
            continue

        plan = _approval_loop(repo, state_dir, text, plan, registry)
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
