import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def load_module():
    path = Path("tools/artifact_workflow/run_proposed_artifact_workflow.py")
    spec = importlib.util.spec_from_file_location("run_proposed_artifact_workflow", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ProposedArtifactWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_accepts_safe_run_id(self):
        self.module.validate_run_id("safe-run_01.abc")

    def test_rejects_path_traversal_run_id(self):
        with self.assertRaises(ValueError):
            self.module.validate_run_id("../escape")

    def test_resolve_under_rejects_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            with self.assertRaises(ValueError):
                self.module.resolve_under(root, root / ".." / "escape.txt")

    def test_confirm_apply_requires_exact_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "tools" / "runtime_runner").mkdir(parents=True)
            args = [
                "--title", "test",
                "--scope", "scope",
                "--run-id", "safe-run",
                "--repo-root", str(repo),
                "--sandbox-root", str(repo / "sandbox"),
                "--artifact-path", "docs/example.md",
                "--content", "hello",
                "--artifact-kind", "markdown",
                "--intended-repo-path", "sandbox/tmp/example.md",
                "--confirm-apply",
                "--approval-token", "WRONG",
                "--json",
            ]
            code = self.module.main(args)
            self.assertEqual(code, 1)

    def test_main_writes_report_when_steps_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sandbox = repo / "sandbox"

            def fake_run_tool(command, cwd):
                # Simulate delegated tools and ensure run dir exists after runtime step.
                run_dir = sandbox / "runs" / "safe-run"
                run_dir.mkdir(parents=True, exist_ok=True)
                return {
                    "command": command,
                    "returncode": 0,
                    "stdout": "ok",
                    "stderr": "",
                    "passed": True,
                }

            args = [
                "--title", "test",
                "--scope", "scope",
                "--run-id", "safe-run",
                "--repo-root", str(repo),
                "--sandbox-root", str(sandbox),
                "--artifact-path", "docs/example.md",
                "--content", "hello",
                "--artifact-kind", "markdown",
                "--intended-repo-path", "sandbox/tmp/example.md",
                "--force",
            ]

            with patch.object(self.module, "run_tool", side_effect=fake_run_tool):
                code = self.module.main(args)

            self.assertEqual(code, 0)
            report_path = sandbox / "runs" / "safe-run" / "proposed_artifact_workflow_report.json"
            self.assertTrue(report_path.exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["boundaries"]["git_operations"], "blocked")
            self.assertEqual(report["boundaries"]["private_context_access"], "blocked")


if __name__ == "__main__":
    unittest.main()
