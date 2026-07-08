import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "mock_adapter" / "run_mock_adapter.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_mock_adapter", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MockAdapterTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.sandbox = self.root / "sandbox"
        self.run_dir = self.sandbox / "runs" / "safe-run"
        self.run_dir.mkdir(parents=True)
        manifest = {
            "schema_version": "0.13.0",
            "run_id": "safe-run",
            "mode": "dry_run",
            "boundaries": {
                "execution": "blocked",
                "adapter_execution": "blocked",
                "git_operations": "blocked",
                "private_context_access": "blocked",
            },
        }
        (self.run_dir / "sandbox_run_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_accepts_safe_run_id(self):
        self.module.assert_safe_run_id("safe-run_01.abc")

    def test_rejects_path_traversal_run_id(self):
        with self.assertRaises(ValueError):
            self.module.assert_safe_run_id("../escape")

    def test_requires_existing_manifest(self):
        code = self.module.main([
            "--sandbox-root", str(self.sandbox),
            "--run-id", "missing-run",
            "--task", "Draft summary",
        ])
        self.assertEqual(code, 1)

    def test_writes_output_and_report_inside_run_dir(self):
        code = self.module.main([
            "--sandbox-root", str(self.sandbox),
            "--run-id", "safe-run",
            "--task", "Draft a public note",
            "--mode", "template_note",
            "--force",
        ])
        self.assertEqual(code, 0)
        self.assertTrue((self.run_dir / "adapter_outputs" / "mock_adapter_output.md").exists())
        report_path = self.run_dir / "mock_adapter_invocation_report.json"
        self.assertTrue(report_path.exists())
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["boundaries"]["adapter_execution"], "mock_only")
        self.assertEqual(report["boundaries"]["git_operations"], "blocked")

    def test_rejects_unsafe_output_name(self):
        code = self.module.main([
            "--sandbox-root", str(self.sandbox),
            "--run-id", "safe-run",
            "--task", "Draft",
            "--output-name", "../escape.md",
        ])
        self.assertEqual(code, 1)

    def test_json_output(self):
        code = self.module.main([
            "--sandbox-root", str(self.sandbox),
            "--run-id", "safe-run",
            "--task", "Draft JSON",
            "--json",
            "--force",
        ])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
