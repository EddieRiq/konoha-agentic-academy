import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "tools" / "git_staging" / "stage_allowlisted_files.py"


def run(cmd, cwd=None, check=True):
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


class GitStagingGateTests(unittest.TestCase):
    def make_repo(self):
        tmp = tempfile.TemporaryDirectory()
        repo = Path(tmp.name)
        run(["git", "init"], cwd=repo)
        (repo / "docs").mkdir()
        (repo / "docs" / "note.md").write_text("# Note\n", encoding="utf-8")
        (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        run(["git", "add", "README.md"], cwd=repo)
        run(["git", "commit", "-m", "initial"], cwd=repo, check=False)
        return tmp, repo

    def test_preview_allowlisted_path_does_not_stage(self):
        tmp, repo = self.make_repo()
        self.addCleanup(tmp.cleanup)

        result = run([
            sys.executable,
            str(TOOL),
            "--repo-root",
            str(repo),
            "--path",
            "docs/note.md",
        ])

        self.assertIn("GIT STAGING PREVIEW", result.stdout)
        status = run(["git", "status", "--short"], cwd=repo).stdout
        self.assertIn("?? docs/", status)

    def test_confirmed_stage_requires_exact_token(self):
        tmp, repo = self.make_repo()
        self.addCleanup(tmp.cleanup)

        result = run([
            sys.executable,
            str(TOOL),
            "--repo-root",
            str(repo),
            "--path",
            "docs/note.md",
            "--confirm-stage",
            "--approval-token",
            "WRONG",
        ], check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GIT STAGING FAILED", result.stdout)

    def test_confirmed_stage_allowlisted_path(self):
        tmp, repo = self.make_repo()
        self.addCleanup(tmp.cleanup)

        result = run([
            sys.executable,
            str(TOOL),
            "--repo-root",
            str(repo),
            "--path",
            "docs/note.md",
            "--confirm-stage",
            "--approval-token",
            "STAGE_ALLOWLISTED_FILES",
        ])

        self.assertIn("GIT STAGING PASSED", result.stdout)
        status = run(["git", "status", "--short"], cwd=repo).stdout
        self.assertIn("A  docs/note.md", status)

    def test_blocks_private_path(self):
        tmp, repo = self.make_repo()
        self.addCleanup(tmp.cleanup)

        private = repo / "alliance" / "kirigakure" / "secret.md"
        private.parent.mkdir(parents=True)
        private.write_text("secret", encoding="utf-8")

        result = run([
            sys.executable,
            str(TOOL),
            "--repo-root",
            str(repo),
            "--path",
            "alliance/kirigakure/secret.md",
        ], check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GIT STAGING FAILED", result.stdout)

    def test_blocks_path_traversal(self):
        tmp, repo = self.make_repo()
        self.addCleanup(tmp.cleanup)

        result = run([
            sys.executable,
            str(TOOL),
            "--repo-root",
            str(repo),
            "--path",
            "../escape.md",
        ], check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GIT STAGING FAILED", result.stdout)

    def test_reads_paths_from_plan(self):
        tmp, repo = self.make_repo()
        self.addCleanup(tmp.cleanup)

        plan = repo / "stage_plan.json"
        plan.write_text(json.dumps({"paths": ["docs/note.md"]}), encoding="utf-8")

        result = run([
            sys.executable,
            str(TOOL),
            "--repo-root",
            str(repo),
            "--plan",
            str(plan),
            "--json",
        ])

        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["mode"], "preview")
        self.assertEqual(payload["requested_paths"], ["docs/note.md"])


if __name__ == "__main__":
    unittest.main()
