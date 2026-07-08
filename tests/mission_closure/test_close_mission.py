import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO_ROOT / "tools" / "mission_closure" / "close_mission.py"


def load_module():
    spec = importlib.util.spec_from_file_location("close_mission_module", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def create_mission(workspace_root: Path, mission_id: str) -> Path:
    mission = workspace_root / "missions" / mission_id
    for rel in ["reports", "plans", "approvals", "evidence", "inputs", "context", "outputs"]:
        (mission / rel).mkdir(parents=True, exist_ok=True)
    (mission / "charter.md").write_text("# Charter\n", encoding="utf-8")
    (mission / "mission_manifest.json").write_text(
        json.dumps({"mission_id": mission_id, "title": "Test mission"}, indent=2) + "\n",
        encoding="utf-8",
    )
    (mission / "reports" / "agent_report.json").write_text("{}\n", encoding="utf-8")
    (mission / "plans" / "plan.md").write_text("# Plan\n", encoding="utf-8")
    (mission / "approvals" / "approval_log.md").write_text("# Approvals\n", encoding="utf-8")
    (mission / "evidence" / "note.md").write_text("# Evidence\n", encoding="utf-8")
    return mission


class MissionClosureTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.workspace = self.root / "workspace"
        self.memory = self.root / "memory" / "vault"
        self.mission_id = "mission-close-test"
        create_mission(self.workspace, self.mission_id)

    def tearDown(self):
        self.tmp.cleanup()

    def base_args(self):
        return [
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--memory-root", str(self.memory),
            "--closure-id", "close-test",
        ]

    def test_preview_does_not_write_outputs(self):
        code = self.module.main(self.base_args())
        self.assertEqual(code, 0)
        self.assertFalse((self.workspace / "missions" / self.mission_id / "reports" / "close-test_mission_closure_report.json").exists())

    def test_confirmed_close_writes_reports_and_memory(self):
        code = self.module.main(self.base_args() + [
            "--confirm-close",
            "--approval-token", "CLOSE_MISSION_WITH_TEACHBACK",
            "--teachback-confirmation", "I_CAN_EXPLAIN_AND_DEFEND_THIS_MISSION",
            "--teachback-summary", "I can explain what was done, why it was done, and how to defend it.",
            "--closure-reason", "Mission reviewed and ready for closure.",
            "--human-actor", "eduardo",
            "--force",
        ])
        self.assertEqual(code, 0)

        mission_root = self.workspace / "missions" / self.mission_id
        self.assertTrue((mission_root / "reports" / "close-test_mission_closure_report.json").exists())
        self.assertTrue((mission_root / "reports" / "close-test_teachback_record.json").exists())
        self.assertTrue((mission_root / "reports" / "close-test_notification_state.json").exists())
        self.assertTrue((mission_root / "mission_status.json").exists())

        status = json.loads((mission_root / "mission_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["status"], "closed")

        self.assertTrue((self.memory / "10-missions" / f"{self.mission_id}.md").exists())
        self.assertTrue((self.memory / "20-decisions" / f"{self.mission_id}_closure_decision.md").exists())
        self.assertTrue((self.memory / "60-context-packs" / f"{self.mission_id}_context_pack.md").exists())

    def test_rejects_wrong_approval_token(self):
        code = self.module.main(self.base_args() + [
            "--confirm-close",
            "--approval-token", "WRONG",
            "--teachback-confirmation", "I_CAN_EXPLAIN_AND_DEFEND_THIS_MISSION",
            "--teachback-summary", "I can explain what was done, why it was done, and how to defend it.",
            "--closure-reason", "Mission reviewed and ready for closure.",
        ])
        self.assertEqual(code, 1)

    def test_rejects_missing_teachback_confirmation(self):
        code = self.module.main(self.base_args() + [
            "--confirm-close",
            "--approval-token", "CLOSE_MISSION_WITH_TEACHBACK",
            "--teachback-summary", "I can explain what was done, why it was done, and how to defend it.",
            "--closure-reason", "Mission reviewed and ready for closure.",
        ])
        self.assertEqual(code, 1)

    def test_rejects_short_teachback_summary(self):
        code = self.module.main(self.base_args() + [
            "--confirm-close",
            "--approval-token", "CLOSE_MISSION_WITH_TEACHBACK",
            "--teachback-confirmation", "I_CAN_EXPLAIN_AND_DEFEND_THIS_MISSION",
            "--teachback-summary", "too short",
            "--closure-reason", "Mission reviewed and ready for closure.",
        ])
        self.assertEqual(code, 1)

    def test_rejects_path_traversal_mission_id(self):
        code = self.module.main([
            "--workspace-root", str(self.workspace),
            "--mission-id", "../escape",
            "--memory-root", str(self.memory),
        ])
        self.assertEqual(code, 1)

    def test_markdown_frontmatter_contains_type(self):
        content = self.module.markdown_frontmatter({"type": "mission_memory", "mission_id": "m1"}, "# Body")
        self.assertIn("---", content)
        self.assertIn("type:", content)
        self.assertIn("# Body", content)


if __name__ == "__main__":
    unittest.main()
