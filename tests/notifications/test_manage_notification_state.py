import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "notifications" / "manage_notification_state.py"


def load_module():
    spec = importlib.util.spec_from_file_location("manage_notification_state_test_module", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MissionNotificationStateTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.workspace = self.root / "workspace"
        self.mission_id = "mission-test"
        self.mission_dir = self.workspace / "missions" / self.mission_id
        (self.mission_dir / "reports").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_preview_does_not_write_state(self):
        code = self.module.main([
            "set",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--event-id", "preview",
            "--state", "waiting_user_input",
            "--reason", "Need user clarification."
        ])
        self.assertEqual(code, 0)
        self.assertFalse((self.mission_dir / "mission_notification_state.json").exists())

    def test_confirmed_state_update_writes_state_log_and_report(self):
        code = self.module.main([
            "set",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--event-id", "confirmed",
            "--state", "waiting_approval",
            "--severity", "attention",
            "--reason", "Need approval to continue.",
            "--required-human-action", "Review the plan proposal.",
            "--actor", "eduardo",
            "--confirm-state-update",
            "--approval-token", "UPDATE_NOTIFICATION_STATE",
            "--force",
        ])
        self.assertEqual(code, 0)

        state_path = self.mission_dir / "mission_notification_state.json"
        log_path = self.mission_dir / "notifications" / "notification_log.md"
        report_path = self.mission_dir / "reports" / "confirmed_mission_notification_state_report.json"

        self.assertTrue(state_path.exists())
        self.assertTrue(log_path.exists())
        self.assertTrue(report_path.exists())

        payload = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["current_state"], "waiting_approval")
        self.assertEqual(payload["updated_by"], "eduardo")

    def test_bad_token_fails(self):
        code = self.module.main([
            "set",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--state", "blocked",
            "--reason", "Bad token test.",
            "--confirm-state-update",
            "--approval-token", "WRONG",
        ])
        self.assertEqual(code, 1)

    def test_rejects_path_traversal_mission_id(self):
        code = self.module.main([
            "set",
            "--workspace-root", str(self.workspace),
            "--mission-id", "../escape",
            "--state", "blocked",
            "--reason", "Traversal should fail.",
        ])
        self.assertEqual(code, 1)

    def test_inspect_existing_state(self):
        self.module.main([
            "set",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--event-id", "inspectable",
            "--state", "ready_for_review",
            "--reason", "Ready for review.",
            "--confirm-state-update",
            "--approval-token", "UPDATE_NOTIFICATION_STATE",
            "--force",
        ])
        code = self.module.main([
            "inspect",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--json",
        ])
        self.assertEqual(code, 0)

    def test_list_states(self):
        code = self.module.main(["states"])
        self.assertEqual(code, 0)

    def test_resolve_under_rejects_escape(self):
        with self.assertRaises(ValueError):
            self.module.resolve_under(self.workspace, "..", "escape")


if __name__ == "__main__":
    unittest.main()
