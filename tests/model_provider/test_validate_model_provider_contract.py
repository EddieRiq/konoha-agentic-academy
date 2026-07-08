import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "model_provider" / "validate_model_provider_contract.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_model_provider_contract", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ModelProviderContractTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.contract = {
            "contract_version": "1.4.0",
            "provider_allowlist": ["mock", "openai", "anthropic", "ollama"],
            "default_provider": "mock",
            "network_access": "blocked",
            "real_model_invocation": "blocked",
            "private_context_access": "blocked",
            "max_prompt_tokens": 4000,
            "max_completion_tokens": 1000,
            "max_estimated_cost_usd": 0.5,
            "allowed_context_sources": ["mission_workspace", "sandbox", "public_repo"],
            "blocked_context_sources": ["private_village", "env", "credentials", "secrets"],
            "required_approval_token": "INVOKE_MODEL_PROVIDER_GATE",
            "redaction_required": True,
            "logging_required": True,
        }
        self.request = {
            "request_id": "req-001",
            "mission_id": "mission-001",
            "provider": "mock",
            "model": "mock-planner-v1",
            "purpose": "planning",
            "prompt": "Draft a public dry-run mission plan.",
            "context_sources": ["mission_workspace", "sandbox"],
            "estimated_prompt_tokens": 500,
            "requested_completion_tokens": 300,
            "estimated_cost_usd": 0.0,
            "contains_private_context": False,
            "requires_network": False,
        }

    def write_json(self, directory, name, payload):
        path = Path(directory) / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_valid_contract_and_request_pass(self):
        blockers = self.module.validate_contract(self.contract)
        blockers.extend(self.module.validate_request(self.contract, self.request))
        self.assertEqual(blockers, [])

    def test_real_provider_request_can_be_planned_but_invocation_is_blocked(self):
        request = dict(self.request)
        request["provider"] = "openai"
        request["model"] = "gpt-example"
        blockers = self.module.validate_request(self.contract, request)
        report = self.module.build_report(self.contract, request, blockers)
        self.assertEqual(blockers, [])
        self.assertEqual(report["checks"]["real_model_invocation"], "blocked")

    def test_rejects_non_allowlisted_provider(self):
        request = dict(self.request)
        request["provider"] = "unknown"
        blockers = self.module.validate_request(self.contract, request)
        self.assertIn("provider is not allowlisted: unknown", blockers)

    def test_rejects_private_context(self):
        request = dict(self.request)
        request["contains_private_context"] = True
        request["context_sources"] = ["private_village"]
        blockers = self.module.validate_request(self.contract, request)
        self.assertTrue(any("private context" in blocker for blocker in blockers))
        self.assertTrue(any("context source is blocked" in blocker for blocker in blockers))

    def test_rejects_network_request(self):
        request = dict(self.request)
        request["requires_network"] = True
        blockers = self.module.validate_request(self.contract, request)
        self.assertIn("request requires network access, which is blocked in v1.4", blockers)

    def test_rejects_budget_overage(self):
        request = dict(self.request)
        request["estimated_prompt_tokens"] = 999999
        request["estimated_cost_usd"] = 10.0
        blockers = self.module.validate_request(self.contract, request)
        self.assertTrue(any("estimated_prompt_tokens exceeds" in blocker for blocker in blockers))
        self.assertTrue(any("estimated_cost_usd exceeds" in blocker for blocker in blockers))

    def test_rejects_secret_like_prompt(self):
        request = dict(self.request)
        request["prompt"] = "Use password=supersecret in the prompt."
        blockers = self.module.validate_request(self.contract, request)
        self.assertIn("prompt appears to contain a secret-like pattern", blockers)

    def test_main_prints_json_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract_path = self.write_json(tmp, "contract.json", self.contract)
            request_path = self.write_json(tmp, "request.json", self.request)
            code = self.module.main([
                "--contract", str(contract_path),
                "--request", str(request_path),
                "--json",
            ])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
