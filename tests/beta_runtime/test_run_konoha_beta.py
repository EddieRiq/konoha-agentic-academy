import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "beta_runtime" / "run_konoha_beta.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_konoha_beta", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class KonohaBetaRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = Path(tempfile.mkdtemp(prefix="konoha_beta_test_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_start_and_plan_create_runtime_files(self):
        workspace = self.tmp / "workspace"
        rc = self.module.main([
            "start",
            "--workspace-root", str(workspace),
            "--mission-id", "beta-smoke",
            "--title", "Beta smoke",
            "--task", "Prepare a Docker and Python supervised task.",
            "--confirm-start",
            "--approval-token", "START_BETA_MISSION",
            "--force",
        ])
        self.assertEqual(rc, 0)
        rc = self.module.main([
            "plan",
            "--workspace-root", str(workspace),
            "--mission-id", "beta-smoke",
            "--plan-id", "beta-plan",
            "--confirm-plan",
            "--approval-token", "PLAN_BETA_MISSION",
            "--force",
        ])
        self.assertEqual(rc, 0)
        base = workspace / "missions" / "beta-smoke"
        self.assertTrue((base / "charter.md").exists())
        self.assertTrue((base / "plans" / "beta-plan_beta_runtime_plan.json").exists())
        proposals = json.loads((base / "plans" / "beta-plan_command_proposals.json").read_text(encoding="utf-8"))
        command_ids = {item["command_id"] for item in proposals["proposals"]}
        self.assertIn("inspect-python", command_ids)
        self.assertIn("inspect-docker", command_ids)

    def test_mock_agent_records_token_usage(self):
        workspace = self.tmp / "workspace"
        self.module.main([
            "start", "--workspace-root", str(workspace), "--mission-id", "agent-smoke",
            "--title", "Agent smoke", "--task", "Review task.", "--confirm-start",
            "--approval-token", "START_BETA_MISSION", "--force",
        ])
        rc = self.module.main([
            "agent",
            "--workspace-root", str(workspace),
            "--mission-id", "agent-smoke",
            "--invocation-id", "mock-agent",
            "--provider", "mock",
            "--prompt", "Plan this supervised task.",
            "--confirm-invoke",
            "--approval-token", "INVOKE_EXTERNAL_AGENT",
            "--force",
        ])
        self.assertEqual(rc, 0)
        base = workspace / "missions" / "agent-smoke"
        self.assertTrue((base / "evidence" / "agent_invocations" / "mock-agent_agent_invocation.json").exists())
        ledger = json.loads((base / "reports" / "beta_token_usage_ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(len(ledger["records"]), 1)
        self.assertGreater(ledger["totals"]["estimated_input_tokens"], 0)

    def test_execute_safe_command_from_proposal(self):
        workspace = self.tmp / "workspace"
        self.module.main([
            "start", "--workspace-root", str(workspace), "--mission-id", "cmd-smoke",
            "--title", "Command smoke", "--task", "Python task.", "--confirm-start",
            "--approval-token", "START_BETA_MISSION", "--force",
        ])
        self.module.main([
            "plan", "--workspace-root", str(workspace), "--mission-id", "cmd-smoke",
            "--plan-id", "cmd-plan", "--confirm-plan", "--approval-token", "PLAN_BETA_MISSION", "--force",
        ])
        rc = self.module.main([
            "execute-command",
            "--workspace-root", str(workspace),
            "--mission-id", "cmd-smoke",
            "--plan-id", "cmd-plan",
            "--command-id", "inspect-python",
            "--working-dir", str(REPO_ROOT),
            "--result-id", "python-version-result",
            "--confirm-execute",
            "--approval-token", "EXECUTE_APPROVED_COMMAND",
            "--force",
        ])
        self.assertEqual(rc, 0)
        result = json.loads((workspace / "missions" / "cmd-smoke" / "evidence" / "command_results" / "python-version-result.json").read_text(encoding="utf-8"))
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("Python", result["stdout"] + result["stderr"])

    def test_dangerous_command_is_blocked(self):
        reason = self.module.command_is_dangerous("rm -rf /")
        self.assertIsNotNone(reason)

    def test_close_requires_exact_teachback(self):
        workspace = self.tmp / "workspace"
        self.module.main([
            "start", "--workspace-root", str(workspace), "--mission-id", "close-smoke",
            "--title", "Close smoke", "--task", "Close task.", "--confirm-start",
            "--approval-token", "START_BETA_MISSION", "--force",
        ])
        rc = self.module.main([
            "close",
            "--workspace-root", str(workspace),
            "--mission-id", "close-smoke",
            "--closure-id", "bad-close",
            "--confirm-close",
            "--approval-token", "CLOSE_BETA_MISSION",
            "--teachback-confirmation", "WRONG",
            "--teachback-summary", "This should fail because the confirmation is wrong.",
        ])
        self.assertEqual(rc, 1)
        rc = self.module.main([
            "close",
            "--workspace-root", str(workspace),
            "--mission-id", "close-smoke",
            "--closure-id", "good-close",
            "--confirm-close",
            "--approval-token", "CLOSE_BETA_MISSION",
            "--teachback-confirmation", "I_CAN_EXPLAIN_AND_DEFEND_THIS_MISSION",
            "--teachback-summary", "I can explain what was done, why it was done, what evidence was recorded, and how to defend the mission result.",
            "--force",
        ])
        self.assertEqual(rc, 0)

    def test_git_stage_and_commit_gate_on_temp_repo(self):
        if not shutil.which("git"):
            self.skipTest("git not available")
        repo = self.tmp / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=str(repo), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subprocess.run(["git", "config", "user.email", "konoha@example.invalid"], cwd=str(repo), check=True)
        subprocess.run(["git", "config", "user.name", "Konoha Test"], cwd=str(repo), check=True)
        (repo / "README.md").write_text("# initial\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=str(repo), check=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=str(repo), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        (repo / "README.md").write_text("# initial\n\nchange\n", encoding="utf-8")
        plan = self.tmp / "git-plan.json"
        rc = self.module.main([
            "git-plan", "--repo-root", str(repo), "--plan-id", "git-smoke",
            "--paths", "README.md", "--commit-message", "Update README",
            "--branch", "master", "--output", str(plan), "--confirm-plan",
            "--approval-token", "PLAN_BETA_GIT_OPERATION", "--force",
        ])
        self.assertEqual(rc, 0)
        rc = self.module.main([
            "git-stage", "--plan", str(plan), "--confirm-stage",
            "--approval-token", "APPROVE_BETA_GIT_STAGE",
        ])
        self.assertEqual(rc, 0)
        rc = self.module.main([
            "git-commit", "--plan", str(plan), "--confirm-commit",
            "--approval-token", "APPROVE_BETA_GIT_COMMIT",
        ])
        self.assertEqual(rc, 0)

    def test_git_push_requires_network_allowance(self):
        plan = self.tmp / "plan.json"
        repo = self.tmp / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        plan.write_text(json.dumps({
            "schema_version": "1.0.0",
            "report_type": "beta_git_operation_plan",
            "plan_id": "push-block",
            "repo_root": str(repo),
            "paths": ["README.md"],
            "remote": "origin",
            "branch": "main",
            "commit_message": "test",
        }), encoding="utf-8")
        rc = self.module.main([
            "git-push", "--plan", str(plan), "--confirm-push",
            "--approval-token", "APPROVE_BETA_GIT_PUSH",
        ])
        self.assertEqual(rc, 1)

    def test_doctor_runs_without_writes(self):
        rc = self.module.main(["doctor", "--json"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
