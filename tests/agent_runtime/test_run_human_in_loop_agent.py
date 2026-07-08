import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "agent_runtime" / "run_human_in_loop_agent.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_human_in_loop_agent", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class HumanInLoopAgentRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo_root = self.root / "repo"
        self.workspace_root = self.root / "workspace"
        self.sandbox_root = self.root / "sandbox"
        self.mission_id = "mission-1"
        self.mission_dir = self.workspace_root / "missions" / self.mission_id
        (self.mission_dir / "reports").mkdir(parents=True)
        (self.repo_root / "tools").mkdir(parents=True)
        (self.sandbox_root / "reports").mkdir(parents=True)
        self.contract = self.root / "contract.json"
        self.request = self.root / "request.json"
        self.plan = self.root / "tool_plan.json"
        self.contract.write_text(json.dumps({"provider": "mock"}), encoding="utf-8")
        self.request.write_text(json.dumps({"provider": "mock"}), encoding="utf-8")
        self.plan.write_text(json.dumps({"action": "mission_workspace_validate"}), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def base_args(self):
        return [
            "--repo-root", str(self.repo_root),
            "--workspace-root", str(self.workspace_root),
            "--mission-id", self.mission_id,
            "--sandbox-root", str(self.sandbox_root),
            "--run-id", "agent-run-1",
            "--contract", str(self.contract),
            "--request", str(self.request),
            "--force",
        ]

    def passing_step(self, name, command):
        return self.module.StepResult(name=name, command=command, returncode=0, stdout="ok", stderr="")

    def test_rejects_path_traversal_run_id(self):
        with self.assertRaises(ValueError):
            self.module.require_safe_id("../escape", "run_id")

    def test_resolve_under_rejects_escape(self):
        with self.assertRaises(ValueError):
            self.module.resolve_under(self.workspace_root, "../escape")

    def test_preview_writes_reports_when_steps_pass(self):
        with mock.patch.object(self.module, "run_command", side_effect=self.passing_step):
            code = self.module.main(self.base_args())
        self.assertEqual(code, 0)

        mission_report = self.mission_dir / "reports" / "agent-run-1_human_in_loop_agent_runtime_report.json"
        sandbox_report = self.sandbox_root / "reports" / "agent-run-1_human_in_loop_agent_runtime_report.json"
        self.assertTrue(mission_report.exists())
        self.assertTrue(sandbox_report.exists())

        data = json.loads(mission_report.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "passed")
        self.assertEqual(data["mode"], "preview")
        self.assertEqual(len(data["steps"]), 2)

    def test_confirmed_planning_requires_exact_token(self):
        args = self.base_args() + ["--confirm-planning", "--planning-approval-token", "WRONG"]
        with mock.patch.object(self.module, "run_command", side_effect=self.passing_step):
            code = self.module.main(args)
        self.assertEqual(code, 1)

    def test_confirmed_tool_requires_plan(self):
        args = self.base_args() + ["--confirm-tool-execution", "--tool-approval-token", "EXECUTE_CONTROLLED_TOOL"]
        with mock.patch.object(self.module, "run_command", side_effect=self.passing_step):
            code = self.module.main(args)
        self.assertEqual(code, 1)

    def test_tool_plan_delegates_controlled_tool(self):
        calls = []

        def fake_run(name, command):
            calls.append((name, command))
            return self.passing_step(name, command)

        args = self.base_args() + [
            "--tool-plan", str(self.plan),
            "--confirm-tool-execution",
            "--tool-approval-token", "EXECUTE_CONTROLLED_TOOL",
        ]
        with mock.patch.object(self.module, "run_command", side_effect=fake_run):
            code = self.module.main(args)
        self.assertEqual(code, 0)
        self.assertEqual([name for name, _ in calls], [
            "mission_workspace_validate",
            "hokage_planner_loop",
            "controlled_tool_execution",
        ])

    def test_failed_delegated_step_returns_failure(self):
        def fake_run(name, command):
            if name == "hokage_planner_loop":
                return self.module.StepResult(name, command, 1, "", "bad")
            return self.passing_step(name, command)

        with mock.patch.object(self.module, "run_command", side_effect=fake_run):
            code = self.module.main(self.base_args())
        self.assertEqual(code, 1)

        report = self.mission_dir / "reports" / "agent-run-1_human_in_loop_agent_runtime_report.json"
        data = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "failed")
        self.assertTrue(data["blockers"])


if __name__ == "__main__":
    unittest.main()
