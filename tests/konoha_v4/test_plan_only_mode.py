from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools.konoha_v4.cli import main
from tools.konoha_v4.conversation import _approval_loop, run
from tools.konoha_v4.models import AgentAssignment, MissionPlan


def _assignment(task_id="t1", execution_gate="plan_approval", **overrides):
    fields = dict(
        task_id=task_id,
        family="repository-auditor",
        provider="codex",
        model="codex",
        objective="Inspeccionar sin mutar.",
        inputs=["tools/konoha_v4"],
        expected_output="Evidencia verificable.",
        estimated_input_tokens=10,
        estimated_output_tokens=5,
        estimated_total_tokens=15,
        execution_gate=execution_gate,
    )
    fields.update(overrides)
    return AgentAssignment(**fields)


def _plan(assignments=None, approval_status="pending", **overrides):
    fields = dict(
        mission_id="mission-plan-only-test",
        understanding="Validar el modo --plan-only.",
        explicit_facts=[],
        missing_context=[],
        assumptions_prohibited=[],
        complexity="low",
        assignments=assignments if assignments is not None else [_assignment()],
        acceptance_criteria=["done"],
        approval_boundaries=["read_only", "mutation", "network", "private_context"],
        estimated_tokens=15,
        estimated_cost_class="low",
        rationale="test",
        approval={
            "status": approval_status,
            "approved_by": "human" if approval_status == "approved" else None,
            "approved_at": "2026-08-24T00:00:00Z" if approval_status == "approved" else None,
            "feedback": None,
        },
    )
    fields.update(overrides)
    return MissionPlan(**fields).seal()


_ACQUIRED = SimpleNamespace(
    provider_readiness={"codex": {"available": True}},
    as_dict=lambda: {},
)
_REPO_STATE = {"branch": "test", "head": "abc", "status": ""}


def _enter_run_patches(stack, state_dir, mission_texts, build_result, approval_inputs):
    """Enter the common set of patches every run()-level plan-only test
    needs, into the caller-owned ExitStack. Callers add/override further
    patches on the same stack afterwards, then call run() and assert while
    still inside the stack (and the TemporaryDirectory) so every
    filesystem-dependent assertion observes real, not-yet-cleaned-up
    state_dir contents."""
    stack.enter_context(
        mock.patch("tools.konoha_v4.conversation.default_state_root", return_value=state_dir)
    )
    stack.enter_context(
        mock.patch("tools.konoha_v4.conversation.CapabilityRegistry", return_value=mock.Mock())
    )
    stack.enter_context(
        mock.patch("tools.konoha_v4.conversation.acquire_context", return_value=_ACQUIRED)
    )
    stack.enter_context(
        mock.patch("tools.konoha_v4.conversation._repo_state", return_value=_REPO_STATE)
    )
    stack.enter_context(
        mock.patch("tools.konoha_v4.conversation._read_turn", side_effect=mission_texts)
    )
    stack.enter_context(
        mock.patch(
            "tools.konoha_v4.conversation._build_validated_plan", return_value=build_result,
        )
    )
    stack.enter_context(
        mock.patch(
            "tools.konoha_v4.conversation._read_approval_input", side_effect=approval_inputs,
        )
    )


# --- A. CLI surface -----------------------------------------------------


class CliSurfaceTests(unittest.TestCase):
    def test_plan_only_flag_is_accepted_and_routes_through(self):
        with mock.patch("tools.konoha_v4.cli.run", return_value=0) as run_mock:
            exit_code = main(["--plan-only"])
        run_mock.assert_called_once()
        self.assertTrue(run_mock.call_args.kwargs["plan_only"])
        self.assertEqual(exit_code, 0)

    def test_plan_only_and_resume_are_mutually_exclusive(self):
        buffer = io.StringIO()
        with contextlib.redirect_stderr(buffer), self.assertRaises(SystemExit):
            main(["--plan-only", "--resume", "mission-x"])

    def test_default_cli_behavior_still_routes_to_normal_run(self):
        with mock.patch("tools.konoha_v4.cli.run", return_value=0) as run_mock:
            main([])
        run_mock.assert_called_once()
        self.assertFalse(run_mock.call_args.kwargs["plan_only"])

    def test_resume_alone_still_routes_to_resume_mission(self):
        with mock.patch("tools.konoha_v4.cli.resume_mission", return_value=0) as resume_mock, \
             mock.patch("tools.konoha_v4.cli.run") as run_mock:
            main(["--resume", "mission-x"])
        resume_mock.assert_called_once()
        run_mock.assert_not_called()

    def test_version_flag_unchanged(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exit_code = main(["--version"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(buffer.getvalue().strip(), "4.1.0")


# --- B. plan-only valid plan: explicit affirmative -----------------------


class PlanOnlyValidAcceptanceTests(unittest.TestCase):
    def test_affirmative_acceptance_never_reaches_execution(self):
        plan = _plan()
        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
            state_dir = Path(tmp)
            _enter_run_patches(
                stack, state_dir, ["hacer algo", "salir"], (plan, [], 1), [("decision", "sí")],
            )
            summary_mock = stack.enter_context(
                mock.patch(
                    "tools.konoha_v4.conversation.approval_summary", return_value="RESUMEN",
                )
            )
            run_exec_mock = stack.enter_context(
                mock.patch("tools.konoha_v4.conversation._run_resumable_execution")
            )
            low_level_exec_mock = stack.enter_context(
                mock.patch("tools.konoha_v4.conversation.execute_or_resume_plan")
            )

            exit_code = run(Path("."), plan_only=True)

            self.assertEqual(exit_code, 0)
            summary_mock.assert_called()
            run_exec_mock.assert_not_called()
            low_level_exec_mock.assert_not_called()

            self.assertEqual(plan.approval["status"], "pending")
            self.assertIsNone(plan.approval["approved_by"])
            self.assertIsNone(plan.approval["approved_at"])

            self.assertFalse(
                (state_dir / "missions" / plan.mission_id / "plan.json").exists()
            )
            self.assertFalse(
                (state_dir / "missions" / plan.mission_id / "execution_state.json").exists()
            )


# --- C. plan-only requested changes / replanning -------------------------


class PlanOnlyRequestedChangeTests(unittest.TestCase):
    def test_requested_change_replans_and_accepts_without_execution(self):
        mission_text = "hacer algo"
        feedback_text = "Usá Claude para la segunda tarea."
        original_plan = _plan()
        replanned = _plan(approval_status="pending")

        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
            state_dir = Path(tmp)
            _enter_run_patches(
                stack, state_dir, [mission_text, "salir"], (original_plan, [], 1),
                [("feedback", feedback_text), ("decision", "sí")],
            )
            stack.enter_context(
                mock.patch("tools.konoha_v4.conversation._confirm_feedback", return_value=True)
            )
            build_plan_mock = stack.enter_context(
                mock.patch("tools.konoha_v4.conversation.build_plan", return_value=replanned)
            )
            validate_mock = stack.enter_context(
                mock.patch("tools.konoha_v4.conversation.validate_plan", return_value=[])
            )
            run_exec_mock = stack.enter_context(
                mock.patch("tools.konoha_v4.conversation._run_resumable_execution")
            )
            low_level_exec_mock = stack.enter_context(
                mock.patch("tools.konoha_v4.conversation.execute_or_resume_plan")
            )

            exit_code = run(Path("."), plan_only=True)

            self.assertEqual(exit_code, 0)

            # The existing replanning path was actually used.
            build_plan_mock.assert_called_once()
            self.assertEqual(build_plan_mock.call_args.kwargs["feedback"], feedback_text)

            # The unchanged mission_constraints provenance contract:
            # authority texts are exactly [mission_text] + confirmed
            # requested-change history - never anything else.
            validate_mock.assert_called_once()
            self.assertEqual(
                validate_mock.call_args.kwargs["mission_authority_texts"],
                [mission_text, feedback_text],
            )

            run_exec_mock.assert_not_called()
            low_level_exec_mock.assert_not_called()

            # The confirmed requested change was recorded as human
            # continuity evidence (private continuity state, explicitly
            # permitted) - checked while state_dir still exists.
            continuity_path = (
                state_dir / "missions" / original_plan.mission_id / "continuity.json"
            )
            self.assertTrue(continuity_path.exists())
            continuity_data = json.loads(continuity_path.read_text(encoding="utf-8"))
            recorded_texts = [
                item["text"] for item in continuity_data["requested_changes_history"]
            ]
            self.assertIn(feedback_text, recorded_texts)

            # No executable plan.json for the (shared) mission_id.
            self.assertFalse(
                (state_dir / "missions" / original_plan.mission_id / "plan.json").exists()
            )
            self.assertEqual(replanned.approval["status"], "pending")


# --- D. rejection / exit --------------------------------------------------


class PlanOnlyRejectionAndExitTests(unittest.TestCase):
    def test_rejection_never_invokes_execution(self):
        plan = _plan()
        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
            state_dir = Path(tmp)
            _enter_run_patches(
                stack, state_dir, ["hacer algo", "salir"], (plan, [], 1), [("decision", "no")],
            )
            run_exec_mock = stack.enter_context(
                mock.patch("tools.konoha_v4.conversation._run_resumable_execution")
            )
            low_level_exec_mock = stack.enter_context(
                mock.patch("tools.konoha_v4.conversation.execute_or_resume_plan")
            )

            exit_code = run(Path("."), plan_only=True)

            self.assertEqual(exit_code, 0)
            run_exec_mock.assert_not_called()
            low_level_exec_mock.assert_not_called()
            self.assertEqual(plan.approval["status"], "rejected")
            self.assertFalse(
                (state_dir / "missions" / plan.mission_id / "plan.json").exists()
            )

    def test_exit_never_invokes_execution(self):
        plan = _plan()
        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
            state_dir = Path(tmp)
            _enter_run_patches(
                stack, state_dir, ["hacer algo"], (plan, [], 1), [("exit", None)],
            )
            run_exec_mock = stack.enter_context(
                mock.patch("tools.konoha_v4.conversation._run_resumable_execution")
            )
            low_level_exec_mock = stack.enter_context(
                mock.patch("tools.konoha_v4.conversation.execute_or_resume_plan")
            )

            exit_code = run(Path("."), plan_only=True)

            self.assertEqual(exit_code, 0)
            run_exec_mock.assert_not_called()
            low_level_exec_mock.assert_not_called()
            self.assertFalse(
                (state_dir / "missions" / plan.mission_id / "plan.json").exists()
            )


# --- E. normal-mode preservation ------------------------------------------


class NormalModeUnaffectedTests(unittest.TestCase):
    def test_default_plan_only_false_still_grants_execution_approval(self):
        plan = _plan()
        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
            state_dir = Path(tmp)
            _enter_run_patches(
                stack, state_dir, ["hacer algo", "salir"], (plan, [], 1), [("decision", "sí")],
            )
            run_exec_mock = stack.enter_context(
                mock.patch(
                    "tools.konoha_v4.conversation._run_resumable_execution",
                    return_value="completed",
                )
            )

            exit_code = run(Path("."))  # plan_only omitted -> default False

            self.assertEqual(exit_code, 0)
            run_exec_mock.assert_called_once()
            self.assertEqual(plan.approval["status"], "approved")
            self.assertEqual(plan.approval["approved_by"], "human")
            self.assertIsNotNone(plan.approval["approved_at"])
            self.assertTrue(
                (state_dir / "missions" / plan.mission_id / "plan.json").exists()
            )


# --- Direct _approval_loop(plan_only=True) unit coverage ------------------


class ApprovalLoopPlanOnlyUnitTests(unittest.TestCase):
    def test_plan_only_acceptance_leaves_approval_and_continuity_pending(self):
        plan = _plan()
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation._read_approval_input",
                return_value=("decision", "sí"),
            ):
                result = _approval_loop(
                    Path("."), state_dir, "hacer algo", plan, mock.Mock(),
                    provider_readiness={"codex": {"available": True}},
                    plan_only=True,
                )

            self.assertIs(result, plan)
            self.assertEqual(plan.approval["status"], "pending")
            self.assertIsNone(plan.approval["approved_by"])
            self.assertIsNone(plan.approval["approved_at"])

            continuity_path = state_dir / "missions" / plan.mission_id / "continuity.json"
            continuity_data = json.loads(continuity_path.read_text(encoding="utf-8"))
            self.assertEqual(continuity_data["approval"]["status"], "pending")
            self.assertIsNone(continuity_data["approval"]["approved_by"])
            self.assertIsNone(continuity_data["approval"]["approved_at"])


if __name__ == "__main__":
    unittest.main()
