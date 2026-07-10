import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "hokage_shell" / "operator_status.py"
SHELL_PATH = REPO_ROOT / "tools" / "hokage_shell" / "run_hokage_shell.py"


def load_module():
    shell_dir = MODULE_PATH.parent
    if str(shell_dir) not in sys.path:
        sys.path.insert(0, str(shell_dir))
    spec = importlib.util.spec_from_file_location(
        "operator_status",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class OperatorStatusTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.workspace = self.root / "workspace"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "user.name", "Konoha Tests")
        (self.repo / "README.md").write_text(
            "# Test repository\n",
            encoding="utf-8",
        )
        self.git("add", "README.md")
        self.git("commit", "-m", "Initial commit")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        completed = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stderr)
        return completed.stdout.strip()

    def write_session(self, mission_id="status-mission"):
        folder = self.workspace / "missions" / mission_id
        folder.mkdir(parents=True)
        payload = {
            "schema_version": "1.0.0",
            "report_type": "hokage_shell_session",
            "mission_id": mission_id,
            "task": "Review operator evidence",
            "state": "needs_human_review",
            "created_at": "2026-07-10T20:00:00+00:00",
            "updated_at": "2026-07-10T20:05:00+00:00",
            "repo_root": str(self.repo.resolve()),
            "workspace_root": str(self.workspace.resolve()),
            "next_recommended_action": "Review evidence before action.",
        }
        (folder / "hokage_shell_session.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )
        return folder

    def test_clean_repository_status(self):
        report = self.module.build_operator_status(
            self.repo,
            self.workspace,
            stdout_tty=False,
        )

        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["operator_state"], "ready")
        self.assertTrue(report["repo"]["working_tree_clean"])
        self.assertEqual(report["repo"]["branch"], "main")
        self.assertEqual(report["mission"]["mission_count"], 0)

    def test_status_does_not_create_workspace(self):
        self.assertFalse(self.workspace.exists())

        self.module.build_operator_status(
            self.repo,
            self.workspace,
            stdout_tty=False,
        )

        self.assertFalse(self.workspace.exists())

    def test_dirty_repository_requires_attention(self):
        (self.repo / "README.md").write_text(
            "# Changed\n",
            encoding="utf-8",
        )

        report = self.module.build_operator_status(
            self.repo,
            self.workspace,
            stdout_tty=False,
        )

        self.assertEqual(
            report["operator_state"],
            "attention_required",
        )
        self.assertIn(
            "working_tree_dirty",
            report["attention_reasons"],
        )
        self.assertFalse(report["repo"]["working_tree_clean"])

    def test_latest_mission_and_evidence_are_visible(self):
        folder = self.write_session()
        reports = folder / "step_reports"
        reports.mkdir()
        report_path = reports / "001_review.md"
        report_path.write_text("# Evidence\n", encoding="utf-8")

        audit_dir = folder / "local_model_audit"
        audit_dir.mkdir()
        audit_path = audit_dir / "status_repo_consistency_audit.json"
        audit_path.write_text("{}\n", encoding="utf-8")
        patch_path = audit_dir / "status_repo_patch_plan.json"
        patch_path.write_text("{}\n", encoding="utf-8")

        result = self.module.build_operator_status(
            self.repo,
            self.workspace,
            stdout_tty=False,
        )

        mission = result["mission"]
        evidence = mission["evidence"]
        self.assertEqual(
            mission["latest_mission_id"],
            "status-mission",
        )
        self.assertEqual(
            mission["latest_mission"]["state"],
            "needs_human_review",
        )
        self.assertEqual(
            evidence["latest_step_report_path"],
            str(report_path),
        )
        self.assertEqual(
            evidence["latest_audit_json_path"],
            str(audit_path),
        )
        self.assertEqual(
            evidence["latest_patch_plan_path"],
            str(patch_path),
        )

    def test_invalid_mission_requires_attention(self):
        invalid = self.workspace / "missions" / "broken"
        invalid.mkdir(parents=True)
        (invalid / "hokage_shell_session.json").write_text(
            "{invalid",
            encoding="utf-8",
        )

        report = self.module.build_operator_status(
            self.repo,
            self.workspace,
            stdout_tty=False,
        )

        self.assertEqual(
            report["mission"]["invalid_mission_count"],
            1,
        )
        self.assertIn(
            "invalid_mission_sessions",
            report["attention_reasons"],
        )

    def test_terminal_viewer_fallback(self):
        def fake_which(name):
            return "/usr/bin/less" if name == "less" else None

        with mock.patch.object(
            self.module.shutil,
            "which",
            side_effect=fake_which,
        ):
            terminal = self.module.collect_terminal_status(
                plain_requested=True,
                stdout_tty=False,
            )

        self.assertEqual(terminal["preferred_viewer"], "less")
        self.assertTrue(terminal["plain_requested"])
        self.assertFalse(terminal["stdout_is_tty"])

    def test_non_git_root_is_blocked(self):
        outside = self.root / "outside"
        outside.mkdir()

        with self.assertRaises(self.module.OperatorStatusError):
            self.module.build_operator_status(
                outside,
                self.workspace,
                stdout_tty=False,
            )

    def test_shell_status_cli_json(self):
        if not SHELL_PATH.exists():
            self.skipTest("shell integration requires patched repository")

        completed = subprocess.run(
            [
                sys.executable,
                str(SHELL_PATH),
                "--repo-root",
                str(self.repo),
                "--workspace-root",
                str(self.workspace),
                "status",
                "--json",
            ],
            text=True,
            capture_output=True,
            timeout=30,
            env={**os.environ, "PYTHONUTF8": "1"},
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(
            report["report_type"],
            "hokage_operator_status_report",
        )
        self.assertTrue(
            report["authority"]["status_report_is_evidence_only"]
        )
        self.assertEqual(
            report["boundaries"]["private_memory_read"],
            "blocked",
        )


if __name__ == "__main__":
    unittest.main()
