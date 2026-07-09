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


    def test_deterministic_scan_writes_markdown_report(self):
        paths = self.module.make_paths(
            str(self.repo),
            str(self.root / "workspace"),
            str(self.root / "memory" / "obsidian"),
        )
        persona = self.module.load_persona("calm_mentor", self.repo)
        session = self.module.create_session(paths, "Review repo docs", persona, mission_id="mission-md")
        scan = self.module.deterministic_repo_scan(self.repo)
        scan_json = paths.workspace_root / "missions" / session["mission_id"] / "deterministic_repo_scan.json"
        self.module.write_json(scan_json, scan)
        md = self.module.write_deterministic_scan_markdown(paths, session["mission_id"], scan, scan_json)
        self.assertTrue(md.exists())
        text = md.read_text(encoding="utf-8")
        self.assertIn("deterministic repo scan", text)
        self.assertIn("Marker coverage", text)

    def test_audit_summary_suppresses_false_positive_without_patch(self):
        paths = self.module.make_paths(
            str(self.repo),
            str(self.root / "workspace"),
            str(self.root / "memory" / "obsidian"),
        )
        persona = self.module.load_persona("calm_mentor", self.repo)
        session = self.module.create_session(paths, "Review repo docs", persona, mission_id="mission-audit")
        audit_dir = paths.workspace_root / "missions" / "mission-audit" / "local_model_audit"
        audit_dir.mkdir(parents=True)
        audit_json = audit_dir / "audit_repo_consistency_audit.json"
        patch_json = audit_dir / "audit_repo_patch_plan.json"
        self.module.write_json(audit_json, {
            "audit": {
                "status": "no_validated_inconsistencies_found",
                "provider": "ollama",
                "model": "mock",
                "usage": {"input_tokens": 10, "output_tokens": 5, "usage_source": "mock_estimated"},
                "model_suggested_issues": [{"id": "readme_missing_v3_beta_status", "severity": "medium"}],
                "validated_issues": [],
                "suppressed_issues": [{"id": "readme_missing_v3_beta_status", "severity": "medium", "reason": "covered by markers"}],
            }
        })
        self.module.write_json(patch_json, {"operations": []})
        audit = {"status": "passed", "model": "mock", "report_path": str(audit_json), "patch_plan_path": str(patch_json)}
        summary = self.module.summarize_audit_result(audit, self.repo)
        self.assertEqual(summary["validated_count"], 0)
        self.assertEqual(summary["suppressed_count"], 1)
        self.assertIn("No patch recommended", summary["recommendation"])
        md = self.module.write_local_audit_markdown(paths, "mission-audit", audit, summary)
        self.assertTrue(md.exists())
        self.assertIn("Suppressed issues", md.read_text(encoding="utf-8"))

    def test_review_cli_json(self):
        subprocess.run(
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
                "review-mission",
                "--json",
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=True,
        )
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
                "review",
                "--mission-id",
                "review-mission",
                "--json",
            ],
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "passed")
        self.assertTrue(payload["latest_report_path"].endswith(".md"))


if __name__ == "__main__":
    unittest.main()
