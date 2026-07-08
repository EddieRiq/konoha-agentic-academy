import importlib.util
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "mission_workflow" / "run_dry_run_mission.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_dry_run_mission", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DryRunMissionWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_rejects_path_traversal_run_id(self):
        with self.assertRaises(ValueError):
            self.module.validate_run_id("../escape")

    def test_accepts_safe_run_id(self):
        self.module.validate_run_id("demo-run_01")

    def test_resolve_under_rejects_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            with self.assertRaises(ValueError):
                self.module.resolve_under(root, root / ".." / "escape")

    def test_write_report_inside_run_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "sandbox" / "runs" / "demo"
            run_dir.mkdir(parents=True)
            report = {"status": "passed"}
            path = self.module.write_report(run_dir, report)
            self.assertTrue(path.exists())
            self.assertEqual(json.loads(path.read_text())["status"], "passed")

    def test_main_writes_report_when_steps_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            sandbox = repo / "sandbox"
            repo.mkdir()
            for rel in [
                "tools/config_validator/validate_konoha_config.py",
                "tools/runtime_runner/run_dry_run_runtime.py",
                "tools/runtime_validator/validate_runtime_package.py",
                "tools/runtime_inspector/inspect_runtime_package.py",
                "tools/runtime_registry/list_runtime_runs.py",
                "tools/repo_inspector/inspect_public_repo.py",
            ]:
                p = repo / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("# stub\n", encoding="utf-8")

            def fake_run(command):
                run_dir = sandbox / "runs" / "demo"
                run_dir.mkdir(parents=True, exist_ok=True)
                (run_dir / "runtime_package.json").write_text("{}", encoding="utf-8")
                return self.module.StepResult(
                    name="",
                    status="passed",
                    returncode=0,
                    command=command,
                    stdout_tail=["ok"],
                    stderr_tail=[],
                )

            with patch.object(self.module, "run_command", side_effect=fake_run):
                code = self.module.main([
                    "--title", "Demo",
                    "--scope", "Demo scope",
                    "--run-id", "demo",
                    "--repo-root", str(repo),
                    "--sandbox-root", str(sandbox),
                    "--force",
                    "--skip-repo-inspection",
                ])

            self.assertEqual(code, 0)
            report_path = sandbox / "runs" / "demo" / "mission_workflow_report.json"
            self.assertTrue(report_path.exists())
            report = json.loads(report_path.read_text())
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["boundaries"]["execution"], "blocked")


if __name__ == "__main__":
    unittest.main()
