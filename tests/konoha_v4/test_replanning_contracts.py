from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tools.konoha_v4.conversation import (
    MAX_PLAN_ATTEMPTS,
    _build_validated_plan,
)


class ReplanningContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Mock()
        self.registry = Mock()
        self.state = {"branch": "test"}
        self.mission = "Inspeccionar el runtime en modo read-only."

    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_replans_once_after_deterministic_failure(
        self,
        build_plan: Mock,
        validate_plan: Mock,
    ) -> None:
        first = SimpleNamespace(missing_context=[])
        corrected = SimpleNamespace(missing_context=[])

        build_plan.side_effect = [first, corrected]
        validate_plan.side_effect = [
            [
                "estimated_tokens debe coincidir con "
                "budget.maximum_total_tokens."
            ],
            [],
        ]

        plan, problems, attempts = _build_validated_plan(
            self.repo,
            self.mission,
            self.state,
            self.registry,
        )

        self.assertIs(plan, corrected)
        self.assertEqual(problems, [])
        self.assertEqual(attempts, 2)
        self.assertEqual(build_plan.call_count, 2)

        first_feedback = build_plan.call_args_list[0].kwargs["feedback"]
        second_feedback = build_plan.call_args_list[1].kwargs["feedback"]

        self.assertIsNone(first_feedback)
        self.assertIn(
            "estimated_tokens debe coincidir",
            second_feedback,
        )
        self.assertIn(
            "Conservá la misión",
            second_feedback,
        )

    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_missing_context_does_not_trigger_replanning(
        self,
        build_plan: Mock,
        validate_plan: Mock,
    ) -> None:
        plan_with_missing_context = SimpleNamespace(
            missing_context=["Se requiere autorización humana."],
        )
        build_plan.return_value = plan_with_missing_context
        validate_plan.return_value = [
            "Falta contexto explícito: Se requiere autorización humana."
        ]

        plan, problems, attempts = _build_validated_plan(
            self.repo,
            self.mission,
            self.state,
            self.registry,
        )

        self.assertIs(plan, plan_with_missing_context)
        self.assertEqual(attempts, 1)
        self.assertEqual(build_plan.call_count, 1)
        self.assertTrue(problems)

    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_stops_after_maximum_attempts(
        self,
        build_plan: Mock,
        validate_plan: Mock,
    ) -> None:
        plans = [
            SimpleNamespace(missing_context=[])
            for _ in range(MAX_PLAN_ATTEMPTS)
        ]
        build_plan.side_effect = plans
        validate_plan.return_value = ["Presupuesto inconsistente."]

        plan, problems, attempts = _build_validated_plan(
            self.repo,
            self.mission,
            self.state,
            self.registry,
        )

        self.assertIs(plan, plans[-1])
        self.assertEqual(attempts, MAX_PLAN_ATTEMPTS)
        self.assertEqual(build_plan.call_count, MAX_PLAN_ATTEMPTS)
        self.assertEqual(problems, ["Presupuesto inconsistente."])


if __name__ == "__main__":
    unittest.main()
