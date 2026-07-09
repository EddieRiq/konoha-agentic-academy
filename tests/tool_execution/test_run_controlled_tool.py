import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "tool_execution" / "run_controlled_tool.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_controlled_tool", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ControlledToolExecutionGateTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.workspace = self.repo / "sandbox" / "workspace"
        self.sandbox = self.repo / "sandbox"
        self.workspace.mkdir(parents=True)
        self.sandbox.mkdir(parents=True, exist_ok=True)

        script = self.repo / "tools" / "mission_workspace" / "manage_mission_workspace.py"
        script.parent.mkdir(parents=True)
        script.write_text(
            "import sys\n"
            "print('fake mission workspace tool passed')\n"
            "raise SystemExit(0)\n",
            encoding="utf-8",
        )

        self.plan = self.repo / "sandbox" / "plan.json"
        self.plan.write_text(
            json.dumps(
                {
                    "execution_id": "unit-controlled-tool",
                    "mission_id": "unit-mission",
                    "action": "mission_workspace_validate",
                    "requires_human_approval": True,
                    "parameters": {"mission_id": "unit-mission"},
                    "safety": {
                        "execution_scope": "allowlisted_tool_only",
                        "private_context_access": False,
                        "network_access": False,
                        "git_operations": False,
                        "repository_apply": False,
                        "real_model_invocation": False,
                        "arbitrary_shell": False,
                        "background_agent": False,
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_preview_does_not_write_report(self):
        code = self.module.main(
            [
                "--plan",
                str(self.plan),
                "--repo-root",
                str(self.repo),
                "--workspace-root",
                str(self.workspace),
                "--sandbox-root",
                str(self.sandbox),
            ]
        )
        self.assertEqual(code, 0)
        self.assertFalse((self.sandbox / "reports" / "unit-controlled-tool_controlled_tool_execution_report.json").exists())

    def test_confirmed_execution_requires_exact_token(self):
        code = self.module.main(
            [
                "--plan",
                str(self.plan),
                "--repo-root",
                str(self.repo),
                "--workspace-root",
                str(self.workspace),
                "--sandbox-root",
                str(self.sandbox),
                "--confirm-execution",
                "--approval-token",
                "WRONG",
            ]
        )
        self.assertEqual(code, 1)

    def test_confirmed_execution_writes_report(self):
        code = self.module.main(
            [
                "--plan",
                str(self.plan),
                "--repo-root",
                str(self.repo),
                "--workspace-root",
                str(self.workspace),
                "--sandbox-root",
                str(self.sandbox),
                "--confirm-execution",
                "--approval-token",
                "EXECUTE_CONTROLLED_TOOL",
                "--force",
            ]
        )
        self.assertEqual(code, 0)
        report_path = self.sandbox / "reports" / "unit-controlled-tool_controlled_tool_execution_report.json"
        self.assertTrue(report_path.exists())
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["git_operations"], "blocked")
        self.assertIn("fake mission workspace tool passed", report["stdout_tail"])

    def test_rejects_unknown_action(self):
        data = json.loads(self.plan.read_text(encoding="utf-8"))
        data["action"] = "arbitrary_shell"
        self.plan.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(
            self.module.main(
                [
                    "--plan",
                    str(self.plan),
                    "--repo-root",
                    str(self.repo),
                    "--workspace-root",
                    str(self.workspace),
                    "--sandbox-root",
                    str(self.sandbox),
                ]
            ),
            1,
        )

    def test_rejects_private_context_access(self):
        data = json.loads(self.plan.read_text(encoding="utf-8"))
        data["safety"]["private_context_access"] = True
        self.plan.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(
            self.module.main(
                [
                    "--plan",
                    str(self.plan),
                    "--repo-root",
                    str(self.repo),
                    "--workspace-root",
                    str(self.workspace),
                    "--sandbox-root",
                    str(self.sandbox),
                ]
            ),
            1,
        )

    def test_rejects_path_traversal_execution_id(self):
        data = json.loads(self.plan.read_text(encoding="utf-8"))
        data["execution_id"] = "../escape"
        self.plan.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(
            self.module.main(
                [
                    "--plan",
                    str(self.plan),
                    "--repo-root",
                    str(self.repo),
                    "--workspace-root",
                    str(self.workspace),
                    "--sandbox-root",
                    str(self.sandbox),
                ]
            ),
            1,
        )

    def test_missing_required_script_blocks_execution(self):
        script = self.repo / "tools" / "mission_workspace" / "manage_mission_workspace.py"
        script.unlink()
        code = self.module.main(
            [
                "--plan",
                str(self.plan),
                "--repo-root",
                str(self.repo),
                "--workspace-root",
                str(self.workspace),
                "--sandbox-root",
                str(self.sandbox),
            ]
        )
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
