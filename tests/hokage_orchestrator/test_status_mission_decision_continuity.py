import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from tools.hokage_orchestrator import authority

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "tools"
    / "hokage_orchestrator"
    / "run_conversational_hokage.py"
)

MISSION_TEXT = (
    "Revisá este repositorio con controles determinísticos. "
    "No modifiques archivos."
)


def load_script():
    spec = importlib.util.spec_from_file_location(
        "run_conversational_hokage_mission_decision",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class StatusMissionDecisionContinuityTests(unittest.TestCase):
    def setUp(self):
        self.module = load_script()

    def make_shell(self, root: Path):
        return self.module.ConversationalHokage(
            repo_root=ROOT,
            workspace_root=root / "workspace",
            state_root=root / "runtime",
            memory_root=root / "obsidian",
            actor="Eduardo",
        )

    def _drive_repro_state(self, shell):
        """Reproduces the exact manual repro: charter approved, first
        action completed, second rejected, the rest still proposed."""

        proposal = shell.one_shot(MISSION_TEXT)
        approved = shell.approve_charter(
            proposal["charter"]["approval_phrase"]
        )
        first = approved["next_action"]
        self.assertEqual(first["skill_id"], "inspect_python_runtime")
        first_result = shell.approve_action(first, first["approval_phrase"])
        self.assertEqual(first_result["status_code"], "ACTION_COMPLETED")

        second = first_result["next_action"]
        self.assertEqual(second["skill_id"], "inspect_git_status")
        second_result = shell.reject_action(second, second["rejection_phrase"])
        self.assertEqual(second_result["status_code"], "ACTION_REJECTED")

        return proposal

    def test_a_status_mission_decision_survives_restart_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            proposal = self._drive_repro_state(shell)

            before = shell.status_payload()["mission_decision"]
            self.assertIsNotNone(before)
            self.assertEqual(before["schema_version"], "1.1.0")

            mission_dir = shell.mission_dir(proposal["mission_id"])
            persisted = json.loads(
                authority.mission_decision_path(mission_dir).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(before, persisted)

            resumed = self.make_shell(root)
            self.assertIsNone(resumed.resume_diagnostic)
            after = resumed.status_payload()["mission_decision"]

            # Exactly the same persisted Decision - not recomputed, not
            # null.
            self.assertEqual(after, before)
            self.assertEqual(after, persisted)

    def test_b_action_queue_states_are_identical_across_that_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            self._drive_repro_state(shell)

            before_actions = {
                a["action_id"]: a["status"]
                for a in shell.status_payload()["action_queue"]["actions"]
            }
            before_skills = {
                a["skill_id"]: a["status"]
                for a in shell.status_payload()["action_queue"]["actions"]
            }
            self.assertEqual(
                before_skills["inspect_python_runtime"], "completed"
            )
            self.assertEqual(
                before_skills["inspect_git_status"], "rejected"
            )
            self.assertEqual(
                before_skills["run_deterministic_audit_checks"], "proposed"
            )
            self.assertEqual(
                before_skills["invoke_local_model_audit"], "proposed"
            )

            resumed = self.make_shell(root)
            self.assertIsNone(resumed.resume_diagnostic)
            after_actions = {
                a["action_id"]: a["status"]
                for a in resumed.status_payload()["action_queue"]["actions"]
            }

            # Identical state per action_id - restore() never
            # auto-dispatched anything.
            self.assertEqual(before_actions, after_actions)

    def test_c_invalid_authoritative_decision_fails_closed_no_fabrication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            proposal = self._drive_repro_state(shell)
            mission_id = proposal["mission_id"]
            mission_dir = shell.mission_dir(mission_id)

            before_actions = {
                a["action_id"]: a["status"]
                for a in shell.status_payload()["action_queue"]["actions"]
            }

            # Corrupt the persisted Decision after approval - the receipt
            # was frozen against the ORIGINAL content, so this must be
            # detected, never silently accepted or recomputed.
            decision_path = authority.mission_decision_path(mission_dir)
            tampered = json.loads(decision_path.read_text(encoding="utf-8"))
            tampered["selection"]["model"] = "some-other-model"
            decision_path.write_text(
                json.dumps(tampered), encoding="utf-8"
            )

            resumed = self.make_shell(root)

            # Fail closed, surfaced via resume_diagnostic - never raised
            # out of the constructor, never silently ignored.
            self.assertIsNotNone(resumed.resume_diagnostic)

            status = resumed.status_payload()
            # No fabricated/recomputed Decision presented in its place.
            self.assertIsNone(status["mission_decision"])

            # No auto-dispatch: the queue's own persisted action states
            # are exactly what they were before this restart attempt -
            # load()/status_payload() only ever read, they never mutate.
            after_actions = {
                a["action_id"]: a["status"]
                for a in status["action_queue"]["actions"]
            }
            self.assertEqual(before_actions, after_actions)


if __name__ == "__main__":
    unittest.main()
