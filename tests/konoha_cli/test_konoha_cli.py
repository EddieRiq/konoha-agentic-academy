import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "konoha_cli.py"


def load_cli_module():
    spec = importlib.util.spec_from_file_location("konoha_cli", CLI_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class KonohaCliTests(unittest.TestCase):
    def setUp(self):
        self.cli = load_cli_module()

    def test_runtime_dry_run_routes_to_runner(self):
        parser = self.cli.build_parser()
        ns = parser.parse_args([
            "runtime", "dry-run",
            "--title", "Test",
            "--scope", "Scope",
            "--run-id", "run-1",
            "--sandbox-root", "sandbox",
            "--force",
        ])
        self.assertEqual(ns.command_key, "runtime_runner")
        tool_args = self.cli.build_tool_args(ns)
        self.assertIn("--title", tool_args)
        self.assertIn("Test", tool_args)
        self.assertIn("--force", tool_args)

    def test_package_validate_routes_to_validator(self):
        parser = self.cli.build_parser()
        ns = parser.parse_args(["package", "validate", "package.json"])
        self.assertEqual(ns.command_key, "runtime_validator")
        self.assertEqual(self.cli.build_tool_args(ns), ["package.json"])

    def test_git_stage_supports_multiple_explicit_paths(self):
        parser = self.cli.build_parser()
        ns = parser.parse_args([
            "git", "stage",
            "--path", "README.md",
            "--path", "docs/guides/example.md",
            "--confirm-stage",
            "--approval-token", "STAGE_ALLOWLISTED_FILES",
        ])
        tool_args = self.cli.build_tool_args(ns)
        self.assertEqual(tool_args.count("--path"), 2)
        self.assertIn("--confirm-stage", tool_args)
        self.assertIn("STAGE_ALLOWLISTED_FILES", tool_args)

    def test_run_internal_tool_uses_python_without_shell(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            script = repo / "tools" / "runtime_validator" / "validate_runtime_package.py"
            script.parent.mkdir(parents=True)
            script.write_text("print('ok')\n", encoding="utf-8")

            completed = subprocess.CompletedProcess(args=[], returncode=0)
            with patch.object(self.cli.subprocess, "run", return_value=completed) as mocked_run:
                code = self.cli.run_internal_tool(repo, "runtime_validator", ["package.json"])

            self.assertEqual(code, 0)
            called_command = mocked_run.call_args.args[0]
            called_kwargs = mocked_run.call_args.kwargs

            self.assertEqual(called_command[0], sys.executable)
            self.assertTrue(str(called_command[1]).endswith("validate_runtime_package.py"))
            self.assertEqual(called_command[-1], "package.json")
            self.assertFalse(called_kwargs.get("shell", False))
            self.assertFalse(called_kwargs.get("check", True))

    def test_missing_tool_returns_error_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            code = self.cli.run_internal_tool(repo, "runtime_validator", ["package.json"])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
