from __future__ import annotations
import json
from pathlib import Path
from .context_acquisition import acquire_context, normalize_missing_context
from .models import AgentAssignment, MissionPlan
from .provider_adapters import invoke_codex, ProviderError
from .registry import CapabilityRegistry, RegistryError
from .required_sources import ResolutionContext, SourceAvailability, resolve_all
from tools.repo_evidence.acquire_repo_evidence import RepositoryEvidencePack, bounded_evidence_view

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
10. Para tests read-only exigí aislamiento de caches, artefactos y state
    privado. La verificación Git antes/después pertenece al runtime y no
    debe delegarse a assignments ni ejecutarse con timeouts elegidos por
    el modelo.
11. mutation debe declararse siempre false: el runtime de worktree aislado
    para escritura todavía no existe en este Patch.

FIDELIDAD A RESTRICCIONES DE MISIÓN (VINCULANTE):
- La misión original tal como la escribió el humano es la autoridad de
  planificación. Sus restricciones explícitas son vinculantes.
- No expandas, relajes, optimices, reemplaces ni reinterpretes en silencio
  una restricción explícita de la misión, aunque un grafo distinto te
  parezca técnicamente preferible.
- Cuando la misión fije explícitamente alguno de los siguientes, preservalo
  exactamente en el plan: cantidad de assignments; orden/dependencias entre
  assignments; family; provider; model; el flag network; el flag mutation;
  el flag private_context; execution_gate; política de fallback; presupuesto
  de tokens por assignment; presupuesto total o de replanning.
- No agregues assignments adicionales solo porque un grafo más elaborado
  normalmente sería preferible: la cantidad y el orden que fijó la misión
  no son un piso, son el contrato.
- "Sin fallback" en la misión significa sin fallback de provider y sin
  fallback de family; no lo sustituyas por una ruta alternativa implícita.
- Un maximum_total_tokens explícito de la misión es un techo duro, nunca un
  objetivo a superar ni una estimación orientativa.
- Si una restricción explícita de la misión resulta imposible bajo el
  capability_registry o el provider_readiness realmente adquiridos, fallá
  cerrado agregando missing_context (el mecanismo existente de bloqueo);
  nunca inventes un provider, modelo, gate o presupuesto sustituto para
  igualmente producir un plan.
- requested_changes son correcciones vinculantes al plan previo, no
  sugerencias: no las descartes ni las diluyas al replanificar.
- La planificación de Codex sigue siendo evidencia/propuesta únicamente; la
  aprobación humana del plan sigue siendo obligatoria en todos los casos.

CONTRATO DE explicit_facts:
- explicit_facts captura los hechos y restricciones que la misión humana declaró explícitamente, no tu interpretación de ellos.
- Cuando la misión fije explícitamente alguna restricción estructural vinculante (cantidad/orden de assignments, family, provider, model, network, mutation, private_context, execution_gate, fallback o un presupuesto explícito), esa restricción debe quedar registrada en explicit_facts.
- No inventes hechos en explicit_facts que la misión no haya declarado.
- No debilites ni reinterpretes en silencio una restricción explícita al redactar explicit_facts: reflejala tal como la fijó la misión.
- explicit_facts es distinto de understanding: understanding es tu síntesis/paráfrasis, explicit_facts son los hechos explícitos, no tu inferencia.
- explicit_facts queda persistido como parte del MissionPlan aprobado y puede suministrarse como mission_context a los assignments autorizados durante la ejecución.

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
contexto privado sin declararlo.

CONTINUIDAD DE MISIÓN:
- mission_continuity es memoria operativa propiedad de Konoha.
- Conservá original_request, mission_id, requested_changes_history,
  validator_findings_history y las restricciones del previous_plan.
- Los cambios son acumulativos. El feedback más reciente no reemplaza cambios anteriores.
- Una sesión de provider es contexto auxiliar; nunca autoriza ejecución ni aprobación.
- No declares mission completion desde memoria, resumen o provider session.

CONTRATO DE mission_constraints (VINCULANTE):
- mission_constraints es un manifiesto estructurado de propuesta/evidencia:
  Hokage lo valida determinísticamente contra el plan y el humano lo revisa
  y aprueba; nunca es autoridad por sí mismo.
- Extraé ÚNICAMENTE restricciones estructurales explícitamente declaradas
  por el humano. No infieras, no completes, no generalices.
- No conviertas una recomendación, preferencia u optimización sugerida en
  una restricción: solo lo que el humano fijó explícitamente.
- source_text debe ser una copia VERBATIM, carácter por carácter, de un
  texto humano autorizado. Nunca la parafrasees, resumas ni traduzcas.
- Fuentes autorizadas para source_text:
  - en planificación inicial: únicamente "mission";
  - en replanificación por pedido humano confirmado: "mission" más cada
    texto de mission_continuity.requested_changes_history[].text.
  - "requested_changes" (el feedback recibido en este turno) NO es por sí
    solo una fuente autorizada: Konoha también usa ese mismo canal para
    feedback determinístico de validación durante replanificación
    correctiva automática, que nunca es autoridad humana.
- Si la misión no fijó explícitamente ninguna restricción estructural
  representable en este contrato, devolvé mission_constraints=[]. Un
  manifiesto vacío es una respuesta válida y esperada, no un error.
- Cada elemento del manifiesto tiene EXACTAMENTE estos campos, sin
  agregar ni omitir ninguno: constraint_id, source_text, scope,
  assignment_index, field, operator, value.
  - constraint_id: string no vacío, único dentro del manifiesto.
  - scope: "plan" o "assignment".
  - assignment_index: null cuando scope="plan"; cuando scope="assignment"
    es la POSICIÓN entera (>=0) del assignment dentro de plan.assignments
    tal como vos lo generaste - nunca su task_id. Esto permite representar
    determinísticamente un orden humano explícito como "Codex primero,
    Claude segundo".
  - field para scope="plan": assignment_count, maximum_total_tokens,
    replanning_reserve_tokens.
  - field para scope="assignment": task_id, family, provider, model,
    network, mutation, private_context, execution_gate, fallback,
    dependencies, estimated_input_tokens, estimated_output_tokens,
    estimated_total_tokens.
  - operator: "equals" (cualquier field) o "at_most" (solo fields
    enteros: assignment_count, maximum_total_tokens,
    replanning_reserve_tokens, estimated_input_tokens,
    estimated_output_tokens, estimated_total_tokens).
  - value: string, integer, boolean, o array de integers. Para
    dependencies, value es un array de POSICIONES de assignment (no
    task_id): Hokage resuelve esas posiciones a task_id y compara contra
    AgentAssignment.dependencies.
- No devuelvas una combinación de field/operator/value que este contrato
  no soporte explícitamente; si la restricción explícita del humano no es
  representable así, preservala igual en explicit_facts y en el diseño
  del plan, pero no inventes un mission_constraints inválido.
- mission_constraints no reemplaza a explicit_facts: explicit_facts sigue
  siendo la síntesis textual de hechos/restricciones explícitas; este
  manifiesto es su forma estructurada y verificable determinísticamente
  para el subconjunto de restricciones que este contrato soporta.

Devolvé exclusivamente JSON válido conforme al schema."""

def build_plan(
 repo: Path,
 mission_text: str,
 state_summary: dict,
 registry: CapabilityRegistry,
 feedback: str | None = None,
 continuity: dict | None = None,
 repo_evidence: RepositoryEvidencePack | None = None,
) -> MissionPlan:
    schema = repo / "schemas" / "runtime" / "konoha_v4_mission_plan.schema.json"
    acquired = acquire_context(repo, registry)
    # bounded_evidence_view is the one materialization path for a
    # RepositoryEvidencePack (see tools/repo_evidence/acquire_repo_evidence.py) -
    # embedded here exactly as the executor later embeds it in a worker's
    # resolved_source_bundle, never a second serializer. repo_evidence is
    # purely additive: an omitted/None pack leaves existing callers/tests
    # byte-for-byte unaffected. Whether repository-backed planning may even
    # proceed without a pack is decided by the caller (conversation.py),
    # never here - see _acquire_repo_evidence_for_planning.
    context = {
        "mission": mission_text,
        "requested_changes": feedback,
        "mission_continuity": continuity,
        "repository_state": state_summary,
        "repository_evidence": bounded_evidence_view(repo_evidence) if repo_evidence is not None else None,
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

    # Deterministic required_sources preview - the SAME resolve_all/
    # resolve_required_sources the executor later enforces at
    # enforcing=True, never a second/parallel resolution path (see
    # tools/konoha_v4/required_sources.py). Evaluated as though this draft
    # plan were already approved: plan approval timing is a separate,
    # already-enforced gate (hokage.validate_plan / executor's
    # plan_approval check at execution time), so the universal,
    # self-resolving "not approved yet" fact never drowns out a genuine
    # gap in plan.missing_context. A PENDING_PRODUCER with an identified
    # producer task_id is normal for a multi-step plan and is never folded
    # in here - only a genuine MISSING or UNAUTHORIZED is.
    # Skips (never raises on) an unresolvable family: hokage.validate_plan
    # already independently reports "Modelo no autorizado"/unknown-family
    # problems through its own established path immediately after
    # build_plan returns - this preview only ever evaluates the families it
    # can actually resolve, never duplicates or preempts that check.
    family_contracts: dict[str, dict] = {}
    for name in {a.family for a in assignments}:
        try:
            family_contracts[name] = registry.agent_family(name)
        except RegistryError:
            continue
    task_family_by_id = {a.task_id: a.family for a in assignments}
    preview_ctx = ResolutionContext(
        plan_approval_status="approved",
        plan_acceptance_criteria=tuple(raw["acceptance_criteria"]),
        user_mission_request=mission_text,
        repo_root=repo,
        repo_evidence_pack=repo_evidence,
        family_contracts=family_contracts,
        task_family_by_id=task_family_by_id,
        evidence_by_task_id={},
    )
    source_gaps: list[str] = []
    for task in assignments:
        required = family_contracts.get(task.family, {}).get("required_sources") or []
        for canonical_id, resolution in resolve_all(required, task, preview_ctx, enforcing=False).items():
            if resolution.availability is SourceAvailability.MISSING:
                source_gaps.append(
                    f"{task.task_id}: required_sources '{canonical_id}' missing ({resolution.reason})."
                )
            elif resolution.availability is SourceAvailability.UNAUTHORIZED:
                source_gaps.append(
                    f"{task.task_id}: required_sources '{canonical_id}' unauthorized ({resolution.reason})."
                )
    raw["missing_context"] = raw["missing_context"] + source_gaps

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
        mission_constraints=raw["mission_constraints"],
    ).seal()
