import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "git_commit" / "create_git_commit.py"


def load_module():
    spec = importlib.util.spec_from_file_location("create_git_commit", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False)


@unittest.skipIf(shutil.which("git") is None, "git is required for git commit gate tests")
class GitCommitGateTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        run(["git", "init"], self.repo)
        run(["git", "config", "user.email", "konoha@example.invalid"], self.repo)
        run(["git", "config", "user.name", "Konoha Test"], self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def write_and_stage(self, path, content="# test"):
        full = self.repo / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        result = run(["git", "add", "--", path], self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_empty_message(self):
        self.assertIsNotNone(self.module.validate_commit_message(""))
        self.assertIsNotNone(self.module.validate_commit_message("bad\nmessage"))

    def test_allows_simple_message(self):
        self.assertIsNone(self.module.validate_commit_message("Add safe docs update"))

    def test_rejects_private_staged_path(self):
        self.write_and_stage("alliance/kirigakure/private.md")
        ok, staged, err = self.module.get_staged_paths(self.repo)
        self.assertTrue(ok, err)
        allowed, blockers = self.module.inspect_staged_paths(staged)
        self.assertEqual(allowed, [])
        self.assertEqual(len(blockers), 1)

    def test_preview_does_not_create_commit(self):
        self.write_and_stage("docs/example.md")
        code = self.module.main([
            "--repo-root", str(self.repo),
            "--message", "Add safe docs update",
        ])
        self.assertEqual(code, 0)
        log = run(["git", "log", "--oneline"], self.repo)
        self.assertNotEqual(log.returncode, 0)

    def test_confirmed_commit_requires_token(self):
        self.write_and_stage("docs/example.md")
        code = self.module.main([
            "--repo-root", str(self.repo),
            "--message", "Add safe docs update",
            "--confirm-commit",
            "--approval-token", "WRONG",
        ])
        self.assertEqual(code, 1)

    def test_confirmed_commit_creates_commit(self):
        self.write_and_stage("docs/example.md")
        code = self.module.main([
            "--repo-root", str(self.repo),
            "--message", "Add safe docs update",
            "--confirm-commit",
            "--approval-token", self.module.APPROVAL_TOKEN,
        ])
        self.assertEqual(code, 0)
        log = run(["git", "log", "--oneline"], self.repo)
        self.assertEqual(log.returncode, 0)
        self.assertIn("Add safe docs update", log.stdout)

    def test_json_preview_report(self):
        self.write_and_stage("docs/example.md")
        # Directly test report shape without capturing stdout from main.
        report = self.module.build_report(
            "passed",
            "preview",
            str(self.repo),
            "Add safe docs update",
            ["docs/example.md"],
            [],
            None,
            [],
        )
        encoded = json.dumps(report)
        self.assertIn("git_commit_gate", encoded)
        self.assertEqual(report["safety"]["git_push"], "blocked")


if __name__ == "__main__":
    unittest.main()
