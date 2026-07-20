from __future__ import annotations
import json
from pathlib import Path
from .context_acquisition import acquire_context, normalize_missing_context
from .models import AgentAssignment, MissionPlan
from .provider_adapters import invoke_codex, ProviderError
from .registry import CapabilityRegistry

SYSTEM = """Sos Codex Mission Conductor de Konoha. Recibís la misión completa y diseñás
un grafo de agentes especializados. Hokage es autoridad constitucional separada:
no lo representes como tarea, agente delegado ni assignment.

ORDEN OBLIGATORIO:
1. Usá primero el contexto local adquirido dentro del workspace autorizado.
2. Tratá context_not_loaded como trabajo local pendiente, nunca como pedido al usuario.
3. Verificá providers mediante provider_readiness; no preguntes si existen.
4. Usá las familias registradas; Jounin es una familia formal.
5. Usá la política read-only cargada; no pidas una allowlist al usuario.
6. Solo agregá missing_context ante una decisión humana, fuente inexistente,
   autorización nueva o contradicción irresoluble.
7. Teachback queda disabled salvo solicitud o política explícita.
8. Distinguí cero mutaciones del workspace de persistencia en state privado.
9. Desglosá presupuesto por assignment, provider y familia. No uses una cifra global
   sin desglose. estimated_total_tokens debe ser input + output.
10. Para tests read-only exigí aislamiento y comparación de git status antes/después.

GOVERNANCE FIJA:
{"conductor":"codex","constitutional_authority":"hokage"}

SEPARACIÓN CONSTITUCIONAL:
- Ningún assignment representa, ejecuta, simula ni delega a Hokage.
- No incluyas "Hokage" en task_id ni objective de una tarea mission-conductor.
- Un mission-conductor puede sintetizar evidencia y preparar un handoff neutral,
  pero no puede aprobar, autorizar ni emitir una decisión constitucional.
- La validación y aprobación constitucional ocurren fuera del grafo operativo.

CONSISTENCIA PRESUPUESTARIA OBLIGATORIA:
- estimated_total_tokens de cada assignment = input + output.
- provider_totals debe sumar exactamente los assignments por provider.
- family_totals debe sumar exactamente los assignments por family.
- maximum_total_tokens = suma de assignments + replanning_reserve_tokens.
- estimated_tokens = maximum_total_tokens.

WORKSPACE POLICY FIJA:
workspace_mutation_allowed=false; private_runtime_state_allowed=true.

APPROVAL INICIAL:
status=pending; approved_by=null; approved_at=null; feedback=null.

REPLANIFICACIÓN:
Si requested_changes no es null, el plan anterior fue rechazado por validación
determinística de Hokage. Conservá la misión original, los límites y los gates.
Corregí exclusivamente los problemas informados. No inventes contexto, permisos,
familias, modelos ni evidencia. Devolvé siempre el plan completo corregido.

No conviertas inferencias en hechos, reglas ni permisos. No propongas red, mutación o
contexto privado sin declararlo. Devolvé exclusivamente JSON válido conforme al schema."""

def build_plan(repo: Path, mission_text: str, state_summary: dict,
               registry: CapabilityRegistry, feedback: str | None = None) -> MissionPlan:
    schema = repo / "schemas" / "runtime" / "konoha_v4_mission_plan.schema.json"
    acquired = acquire_context(repo, registry)
    context = {
        "mission": mission_text,
        "requested_changes": feedback,
        "repository_state": state_summary,
        "acquired_context": acquired.as_dict(),
        "available_agent_families": registry.available_families(),
        "capability_registry": registry.data,
        "missing_context_contract": {
            "context_not_loaded": "resolve locally before planning",
            "provider_unknown": "run deterministic readiness probe",
            "workspace_read": "current Git workspace is authorized for read-only inspection",
            "private_paths": "excluded unless separately approved",
            "user_input_required": "only genuine human decision, unavailable source or new permission",
        },
    }
    result = invoke_codex(
        SYSTEM + "\n\nCONTEXTO ESTRUCTURADO:\n" +
        json.dumps(context, ensure_ascii=False, indent=2),
        cwd=repo, schema=schema,
    )
    try:
        raw = json.loads(result.text)
    except json.JSONDecodeError as exc:
        raise ProviderError("Codex no devolvió un plan JSON válido.") from exc

    user_missing, locally_resolved = normalize_missing_context(
        raw.get("missing_context", []), acquired
    )
    raw["missing_context"] = user_missing
    if locally_resolved:
        raw.setdefault("explicit_facts", []).append(
            "Contexto resuelto localmente antes del plan: " + " | ".join(locally_resolved)
        )

    assignments = [AgentAssignment(**item) for item in raw["assignments"]]
    return MissionPlan(
        mission_id=raw["mission_id"],
        understanding=raw["understanding"],
        explicit_facts=raw["explicit_facts"],
        missing_context=raw["missing_context"],
        assumptions_prohibited=raw["assumptions_prohibited"],
        complexity=raw["complexity"],
        assignments=assignments,
        acceptance_criteria=raw["acceptance_criteria"],
        approval_boundaries=raw["approval_boundaries"],
        estimated_tokens=raw["estimated_tokens"],
        estimated_cost_class=raw["estimated_cost_class"],
        rationale=raw["rationale"],
        approval=raw["approval"],
        teachback_policy=raw["teachback_policy"],
        workspace_policy=raw["workspace_policy"],
        budget=raw["budget"],
        governance=raw["governance"],
    ).seal()
