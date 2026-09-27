"""Separate-process, terminal-first workflow using synthetic public repos."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class StudyTerminalTests(unittest.TestCase):
    def run_command(self, command, options, *extra):
        return subprocess.run([sys.executable, "-m", "tools.repo_evidence.workflow", command, *options, *extra],
                              capture_output=True, text=True, timeout=20,
                              env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})

    def test_two_local_studies_human_teachback_and_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            setups = []
            for name in ("donor", "target"):
                repo, state = base / name, base / (name + "-state")
                repo.mkdir()
                (repo / "app.py").write_text("def main(): return 1\n")
                (repo / "test_app.py").write_text("import app\n")
                options = ["--repo", str(repo), "--authorize-repo", str(repo), "--public",
                           "--authorization-note", "synthetic terminal fixture", "--state-root", str(state)]
                cp = self.run_command("study", options)
                self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
                record = json.loads(cp.stdout)
                identity = record["study"]["study_id"]
                options += ["--study-id", identity]
                cp = self.run_command("explain", options)
                self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
                self.assertIn(":entendido", cp.stdout)
                cp = self.run_command("respond", options, "--human-input", "understood")
                self.assertFalse(json.loads(cp.stdout)["completed_by_user"])
                cp = self.run_command("recommend", options)
                self.assertEqual(cp.returncode, 1)
                cp = self.run_command("respond", options, "--human-input", ":entendido")
                self.assertTrue(json.loads(cp.stdout)["completed_by_user"])
                setups.append((repo, state, identity, options))
            target_repo, target_state, target_id, _ = setups[1]
            cp = self.run_command("compare", setups[0][3], "--target-repo", str(target_repo),
                "--authorize-target-repo", str(target_repo), "--target-public",
                "--target-authorization-note", "synthetic terminal fixture", "--target-state-root", str(target_state),
                "--target-study-id", target_id)
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            report = json.loads(cp.stdout)
            self.assertTrue(report["recommendations"])
            self.assertFalse(report["authorizes_action"])
            self.assertEqual(report["target_study_id"], target_id)
