from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tools.konoha_v4.continuity import (
    MissionContinuityStore,
    default_state_root,
)
from tools.konoha_v4.conversation import _build_validated_plan


class DefaultStateRootTests(unittest.TestCase):
    def test_default_state_root_is_outside_repo_contract(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            root = default_state_root()
        self.assertEqual(root.name, "v4")
        self.assertEqual(root.parent.name, "konoha")
        self.assertIn(".local/state", root.as_posix())

    def test_explicit_state_root_wins(self) -> None:
        with patch.dict(
            os.environ,
            {"KONOHA_STATE_ROOT": "/tmp/konoha-state-test"},
            clear=True,
        ):
            self.assertEqual(
                default_state_root(),
                Path("/tmp/konoha-state-test"),
            )


class MissionContinuityStoreTests(unittest.TestCase):
    def test_changes_and_findings_survive_reload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = SimpleNamespace(
                mission_id="mission-1",
                plan_hash="plan-1",
                approval={"status": "pending"},
            )
            store = MissionContinuityStore.create(
                root,
                "mission-1",
                "Read-only mission",
                {"head": "abc", "branch": "test", "status": ""},
            )
            store.record_plan(plan, reason="initial")
            store.record_requested_change("Jounin independiente", plan)
            store.record_validator_findings(
                ["budget mismatch"],
                plan=plan,
            )

            reloaded = MissionContinuityStore.create(
                root,
                "mission-1",
                "Read-only mission",
                {"head": "abc", "branch": "test", "status": ""},
            )
            context = reloaded.planner_context()

            self.assertEqual(
                context["requested_changes_history"][0]["text"],
                "Jounin independiente",
            )
            self.assertEqual(
                context["validator_findings_history"][0]["findings"],
                ["budget mismatch"],
            )
            self.assertEqual(
                context["previous_plan"]["plan_hash"],
                "plan-1",
            )

    def test_replan_cannot_change_mission_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MissionContinuityStore.create(
                Path(tmp),
                "mission-1",
                "Read-only mission",
                {"head": "abc"},
            )
            problems = store.validate_replanned_plan(
                SimpleNamespace(mission_id="mission-2")
            )
            self.assertTrue(problems)


class AutomaticReplanningContinuityTests(unittest.TestCase):
    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_previous_plan_and_findings_are_replayed(
        self,
        build_plan: Mock,
        validate_plan: Mock,
    ) -> None:
        first = SimpleNamespace(
            mission_id="mission-1",
            plan_hash="plan-1",
            missing_context=[],
        )
        corrected = SimpleNamespace(
            mission_id="mission-1",
            plan_hash="plan-2",
            missing_context=[],
        )
        build_plan.side_effect = [first, corrected]
        validate_plan.side_effect = [["budget mismatch"], []]

        plan, problems, attempts = _build_validated_plan(
            Mock(),
            "Read-only mission",
            {"branch": "test", "head": "abc", "status": ""},
            Mock(),
        )

        self.assertIs(plan, corrected)
        self.assertEqual(problems, [])
        self.assertEqual(attempts, 2)

        second_call = build_plan.call_args_list[1]
        continuity = second_call.kwargs["continuity"]
        self.assertEqual(
            continuity["previous_plan"]["plan_hash"],
            "plan-1",
        )
        self.assertEqual(
            continuity["validator_findings_history"][0]["findings"],
            ["budget mismatch"],
        )


if __name__ == "__main__":
    unittest.main()
