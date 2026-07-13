import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT
    / "tools"
    / "release_workflow"
    / "run_supervised_release.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "run_supervised_release",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class UnifiedSupervisedReleaseTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()

        self.notes = self.repo / "sandbox/tmp/release-notes.md"
        self.notes.parent.mkdir(parents=True)
        self.notes.write_text("# Release notes\n", encoding="utf-8")

        self.plan = {
            "schema_version": "1.0.0",
            "report_type": "supervised_release_workflow_plan",
            "workflow_id": "release-v3-2-4",
            "expected_base_commit": "a" * 40,
            "expected_branch": "main",
            "remote": "origin",
            "github_repo": "owner/repo",
            "target_version": "v3.2.4",
            "previous_version": "v3.2.3",
            "commit_message": "Add supervised release recovery status",
            "release_title": (
                "Konoha Agentic Academy v3.2.4 - "
                "Supervised Release Recovery and Status"
            ),
            "release_notes_path": "sandbox/tmp/release-notes.md",
            "release_notes_sha256": self.module.sha256_file(self.notes),
            "public_paths": [
                "README.md",
                "tools/release_workflow/run_supervised_release.py",
            ],
            "expected_test_gate": {
                "suite_count": 49,
                "test_count": 371,
                "focused_suite": "release_workflow",
                "focused_tests": 24,
            },
            "max_transitions": 8,
            "authority": {
                "plan_is_not_permission": True,
                "operation_tokens_required": True,
                "test_results_are_evidence_only": True,
                "guard_reports_are_evidence_only": True,
                "release_mutations_are_explicit": True,
            },
        }

    def tearDown(self):
        self.tmp.cleanup()

    def args(self, **overrides):
        values = {
            "confirm_run": True,
            "allow_network": True,
            "workflow_token": self.module.RUN_TOKEN,
            "git_plan_token": "PLAN_BETA_GIT_OPERATION",
            "git_stage_token": "APPROVE_BETA_GIT_STAGE",
            "git_commit_token": "APPROVE_BETA_GIT_COMMIT",
            "git_push_token": "APPROVE_BETA_GIT_PUSH",
            "tag_create_token": self.module.TAG_CREATE_TOKEN,
            "tag_push_token": self.module.TAG_PUSH_TOKEN,
            "release_publish_token": self.module.RELEASE_PUBLISH_TOKEN,
            "latest_promotion_token": self.module.LATEST_PROMOTION_TOKEN,
            "test_timeout": 60,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def init_git_repo(self):
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=self.repo,
            check=True,
            text=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Konoha Test"],
            cwd=self.repo,
            check=True,
        )

        for relative in (
            "tools/beta_runtime/run_konoha_beta.py",
            "tools/release_closure/check_release_closure.py",
            "tools/release_testing/run_release_tests.py",
            "README.md",
            "tools/release_workflow/run_supervised_release.py",
        ):
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{relative}\n", encoding="utf-8")

        subprocess.run(
            ["git", "add", "."],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Base"],
            cwd=self.repo,
            check=True,
            text=True,
            capture_output=True,
        )
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        subprocess.run(
            ["git", "tag", "-a", "v3.2.3", "-m", "v3.2.3"],
            cwd=self.repo,
            check=True,
        )

        remote = Path(self.tmp.name) / "remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            text=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "remote", "add", "origin", str(remote)],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            cwd=self.repo,
            check=True,
            text=True,
            capture_output=True,
        )

        self.plan["expected_base_commit"] = base
        return base

    def write_public_changes(self):
        (self.repo / "README.md").write_text(
            "changed README\n",
            encoding="utf-8",
        )
        (self.repo / "tools/release_workflow/run_supervised_release.py").write_text(
            "changed tool\n",
            encoding="utf-8",
        )

    def closure_report(self, status):
        return {
            "schema_version": "1.0.0",
            "report_type": "release_readiness_closure_guard_report",
            "status": "passed" if status == "RELEASE_CLOSED" else "incomplete",
            "status_code": status,
            "release_closed": status == "RELEASE_CLOSED",
            "git": {
                "head": "b" * 40,
            },
            "test_gate": {
                "passed": True,
                "head_unchanged": True,
                "head_after": "b" * 40,
                "summary": {
                    "discovered_suite_count": 49,
                    "selected_suite_count": 49,
                    "passed_suite_count": 49,
                    "failed_suite_count": 0,
                    "test_count": 371,
                    "failure_count": 0,
                    "error_count": 0,
                    "timeout_count": 0,
                },
            },
        }

    def test_validate_plan_accepts_complete_plan(self):
        validated = self.module.validate_plan(self.plan)

        self.assertEqual(validated["workflow_id"], "release-v3-2-4")
        self.assertEqual(
            validated["public_paths"],
            sorted(self.plan["public_paths"]),
        )

    def test_validate_plan_rejects_missing_field(self):
        payload = dict(self.plan)
        payload.pop("release_title")

        with self.assertRaisesRegex(
            self.module.WorkflowError,
            "missing fields",
        ):
            self.module.validate_plan(payload)

    def test_validate_plan_rejects_private_public_path(self):
        payload = json.loads(json.dumps(self.plan))
        payload["public_paths"].append("vault/private.json")

        with self.assertRaisesRegex(
            self.module.WorkflowError,
            "blocked context",
        ):
            self.module.validate_plan(payload)

    def test_validate_plan_rejects_duplicate_paths(self):
        payload = json.loads(json.dumps(self.plan))
        payload["public_paths"].append("README.md")

        with self.assertRaisesRegex(
            self.module.WorkflowError,
            "duplicates",
        ):
            self.module.validate_plan(payload)

    def test_validate_tokens_requires_every_explicit_token(self):
        args = self.args(tag_push_token="")

        with self.assertRaisesRegex(
            self.module.WorkflowError,
            "tag_push_token",
        ):
            self.module.validate_tokens(args)

    def test_output_must_stay_under_sandbox(self):
        with self.assertRaisesRegex(
            self.module.WorkflowError,
            "under <repo-root>/sandbox",
        ):
            self.module.resolve_output(
                self.repo,
                "unsafe-report.json",
            )

    def test_expected_action_maps_all_supported_states(self):
        expected = {
            "BLOCKED_BRANCH_NOT_SYNCED": "push_main",
            "NEEDS_TAG_CREATION": "create_tag",
            "NEEDS_TAG_PUBLICATION": "push_tag",
            "NEEDS_RELEASE_PUBLICATION": "publish_release",
            "NEEDS_LATEST_PROMOTION": "promote_latest",
            "RELEASE_CLOSED": "complete",
        }

        actual = {
            state: self.module.expected_action(state)
            for state in expected
        }

        self.assertEqual(actual, expected)

        incomplete = self.closure_report("NEEDS_TAG_CREATION")
        self.module.validate_closure_rc_status(incomplete, 1)

        closed = self.closure_report("RELEASE_CLOSED")
        self.module.validate_closure_rc_status(closed, 0)

        with self.assertRaisesRegex(
            self.module.WorkflowError,
            "requires RC=1",
        ):
            self.module.validate_closure_rc_status(incomplete, 0)

    def test_expected_action_rejects_unexpected_state(self):
        with self.assertRaisesRegex(
            self.module.WorkflowError,
            "unexpected closure status",
        ):
            self.module.expected_action("BLOCKED_GH_AUTH")

    def test_validate_test_summary_accepts_expected_counts(self):
        report = self.closure_report("BLOCKED_BRANCH_NOT_SYNCED")

        summary = self.module.validate_test_summary(
            report,
            self.plan["expected_test_gate"],
        )

        self.assertEqual(summary["test_count"], 371)

    def test_validate_test_summary_rejects_count_mismatch(self):
        report = self.closure_report("BLOCKED_BRANCH_NOT_SYNCED")
        report["test_gate"]["summary"]["test_count"] = 370

        with self.assertRaisesRegex(
            self.module.WorkflowError,
            "test_count",
        ):
            self.module.validate_test_summary(
                report,
                self.plan["expected_test_gate"],
            )

    def test_preflight_accepts_exact_dirty_scope(self):
        base = self.init_git_repo()
        self.write_public_changes()
        self.plan["expected_base_commit"] = base

        workflow = self.module.SupervisedReleaseWorkflow(
            repo_root=self.repo,
            plan=self.module.validate_plan(self.plan),
            args=self.args(),
        )

        self.assertEqual(workflow.preflight(), "needs_commit")

    def test_preflight_rejects_scope_mismatch(self):
        base = self.init_git_repo()
        self.write_public_changes()
        (self.repo / "extra.txt").write_text("extra\n", encoding="utf-8")
        self.plan["expected_base_commit"] = base

        workflow = self.module.SupervisedReleaseWorkflow(
            repo_root=self.repo,
            plan=self.module.validate_plan(self.plan),
            args=self.args(),
        )

        with self.assertRaisesRegex(
            self.module.WorkflowError,
            "public scope mismatch",
        ):
            workflow.preflight()

    def test_preflight_resumes_aligned_existing_commit(self):
        base = self.init_git_repo()
        self.write_public_changes()
        subprocess.run(
            ["git", "add", "README.md", "tools/release_workflow/run_supervised_release.py"],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", self.plan["commit_message"]],
            cwd=self.repo,
            check=True,
            text=True,
            capture_output=True,
        )
        self.plan["expected_base_commit"] = base

        workflow = self.module.SupervisedReleaseWorkflow(
            repo_root=self.repo,
            plan=self.module.validate_plan(self.plan),
            args=self.args(),
        )

        self.assertEqual(workflow.preflight(), "resume_committed")
        self.assertRegex(workflow.current_head, r"^[0-9a-f]{40}$")

    def test_execute_follows_full_expected_state_machine(self):
        module = self.module
        states = [
            "BLOCKED_BRANCH_NOT_SYNCED",
            "NEEDS_TAG_CREATION",
            "NEEDS_TAG_PUBLICATION",
            "NEEDS_RELEASE_PUBLICATION",
            "NEEDS_LATEST_PROMOTION",
            "RELEASE_CLOSED",
        ]
        actions = []

        class SimulatedWorkflow(module.SupervisedReleaseWorkflow):
            def run_logged(
                self,
                label,
                command,
                *,
                timeout=900,
                expected_rcs=(0,),
            ):
                return module.CommandResult(
                    command=list(command),
                    returncode=0,
                    stdout="",
                    stderr="",
                )

            def preflight(self):
                return "needs_commit"

            def create_commit(self):
                self.current_head = "b" * 40
                actions.append("commit")

            def run_initial_closure_guard(self):
                self.test_summary = self.plan["expected_test_gate"].copy()
                self.test_summary.update(
                    {
                        "discovered_suite_count": 49,
                        "selected_suite_count": 49,
                        "passed_suite_count": 49,
                        "failed_suite_count": 0,
                        "test_count": 371,
                        "failure_count": 0,
                        "error_count": 0,
                        "timeout_count": 0,
                    }
                )
                path = self.report_dir / "initial.json"
                return {"status_code": states[0]}, path

            def run_reused_closure_guard(self, prior_evidence, step):
                path = self.report_dir / f"step-{step}.json"
                return {"status_code": states[step]}, path

            def push_main(self):
                actions.append("push_main")

            def create_tag(self):
                actions.append("create_tag")

            def push_tag(self):
                actions.append("push_tag")

            def publish_release(self):
                actions.append("publish_release")

            def promote_latest(self):
                actions.append("promote_latest")

            def verify_final(self, final_report):
                return {
                    "head": self.current_head,
                    "local_tag_target": self.current_head,
                    "tracking": {"behind": 0, "ahead": 0},
                    "release": {"url": "https://example.invalid/release"},
                }

        workflow = SimulatedWorkflow(
            repo_root=self.repo,
            plan=self.module.validate_plan(self.plan),
            args=self.args(),
        )

        from unittest.mock import patch

        with patch.object(module.shutil, "which", return_value="/usr/bin/tool"):
            report = workflow.execute()

        self.assertEqual(
            actions,
            [
                "commit",
                "push_main",
                "create_tag",
                "push_tag",
                "publish_release",
                "promote_latest",
            ],
        )
        self.assertEqual(report["status_code"], "RELEASE_CLOSED")
        self.assertTrue(report["release_closed"])
        self.assertEqual(len(report["transitions"]), 6)


    def status_snapshot(self):
        head = "b" * 40
        return {
            "branch": "main",
            "expected_branch": "main",
            "head": head,
            "expected_base_commit": "a" * 40,
            "working_tree_clean": True,
            "scope_matches": False,
            "actual_scope": [],
            "release_commit_aligned": True,
            "tracking": {
                "behind": 0,
                "ahead": 0,
            },
            "network_requested": True,
            "remote_branch_head": head,
            "local_tag": {
                "exists": True,
                "annotated": True,
                "target_matches_head": True,
            },
            "remote_tag": {
                "exists": True,
                "target_matches_head": True,
                "object_matches_local": True,
            },
            "release": {
                "exists": True,
                "tag_matches": True,
                "title_matches": True,
                "draft": False,
                "prerelease": False,
                "latest": True,
            },
        }

    def test_status_dirty_exact_scope_needs_git_delivery(self):
        snapshot = self.status_snapshot()
        snapshot["head"] = snapshot["expected_base_commit"]
        snapshot["working_tree_clean"] = False
        snapshot["scope_matches"] = True
        snapshot["release_commit_aligned"] = False
        snapshot["tracking"] = {"behind": 0, "ahead": 0}

        result = self.module.derive_recovery_state(snapshot)

        self.assertEqual(result["status_code"], "NEEDS_GIT_DELIVERY")
        self.assertTrue(result["safe_to_resume"])

    def test_status_local_ahead_needs_branch_push(self):
        snapshot = self.status_snapshot()
        snapshot["tracking"] = {"behind": 0, "ahead": 1}
        snapshot["remote_branch_head"] = snapshot["expected_base_commit"]

        result = self.module.derive_recovery_state(snapshot)

        self.assertEqual(result["status_code"], "NEEDS_BRANCH_PUSH")
        self.assertTrue(result["safe_to_resume"])

    def test_status_local_tag_without_remote_needs_tag_publication(self):
        snapshot = self.status_snapshot()
        snapshot["remote_tag"] = {
            "exists": False,
            "target_matches_head": False,
            "object_matches_local": False,
        }
        snapshot["release"] = {
            "exists": False,
            "tag_matches": False,
            "title_matches": False,
            "draft": None,
            "prerelease": None,
            "latest": None,
        }

        result = self.module.derive_recovery_state(snapshot)

        self.assertEqual(
            result["status_code"],
            "NEEDS_TAG_PUBLICATION",
        )

    def test_status_remote_tag_without_release_needs_publication(self):
        snapshot = self.status_snapshot()
        snapshot["release"] = {
            "exists": False,
            "tag_matches": False,
            "title_matches": False,
            "draft": None,
            "prerelease": None,
            "latest": None,
        }

        result = self.module.derive_recovery_state(snapshot)

        self.assertEqual(
            result["status_code"],
            "NEEDS_RELEASE_PUBLICATION",
        )

    def test_status_release_not_latest_needs_promotion(self):
        snapshot = self.status_snapshot()
        snapshot["release"]["latest"] = False

        result = self.module.derive_recovery_state(snapshot)

        self.assertEqual(
            result["status_code"],
            "NEEDS_LATEST_PROMOTION",
        )

    def test_status_aligned_release_is_closed(self):
        result = self.module.derive_recovery_state(
            self.status_snapshot()
        )

        self.assertEqual(result["status_code"], "RELEASE_CLOSED")
        self.assertTrue(result["release_closed"])
        self.assertTrue(result["safe_to_resume"])

    def test_status_scope_mismatch_blocks(self):
        snapshot = self.status_snapshot()
        snapshot["head"] = snapshot["expected_base_commit"]
        snapshot["working_tree_clean"] = False
        snapshot["scope_matches"] = False
        snapshot["release_commit_aligned"] = False

        result = self.module.derive_recovery_state(snapshot)

        self.assertEqual(
            result["status_code"],
            "BLOCKED_SCOPE_MISMATCH",
        )
        self.assertTrue(result["blocked"])

    def test_cached_evidence_corrupt_is_not_reusable(self):
        evidence = (
            self.repo
            / "sandbox"
            / "reports"
            / "release-v3-2-4-closure-tests.json"
        )
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text("{", encoding="utf-8")

        result = self.module.inspect_cached_test_evidence(
            self.repo,
            self.plan,
            "b" * 40,
        )

        self.assertEqual(result["state"], "corrupt")
        self.assertFalse(result["reusable"])

    def test_cached_evidence_stale_is_not_reusable(self):
        evidence = (
            self.repo
            / "sandbox"
            / "reports"
            / "release-v3-2-4-closure-tests.json"
        )
        evidence.parent.mkdir(parents=True, exist_ok=True)
        report = self.closure_report("NEEDS_TAG_CREATION")
        report["git"]["head"] = "c" * 40
        report["test_gate"]["head_after"] = "c" * 40
        evidence.write_text(
            json.dumps(report, indent=2) + "\n",
            encoding="utf-8",
        )

        result = self.module.inspect_cached_test_evidence(
            self.repo,
            self.plan,
            "b" * 40,
        )

        self.assertEqual(result["state"], "stale")
        self.assertFalse(result["reusable"])

    def test_status_cli_is_read_only_and_needs_no_tokens(self):
        base = self.init_git_repo()
        self.write_public_changes()
        self.plan["expected_base_commit"] = base
        self.plan["release_notes_sha256"] = self.module.sha256_file(
            self.notes
        )

        plan_path = self.repo / "status-plan.json"
        plan_path.write_text(
            json.dumps(self.plan, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        output = self.repo / "sandbox/reports/status.json"
        before_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--repo-root",
                str(self.repo),
                "--plan",
                str(plan_path),
                "--output",
                str(output),
                "--status",
                "--json",
                "--force",
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )

        self.assertEqual(completed.returncode, 1, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(
            report["status_code"],
            "BLOCKED_SCOPE_MISMATCH",
        )
        self.assertTrue(report["authority"]["no_mutation_was_performed"])

        after_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        self.assertEqual(before_head, after_head)
        self.assertEqual(
            subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.repo,
                check=True,
                text=True,
                capture_output=True,
            ).stdout,
            "",
        )

if __name__ == "__main__":
    unittest.main()
