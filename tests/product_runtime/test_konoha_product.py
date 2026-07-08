import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "product_runtime" / "konoha_product.py"


def load_module():
    spec = importlib.util.spec_from_file_location("konoha_product_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class KonohaProductRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_required_repo_files(self):
        for rel in self.module.REQUIRED_PUBLIC_PATHS:
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if rel.endswith(".json"):
                path.write_text(
                    json.dumps(
                        {
                            "sandbox": {"root": "sandbox"},
                            "approval": {"required": True},
                            "blocked": ["private_context", "network"],
                        }
                    ),
                    encoding="utf-8",
                )
            else:
                path.write_text("Execution: blocked\nGit operations\nPrivate context access\nNetwork access\n", encoding="utf-8")

    def test_init_creates_workspace_manifest(self):
        code = self.module.main([
            "init",
            "--repo-root", str(self.repo),
            "--workspace-root", "sandbox/workspace",
        ])
        self.assertEqual(code, 0)
        manifest = self.repo / "sandbox" / "workspace" / "workspace_manifest.json"
        self.assertTrue(manifest.exists())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["workspace_type"], "konoha_product_runtime_workspace")

    def test_mission_new_creates_expected_structure(self):
        code = self.module.main([
            "mission", "new",
            "--repo-root", str(self.repo),
            "--workspace-root", "sandbox/workspace",
            "--mission-id", "mission-001",
            "--title", "Test mission",
            "--scope", "Create a safe local workspace.",
        ])
        self.assertEqual(code, 0)
        mission = self.repo / "sandbox" / "workspace" / "missions" / "mission-001"
        self.assertTrue((mission / "charter.md").exists())
        self.assertTrue((mission / "mission_manifest.json").exists())
        for rel in self.module.MISSION_DIRS:
            self.assertTrue((mission / rel).is_dir())

    def test_mission_id_rejects_path_traversal(self):
        code = self.module.main([
            "mission", "new",
            "--repo-root", str(self.repo),
            "--workspace-root", "sandbox/workspace",
            "--mission-id", "../escape",
            "--title", "Bad",
            "--scope", "Bad",
        ])
        self.assertEqual(code, 1)

    def test_config_validate_passes_public_config_shape(self):
        config = self.repo / "konoha.config.example.json"
        config.write_text(
            json.dumps(
                {
                    "sandbox": {"root": "sandbox"},
                    "approval": {"required": True},
                    "blocked": ["network", "private_context"],
                }
            ),
            encoding="utf-8",
        )
        code = self.module.main(["config", "validate", "--config", str(config)])
        self.assertEqual(code, 0)

    def test_config_validate_rejects_invalid_json(self):
        config = self.repo / "bad.json"
        config.write_text("{bad", encoding="utf-8")
        code = self.module.main(["config", "validate", "--config", str(config)])
        self.assertEqual(code, 1)

    def test_doctor_passes_when_required_paths_exist(self):
        self.write_required_repo_files()
        code = self.module.main([
            "doctor",
            "--repo-root", str(self.repo),
            "--workspace-root", "sandbox/workspace",
            "--config", "konoha.config.example.json",
        ])
        self.assertEqual(code, 0)

    def test_run_dry_run_delegates_to_allowlisted_tool(self):
        calls = []

        def fake_delegate(repo_root, script_rel_path, args):
            calls.append((repo_root, script_rel_path, list(args)))
            return 0

        original = self.module.run_delegated_tool
        self.module.run_delegated_tool = fake_delegate
        try:
            code = self.module.main([
                "run", "dry-run",
                "--repo-root", str(self.repo),
                "--sandbox-root", "sandbox",
                "--run-id", "safe-run",
                "--title", "Safe run",
                "--scope", "Delegate only.",
                "--force",
            ])
        finally:
            self.module.run_delegated_tool = original

        self.assertEqual(code, 0)
        self.assertEqual(calls[0][1], "tools/mission_workflow/run_dry_run_mission.py")
        self.assertIn("--run-id", calls[0][2])
        self.assertIn("safe-run", calls[0][2])


if __name__ == "__main__":
    unittest.main()
