import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "hokage_shell" / "run_hokage_shell.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_hokage_shell", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["run_hokage_shell"] = module
    spec.loader.exec_module(module)
    return module


class HokageShellTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        (self.repo / "docs" / "guides").mkdir(parents=True)
        (self.repo / "README.md").write_text(
            "# Konoha\n\n"
            "## Konoha Beta Real Supervised Task Runtime\n\n"
            "v3.0.0 is the first beta.\n\n"
            "## v3.0.1 Local Model Bootstrap\n\n"
            "Ollama local model audit path.\n",
            encoding="utf-8",
        )
        (self.repo / "CHANGELOG.md").write_text(
            "## [Unreleased]\n\n- Added v3.0.1 Local Model Bootstrap.\n",
            encoding="utf-8",
        )
        (self.repo / "docs" / "roadmap.md").write_text(
            "### v3.0.1 Local Model Bootstrap, Repo Audit and Patch Flow\n",
            encoding="utf-8",
        )
        (self.repo / "docs" / "guides" / "README.md").write_text(
            "## Konoha Beta Runtime\n\nlocal model repo consistency audit.\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_persona_loads(self):
        persona = self.module.load_persona("sarcastic_lab_ai", self.repo)
        self.assertEqual(persona["persona_id"], "sarcastic_lab_ai")
        self.assertTrue(persona["must_not_override_safety"])

    def test_deterministic_scan_finds_markers(self):
        scan = self.module.deterministic_repo_scan(self.repo)
        self.assertEqual(scan["status"], "passed")
        self.assertGreater(len(scan["coverage"]["beta_runtime_status"]), 0)
        self.assertGreater(len(scan["coverage"]["local_model_bootstrap"]), 0)

    def test_create_session_and_memory_note(self):
        paths = self.module.make_paths(
            str(self.repo),
            str(self.root / "workspace"),
            str(self.root / "memory" / "obsidian"),
        )
        persona = self.module.load_persona("calm_mentor", self.repo)
        session = self.module.create_session(paths, "Review repo docs", persona, mission_id="mission-1")
        note = self.module.write_obsidian_mission_note(paths, session, {"deterministic_scan": None})
        self.assertTrue((paths.workspace_root / "missions" / "mission-1" / "hokage_shell_session.json").exists())
        self.assertTrue(note.exists())
        self.assertIn("Mission: mission-1", note.read_text(encoding="utf-8"))

    def test_smoke_cli_json(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(self.repo),
                "--workspace-root",
                str(self.root / "workspace"),
                "--memory-root",
                str(self.root / "memory" / "obsidian"),
                "--persona",
                "sarcastic_lab_ai",
                "--no-animation",
                "smoke",
                "--task",
                "Review README alignment",
                "--mission-id",
                "smoke-mission",
                "--json",
            ],
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["mission_id"], "smoke-mission")
        self.assertTrue(Path(payload["session_path"]).exists())
        self.assertTrue(Path(payload["memory_note_path"]).exists())


if __name__ == "__main__":
    unittest.main()
