import importlib.util
import json
import sys
import shutil
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "mission_workspace" / "manage_mission_workspace.py"


def load_module():
    spec = importlib.util.spec_from_file_location("manage_mission_workspace", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MissionWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self.tmp.name) / "workspace"

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_workspace_writes_expected_structure(self):
        code = self.module.main([
            "create",
            "--workspace-root", str(self.workspace_root),
            "--mission-id", "safe-mission-1",
            "--title", "Safe mission",
            "--scope", "Create a mission workspace.",
        ])
        self.assertEqual(code, 0)

        root = self.workspace_root / "missions" / "safe-mission-1"
        self.assertTrue((root / "mission_manifest.json").exists())
        self.assertTrue((root / "charter.md").exists())
        self.assertTrue((root / "approvals" / "approval_log.md").exists())
        self.assertTrue((root / "reports" / "mission_workspace_report.json").exists())

        for dirname in self.module.REQUIRED_MISSION_DIRS:
            self.assertTrue((root / dirname).is_dir())

        manifest = json.loads((root / "mission_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["mission_id"], "safe-mission-1")
        self.assertEqual(manifest["safety"]["git_operations"], "blocked")

    def test_validate_workspace_passes_after_create(self):
        self.module.main([
            "create",
            "--workspace-root", str(self.workspace_root),
            "--mission-id", "validate-me",
            "--title", "Validate me",
            "--scope", "Validate this workspace.",
        ])

        code = self.module.main([
            "validate",
            "--workspace-root", str(self.workspace_root),
            "--mission-id", "validate-me",
        ])
        self.assertEqual(code, 0)

        report = self.workspace_root / "missions" / "validate-me" / "reports" / "mission_workspace_validation_report.json"
        self.assertTrue(report.exists())

    def test_validate_workspace_fails_when_missing_required_directory(self):
        self.module.main([
            "create",
            "--workspace-root", str(self.workspace_root),
            "--mission-id", "broken",
            "--title", "Broken",
            "--scope", "Break validation.",
        ])
        target = self.workspace_root / "missions" / "broken" / "plans"
        shutil.rmtree(target)

        code = self.module.main([
            "validate",
            "--workspace-root", str(self.workspace_root),
            "--mission-id", "broken",
        ])
        self.assertEqual(code, 1)

    def test_rejects_path_traversal_mission_id(self):
        code = self.module.main([
            "create",
            "--workspace-root", str(self.workspace_root),
            "--mission-id", "../escape",
            "--title", "Bad",
            "--scope", "Bad.",
        ])
        self.assertEqual(code, 1)
        self.assertFalse((self.workspace_root.parent / "escape").exists())

    def test_force_required_for_existing_workspace(self):
        args = [
            "create",
            "--workspace-root", str(self.workspace_root),
            "--mission-id", "dupe",
            "--title", "Dupe",
            "--scope", "Duplicate.",
        ]
        self.assertEqual(self.module.main(args), 0)
        self.assertEqual(self.module.main(args), 1)
        self.assertEqual(self.module.main(args + ["--force"]), 0)

    def test_list_workspaces(self):
        self.module.main([
            "create",
            "--workspace-root", str(self.workspace_root),
            "--mission-id", "a",
            "--title", "A",
            "--scope", "A.",
        ])
        self.module.main([
            "create",
            "--workspace-root", str(self.workspace_root),
            "--mission-id", "b",
            "--title", "B",
            "--scope", "B.",
        ])

        code = self.module.main([
            "list",
            "--workspace-root", str(self.workspace_root),
        ])
        self.assertEqual(code, 0)

    def test_resolve_under_rejects_escape(self):
        with self.assertRaises(self.module.MissionWorkspaceError):
            self.module.resolve_under(self.workspace_root, self.workspace_root / ".." / "escape")


if __name__ == "__main__":
    unittest.main()
