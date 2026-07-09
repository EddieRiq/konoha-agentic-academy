import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "mission_runtime" / "run_unified_mission.py"
SPEC = importlib.util.spec_from_file_location("run_unified_mission", MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class UnifiedMissionRuntimeTests(unittest.TestCase):
    def test_preview_does_not_write_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code = module.main([
                "run",
                "--workspace-root", str(root / "workspace"),
                "--sandbox-root", str(root / "sandbox"),
                "--mission-id", "preview-mission",
                "--title", "Preview Mission",
                "--task", "Inspect a Python project.",
                "--run-id", "preview-run",
            ])
            self.assertEqual(code, 0)
            self.assertFalse((root / "workspace" / "missions" / "preview-mission").exists())

    def test_confirmed_run_writes_plan_report_and_proposals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code = module.main([
                "run",
                "--workspace-root", str(root / "workspace"),
                "--sandbox-root", str(root / "sandbox"),
                "--mission-id", "docker-airflow-mission",
                "--title", "Docker Airflow Mission",
                "--task", "Create a Docker Airflow workflow that can run JAR files.",
                "--run-id", "run-1",
                "--confirm-start",
                "--approval-token", "START_UNIFIED_MISSION",
                "--force",
            ])
            self.assertEqual(code, 0)
            mission = root / "workspace" / "missions" / "docker-airflow-mission"
            self.assertTrue((mission / "charter.md").exists())
            self.assertTrue((mission / "mission_manifest.json").exists())
            self.assertTrue((mission / "plans" / "run-1_unified_mission_runtime_plan.json").exists())
            proposals = json.loads((mission / "plans" / "run-1_command_proposals.json").read_text(encoding="utf-8"))
            commands = [item["command_id"] for item in proposals["commands"]]
            self.assertIn("inspect-docker-version", commands)
            self.assertIn("inspect-java-version", commands)
            for item in proposals["commands"]:
                self.assertEqual(item["execution_status"], "proposed_only")
                self.assertTrue(item["requires_human_approval"])
            self.assertTrue((mission / "reports" / "run-1_unified_mission_runtime_report.json").exists())
            self.assertTrue((mission / "mission_notification_state.json").exists())

    def test_wrong_token_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code = module.main([
                "run",
                "--workspace-root", str(root / "workspace"),
                "--sandbox-root", str(root / "sandbox"),
                "--mission-id", "bad-token",
                "--title", "Bad Token",
                "--task", "Do something.",
                "--run-id", "run-1",
                "--confirm-start",
                "--approval-token", "WRONG",
            ])
            self.assertEqual(code, 1)

    def test_status_reads_latest_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code = module.main([
                "run",
                "--workspace-root", str(root / "workspace"),
                "--sandbox-root", str(root / "sandbox"),
                "--mission-id", "status-mission",
                "--title", "Status Mission",
                "--task", "Inspect Docker and Python.",
                "--run-id", "run-1",
                "--confirm-start",
                "--approval-token", "START_UNIFIED_MISSION",
                "--force",
            ])
            self.assertEqual(code, 0)
            code = module.main([
                "status",
                "--workspace-root", str(root / "workspace"),
                "--mission-id", "status-mission",
                "--json",
            ])
            self.assertEqual(code, 0)

    def test_path_traversal_identifier_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code = module.main([
                "run",
                "--workspace-root", str(root / "workspace"),
                "--sandbox-root", str(root / "sandbox"),
                "--mission-id", "../escape",
                "--title", "Escape",
                "--task", "Escape.",
                "--run-id", "run-1",
                "--confirm-start",
                "--approval-token", "START_UNIFIED_MISSION",
            ])
            self.assertEqual(code, 1)

    def test_memory_note_requires_memory_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code = module.main([
                "run",
                "--workspace-root", str(root / "workspace"),
                "--sandbox-root", str(root / "sandbox"),
                "--mission-id", "memory-mission",
                "--title", "Memory Mission",
                "--task", "Record memory.",
                "--run-id", "run-1",
                "--confirm-start",
                "--approval-token", "START_UNIFIED_MISSION",
                "--write-memory",
                "--memory-root", str(root / "memory"),
                "--memory-approval-token", "WRONG",
                "--force",
            ])
            self.assertEqual(code, 1)

    def test_memory_note_can_be_written_with_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code = module.main([
                "run",
                "--workspace-root", str(root / "workspace"),
                "--sandbox-root", str(root / "sandbox"),
                "--mission-id", "memory-ok",
                "--title", "Memory OK",
                "--task", "Record memory.",
                "--run-id", "run-1",
                "--confirm-start",
                "--approval-token", "START_UNIFIED_MISSION",
                "--write-memory",
                "--memory-root", str(root / "memory"),
                "--memory-approval-token", "RECORD_YAMANAKA_MEMORY",
                "--force",
            ])
            self.assertEqual(code, 0)
            self.assertTrue((root / "memory" / "10-missions" / "memory-ok_run-1_runtime_note.md").exists())


if __name__ == "__main__":
    unittest.main()
