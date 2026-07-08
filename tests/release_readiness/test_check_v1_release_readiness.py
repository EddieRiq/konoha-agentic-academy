import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "release_readiness" / "check_v1_release_readiness.py"


def load_module():
    spec = importlib.util.spec_from_file_location("check_v1_release_readiness", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReleaseReadinessTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.tmp.name) / "repo"
        self.sandbox_root = Path(self.tmp.name) / "sandbox"
        self.repo_root.mkdir()
        self.sandbox_root.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def create_required_paths(self):
        for relative in self.module.REQUIRED_PUBLIC_PATHS:
            path = self.repo_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if relative.endswith(".md"):
                path.write_text(
                    "Execution: blocked\nGit operations\nPrivate context access\nNetwork access\n",
                    encoding="utf-8",
                )
            else:
                path.write_text("placeholder\n", encoding="utf-8")

    def test_rejects_path_traversal_run_id(self):
        with self.assertRaises(ValueError):
            self.module.validate_run_id("../escape")

    def test_missing_required_paths_fail(self):
        result = self.module.check_required_paths(self.repo_root)
        self.assertFalse(result["passed"])
        self.assertGreater(result["missing_count"], 0)

    def test_required_paths_pass_when_present(self):
        self.create_required_paths()
        result = self.module.check_required_paths(self.repo_root)
        self.assertTrue(result["passed"])
        self.assertEqual(result["missing_count"], 0)

    def test_report_written_with_skip_smoke_and_stubbed_commands(self):
        self.create_required_paths()

        def fake_run_command(name, command, cwd):
            return {
                "name": name,
                "command": list(command),
                "returncode": 0,
                "passed": True,
                "stdout": "",
                "stderr": "",
            }

        original = self.module.run_command
        self.module.run_command = fake_run_command
        try:
            args = [
                "--repo-root",
                str(self.repo_root),
                "--sandbox-root",
                str(self.sandbox_root),
                "--run-id",
                "release-test",
                "--skip-smoke",
                "--force",
            ]
            code = self.module.main(args)
            self.assertEqual(code, 0)
            report_path = self.sandbox_root / "reports" / "release-test_v1_release_readiness_report.json"
            self.assertTrue(report_path.exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])
            self.assertEqual(report["release"]["target_version"], "v1.0.0")
        finally:
            self.module.run_command = original

    def test_existing_report_requires_force(self):
        self.create_required_paths()

        def fake_run_command(name, command, cwd):
            return {
                "name": name,
                "command": list(command),
                "returncode": 0,
                "passed": True,
                "stdout": "",
                "stderr": "",
            }

        original = self.module.run_command
        self.module.run_command = fake_run_command
        try:
            args = SimpleNamespace(
                repo_root=str(self.repo_root),
                sandbox_root=str(self.sandbox_root),
                run_id="existing-report",
                allow_dirty=True,
                skip_smoke=True,
                json=False,
                force=True,
            )
            report = self.module.build_report(args)
            report_path = self.sandbox_root / "reports" / "existing-report_v1_release_readiness_report.json"
            self.module.write_json_lf(report_path, report)

            code = self.module.main([
                "--repo-root",
                str(self.repo_root),
                "--sandbox-root",
                str(self.sandbox_root),
                "--run-id",
                "existing-report",
                "--skip-smoke",
            ])
            self.assertEqual(code, 1)
        finally:
            self.module.run_command = original


if __name__ == "__main__":
    unittest.main()
