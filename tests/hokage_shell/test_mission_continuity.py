import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "hokage_shell" / "mission_continuity.py"
SHELL_PATH = REPO_ROOT / "tools" / "hokage_shell" / "run_hokage_shell.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "mission_continuity",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MissionContinuityTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.workspace = self.root / "workspace"
        self.repo.mkdir()
        self.workspace.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def write_session(
        self,
        mission_id,
        *,
        created_at,
        updated_at,
        state="needs_human_review",
        task="Review repository evidence",
        repo_root=None,
        workspace_root=None,
    ):
        folder = self.workspace / "missions" / mission_id
        folder.mkdir(parents=True)
        payload = {
            "schema_version": "1.0.0",
            "report_type": "hokage_shell_session",
            "mission_id": mission_id,
            "task": task,
            "state": state,
            "created_at": created_at,
            "updated_at": updated_at,
            "repo_root": str((repo_root or self.repo).resolve()),
            "workspace_root": str(
                (workspace_root or self.workspace).resolve()
            ),
            "memory_root": str((self.root / "private-memory").resolve()),
            "persona": {"persona_id": "calm_mentor"},
            "authority": {
                "ui_is_not_permission": True,
            },
            "boundaries": {},
            "outputs": {},
            "token_usage": {},
            "next_recommended_action": "Review evidence before action.",
        }
        (folder / "hokage_shell_session.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )
        return folder

    def test_latest_uses_updated_at_not_directory_name(self):
        self.write_session(
            "z-old",
            created_at="2026-07-01T00:00:00+00:00",
            updated_at="2026-07-02T00:00:00+00:00",
        )
        self.write_session(
            "a-new",
            created_at="2026-07-01T00:00:00+00:00",
            updated_at="2026-07-03T00:00:00+00:00",
        )

        report = self.module.list_missions(
            self.workspace,
            repo_root=self.repo,
        )

        self.assertEqual(report["mission_count"], 2)
        self.assertEqual(report["latest_mission_id"], "a-new")
        self.assertEqual(
            [item["mission_id"] for item in report["missions"]],
            ["a-new", "z-old"],
        )

    def test_invalid_session_is_excluded_from_latest(self):
        valid = self.write_session(
            "valid-mission",
            created_at="2026-07-01T00:00:00+00:00",
            updated_at="2026-07-03T00:00:00+00:00",
        )
        invalid = self.workspace / "missions" / "broken-mission"
        invalid.mkdir(parents=True)
        (invalid / "hokage_shell_session.json").write_text(
            "{not-json",
            encoding="utf-8",
        )

        report = self.module.list_missions(self.workspace)

        self.assertEqual(report["mission_count"], 1)
        self.assertEqual(report["invalid_mission_count"], 1)
        self.assertEqual(report["latest_mission_id"], valid.name)
        self.assertEqual(
            report["invalid_missions"][0]["mission_id"],
            "broken-mission",
        )

    def test_resume_snapshot_includes_latest_event(self):
        folder = self.write_session(
            "mission-events",
            created_at="2026-07-01T00:00:00+00:00",
            updated_at="2026-07-03T00:00:00+00:00",
        )
        events = [
            {
                "event_type": "session_created",
                "created_at": "2026-07-01T00:00:00+00:00",
            },
            {
                "event_type": "deterministic_repo_scan_recorded",
                "created_at": "2026-07-03T00:00:00+00:00",
            },
        ]
        (folder / "events.ndjson").write_text(
            "\n".join(json.dumps(item) for item in events) + "\n",
            encoding="utf-8",
        )

        report = self.module.build_resume_report(
            self.workspace,
            repo_root=self.repo,
            mission_id="mission-events",
        )

        self.assertEqual(report["status"], "passed")
        self.assertEqual(
            report["continuity"]["last_event_type"],
            "deterministic_repo_scan_recorded",
        )
        self.assertEqual(report["continuity"]["event_count"], 2)
        self.assertTrue(report["continuity"]["repo_root_matches"])

    def test_resume_reports_invalid_event_lines_without_failing(self):
        folder = self.write_session(
            "mission-invalid-event",
            created_at="2026-07-01T00:00:00+00:00",
            updated_at="2026-07-03T00:00:00+00:00",
        )
        (folder / "events.ndjson").write_text(
            '{"event_type":"session_created","created_at":"2026-07-01T00:00:00+00:00"}\n'
            "invalid-json\n",
            encoding="utf-8",
        )

        report = self.module.build_resume_report(
            self.workspace,
            latest=True,
        )

        self.assertEqual(report["status"], "passed")
        self.assertEqual(
            report["continuity"]["invalid_event_count"],
            1,
        )

    def test_path_traversal_mission_id_is_blocked(self):
        with self.assertRaises(self.module.MissionContinuityError):
            self.module.validate_mission_id("../outside")

    def test_missing_mission_returns_not_found_exit_code(self):
        report = self.module.build_resume_report(
            self.workspace,
            mission_id="missing-mission",
        )

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(self.module.exit_code_for_report(report), 1)

    def test_repo_root_mismatch_is_visible(self):
        self.write_session(
            "moved-mission",
            created_at="2026-07-01T00:00:00+00:00",
            updated_at="2026-07-03T00:00:00+00:00",
            repo_root=self.root / "another-repo",
        )

        report = self.module.build_resume_report(
            self.workspace,
            repo_root=self.repo,
            latest=True,
        )

        self.assertFalse(
            report["continuity"]["repo_root_matches"]
        )
        self.assertTrue(
            report["continuity"]["workspace_root_matches"]
        )

    def test_shell_missions_and_resume_cli_json(self):
        if not SHELL_PATH.exists():
            self.skipTest("shell integration requires patched repository")

        mission = self.write_session(
            "cli-mission",
            created_at="2026-07-01T00:00:00+00:00",
            updated_at="2026-07-03T00:00:00+00:00",
        )

        common = [
            sys.executable,
            str(SHELL_PATH),
            "--repo-root",
            str(self.repo),
            "--workspace-root",
            str(self.workspace),
        ]

        listed = subprocess.run(
            [*common, "missions", "--json"],
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(listed.returncode, 0, listed.stderr)
        listing = json.loads(listed.stdout)
        self.assertEqual(
            listing["latest_mission_id"],
            mission.name,
        )

        resumed = subprocess.run(
            [*common, "resume", "--latest", "--json"],
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        resume_report = json.loads(resumed.stdout)
        self.assertEqual(resume_report["status"], "passed")
        self.assertEqual(
            resume_report["mission_id"],
            mission.name,
        )


if __name__ == "__main__":
    unittest.main()
