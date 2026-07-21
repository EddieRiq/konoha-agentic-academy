from __future__ import annotations

from dataclasses import dataclass, field
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools.konoha_v4.conversation import (
    _SESSION_EXIT,
    _approval_loop,
    _confirm_feedback,
    _read_approval_input,
)


@dataclass
class FakePlan:
    mission_id: str
    plan_hash: str
    approval: dict = field(default_factory=lambda: {
        "status": "pending",
        "approved_by": None,
        "approved_at": None,
        "feedback": None,
    })
    missing_context: list = field(default_factory=list)
    assignments: list = field(default_factory=list)


class ApprovalInputStabilizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(".")
        self.registry = Mock()
        self.plan = FakePlan("mission-1", "plan-1")
        self.replanned = FakePlan("mission-1", "plan-2")
        self.store = Mock()
        self.store.planner_context.return_value = {"mission_id": "mission-1"}
        self.store.validate_replanned_plan.return_value = []

    def common(self):
        return (
            patch(
                "tools.konoha_v4.conversation.MissionContinuityStore.create",
                return_value=self.store,
            ),
            patch(
                "tools.konoha_v4.conversation._repo_state",
                return_value={"branch": "test", "head": "abc", "status": ""},
            ),
            patch(
                "tools.konoha_v4.conversation.approval_summary",
                return_value="VISIBLE PLAN",
            ),
            patch("tools.konoha_v4.conversation._persist_plan"),
        )

    def test_multiline_feedback_uses_first_line_and_fin(self) -> None:
        with patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_line",
            return_value="Primera regla.",
        ), patch(
            "tools.konoha_v4.conversation._read_feedback_from_first_line",
            return_value=("Primera regla.\nSegunda regla.", False),
        ):
            self.assertEqual(
                _read_approval_input(),
                ("feedback", "Primera regla.\nSegunda regla."),
            )

    def test_single_line_cambio_prefix(self) -> None:
        with patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_line",
            return_value="cambio: Jounin debe ser independiente.",
        ):
            self.assertEqual(
                _read_approval_input(),
                ("feedback", "Jounin debe ser independiente."),
            )

    def test_exit_is_never_feedback(self) -> None:
        with patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_line",
            return_value="salir",
        ):
            self.assertEqual(_read_approval_input(), ("exit", None))

    def test_exit_does_not_invoke_or_record(self) -> None:
        create, state, summary, persist = self.common()
        with tempfile.TemporaryDirectory() as tmp, create, state, summary, persist,              patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 return_value=("exit", None),
             ),              patch("tools.konoha_v4.conversation.build_plan") as build:
            result = _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry
            )
        self.assertIs(result, _SESSION_EXIT)
        build.assert_not_called()
        self.store.record_requested_change.assert_not_called()

    def test_empty_input_does_not_invoke_provider_or_rerender(self) -> None:
        create, state, summary, persist = self.common()
        with tempfile.TemporaryDirectory() as tmp, create, state, summary as show, persist,              patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 side_effect=[("pending", None), ("decision", "no")],
             ),              patch("tools.konoha_v4.conversation.build_plan") as build:
            result = _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry
            )
        self.assertIsNone(result)
        build.assert_not_called()
        self.assertEqual(show.call_count, 1)

    def test_cancelled_feedback_does_not_invoke_or_record(self) -> None:
        create, state, summary, persist = self.common()
        with tempfile.TemporaryDirectory() as tmp, create, state, summary, persist,              patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 side_effect=[
                     ("feedback", "change"),
                     ("decision", "no"),
                 ],
             ),              patch(
                 "tools.konoha_v4.conversation._confirm_feedback",
                 return_value=False,
             ),              patch("tools.konoha_v4.conversation.build_plan") as build:
            _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry
            )
        build.assert_not_called()
        self.store.record_requested_change.assert_not_called()

    def test_confirmed_multiline_records_exact_text_once(self) -> None:
        feedback = "Primera regla.\nSegunda regla."
        create, state, summary, persist = self.common()
        with tempfile.TemporaryDirectory() as tmp, create, state, summary as show, persist,              patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 side_effect=[
                     ("feedback", feedback),
                     ("decision", "no"),
                 ],
             ),              patch(
                 "tools.konoha_v4.conversation._confirm_feedback",
                 return_value=True,
             ),              patch(
                 "tools.konoha_v4.conversation.build_plan",
                 return_value=self.replanned,
             ) as build,              patch(
                 "tools.konoha_v4.conversation.validate_plan",
                 return_value=[],
             ):
            _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry
            )
        build.assert_called_once()
        self.assertEqual(build.call_args.kwargs["feedback"], feedback)
        self.store.record_requested_change.assert_called_once_with(
            feedback, self.plan
        )
        self.assertEqual(show.call_count, 2)

    def test_confirm_feedback_discards_residual(self) -> None:
        with patch(
            "tools.konoha_v4.conversation._read_fresh_decision",
            return_value=("sí", ["residual"]),
        ):
            self.assertTrue(_confirm_feedback("candidate"))

    def test_yes_approves_without_replanning(self) -> None:
        create, state, summary, persist = self.common()
        with tempfile.TemporaryDirectory() as tmp, create, state, summary, persist,              patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 return_value=("decision", "sí"),
             ),              patch("tools.konoha_v4.conversation.build_plan") as build:
            result = _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry
            )
        self.assertIs(result, self.plan)
        build.assert_not_called()


if __name__ == "__main__":
    unittest.main()
