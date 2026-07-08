import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "dogfood" / "run_dogfood_mission_suite.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_dogfood_mission_suite", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DogfoodMissionSuiteTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_accepts_safe_run_id(self):
        self.assertEqual(self.module.validate_run_id("v0-29_dogfood.smoke"), "v0-29_dogfood.smoke")

    def test_rejects_path_traversal_run_id(self):
        with self.assertRaises(self.module.DogfoodError):
            self.module.validate_run_id("../escape")
        with self.assertRaises(self.module.DogfoodError):
            self.module.validate_run_id("bad..id")

    def test_resolve_under_rejects_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sandbox"
            root.mkdir()
            with self.assertRaises(self.module.DogfoodError):
                self.module.resolve_under(root, "../escape")

    def test_build_steps_contains_expected_safe_workflows(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            sandbox = Path(tmp) / "sandbox"
            repo.mkdir()
            sandbox.mkdir()
            config = repo / "konoha.config.example.json"
            config.write_text("{}", encoding="utf-8")

            steps = self.module.build_steps(repo, sandbox, "dogfood", config)
            names = [step["name"] for step in steps]

            self.assertIn("project_config_validation", names)
            self.assertIn("end_to_end_dry_run_mission_workflow", names)
            self.assertIn("proposed_artifact_workflow_preview", names)
            self.assertIn("adapter_invocation_gate_mock_confirmed", names)
            self.assertIn("git_readiness_read_only", names)

    def test_main_writes_report_when_steps_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            sandbox = Path(tmp) / "sandbox"
            repo.mkdir()
            sandbox.mkdir()
            config = repo / "konoha.config.example.json"
            config.write_text("{}", encoding="utf-8")

            original_run_command = self.module.run_command
            try:
                self.module.run_command = lambda command, repo_root, timeout_seconds: {
                    "returncode": 0,
                    "stdout": "ok",
                    "stderr": "",
                }
                code = self.module.main([
                    "--repo-root",
                    str(repo),
                    "--sandbox-root",
                    str(sandbox),
                    "--config",
                    str(config),
                    "--run-id",
                    "dogfood-test",
                ])
            finally:
                self.module.run_command = original_run_command

            self.assertEqual(code, 0)
            report_path = sandbox / "reports" / "dogfood-test_dogfood_mission_suite_report.json"
            self.assertTrue(report_path.exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["summary"]["failed_steps"], 0)
            self.assertTrue(report["human_review_required"])

    def test_main_stops_on_failed_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            sandbox = Path(tmp) / "sandbox"
            repo.mkdir()
            sandbox.mkdir()
            config = repo / "konoha.config.example.json"
            config.write_text("{}", encoding="utf-8")

            calls = []

            def fake_run_command(command, repo_root, timeout_seconds):
                calls.append(command)
                return {"returncode": 1, "stdout": "", "stderr": "failed"}

            original_run_command = self.module.run_command
            try:
                self.module.run_command = fake_run_command
                code = self.module.main([
                    "--repo-root",
                    str(repo),
                    "--sandbox-root",
                    str(sandbox),
                    "--config",
                    str(config),
                    "--run-id",
                    "dogfood-fail",
                ])
            finally:
                self.module.run_command = original_run_command

            self.assertEqual(code, 1)
            self.assertEqual(len(calls), 1)
            report = json.loads(
                (sandbox / "reports" / "dogfood-fail_dogfood_mission_suite_report.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["summary"]["failed_steps"], 1)


if __name__ == "__main__":
    unittest.main()
