from __future__ import annotations

import unittest

from tools.konoha_v4.hokage import approval_summary
from tools.konoha_v4.models import AgentAssignment, MissionPlan
from tools.konoha_v4.planner import SYSTEM

# planner.SYSTEM is deliberately wrapped/indented for human readability and
# is never reformatted just to satisfy a test. Semantic-wording assertions
# below run against this whitespace-collapsed view instead of SYSTEM
# directly, so they tolerate line wrapping/indentation/adjacent-literal
# formatting without weakening what they actually verify.
_NORMALIZED_SYSTEM = " ".join(SYSTEM.split())


class PlannerPromptContractTests(unittest.TestCase):
    def test_separates_hokage_from_operational_assignments(self) -> None:
        self.assertIn(
            'No incluyas "Hokage" en task_id ni objective '
            "de una tarea mission-conductor.",
            SYSTEM,
        )
        self.assertIn(
            "no puede aprobar, autorizar ni emitir una decisión constitucional",
            SYSTEM,
        )

    def test_requires_exact_budget_arithmetic(self) -> None:
        self.assertIn(
            "maximum_total_tokens = suma de assignments "
            "+ replanning_reserve_tokens",
            SYSTEM,
        )
        self.assertIn(
            "estimated_tokens = maximum_total_tokens",
            SYSTEM,
        )

    def test_explicit_mission_constraints_are_binding(self) -> None:
        # Test A
        self.assertIn(
            "Sus restricciones explícitas son vinculantes.",
            _NORMALIZED_SYSTEM,
        )
        self.assertIn(
            "no expandas, relajes, optimices, reemplaces ni reinterpretes en silencio",
            _NORMALIZED_SYSTEM.lower(),
        )

    def test_fixed_structural_constraints_must_not_be_silently_expanded(self) -> None:
        # Test B: fixed assignment count/order/provider/gate/budget must not
        # be silently expanded or replaced.
        self.assertIn("cantidad de assignments", _NORMALIZED_SYSTEM)
        self.assertIn("orden/dependencias entre assignments", _NORMALIZED_SYSTEM)
        self.assertIn("provider; model", _NORMALIZED_SYSTEM)
        self.assertIn("execution_gate; política de fallback", _NORMALIZED_SYSTEM)
        self.assertIn(
            "No agregues assignments adicionales solo porque un grafo más "
            "elaborado normalmente sería preferible",
            _NORMALIZED_SYSTEM,
        )

    def test_no_fallback_and_explicit_budget_ceiling_are_preserved(self) -> None:
        # Test C
        self.assertIn(
            '"Sin fallback" en la misión significa sin fallback de provider '
            "y sin fallback de family",
            _NORMALIZED_SYSTEM,
        )
        self.assertIn(
            "Un maximum_total_tokens explícito de la misión es un techo duro, "
            "nunca un objetivo a superar",
            _NORMALIZED_SYSTEM,
        )

    def test_impossible_explicit_constraint_fails_closed(self) -> None:
        # Test D: impossible explicit constraints must fail closed rather
        # than cause an invented substitution.
        self.assertIn(
            "fallá cerrado agregando missing_context", _NORMALIZED_SYSTEM,
        )
        self.assertIn(
            "nunca inventes un provider, modelo, gate o presupuesto sustituto",
            _NORMALIZED_SYSTEM,
        )

    def test_requested_changes_are_binding_during_replanning(self) -> None:
        # Test E
        self.assertIn(
            "requested_changes son correcciones vinculantes al plan previo, "
            "no sugerencias",
            _NORMALIZED_SYSTEM,
        )
        self.assertIn(
            "no las descartes ni las diluyas al replanificar", _NORMALIZED_SYSTEM,
        )

    def test_model_planning_remains_proposal_pending_human_approval(self) -> None:
        self.assertIn(
            "La planificación de Codex sigue siendo evidencia/propuesta "
            "únicamente; la aprobación humana del plan sigue siendo "
            "obligatoria en todos los casos.",
            _NORMALIZED_SYSTEM,
        )


class ExplicitFactsContractTests(unittest.TestCase):
    """BLOCK_4 FINDING #10 PART 2: explicit_facts is what executor's
    _task_prompt() now exposes to assignments as mission_context, so the
    planner contract must be explicit about what it may and may not
    contain."""

    def test_explicit_facts_captures_explicit_human_mission_facts(self) -> None:
        self.assertIn(
            "explicit_facts captura los hechos y restricciones que la "
            "misión humana declaró explícitamente, no tu interpretación "
            "de ellos.",
            _NORMALIZED_SYSTEM,
        )
        self.assertIn(
            "Cuando la misión fije explícitamente alguna restricción "
            "estructural vinculante (cantidad/orden de assignments, "
            "family, provider, model, network, mutation, private_context, "
            "execution_gate, fallback o un presupuesto explícito), esa "
            "restricción debe quedar registrada en explicit_facts.",
            _NORMALIZED_SYSTEM,
        )

    def test_explicit_facts_must_not_contain_invented_facts(self) -> None:
        self.assertIn(
            "No inventes hechos en explicit_facts que la misión no haya "
            "declarado.",
            _NORMALIZED_SYSTEM,
        )

    def test_explicit_binding_constraints_must_not_be_weakened_or_reinterpreted(self) -> None:
        self.assertIn(
            "No debilites ni reinterpretes en silencio una restricción "
            "explícita al redactar explicit_facts: reflejala tal como la "
            "fijó la misión.",
            _NORMALIZED_SYSTEM,
        )

    def test_explicit_facts_is_distinct_from_understanding_inference(self) -> None:
        self.assertIn(
            "explicit_facts es distinto de understanding: understanding "
            "es tu síntesis/paráfrasis, explicit_facts son los hechos "
            "explícitos, no tu inferencia.",
            _NORMALIZED_SYSTEM,
        )

    def test_explicit_facts_may_become_mission_context_for_authorized_assignments(self) -> None:
        self.assertIn(
            "explicit_facts queda persistido como parte del MissionPlan "
            "aprobado y puede suministrarse como mission_context a los "
            "assignments autorizados durante la ejecución.",
            _NORMALIZED_SYSTEM,
        )


def _assignment() -> AgentAssignment:
    return AgentAssignment(
        task_id="t1",
        family="repository-auditor",
        provider="codex",
        model="codex",
        objective="Inspeccionar sin mutar.",
        inputs=["tools/konoha_v4"],
        expected_output="Evidencia verificable.",
        execution_gate="plan_approval",
    )


def _plan() -> MissionPlan:
    return MissionPlan(
        mission_id="mission-approval-wording-test",
        understanding="Validar el wording de alcance de validación.",
        explicit_facts=[],
        missing_context=[],
        assumptions_prohibited=[],
        complexity="low",
        assignments=[_assignment()],
        acceptance_criteria=["done"],
        approval_boundaries=[],
        estimated_tokens=0,
        estimated_cost_class="low",
        rationale="test",
    ).seal()


class ApprovalSummaryValidationScopeTests(unittest.TestCase):
    """BLOCK_4 FINDING #9 PART 2: approval_summary() must not claim
    deterministic proof of semantic mission fidelity - only that
    deterministic constitutional checks passed and human review of that
    fidelity, plus human plan approval, are still pending."""

    def test_states_deterministic_constitutional_validation_passed(self) -> None:
        summary = approval_summary(_plan())
        self.assertIn(
            "Hokage: El plan pasó las validaciones constitucionales determinísticas.",
            summary,
        )

    def test_states_semantic_mission_fidelity_requires_human_review(self) -> None:
        summary = approval_summary(_plan())
        self.assertIn(
            "La fidelidad semántica a la misión requiere revisión humana.",
            summary,
        )

    def test_still_states_human_approval_is_pending(self) -> None:
        summary = approval_summary(_plan())
        self.assertIn("El plan está pendiente de aprobación.", summary)

    def test_no_longer_claims_constitutional_validation_alone(self) -> None:
        summary = approval_summary(_plan())
        self.assertNotIn(
            "El plan está constitucionalmente validado y pendiente de aprobación humana.",
            summary,
        )


if __name__ == "__main__":
    unittest.main()
