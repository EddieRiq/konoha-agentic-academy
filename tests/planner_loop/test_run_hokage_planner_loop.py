import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "planner_loop" / "run_hokage_planner_loop.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_hokage_planner_loop", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class HokagePlannerLoopTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo_root = self.root / "repo"
        self.workspace_root = self.root / "workspace"
        self.sandbox_root = self.root / "sandbox"
        self.repo_root.mkdir()
        self._write_mission("mission-1")

    def tearDown(self):
        self.tmp.cleanup()

    def _write_mission(self, mission_id):
        mission = self.workspace_root / "missions" / mission_id
        for subdir in ["plans", "reports", "inputs", "context", "outputs", "approvals", "evidence"]:
            (mission / subdir).mkdir(parents=True, exist_ok=True)
        (mission / "charter.md").write_text("# Mission Charter\n\nPlan only.\n", encoding="utf-8")
        (mission / "mission_manifest.json").write_text(
            json.dumps({"mission_id": mission_id, "title": "Test mission"}),
            encoding="utf-8",
        )

    def _fake_delegated_tool(self, repo_root, script, args):
        if script.endswith("run_dry_run_runtime.py"):
            run_id = args[args.index("--run-id") + 1]
            (self.sandbox_root / "runs" / run_id).mkdir(parents=True, exist_ok=True)
            return {"script": script, "returncode": 0, "stdout": "runtime ok", "stderr": ""}

        if script.endswith("invoke_model_gate.py"):
            run_id = args[args.index("--run-id") + 1]
            run_root = self.sandbox_root / "runs" / run_id
            if "--confirm-invocation" in args:
                out_dir = run_root / "model_outputs"
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "model_invocation_output.md").write_text(
                    "# Mock model output\n\n- Step 1: Review charter.\n",
                    encoding="utf-8",
                )
            return {"script": script, "returncode": 0, "stdout": "model ok", "stderr": ""}

        return {"script": script, "returncode": 1, "stdout": "", "stderr": "unexpected"}

    def test_rejects_path_traversal_mission_id(self):
        with self.assertRaises(ValueError):
            self.module.safe_id("../escape", "mission_id")

    def test_resolve_under_rejects_escape(self):
        with self.assertRaises(ValueError):
            self.module.resolve_under(self.workspace_root, "..", "escape")

    def test_preview_writes_reports_but_no_plan(self):
        self.module.run_delegated_tool = self._fake_delegated_tool
        code = self.module.main([
            "--repo-root", str(self.repo_root),
            "--workspace-root", str(self.workspace_root),
            "--mission-id", "mission-1",
            "--sandbox-root", str(self.sandbox_root),
            "--run-id", "planner-preview",
            "--force",
        ])
        self.assertEqual(code, 0)

        report = self.workspace_root / "missions" / "mission-1" / "reports" / "planner-preview_hokage_planner_loop_report.json"
        plan = self.workspace_root / "missions" / "mission-1" / "plans" / "planner-preview_hokage_plan_proposal.md"
        self.assertTrue(report.exists())
        self.assertFalse(plan.exists())

    def test_confirmed_mock_writes_plan_and_reports(self):
        self.module.run_delegated_tool = self._fake_delegated_tool
        code = self.module.main([
            "--repo-root", str(self.repo_root),
            "--workspace-root", str(self.workspace_root),
            "--mission-id", "mission-1",
            "--sandbox-root", str(self.sandbox_root),
            "--run-id", "planner-confirmed",
            "--confirm-invocation",
            "--approval-token", "INVOKE_REAL_MODEL",
            "--force",
        ])
        self.assertEqual(code, 0)

        plan = self.workspace_root / "missions" / "mission-1" / "plans" / "planner-confirmed_hokage_plan_proposal.md"
        report = self.workspace_root / "missions" / "mission-1" / "reports" / "planner-confirmed_hokage_planner_loop_report.json"
        sandbox_report = self.sandbox_root / "runs" / "planner-confirmed" / "hokage_planner_loop_report.json"
        self.assertTrue(plan.exists())
        self.assertTrue(report.exists())
        self.assertTrue(sandbox_report.exists())
        self.assertIn("Model output is evidence only", plan.read_text(encoding="utf-8"))

    def test_confirmed_requires_exact_token(self):
        self.module.run_delegated_tool = self._fake_delegated_tool
        code = self.module.main([
            "--repo-root", str(self.repo_root),
            "--workspace-root", str(self.workspace_root),
            "--mission-id", "mission-1",
            "--sandbox-root", str(self.sandbox_root),
            "--run-id", "bad-token",
            "--confirm-invocation",
            "--approval-token", "WRONG",
            "--force",
        ])
        self.assertEqual(code, 1)

    def test_existing_plan_requires_force(self):
        self.module.run_delegated_tool = self._fake_delegated_tool
        plan = self.workspace_root / "missions" / "mission-1" / "plans" / "existing_hokage_plan_proposal.md"
        plan.write_text("already here", encoding="utf-8")

        code = self.module.main([
            "--repo-root", str(self.repo_root),
            "--workspace-root", str(self.workspace_root),
            "--mission-id", "mission-1",
            "--sandbox-root", str(self.sandbox_root),
            "--run-id", "existing",
            "--confirm-invocation",
            "--approval-token", "INVOKE_REAL_MODEL",
        ])
        self.assertEqual(code, 1)

    def test_missing_workspace_fails(self):
        code = self.module.main([
            "--repo-root", str(self.repo_root),
            "--workspace-root", str(self.workspace_root),
            "--mission-id", "missing",
            "--sandbox-root", str(self.sandbox_root),
            "--run-id", "missing-workspace",
            "--force",
        ])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
