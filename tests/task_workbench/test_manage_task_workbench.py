import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "task_workbench" / "manage_task_workbench.py"
SPEC = importlib.util.spec_from_file_location("manage_task_workbench", MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class TaskWorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.workspace = self.root / "workspace"

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, args):
        return module.main(args)

    def init_args(self):
        return [
            "init",
            "--workspace-root", str(self.workspace),
            "--mission-id", "mission-smoke",
            "--run-id", "run-smoke",
            "--title", "Smoke mission",
            "--task", "Prepare a supervised Docker and server task.",
            "--task-domain", "devops",
            "--target-environment", "mixed",
        ]

    def test_preview_init_does_not_create_workspace(self):
        code = self.run_cli(self.init_args())
        self.assertEqual(code, 0)
        self.assertFalse((self.workspace / "missions" / "mission-smoke").exists())

    def test_confirmed_init_creates_charter_manifest_and_report(self):
        code = self.run_cli(self.init_args() + [
            "--confirm-start",
            "--approval-token", "START_TASK_WORKBENCH",
            "--force",
        ])
        self.assertEqual(code, 0)
        mission = self.workspace / "missions" / "mission-smoke"
        self.assertTrue((mission / "charter.md").exists())
        self.assertTrue((mission / "mission_manifest.json").exists())
        self.assertTrue((mission / "mission_notification_state.json").exists())
        self.assertTrue((mission / "reports" / "run-smoke_task_workbench_init_report.json").exists())

    def test_plan_creates_command_batches_and_checklists(self):
        self.run_cli(self.init_args() + [
            "--confirm-start",
            "--approval-token", "START_TASK_WORKBENCH",
            "--force",
        ])
        code = self.run_cli([
            "plan",
            "--workspace-root", str(self.workspace),
            "--mission-id", "mission-smoke",
            "--plan-id", "plan-smoke",
            "--task", "Prepare Docker service and verify logs.",
            "--task-domain", "docker_workflow",
            "--target-environment", "docker",
            "--confirm-plan",
            "--approval-token", "PLAN_GENERAL_TASK_WORKBENCH",
            "--force",
        ])
        self.assertEqual(code, 0)
        mission = self.workspace / "missions" / "mission-smoke"
        plan_path = mission / "plans" / "plan-smoke_task_workbench_plan.json"
        batch_path = mission / "plans" / "plan-smoke_command_batches.json"
        self.assertTrue(plan_path.exists())
        self.assertTrue(batch_path.exists())
        batches = json.loads(batch_path.read_text(encoding="utf-8"))
        self.assertFalse(batches["authority"]["command_proposals_are_permission"])
        self.assertGreaterEqual(len(batches["batches"]), 2)

    def test_record_result_creates_evidence_only_result(self):
        self.run_cli(self.init_args() + [
            "--confirm-start",
            "--approval-token", "START_TASK_WORKBENCH",
            "--force",
        ])
        code = self.run_cli([
            "record-result",
            "--workspace-root", str(self.workspace),
            "--mission-id", "mission-smoke",
            "--result-id", "result-smoke",
            "--command-id", "inspect-01",
            "--command", "python --version",
            "--exit-code", "0",
            "--stdout-summary", "Python 3.x",
            "--confirm-record",
            "--approval-token", "RECORD_TASK_COMMAND_RESULT",
            "--force",
        ])
        self.assertEqual(code, 0)
        result_path = self.workspace / "missions" / "mission-smoke" / "evidence" / "command_results" / "result-smoke.json"
        self.assertTrue(result_path.exists())
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertFalse(payload["authority"]["recorded_results_are_permission"])

    def test_review_reports_readiness(self):
        self.run_cli(self.init_args() + [
            "--confirm-start",
            "--approval-token", "START_TASK_WORKBENCH",
            "--force",
        ])
        self.run_cli([
            "plan",
            "--workspace-root", str(self.workspace),
            "--mission-id", "mission-smoke",
            "--plan-id", "plan-smoke",
            "--task", "Prepare a general task.",
            "--confirm-plan",
            "--approval-token", "PLAN_GENERAL_TASK_WORKBENCH",
            "--force",
        ])
        code = self.run_cli([
            "review",
            "--workspace-root", str(self.workspace),
            "--mission-id", "mission-smoke",
            "--review-id", "review-smoke",
            "--confirm-review",
            "--approval-token", "REVIEW_TASK_WORKBENCH",
            "--force",
        ])
        self.assertEqual(code, 0)
        report = self.workspace / "missions" / "mission-smoke" / "reports" / "review-smoke_task_workbench_review_report.json"
        self.assertTrue(report.exists())
        data = json.loads(report.read_text(encoding="utf-8"))
        self.assertTrue(data["readiness"]["has_plan"])

    def test_wrong_token_blocks_confirmed_init(self):
        code = self.run_cli(self.init_args() + [
            "--confirm-start",
            "--approval-token", "WRONG",
        ])
        self.assertEqual(code, 1)

    def test_unsafe_mission_id_blocks_path_traversal(self):
        code = self.run_cli([
            "init",
            "--workspace-root", str(self.workspace),
            "--mission-id", "../bad",
            "--run-id", "run-smoke",
            "--title", "Bad",
            "--task", "Bad",
            "--confirm-start",
            "--approval-token", "START_TASK_WORKBENCH",
        ])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
