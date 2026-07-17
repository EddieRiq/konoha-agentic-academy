from __future__ import annotations
from .models import MissionPlan
from .registry import CapabilityRegistry, RegistryError

class ConstitutionalViolation(RuntimeError):
    pass

def validate_plan(plan: MissionPlan, registry: CapabilityRegistry) -> list[str]:
    problems: list[str] = []
    if plan.missing_context:
        problems.append("Falta contexto explícito: " + "; ".join(plan.missing_context))
    if plan.governance != {"conductor": "codex", "constitutional_authority": "hokage"}:
        problems.append("Gobernanza inválida: Codex debe conducir y Hokage debe ser autoridad constitucional separada.")
    if plan.teachback_policy not in {"disabled", "optional", "required"}:
        problems.append("teachback_policy inválida.")
    if plan.teachback_policy == "required" and not any(
        token in plan.rationale.lower() for token in ("formación", "training", "constitucional", "safety contract", "solicitud explícita")
    ):
        problems.append("Teachback requerido sin justificación explícita.")
    if plan.workspace_policy.get("workspace_mutation_allowed") is not False:
        problems.append("El workspace auditado debe permanecer read-only.")
    if not plan.workspace_policy.get("private_runtime_state_allowed", False):
        problems.append("El plan debe distinguir persistencia privada de mutación del workspace.")
    if plan.approval.get("status") != "pending":
        problems.append("Todo plan nuevo debe iniciar con aprobación pending.")

    seen: set[str] = set()
    provider_totals: dict[str, int] = {}
    family_totals: dict[str, int] = {}
    task_total = 0
    for a in plan.assignments:
        if a.task_id in seen:
            problems.append(f"task_id duplicado: {a.task_id}")
        seen.add(a.task_id)
        if a.family == "mission-conductor" and "hokage" in (a.task_id + " " + a.objective).lower():
            problems.append(f"{a.task_id} mezcla Hokage con una tarea operativa de Codex.")
        try:
            family = registry.agent_family(a.family)
        except RegistryError as exc:
            problems.append(str(exc))
            continue
        if not registry.model_allowed(a.provider, a.model, a.family):
            problems.append(f"Modelo no autorizado: {a.provider}/{a.model} para {a.family}")
        if a.mutation and "mutation" not in plan.approval_boundaries:
            problems.append(f"{a.task_id} muta sin boundary mutation")
        if a.network and "network" not in plan.approval_boundaries:
            problems.append(f"{a.task_id} usa red sin boundary network")
        if a.private_context and "private_context" not in plan.approval_boundaries:
            problems.append(f"{a.task_id} usa contexto privado sin boundary private_context")
        if not family.get("allowed_task_patterns"):
            problems.append(f"Familia sin allowed_task_patterns: {a.family}")
        if a.estimated_total_tokens != a.estimated_input_tokens + a.estimated_output_tokens:
            problems.append(f"Presupuesto inconsistente en {a.task_id}.")
        if a.estimated_total_tokens < 0:
            problems.append(f"Presupuesto negativo en {a.task_id}.")
        task_total += a.estimated_total_tokens
        provider_totals[a.provider] = provider_totals.get(a.provider, 0) + a.estimated_total_tokens
        family_totals[a.family] = family_totals.get(a.family, 0) + a.estimated_total_tokens

    reserve = int(plan.budget.get("replanning_reserve_tokens", 0))
    maximum = int(plan.budget.get("maximum_total_tokens", 0))
    if plan.budget.get("provider_totals") != provider_totals:
        problems.append("budget.provider_totals no coincide con las tareas.")
    if plan.budget.get("family_totals") != family_totals:
        problems.append("budget.family_totals no coincide con las tareas.")
    if maximum != task_total + reserve:
        problems.append("budget.maximum_total_tokens debe ser tareas + reserva.")
    if plan.estimated_tokens != maximum:
        problems.append("estimated_tokens debe coincidir con budget.maximum_total_tokens.")
    return problems

def approval_summary(plan: MissionPlan) -> str:
    lines = [
        f"Entendí: {plan.understanding}",
        f"Complejidad: {plan.complexity}",
        f"Plan preparado: {plan.plan_hash}",
        "",
        "Conductor:",
        "- Codex",
        "Autoridad constitucional:",
        "- Hokage",
        "",
        "Agentes propuestos:",
    ]
    for a in plan.assignments:
        flags = ", ".join(k for k,v in {
            "privado": a.private_context, "red": a.network, "mutación": a.mutation
        }.items() if v) or "solo lectura/local"
        lines.append(f"- {a.task_id}: {a.family} → {a.provider}/{a.model} ({flags})")
        lines.append(f"  {a.objective}")
        lines.append(
            f"  Presupuesto: {a.estimated_input_tokens} input + "
            f"{a.estimated_output_tokens} output = {a.estimated_total_tokens}; "
            f"clase {a.cost_class}; fallback: {a.fallback}"
        )
    lines += ["", "Presupuesto por provider:"]
    for provider, total in sorted(plan.budget.get("provider_totals", {}).items()):
        lines.append(f"- {provider}: {total} tokens")
    lines += [
        f"- Reserva de replanning: {plan.budget.get('replanning_reserve_tokens', 0)} tokens",
        f"- Máximo: {plan.budget.get('maximum_total_tokens', 0)} tokens",
        "",
        f"Teachback: {plan.teachback_policy}",
        "",
        "Mutaciones:",
        "- workspace: prohibidas",
        "- state root privado: permitido",
        "",
        "Criterios de aceptación:",
        *[f"- {x}" for x in plan.acceptance_criteria],
        "",
        "Hokage: El plan está constitucionalmente validado y pendiente de aprobación humana.",
        "¿Aprobás el plan?",
        '- “sí” para aprobar;',
        '- “no” para rechazar;',
        "- o escribí los cambios requeridos.",
    ]
    return "\n".join(lines)
