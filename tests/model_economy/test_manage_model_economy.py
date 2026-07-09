import importlib.util
import json
import tempfile
import unittest
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "model_economy" / "manage_model_economy.py"
SPEC = importlib.util.spec_from_file_location("manage_model_economy", MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class ModelEconomyTests(unittest.TestCase):
    def test_estimate_tokens_uses_chars_div_four(self):
        self.assertEqual(module.estimate_tokens("abcd"), 1)
        self.assertEqual(module.estimate_tokens("abcde"), 2)
        self.assertEqual(module.estimate_tokens(""), 0)

    def test_profile_preview_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code = module.main([
                "profile",
                "--sandbox-root", str(root / "sandbox"),
                "--profile-id", "profile-preview",
                "--task-type", "technical_development",
                "--risk-level", "medium",
                "--privacy-level", "local_private",
                "--estimated-input-text", "hello world",
                "--json",
            ])
            self.assertEqual(code, 0)
            self.assertFalse((root / "sandbox" / "reports" / "profile-preview_model_runtime_profile.json").exists())

    def test_profile_confirmed_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "profile.json"
            code = module.main([
                "profile",
                "--sandbox-root", str(root / "sandbox"),
                "--profile-id", "profile-confirmed",
                "--task-type", "summarization",
                "--risk-level", "low",
                "--privacy-level", "internal",
                "--confirm-profile",
                "--approval-token", "PROFILE_MODEL_RUNTIME",
                "--output", str(out),
                "--force",
                "--json",
            ])
            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "profiled")
            self.assertTrue(data["authority"]["model_routing_is_evidence_only"])

    def test_wrong_profile_token_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = module.main([
                "profile",
                "--sandbox-root", str(Path(tmp) / "sandbox"),
                "--profile-id", "bad",
                "--confirm-profile",
                "--approval-token", "WRONG",
            ])
            self.assertEqual(code, 1)

    def test_recommend_records_decision_from_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "profile.json"
            module.main([
                "profile",
                "--sandbox-root", str(root / "sandbox"),
                "--profile-id", "profile",
                "--task-type", "technical_development",
                "--risk-level", "medium",
                "--privacy-level", "local_private",
                "--confirm-profile",
                "--approval-token", "PROFILE_MODEL_RUNTIME",
                "--output", str(profile),
                "--force",
            ])
            out = root / "decision.json"
            code = module.main([
                "recommend",
                "--profile", str(profile),
                "--decision-id", "decision",
                "--mission-id", "mission",
                "--confirm-decision",
                "--approval-token", "RECORD_MODEL_ROUTING_DECISION",
                "--output", str(out),
                "--force",
                "--json",
            ])
            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "recorded")
            self.assertEqual(data["selected"]["model_invocation_status"], "not_invoked")

    def test_download_plan_never_executes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "download.json"
            code = module.main([
                "plan-download",
                "--sandbox-root", str(root / "sandbox"),
                "--plan-id", "download",
                "--provider", "ollama",
                "--model", "qwen2.5-coder:7b-instruct",
                "--confirm-plan",
                "--approval-token", "PLAN_LOCAL_MODEL_DOWNLOAD",
                "--output", str(out),
                "--force",
                "--json",
            ])
            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["download_status"], "not_downloaded")
            self.assertEqual(data["execution_status"], "not_executed")

    def test_record_usage_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ledger"
            code = module.main([
                "record-usage",
                "--ledger-root", str(root),
                "--usage-id", "usage-1",
                "--mission-id", "mission",
                "--stage", "planning",
                "--provider", "ollama",
                "--model", "qwen2.5-coder:7b-instruct",
                "--prompt-text", "abcd" * 10,
                "--completion-text", "efgh" * 5,
                "--confirm-record",
                "--approval-token", "RECORD_TOKEN_USAGE",
                "--json",
            ])
            self.assertEqual(code, 0)
            ledger = json.loads((root / "token_usage_ledger.json").read_text(encoding="utf-8"))
            self.assertEqual(ledger["totals"]["records"], 1)
            self.assertEqual(ledger["totals"]["estimated_records"], 1)
            code = module.main(["summarize", "--ledger-root", str(root), "--json"])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
