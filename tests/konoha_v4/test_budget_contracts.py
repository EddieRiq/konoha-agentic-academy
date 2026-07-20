from __future__ import annotations

import unittest

from tools.konoha_v4.hokage import validate_plan
from tools.konoha_v4.models import AgentAssignment, MissionPlan


class _Registry:
    def agent_family(self, family: str) -> dict:
        return {"allowed_task_patterns": ["read-only inspection"]}

    def model_allowed(
        self,
        provider: str,
        model: str,
        family: str,
    ) -> bool:
        return True


def _plan() -> MissionPlan:
    return MissionPlan(
        mission_id="mission-budget-contract",
        understanding="Calificar de forma read-only el presupuesto del plan.",
        explicit_facts=["El workspace permanece read-only."],
        missing_context=[],
        assumptions_prohibited=["No inferir autorización."],
        complexity="medium",
        assignments=[
            AgentAssignment(
                task_id="inspect-runtime",
                family="repository-auditor",
                provider="codex",
                model="codex",
                objective="Inspeccionar el runtime sin modificar archivos.",
                inputs=["tools/konoha_v4"],
                expected_output="Evidencia verificable.",
                estimated_input_tokens=100,
                estimated_output_tokens=50,
                estimated_total_tokens=150,
            ),
        ],
        acceptance_criteria=["No hubo mutación."],
        approval_boundaries=["read_only"],
        estimated_tokens=175,
        estimated_cost_class="low",
        rationale="Validación constitucional read-only.",
        budget={
            "provider_totals": [
                {
                    "provider": "codex",
                    "total_tokens": 150,
                },
            ],
            "family_totals": [
                {
                    "family": "repository-auditor",
                    "total_tokens": 150,
                },
            ],
            "replanning_reserve_tokens": 25,
            "maximum_total_tokens": 175,
        },
    ).seal()


class BudgetContractTests(unittest.TestCase):
    def test_list_totals_match_assignments(self) -> None:
        self.assertEqual(validate_plan(_plan(), _Registry()), [])

    def test_incorrect_provider_total_is_rejected(self) -> None:
        plan = _plan()
        plan.budget["provider_totals"][0]["total_tokens"] = 149

        problems = validate_plan(plan, _Registry())

        self.assertIn(
            "budget.provider_totals no coincide con las tareas.",
            problems,
        )

    def test_incorrect_family_total_is_rejected(self) -> None:
        plan = _plan()
        plan.budget["family_totals"][0]["total_tokens"] = 149

        problems = validate_plan(plan, _Registry())

        self.assertIn(
            "budget.family_totals no coincide con las tareas.",
            problems,
        )


if __name__ == "__main__":
    unittest.main()
