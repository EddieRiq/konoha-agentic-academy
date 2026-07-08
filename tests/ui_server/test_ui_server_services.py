import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_module(name, relative_path):
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class LocalWebUIServicesTests(unittest.TestCase):
    def setUp(self):
        self.workspace_service = load_module(
            "workspace_service_under_test",
            "tools/ui_server/services/workspace_service.py",
        )
        self.approval_service = load_module(
            "approval_service_under_test",
            "tools/ui_server/services/approval_service.py",
        )
        self.report_service = load_module(
            "report_service_under_test",
            "tools/ui_server/services/report_service.py",
        )
        self.command_service = load_module(
            "command_service_under_test",
            "tools/ui_server/services/command_service.py",
        )
        self.safety_service = load_module(
            "safety_service_under_test",
            "tools/ui_server/services/safety_service.py",
        )
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.workspace = self.root / "workspace"
        self.sandbox = self.root / "sandbox"

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_and_list_mission_workspace(self):
        manifest = self.workspace_service.create_mission_workspace(
            workspace_root=self.workspace,
            mission_id="mission-alpha",
            title="Mission Alpha",
            scope="Validate UI workspace creation.",
        )
        self.assertEqual(manifest["mission_id"], "mission-alpha")
        self.assertTrue((self.workspace / "missions" / "mission-alpha" / "charter.md").exists())

        missions = self.workspace_service.list_missions(self.workspace)
        self.assertEqual(len(missions), 1)
        self.assertEqual(missions[0]["mission_id"], "mission-alpha")

    def test_rejects_path_traversal_mission_id(self):
        with self.assertRaises(ValueError):
            self.workspace_service.create_mission_workspace(
                workspace_root=self.workspace,
                mission_id="../escape",
                title="bad",
                scope="bad",
            )

    def test_inspect_mission_lists_plans_reports_and_evidence(self):
        self.workspace_service.create_mission_workspace(
            workspace_root=self.workspace,
            mission_id="mission-beta",
            title="Mission Beta",
            scope="Inspect structure.",
        )
        mission_dir = self.workspace / "missions" / "mission-beta"
        (mission_dir / "plans" / "plan.md").write_text("# plan", encoding="utf-8")
        (mission_dir / "reports" / "report.json").write_text("{}", encoding="utf-8")
        (mission_dir / "evidence" / "evidence.md").write_text("# evidence", encoding="utf-8")

        detail = self.workspace_service.inspect_mission(self.workspace, "mission-beta")
        self.assertIn("plan.md", detail["plans"])
        self.assertIn("report.json", detail["reports"])
        self.assertIn("evidence.md", detail["evidence"])

    def test_record_approval_requires_exact_token(self):
        self.workspace_service.create_mission_workspace(
            workspace_root=self.workspace,
            mission_id="mission-gamma",
            title="Mission Gamma",
            scope="Approval token test.",
        )
        with self.assertRaises(PermissionError):
            self.approval_service.record_decision(
                workspace_root=self.workspace,
                mission_id="mission-gamma",
                transition="planner_review",
                decision="approved",
                reason="bad token",
                approval_token="WRONG",
            )

        report = self.approval_service.record_decision(
            workspace_root=self.workspace,
            mission_id="mission-gamma",
            transition="planner_review",
            decision="approved",
            reason="reviewed",
            approval_token="APPROVE_MISSION_TRANSITION",
        )
        self.assertEqual(report["status"], "passed")
        events = self.approval_service.list_approval_events(self.workspace, "mission-gamma")
        self.assertEqual(len(events), 1)
        self.assertFalse(events[0]["token_stored"])

    def test_write_ui_session_report_under_sandbox_reports(self):
        report = self.report_service.write_ui_session_report(
            sandbox_root=self.sandbox,
            workspace_root=self.workspace,
            mission_count=2,
        )
        report_path = Path(report["report_path"])
        self.assertTrue(report_path.exists())
        self.assertEqual(json.loads(report_path.read_text(encoding="utf-8"))["mission_count"], 2)
        self.assertEqual(report["git_operations"], "blocked")

    def test_command_suggestions_do_not_execute(self):
        commands = self.command_service.suggest_commands(
            repo_root=Path("."),
            workspace_root=Path("sandbox/workspace"),
            sandbox_root=Path("sandbox"),
            mission_id="mission-delta",
        )
        self.assertIn("planner_preview", commands)
        self.assertIn("run_hokage_planner_loop.py", commands["planner_preview"])

    def test_safety_boundaries_include_v2_alignment_gate(self):
        boundaries = self.safety_service.boundaries()
        names = {item["name"] for item in boundaries}
        self.assertIn("v2.0 Alignment Review Gate", names)
        self.assertIn("Git operations", names)


if __name__ == "__main__":
    unittest.main()
