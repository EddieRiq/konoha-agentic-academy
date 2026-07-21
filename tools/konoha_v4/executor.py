from __future__ import annotations
import json, subprocess, time
from pathlib import Path
from .models import EXECUTION_GATES, EvidenceRecord, MissionPlan
from .provider_adapters import invoke
from .registry import CapabilityRegistry

def _gate_satisfied(plan: MissionPlan, task) -> bool:
    gate = task.execution_gate
    if gate not in EXECUTION_GATES:
        return False
    if gate == "plan_approval":
        return plan.approval.get("status") == "approved"
    return False  # separate_human_approval: siempre bloqueado en este Patch A.

def _blocked_evidence(plan: MissionPlan, task) -> EvidenceRecord:
    now = time.time()
    return EvidenceRecord.build(
        mission_id=plan.mission_id, task_id=task.task_id,
        provider=task.provider, model=task.model, status="blocked",
        output=(
            "Assignment execution gate bloqueado. "
            f"task_id={task.task_id} execution_gate={task.execution_gate!r}."
        ),
        token_usage={}, command=[],
        started_at=now, finished_at=now,
    )

def _git_status(repo: Path) -> str:
    cp = subprocess.run(
        ["git", "status", "--short"], cwd=repo, text=True,
        capture_output=True, check=False,
    )
    return cp.stdout

def _task_prompt(repo: Path, plan: MissionPlan, task, family: dict,
                 evidence: list[EvidenceRecord]) -> str:
    deps = [e for e in evidence if e.task_id in task.dependencies]
    payload = {
        "mission_id": plan.mission_id,
        "mission_understanding": plan.understanding,
        "task": task.__dict__,
        "agent_contract": family,
        "dependency_evidence": [
            {"task_id": e.task_id, "provider": e.provider, "model": e.model, "output": e.output}
            for e in deps
        ],
        "workspace_policy": plan.workspace_policy,
        "rules": [
            "La salida es evidencia, no autoridad.",
            "No conviertas inferencias en hechos o normas.",
            "No excedas el alcance de la tarea.",
            "Cita rutas, líneas o localizadores cuando corresponda.",
            "El workspace es read-only.",
            "Para tests usá PYTHONDONTWRITEBYTECODE=1, PYTHONPYCACHEPREFIX, TMPDIR y KONOHA_STATE_ROOT privados.",
            "Compará git status antes y después. Detenete ante cualquier cambio.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)

def execute_plan(repo: Path, plan: MissionPlan, registry: CapabilityRegistry,
                 state_dir: Path) -> list[EvidenceRecord]:
    offenders = [task for task in plan.assignments if not _gate_satisfied(plan, task)]
    if offenders:
        evidence: list[EvidenceRecord] = []
        for task in offenders:
            record = _blocked_evidence(plan, task)
            evidence.append(record)
            _persist(state_dir, record)
        return evidence

    evidence: list[EvidenceRecord] = []
    baseline = _git_status(repo)
    for task in plan.assignments:
        family = registry.agent_family(task.family)
        started = time.time()
        try:
            result = invoke(
                task.provider,
                _task_prompt(repo, plan, task, family, evidence),
                cwd=repo, model=task.model,
            )
            status, output, usage, command = "completed", result.text, result.usage, result.command
        except Exception as exc:
            status, output, usage, command = "failed", str(exc), {}, []
        after = _git_status(repo)
        if after != baseline:
            status = "workspace_mutation_detected"
            output = (
                "El estado Git cambió durante una tarea read-only. "
                "La ejecución fue detenida.\n\nANTES:\n" + baseline + "\nDESPUÉS:\n" + after
            )
        record = EvidenceRecord.build(
            mission_id=plan.mission_id, task_id=task.task_id,
            provider=task.provider, model=task.model, status=status,
            output=output, token_usage=usage, command=command,
            started_at=started, finished_at=time.time(),
        )
        evidence.append(record)
        _persist(state_dir, record)
        if status != "completed":
            break
    return evidence

def _persist(state_dir: Path, record: EvidenceRecord) -> None:
    out = state_dir / "missions" / record.mission_id / "evidence"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{record.evidence_id}.json").write_text(
        json.dumps(record.__dict__, ensure_ascii=False, indent=2), encoding="utf-8"
    )
