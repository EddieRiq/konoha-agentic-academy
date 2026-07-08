import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "model_invocation" / "invoke_model_gate.py"


def load_module():
    spec = importlib.util.spec_from_file_location("invoke_model_gate", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ModelInvocationGateTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.sandbox = self.root / "sandbox"
        self.run_id = "unit-model-run"
        self.run_dir = self.sandbox / "runs" / self.run_id
        self.run_dir.mkdir(parents=True)

        self.contract = self.root / "contract.json"
        self.request = self.root / "request.json"

        self.contract.write_text(json.dumps({
            "contract_version": "1.5.0",
            "real_model_invocation_enabled": True,
            "providers": {
                "mock": {"enabled": True},
                "openai": {"enabled": True, "endpoint": "https://api.openai.com/v1/chat/completions"}
            },
            "blocked_context_sources": ["private_village", "alliance/kirigakure"],
            "max_prompt_tokens": 2000,
            "max_completion_tokens": 1000,
            "max_estimated_cost_usd": 1.0
        }), encoding="utf-8")

        self.request.write_text(json.dumps({
            "request_id": "unit-request",
            "mission_id": "unit-mission",
            "provider": "mock",
            "model": "mock-reviewer",
            "purpose": "planning",
            "prompt": "Draft a public checklist.",
            "context_sources": ["mission_workspace", "sandbox"],
            "estimated_prompt_tokens": 100,
            "requested_completion_tokens": 50,
            "estimated_cost_usd": 0.0,
            "contains_private_context": False,
            "requires_network": False
        }), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def args(self, *extra):
        return [
            "--contract", str(self.contract),
            "--request", str(self.request),
            "--sandbox-root", str(self.sandbox),
            "--run-id", self.run_id,
            *extra,
        ]

    def test_preview_does_not_write_outputs(self):
        code = self.module.main(self.args())
        self.assertEqual(code, 0)
        self.assertFalse((self.run_dir / "model_outputs").exists())
        self.assertFalse((self.run_dir / "model_invocation_gate_report.json").exists())

    def test_confirmed_mock_writes_report_and_output(self):
        code = self.module.main(self.args(
            "--confirm-invocation",
            "--approval-token", "INVOKE_REAL_MODEL",
            "--force",
        ))
        self.assertEqual(code, 0)
        self.assertTrue((self.run_dir / "model_outputs" / "model_invocation_output.md").exists())
        report = json.loads((self.run_dir / "model_invocation_gate_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["provider"], "mock")
        self.assertFalse(report["model_output_is_permission"])

    def test_wrong_token_blocks_confirmed_invocation(self):
        code = self.module.main(self.args(
            "--confirm-invocation",
            "--approval-token", "WRONG",
            "--force",
        ))
        self.assertEqual(code, 1)

    def test_existing_output_requires_force(self):
        self.assertEqual(self.module.main(self.args(
            "--confirm-invocation",
            "--approval-token", "INVOKE_REAL_MODEL",
            "--force",
        )), 0)
        self.assertEqual(self.module.main(self.args(
            "--confirm-invocation",
            "--approval-token", "INVOKE_REAL_MODEL",
        )), 1)

    def test_private_context_is_blocked(self):
        request = json.loads(self.request.read_text(encoding="utf-8"))
        request["contains_private_context"] = True
        self.request.write_text(json.dumps(request), encoding="utf-8")
        self.assertEqual(self.module.main(self.args()), 1)

    def test_secret_like_prompt_is_blocked(self):
        request = json.loads(self.request.read_text(encoding="utf-8"))
        request["prompt"] = "Use api_key=abc123 in the request"
        self.request.write_text(json.dumps(request), encoding="utf-8")
        self.assertEqual(self.module.main(self.args()), 1)

    def test_real_provider_requires_network_flag(self):
        request = json.loads(self.request.read_text(encoding="utf-8"))
        request["provider"] = "openai"
        request["model"] = "gpt-example"
        request["requires_network"] = True
        self.request.write_text(json.dumps(request), encoding="utf-8")
        code = self.module.main(self.args(
            "--confirm-invocation",
            "--approval-token", "INVOKE_REAL_MODEL",
        ))
        self.assertEqual(code, 1)

    def test_rejects_path_traversal_run_id(self):
        code = self.module.main([
            "--contract", str(self.contract),
            "--request", str(self.request),
            "--sandbox-root", str(self.sandbox),
            "--run-id", "../escape",
        ])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
