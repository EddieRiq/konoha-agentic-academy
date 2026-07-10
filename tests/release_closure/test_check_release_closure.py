import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "release_closure" / "check_release_closure.py"


def load_module():
    spec = importlib.util.spec_from_file_location("check_release_closure", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def base_git_state():
    return {
        "head": "a" * 40,
        "branch": "main",
        "expected_branch": "main",
        "branch_matches": True,
        "status_short": "",
        "working_tree_clean": True,
        "tracking_ref": "origin/main",
        "tracking_ref_exists": True,
        "tracked_remote_head": "a" * 40,
        "behind": 0,
        "ahead": 0,
        "tracking_synced": True,
        "local_tag": {
            "name": "v3.1.4",
            "exists": True,
            "object": "b" * 40,
            "target": "a" * 40,
            "target_matches_head": True,
        },
    }


def passing_test_gate():
    return {
        "source": "executed_now",
        "passed": True,
        "head_before": "a" * 40,
        "head_after": "a" * 40,
        "head_unchanged": True,
    }


def passing_remote():
    return {
        "checked": True,
        "passed": True,
        "branch_head": "a" * 40,
        "tag_object": "b" * 40,
        "tag_target": "a" * 40,
        "tag_exists": True,
    }


def published_latest():
    return {
        "checked": True,
        "gh_available": True,
        "authenticated": True,
        "query_passed": True,
        "release_exists": True,
        "is_latest": True,
        "is_draft": False,
        "is_prerelease": False,
    }


class ReleaseClosureGuardTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        (self.repo / "sandbox").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_rejects_invalid_version_and_repo_slug(self):
        with self.assertRaises(self.module.ClosureGuardError):
            self.module.validate_version("3.1.4")
        with self.assertRaises(self.module.ClosureGuardError):
            self.module.validate_repo_slug("owner only")

    def test_dirty_worktree_is_blocked_first(self):
        state = base_git_state()
        state["working_tree_clean"] = False
        code, _ = self.module.decide_status(
            state,
            passing_test_gate(),
            True,
            passing_remote(),
            published_latest(),
        )
        self.assertEqual(code, "BLOCKED_DIRTY_WORKTREE")

    def test_missing_local_tag_requests_creation(self):
        state = base_git_state()
        state["local_tag"]["exists"] = False
        state["local_tag"]["target_matches_head"] = None
        code, _ = self.module.decide_status(
            state,
            passing_test_gate(),
            False,
            None,
            None,
        )
        self.assertEqual(code, "NEEDS_TAG_CREATION")

    def test_local_tag_without_network_requests_verification(self):
        code, _ = self.module.decide_status(
            base_git_state(),
            passing_test_gate(),
            False,
            None,
            None,
        )
        self.assertEqual(code, "NEEDS_NETWORK_VERIFICATION")

    def test_missing_remote_tag_requests_publication(self):
        remote = passing_remote()
        remote["tag_exists"] = False
        remote["tag_target"] = None
        code, _ = self.module.decide_status(
            base_git_state(),
            passing_test_gate(),
            True,
            remote,
            published_latest(),
        )
        self.assertEqual(code, "NEEDS_TAG_PUBLICATION")

    def test_missing_release_requests_publication(self):
        release = published_latest()
        release["release_exists"] = False
        release["is_latest"] = None
        code, _ = self.module.decide_status(
            base_git_state(),
            passing_test_gate(),
            True,
            passing_remote(),
            release,
        )
        self.assertEqual(code, "NEEDS_RELEASE_PUBLICATION")

    def test_non_latest_release_requests_promotion(self):
        release = published_latest()
        release["is_latest"] = False
        code, _ = self.module.decide_status(
            base_git_state(),
            passing_test_gate(),
            True,
            passing_remote(),
            release,
        )
        self.assertEqual(code, "NEEDS_LATEST_PROMOTION")

    def test_complete_release_is_closed(self):
        code, _ = self.module.decide_status(
            base_git_state(),
            passing_test_gate(),
            True,
            passing_remote(),
            published_latest(),
        )
        self.assertEqual(code, "RELEASE_CLOSED")

    def test_output_is_restricted_to_sandbox(self):
        allowed = self.module.validate_output(
            self.repo,
            Path("sandbox/reports/closure.json"),
        )
        self.assertEqual(
            allowed,
            (self.repo / "sandbox" / "reports" / "closure.json").resolve(),
        )
        with self.assertRaises(self.module.ClosureGuardError):
            self.module.validate_output(
                self.repo,
                Path("reports/outside.json"),
            )

    def test_reused_evidence_must_match_current_head(self):
        report = {
            "report_type": self.module.REPORT_TYPE,
            "git": {"head": "a" * 40},
            "test_gate": {
                "passed": True,
                "head_after": "a" * 40,
                "head_unchanged": True,
            },
        }
        path = self.repo / "sandbox" / "reports" / "source.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(report), encoding="utf-8")

        loaded = self.module.load_test_evidence(
            self.repo,
            Path("sandbox/reports/source.json"),
            "c" * 40,
        )
        self.assertFalse(loaded["passed"])
        self.assertFalse(loaded["evidence_head_matches"])


    def test_run_canonical_tests_parses_large_json_without_truncation(self):
        repo = Path(self.tmp.name) / "large-json-repo"
        runner = repo / "tools" / "release_testing" / "run_release_tests.py"
        runner.parent.mkdir(parents=True)

        runner.write_text(
            "import json\n"
            "payload = {\n"
            "    'report_type': 'canonical_release_test_gate_report',\n"
            "    'schema_version': '1.0.0',\n"
            "    'passed': True,\n"
            "    'summary': {\n"
            "        'failed_suite_count': 0,\n"
            "        'passed_suite_count': 1,\n"
            "    },\n"
            "    'padding': 'x' * 9000,\n"
            "}\n"
            "print(json.dumps(payload))\n",
            encoding="utf-8",
        )

        commands = [
            ["git", "init"],
            ["git", "config", "user.email", "tests@example.invalid"],
            ["git", "config", "user.name", "Konoha Tests"],
            ["git", "add", "."],
            ["git", "commit", "-m", "Create large JSON fixture"],
        ]
        for command in commands:
            subprocess.run(
                command,
                cwd=repo,
                text=True,
                capture_output=True,
                check=True,
            )

        result = self.module.run_canonical_tests(repo, timeout=30)

        self.assertTrue(result["parsed"])
        self.assertTrue(result["passed"])
        self.assertEqual(
            result["summary"]["failed_suite_count"],
            0,
        )

    def test_main_returns_one_when_release_is_incomplete(self):
        report = {
            "status": "incomplete",
            "status_code": "NEEDS_TAG_CREATION",
            "release_closed": False,
        }

        argv = [
            "--target-version",
            "v3.1.4",
            "--github-repo",
            "owner/repository",
            "--run-tests",
            "--json",
        ]

        with mock.patch.object(
            self.module,
            "build_report",
            return_value=report,
        ):
            with redirect_stdout(io.StringIO()):
                returncode = self.module.main(argv)

        self.assertEqual(returncode, 1)



    def test_collect_github_release_uses_compatible_auth_command(self):
        responses = [
            {
                "command": [],
                "returncode": 0,
                "passed": True,
                "stdout": "authenticated",
                "stderr": "",
                "timed_out": False,
            },
            {
                "command": [],
                "returncode": 0,
                "passed": True,
                "stdout": "[]",
                "stderr": "",
                "timed_out": False,
            },
        ]

        with mock.patch.object(
            self.module.shutil,
            "which",
            return_value="/usr/bin/gh",
        ):
            with mock.patch.object(
                self.module,
                "run_command",
                side_effect=responses,
            ) as mocked_run:
                result = self.module.collect_github_release(
                    self.repo,
                    "owner/repository",
                    "v3.1.4",
                )

        auth_command = mocked_run.call_args_list[0].args[0]

        self.assertEqual(
            auth_command,
            [
                "gh",
                "auth",
                "status",
                "--hostname",
                "github.com",
            ],
        )
        self.assertNotIn("--active", auth_command)
        self.assertTrue(result["authenticated"])
        self.assertTrue(result["query_passed"])
        self.assertFalse(result["release_exists"])



if __name__ == "__main__":
    unittest.main()
