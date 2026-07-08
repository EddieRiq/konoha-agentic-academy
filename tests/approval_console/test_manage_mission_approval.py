import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "approval_console" / "manage_mission_approval.py"


def load_module():
    spec = importlib.util.spec_from_file_location("manage_mission_approval", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class HumanApprovalConsoleTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp.name) / "workspace"
        self.mission_id = "mission-approval-smoke"
        self.mission = self.workspace / "missions" / self.mission_id

        for folder in [
            "inputs",
            "context",
            "plans",
            "outputs",
            "reports",
            "approvals",
            "evidence",
        ]:
            (self.mission / folder).mkdir(parents=True, exist_ok=True)

        (self.mission / "README.md").write_text("# Mission\n", encoding="utf-8")
        (self.mission / "charter.md").write_text("# Charter\n", encoding="utf-8")
        (self.mission / "approvals" / "approval_log.md").write_text("# Approval log\n", encoding="utf-8")
        (self.mission / "mission_manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "mission_id": self.mission_id,
                    "title": "Approval console smoke mission",
                    "scope": "Test approval console.",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_status_accepts_valid_workspace(self):
        code = self.module.main([
            "status",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
        ])
        self.assertEqual(code, 0)

    def test_inspect_json_accepts_valid_workspace(self):
        code = self.module.main([
            "inspect",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--json",
        ])
        self.assertEqual(code, 0)

    def test_approve_writes_event_log_and_report(self):
        code = self.module.main([
            "approve",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--transition", "apply_plan_preview",
            "--decision", "approved_for_preview",
            "--reason", "Evidence reviewed by human.",
            "--approval-token", "APPROVE_MISSION_TRANSITION",
        ])
        self.assertEqual(code, 0)

        events = self.mission / "approvals" / "approval_events.jsonl"
        report = self.mission / "reports" / "mission_approval_console_report.json"
        self.assertTrue(events.exists())
        self.assertTrue(report.exists())

        lines = [line for line in events.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        payload = json.loads(lines[0])
        self.assertEqual(payload["event_type"], "approval")
        self.assertTrue(payload["approval_token_verified"])

    def test_reject_wrong_token_fails(self):
        code = self.module.main([
            "reject",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--transition", "apply_plan",
            "--decision", "rejected",
            "--reason", "Token should fail.",
            "--approval-token", "WRONG",
        ])
        self.assertEqual(code, 1)
        self.assertFalse((self.mission / "approvals" / "approval_events.jsonl").exists())

    def test_rejects_path_traversal_mission_id(self):
        code = self.module.main([
            "status",
            "--workspace-root", str(self.workspace),
            "--mission-id", "../escape",
        ])
        self.assertEqual(code, 1)

    def test_approvals_list_after_approval(self):
        self.assertEqual(self.module.main([
            "approve",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--transition", "mission_close",
            "--decision", "approved_for_close_review",
            "--reason", "Human confirmed teachback.",
            "--approval-token", "APPROVE_MISSION_TRANSITION",
        ]), 0)

        code = self.module.main([
            "approvals", "list",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
        ])
        self.assertEqual(code, 0)

    def test_evidence_and_report_lists_are_read_only(self):
        (self.mission / "evidence" / "note.md").write_text("evidence", encoding="utf-8")
        (self.mission / "reports" / "report.json").write_text("{}", encoding="utf-8")

        evidence_code = self.module.main([
            "evidence", "list",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
        ])
        reports_code = self.module.main([
            "reports", "list",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
        ])

        self.assertEqual(evidence_code, 0)
        self.assertEqual(reports_code, 0)


if __name__ == "__main__":
    unittest.main()
