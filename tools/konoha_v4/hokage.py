from __future__ import annotations
import json
from .models import EXECUTION_GATES, MissionPlan
from .registry import CapabilityRegistry, RegistryError

class ConstitutionalViolation(RuntimeError):
    pass


# mission_constraints (v4.0.1) field/operator metadata - see
# _validate_mission_constraints below and the schema at
# schemas/runtime/konoha_v4_mission_plan.schema.json.
_CONSTRAINT_PLAN_FIELDS = {
    "assignment_count", "maximum_total_tokens", "replanning_reserve_tokens",
}
_CONSTRAINT_ASSIGNMENT_FIELDS = {
    "task_id", "family", "provider", "model", "network", "mutation",
    "private_context", "execution_gate", "fallback", "dependencies",
    "estimated_input_tokens", "estimated_output_tokens", "estimated_total_tokens",
}
_CONSTRAINT_FIELDS = _CONSTRAINT_PLAN_FIELDS | _CONSTRAINT_ASSIGNMENT_FIELDS
_CONSTRAINT_OPERATORS = {"equals", "at_most"}
# Exactly the integer-valued fields; at_most is only ever meaningful here.
_CONSTRAINT_AT_MOST_FIELDS = {
    "assignment_count", "maximum_total_tokens", "replanning_reserve_tokens",
    "estimated_input_tokens", "estimated_output_tokens", "estimated_total_tokens",
}
_CONSTRAINT_BOOL_FIELDS = {"network", "mutation", "private_context"}
_CONSTRAINT_STR_FIELDS = {"task_id", "family", "provider", "model", "execution_gate", "fallback"}
_CONSTRAINT_LIST_INT_FIELDS = {"dependencies"}
_CONSTRAINT_EXPECTED_KEYS = {
    "constraint_id", "source_text", "scope", "assignment_index", "field", "operator", "value",
}


def _is_strict_int(value: object) -> bool:
    """True only for a real int - bool is a int subclass in Python and
    must never be silently accepted where an integer constraint value is
    expected."""
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_mission_constraints(
    plan: MissionPlan,
    mission_authority_texts: list[str] | None,
) -> list[str]:
    """Validate the v4.0.1 structured mission-constraint manifest.

    A no-op returning [] when plan.mission_constraints is None - that is
    the legacy v4.0.0 shape and carries no manifest to validate. For a
    non-None manifest ([] or populated), performs, per constraint:

      A. authority provenance - source_text must be an exact substring of
         at least one mission_authority_texts entry;
      B. shape defense - exact key set, valid/unique constraint_id, valid
         scope/field/operator/assignment_index/value, fails closed on any
         malformed manually-constructed MissionPlan even though the
         provider schema already validates provider output;
      C. structural comparison - the constraint's claimed value must
         actually match the plan it was extracted from.

    Diagnostics are stable-prefixed (mission_constraint_invalid: /
    mission_constraint_source_not_authorized: / mission_constraint_mismatch:)
    so callers/tests can match on the prefix. This function is pure
    evidence-checking: it never grants provider output authority, it only
    proves or disproves a match against the plan and against the human
    text(s) the caller supplies.
    """
    problems: list[str] = []
    constraints = plan.mission_constraints
    if constraints is None:
        return problems
    if not isinstance(constraints, list):
        problems.append(
            "mission_constraint_invalid: mission_constraints debe ser una lista."
        )
        return problems

    if mission_authority_texts is None:
        problems.append(
            "mission_constraint_source_not_authorized: no se proveyó "
            "mission_authority_texts; no se puede validar la procedencia "
            "humana de mission_constraints."
        )

    seen_ids: set[str] = set()
    assignment_count_actual = len(plan.assignments)

    for index, raw_c in enumerate(constraints):
        label = f"mission_constraints[{index}]"
        if not isinstance(raw_c, dict):
            problems.append(f"mission_constraint_invalid: {label} no es un objeto.")
            continue
        if set(raw_c) != _CONSTRAINT_EXPECTED_KEYS:
            missing = _CONSTRAINT_EXPECTED_KEYS - set(raw_c)
            unknown = set(raw_c) - _CONSTRAINT_EXPECTED_KEYS
            problems.append(
                f"mission_constraint_invalid: {label}: campos incorrectos "
                f"(faltantes={sorted(missing)} desconocidos={sorted(unknown)})."
            )
            continue

        constraint_id = raw_c["constraint_id"]
        if not isinstance(constraint_id, str) or not constraint_id.strip():
            problems.append(f"mission_constraint_invalid: {label}: constraint_id vacío o inválido.")
            continue
        if constraint_id in seen_ids:
            problems.append(f"mission_constraint_invalid: {constraint_id}: constraint_id duplicado.")
            continue
        seen_ids.add(constraint_id)

        source_text = raw_c["source_text"]
        if not isinstance(source_text, str) or not source_text:
            problems.append(f"mission_constraint_invalid: {constraint_id}: source_text vacío o inválido.")
            continue

        scope = raw_c["scope"]
        if scope not in {"plan", "assignment"}:
            problems.append(f"mission_constraint_invalid: {constraint_id}: scope inválido: {scope!r}.")
            continue

        field_name = raw_c["field"]
        if field_name not in _CONSTRAINT_FIELDS:
            problems.append(f"mission_constraint_invalid: {constraint_id}: field inválido: {field_name!r}.")
            continue

        field_scope = "plan" if field_name in _CONSTRAINT_PLAN_FIELDS else "assignment"
        if field_scope != scope:
            problems.append(
                f"mission_constraint_invalid: {constraint_id}: field {field_name!r} "
                f"no pertenece a scope {scope!r}."
            )
            continue

        assignment_index = raw_c["assignment_index"]
        assignment = None
        if scope == "plan":
            if assignment_index is not None:
                problems.append(
                    f"mission_constraint_invalid: {constraint_id}: assignment_index "
                    "debe ser null cuando scope=plan."
                )
                continue
        else:
            if (
                not _is_strict_int(assignment_index)
                or assignment_index < 0
                or assignment_index >= len(plan.assignments)
            ):
                problems.append(
                    f"mission_constraint_invalid: {constraint_id}: assignment_index "
                    f"{assignment_index!r} no resuelve a un assignment existente."
                )
                continue
            assignment = plan.assignments[assignment_index]

        operator = raw_c["operator"]
        if operator not in _CONSTRAINT_OPERATORS:
            problems.append(f"mission_constraint_invalid: {constraint_id}: operator inválido: {operator!r}.")
            continue
        if operator == "at_most" and field_name not in _CONSTRAINT_AT_MOST_FIELDS:
            problems.append(
                f"mission_constraint_invalid: {constraint_id}: operator at_most no "
                f"soportado para field {field_name!r}."
            )
            continue

        value = raw_c["value"]
        resolved_dependency_task_ids: list[str] | None = None
        if field_name in _CONSTRAINT_AT_MOST_FIELDS:
            if not _is_strict_int(value):
                problems.append(
                    f"mission_constraint_invalid: {constraint_id}: value debe ser "
                    f"integer para field {field_name!r}."
                )
                continue
        elif field_name in _CONSTRAINT_BOOL_FIELDS:
            if not isinstance(value, bool):
                problems.append(
                    f"mission_constraint_invalid: {constraint_id}: value debe ser "
                    f"boolean para field {field_name!r}."
                )
                continue
        elif field_name in _CONSTRAINT_STR_FIELDS:
            if not isinstance(value, str):
                problems.append(
                    f"mission_constraint_invalid: {constraint_id}: value debe ser "
                    f"string para field {field_name!r}."
                )
                continue
        elif field_name in _CONSTRAINT_LIST_INT_FIELDS:
            if not isinstance(value, list) or not all(_is_strict_int(v) for v in value):
                problems.append(
                    f"mission_constraint_invalid: {constraint_id}: value debe ser un "
                    f"array de integers para field {field_name!r}."
                )
                continue
            if any(v < 0 or v >= len(plan.assignments) for v in value):
                problems.append(
                    f"mission_constraint_invalid: {constraint_id}: value contiene una "
                    "posición de assignment fuera de rango."
                )
                continue
            resolved_dependency_task_ids = [plan.assignments[v].task_id for v in value]
        else:  # pragma: no cover - unreachable, _CONSTRAINT_FIELDS covers all cases
            problems.append(f"mission_constraint_invalid: {constraint_id}: field sin tipo de value soportado.")
            continue

        # A. Authority provenance (per-constraint; the manifest-level "not
        # supplied at all" problem was already recorded above).
        if mission_authority_texts is not None and not any(
            source_text in text for text in mission_authority_texts
        ):
            problems.append(
                f"mission_constraint_source_not_authorized: {constraint_id}: "
                "source_text no aparece verbatim en ninguna fuente humana autorizada."
            )

        # C. Structural comparison against the actual plan.
        if scope == "plan":
            if field_name == "assignment_count":
                actual = assignment_count_actual
            elif field_name == "maximum_total_tokens":
                actual = plan.budget.get("maximum_total_tokens")
            else:
                actual = plan.budget.get("replanning_reserve_tokens")
            expected = value
        elif field_name == "dependencies":
            actual = list(assignment.dependencies)
            expected = resolved_dependency_task_ids
        else:
            actual = getattr(assignment, field_name)
            expected = value

        matches = (actual <= expected) if operator == "at_most" else (actual == expected)
        if not matches:
            target = (
                f"plan.{field_name}" if scope == "plan"
                else f"assignment[{assignment_index}].{field_name}"
            )
            problems.append(
                f"mission_constraint_mismatch: {constraint_id}: {target} {operator} "
                f"{value!r} pero el plan tiene {actual!r}."
            )

    return problems


def validate_plan(
    plan: MissionPlan,
    registry: CapabilityRegistry,
    *,
    provider_readiness: dict[str, dict] | None = None,
    mission_authority_texts: list[str] | None = None,
) -> list[str]:
    """Deterministic constitutional/structural validation of a MissionPlan.

    provider_readiness is optional and keyword-only: when omitted (existing
    callers validating only the static plan contract), behavior is
    unchanged from before this parameter existed - no readiness failure is
    ever invented. When supplied, it must be the already-acquired
    provider_readiness snapshot from context_acquisition.acquire_context()
    for the current session (see conversation.run()) - this function never
    re-probes providers itself, it only reads the given mapping.

    Static eligibility (registry.model_allowed) and runtime readiness
    (provider_readiness) are deliberately kept as two separate checks:
    a provider/model/family being statically configured/eligible never
    implies it is currently available, and vice versa.

    mission_authority_texts is optional and keyword-only, and is only ever
    consulted when plan.mission_constraints is not None (a v4.0.1
    new-format plan): every constraint's source_text must then occur
    verbatim as a substring of at least one entry here. For a legacy plan
    (plan.mission_constraints is None) this parameter is never consulted
    and behavior is byte-for-byte unchanged from before mission_constraints
    existed. See _validate_mission_constraints for the full contract.
    """
    problems: list[str] = []
    problems.extend(
        _validate_mission_constraints(plan, mission_authority_texts)
    )

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
        if provider_readiness is not None:
            # Fail closed: only an entry shaped as a mapping with
            # available is exactly True counts as ready. Absent entries,
            # non-mapping entries, a missing "available" field, False,
            # None, and any non-bool-True value (e.g. the string "true")
            # are all treated as not ready - this is deterministic runtime
            # readiness evidence, never inferred from executable path,
            # model registration, version text, or evidence strings.
            entry = provider_readiness.get(a.provider)
            ready = isinstance(entry, dict) and entry.get("available") is True
            if not ready:
                problems.append(f"{a.task_id}: provider_not_ready: {a.provider}")
        if a.mutation:
            problems.append(
                f"{a.task_id}: mutation_runtime_not_supported (el runtime de "
                "worktree aislado para mutación todavía no existe)."
            )
        if a.network and "network" not in plan.approval_boundaries:
            problems.append(f"{a.task_id} usa red sin boundary network")
        if a.private_context and "private_context" not in plan.approval_boundaries:
            problems.append(f"{a.task_id} usa contexto privado sin boundary private_context")
        if a.execution_gate not in EXECUTION_GATES:
            problems.append(
                f"{a.task_id}: execution_gate inválido: {a.execution_gate!r}. "
                f"Valores permitidos: {sorted(EXECUTION_GATES)}."
            )
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

    declared_provider_totals = {
        item["provider"]: item["total_tokens"]
        for item in plan.budget.get("provider_totals", [])
    }
    declared_family_totals = {
        item["family"]: item["total_tokens"]
        for item in plan.budget.get("family_totals", [])
    }

    if declared_provider_totals != provider_totals:
        problems.append("budget.provider_totals no coincide con las tareas.")
    if declared_family_totals != family_totals:
        problems.append("budget.family_totals no coincide con las tareas.")
    if maximum != task_total + reserve:
        problems.append("budget.maximum_total_tokens debe ser tareas + reserva.")
    if plan.estimated_tokens != maximum:
        problems.append("estimated_tokens debe coincidir con budget.maximum_total_tokens.")
    return problems

def _format_constraint_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return json.dumps(value, ensure_ascii=False)


def _constraint_target(c: dict) -> str:
    if c.get("scope") == "plan":
        return f"plan.{c.get('field')}"
    return f"assignment[{c.get('assignment_index')}].{c.get('field')}"


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
        gate_label = a.execution_gate if a.execution_gate in EXECUTION_GATES else "⚠ NO DECLARADO"
        lines.append(f"  Gate de ejecución: {gate_label}")
    lines += ["", "Presupuesto por provider:"]
    for item in sorted(
        plan.budget.get("provider_totals", []),
        key=lambda value: value["provider"],
    ):
        lines.append(
            f"- {item['provider']}: {item['total_tokens']} tokens"
        )
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
    ]

    if plan.mission_constraints is None:
        lines.append(
            "Restricciones estructurales: plan legacy v4.0.0 sin manifest estructurado."
        )
    else:
        lines.append("Restricciones estructurales extraídas:")
        if not plan.mission_constraints:
            lines.append("- Ninguna restricción estructural representable fue extraída.")
        else:
            for c in plan.mission_constraints:
                lines.append(f"- {c.get('constraint_id')}:")
                lines.append(
                    f"  {_constraint_target(c)} {c.get('operator')} "
                    f"{_format_constraint_value(c.get('value'))}"
                )
                lines.append(f"  fuente: {json.dumps(c.get('source_text'), ensure_ascii=False)}")
        lines.append(
            "Hokage: La completitud semántica de la extracción de "
            "mission_constraints requiere revisión humana."
        )

    lines += [
        "",
        "Hokage: El plan pasó las validaciones constitucionales determinísticas.",
        "La fidelidad semántica a la misión requiere revisión humana.",
        "El plan está pendiente de aprobación.",
        "¿Aprobás el plan?",
        '- “sí” para aprobar;',
        '- “no” para rechazar;',
        "- o escribí los cambios requeridos.",
    ]
    return "\n".join(lines)
