import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "self_review" / "run_self_review_git_gate.py"

spec = importlib.util.spec_from_file_location("run_self_review_git_gate", SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, check=False)


class SelfReviewGitGateTests(unittest.TestCase):
    def make_mission(self, root: Path):
        workspace = root / "workspace"
        mission = workspace / "missions" / "mission-1"
        (mission / "reports").mkdir(parents=True)
        (mission / "evidence").mkdir()
        (mission / "plans").mkdir()
        (mission / "reports" / "runtime.json").write_text('{"status":"passed"}', encoding="utf-8")
        (mission / "evidence" / "note.md").write_text("# evidence\n", encoding="utf-8")
        (mission / "plans" / "plan.json").write_text('{"plan":"ok"}', encoding="utf-8")
        return workspace, mission

    def make_git_repo(self, root: Path):
        repo = root / "repo"
        repo.mkdir()
        git(repo, "init")
        git(repo, "config", "user.email", "konoha@example.invalid")
        git(repo, "config", "user.name", "Konoha Test")
        (repo / "README.md").write_text("# repo\n", encoding="utf-8")
        git(repo, "add", "README.md")
        git(repo, "commit", "-m", "Initial commit")
        return repo

    def test_review_preview_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace, mission = self.make_mission(Path(tmp))
            rc = module.main([
                "review",
                "--workspace-root", str(workspace),
                "--mission-id", "mission-1",
                "--review-id", "review-1",
            ])
            self.assertEqual(rc, 0)
            self.assertFalse((mission / "reports" / "review-1_self_review_report.json").exists())

    def test_confirmed_review_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace, mission = self.make_mission(Path(tmp))
            rc = module.main([
                "review",
                "--workspace-root", str(workspace),
                "--mission-id", "mission-1",
                "--review-id", "review-1",
                "--confirm-review",
                "--approval-token", "RECORD_SELF_REVIEW",
                "--force",
            ])
            self.assertEqual(rc, 0)
            report = json.loads((mission / "reports" / "review-1_self_review_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "recorded")
            self.assertEqual(report["mission_inventory"]["evidence_files_count"], 1)

    def test_optimization_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace, mission = self.make_mission(Path(tmp))
            rc = module.main([
                "optimize",
                "--workspace-root", str(workspace),
                "--mission-id", "mission-1",
                "--optimization-id", "opt-1",
                "--confirm-optimization",
                "--approval-token", "RECORD_OPTIMIZATION_PLAN",
                "--force",
            ])
            self.assertEqual(rc, 0)
            self.assertTrue((mission / "reports" / "opt-1_optimization_plan.json").exists())

    def test_git_plan_rejects_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.make_git_repo(Path(tmp))
            rc = module.main([
                "git-plan",
                "--repo-root", str(repo),
                "--plan-id", "bad-plan",
                "--paths", ".env",
                "--commit-message", "Bad",
                "--confirm-plan",
                "--approval-token", "PLAN_GIT_OPERATION",
            ])
            self.assertEqual(rc, 1)

    def test_git_plan_writes_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self.make_git_repo(root)
            (repo / "README.md").write_text("# repo\n\nchange\n", encoding="utf-8")
            out = root / "plan.json"
            rc = module.main([
                "git-plan",
                "--repo-root", str(repo),
                "--plan-id", "plan-1",
                "--paths", "README.md",
                "--commit-message", "Update README",
                "--confirm-plan",
                "--approval-token", "PLAN_GIT_OPERATION",
                "--output", str(out),
                "--force",
            ])
            self.assertEqual(rc, 0)
            plan = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(plan["paths"], ["README.md"])
            self.assertEqual(plan["status"], "recorded")

    def test_stage_and_commit_from_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self.make_git_repo(root)
            (repo / "README.md").write_text("# repo\n\nchange\n", encoding="utf-8")
            out = root / "plan.json"
            rc = module.main([
                "git-plan",
                "--repo-root", str(repo),
                "--plan-id", "plan-1",
                "--paths", "README.md",
                "--commit-message", "Update README",
                "--confirm-plan",
                "--approval-token", "PLAN_GIT_OPERATION",
                "--output", str(out),
                "--force",
            ])
            self.assertEqual(rc, 0)
            rc = module.main([
                "stage",
                "--plan", str(out),
                "--confirm-stage",
                "--approval-token", "APPROVE_GIT_STAGE",
                "--force",
            ])
            self.assertEqual(rc, 0)
            rc = module.main([
                "commit",
                "--plan", str(out),
                "--confirm-commit",
                "--approval-token", "APPROVE_GIT_COMMIT",
                "--force",
            ])
            self.assertEqual(rc, 0)
            log = git(repo, "log", "--oneline", "-1")
            self.assertIn("Update README", log.stdout)

    def test_push_requires_allow_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = self.make_git_repo(root)
            out = root / "plan.json"
            rc = module.main([
                "git-plan",
                "--repo-root", str(repo),
                "--plan-id", "plan-1",
                "--paths", "README.md",
                "--commit-message", "Noop",
                "--branch", "main",
                "--confirm-plan",
                "--approval-token", "PLAN_GIT_OPERATION",
                "--output", str(out),
                "--force",
            ])
            self.assertEqual(rc, 0)
            rc = module.main([
                "push",
                "--plan", str(out),
                "--confirm-push",
                "--approval-token", "APPROVE_GIT_PUSH",
                "--force",
            ])
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
