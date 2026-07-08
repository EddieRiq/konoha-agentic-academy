import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "adapter_gate" / "invoke_adapter_gate.py"


def load_module():
    spec = importlib.util.spec_from_file_location("invoke_adapter_gate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def create_run(root: Path, run_id: str = "run-1") -> Path:
    run_dir = root / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "sandbox_run_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "0.13.0",
                "run_id": run_id,
                "mode": "dry_run",
                "boundaries": {
                    "execution": "blocked",
                    "git_operations": "blocked",
                    "private_context_access": "blocked",
                    "network_access": "blocked",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return run_dir


class AdapterInvocationGateTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "sandbox"
        self.run_dir = create_run(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_preview_does_not_write_outputs(self):
        code = self.module.main(
            [
                "--sandbox-root",
                str(self.root),
                "--run-id",
                "run-1",
                "--task",
                "Draft a checklist.",
            ]
        )
        self.assertEqual(code, 0)
        self.assertFalse((self.run_dir / "adapter_outputs").exists())
        self.assertFalse((self.run_dir / "adapter_invocation_gate_report.json").exists())

    def test_confirmed_mock_writes_report_and_output(self):
        code = self.module.main(
            [
                "--sandbox-root",
                str(self.root),
                "--run-id",
                "run-1",
                "--task",
                "Draft a checklist.",
                "--mode",
                "checklist",
                "--confirm-invocation",
                "--approval-token",
                "INVOKE_ADAPTER_GATE",
                "--enable-mock-adapter",
            ]
        )
        self.assertEqual(code, 0)
        self.assertTrue((self.run_dir / "adapter_outputs" / "adapter_gate_mock_output.md").exists())
        report = json.loads((self.run_dir / "adapter_invocation_gate_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["invocation_state"], "mock_invoked")
        self.assertEqual(report["boundaries"]["real_adapter_execution"], "blocked")

    def test_wrong_token_blocks_invocation(self):
        code = self.module.main(
            [
                "--sandbox-root",
                str(self.root),
                "--run-id",
                "run-1",
                "--task",
                "Draft a checklist.",
                "--confirm-invocation",
                "--approval-token",
                "WRONG",
                "--enable-mock-adapter",
            ]
        )
        self.assertEqual(code, 1)
        self.assertFalse((self.run_dir / "adapter_outputs").exists())

    def test_real_adapter_is_blocked(self):
        code = self.module.main(
            [
                "--sandbox-root",
                str(self.root),
                "--run-id",
                "run-1",
                "--adapter",
                "real",
                "--task",
                "Call a real adapter.",
                "--confirm-invocation",
                "--approval-token",
                "INVOKE_ADAPTER_GATE",
            ]
        )
        self.assertEqual(code, 1)

    def test_rejects_path_traversal_run_id(self):
        code = self.module.main(
            [
                "--sandbox-root",
                str(self.root),
                "--run-id",
                "../escape",
                "--task",
                "bad",
            ]
        )
        self.assertEqual(code, 1)

    def test_existing_output_requires_force(self):
        args = [
            "--sandbox-root",
            str(self.root),
            "--run-id",
            "run-1",
            "--task",
            "Draft a checklist.",
            "--confirm-invocation",
            "--approval-token",
            "INVOKE_ADAPTER_GATE",
            "--enable-mock-adapter",
        ]
        self.assertEqual(self.module.main(args), 0)
        self.assertEqual(self.module.main(args), 1)
        self.assertEqual(self.module.main(args + ["--force"]), 0)


if __name__ == "__main__":
    unittest.main()
