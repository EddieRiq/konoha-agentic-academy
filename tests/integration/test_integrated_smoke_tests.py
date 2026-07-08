import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "integration" / "run_integrated_smoke_tests.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_integrated_smoke_tests", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class IntegratedSmokeTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_accepts_safe_run_id(self):
        self.assertEqual(self.module.validate_run_id("v0-26-smoke_1"), "v0-26-smoke_1")

    def test_rejects_path_traversal_run_id(self):
        with self.assertRaises(self.module.IntegrationError):
            self.module.validate_run_id("../escape")

    def test_resolve_under_rejects_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(self.module.IntegrationError):
                self.module.resolve_under(root, "../escape.json")

    def test_build_report_marks_failed_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            steps = [
                {"name": "first", "passed": True},
                {"name": "second", "passed": False},
            ]
            report = self.module.build_report(root, root / "sandbox", "safe-run", steps)
            self.assertFalse(report["passed"])
            self.assertEqual(report["failed_steps"], ["second"])
            self.assertEqual(report["safety"]["execution"], "blocked")

    def test_write_report_stays_inside_sandbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp) / "sandbox"
            report = {"passed": True}
            report_path = self.module.write_report(sandbox, "safe-run", report)
            self.assertTrue(report_path.exists())
            loaded = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(loaded["passed"])
            self.assertIn("reports", report_path.parts)


if __name__ == "__main__":
    unittest.main()
