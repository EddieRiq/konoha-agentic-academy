from __future__ import annotations

import unittest

from tools.konoha_v4.planner import SYSTEM


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


if __name__ == "__main__":
    unittest.main()
