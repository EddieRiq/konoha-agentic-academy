import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "tools"
    / "release_delivery"
    / "run_supervised_package_release.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "run_supervised_package_release_test",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SupervisedPackageReleaseTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.plan = {
            "schema_version": "1.0.0",
            "report_type": "supervised_package_release_plan",
            "delivery_id": "release-v3-3-0",
            "expected_base_commit": "a" * 40,
            "target_version": "v3.3.0",
            "installation_manifest_path": (
                "examples/package_installation/install.json"
            ),
            "release_plan_path": (
                "examples/release_workflow/release.json"
            ),
            "focused_suites": [
                {
                    "name": "distribution",
                    "path": "tests/distribution",
                    "pattern": "test_*.py",
                    "expected_tests": 17,
                }
            ],
            "clean_install_smoke": {
                "tool_path": (
                    "tools/distribution/"
                    "run_clean_install_smoke.py"
                ),
                "expected_version": "3.3.0",
            },
            "authority": {
                "plan_is_not_permission": True,
                "installation_token_required": True,
                "release_tokens_required": True,
                "network_is_explicit": True,
                "tests_are_evidence_only": True,
            },
        }
        self.args = argparse.Namespace(
            confirm_run=False,
            delivery_token="",
            installation_token="",
            allow_network=False,
            test_timeout=1200,
            workflow_token="",
            git_plan_token="",
            git_stage_token="",
            git_commit_token="",
            git_push_token="",
            tag_create_token="",
            tag_push_token="",
            release_publish_token="",
            latest_promotion_token="",
        )

    def test_validate_plan_accepts_complete_plan(self):
        validated = self.module.validate_plan(self.plan)
        self.assertEqual(
            validated["target_version"],
            "v3.3.0",
        )

    def test_validate_plan_rejects_missing_field(self):
        payload = deepcopy(self.plan)
        del payload["delivery_id"]
        with self.assertRaisesRegex(
            self.module.DeliveryError,
            "missing fields",
        ):
            self.module.validate_plan(payload)

    def test_validate_plan_rejects_invalid_version(self):
        payload = deepcopy(self.plan)
        payload["target_version"] = "3.3.0"
        with self.assertRaisesRegex(
            self.module.DeliveryError,
            "target_version",
        ):
            self.module.validate_plan(payload)

    def test_validate_plan_rejects_duplicate_suite(self):
        payload = deepcopy(self.plan)
        payload["focused_suites"].append(
            deepcopy(payload["focused_suites"][0])
        )
        with self.assertRaisesRegex(
            self.module.DeliveryError,
            "name is invalid",
        ):
            self.module.validate_plan(payload)

    def test_validate_plan_rejects_non_test_path(self):
        payload = deepcopy(self.plan)
        payload["focused_suites"][0]["path"] = "tools"
        with self.assertRaisesRegex(
            self.module.DeliveryError,
            "path is invalid",
        ):
            self.module.validate_plan(payload)

    def test_validate_plan_rejects_nonpositive_count(self):
        payload = deepcopy(self.plan)
        payload["focused_suites"][0]["expected_tests"] = 0
        with self.assertRaisesRegex(
            self.module.DeliveryError,
            "expected_tests",
        ):
            self.module.validate_plan(payload)

    def test_validate_plan_rejects_smoke_version_mismatch(self):
        payload = deepcopy(self.plan)
        payload["clean_install_smoke"][
            "expected_version"
        ] = "3.2.6"
        with self.assertRaisesRegex(
            self.module.DeliveryError,
            "clean_install_smoke",
        ):
            self.module.validate_plan(payload)

    def test_validate_plan_rejects_missing_authority(self):
        payload = deepcopy(self.plan)
        payload["authority"]["network_is_explicit"] = False
        with self.assertRaisesRegex(
            self.module.DeliveryError,
            "network_is_explicit",
        ):
            self.module.validate_plan(payload)

    def test_output_outside_sandbox_is_blocked(self):
        with self.assertRaisesRegex(
            self.module.DeliveryError,
            "under sandbox",
        ):
            self.module.resolve_output(
                ROOT,
                str(ROOT / "unsafe.json"),
            )

    def test_private_repo_file_is_blocked(self):
        with self.assertRaisesRegex(
            self.module.DeliveryError,
            "blocked context",
        ):
            self.module.resolve_repo_file(
                ROOT,
                "vault/private.json",
                "private",
            )

    def runner(self):
        return self.module.DeliveryRunner(
            ROOT,
            self.module.validate_plan(self.plan),
            self.args,
        )

    def test_execute_requires_confirmation(self):
        self.args.delivery_token = self.module.RUN_TOKEN
        self.args.installation_token = (
            self.module.INSTALL_TOKEN
        )
        self.args.allow_network = True
        with self.assertRaisesRegex(
            self.module.DeliveryError,
            "confirm-run",
        ):
            self.runner().execute()

    def test_execute_requires_delivery_token(self):
        self.args.confirm_run = True
        self.args.installation_token = (
            self.module.INSTALL_TOKEN
        )
        self.args.allow_network = True
        with self.assertRaisesRegex(
            self.module.DeliveryError,
            "delivery-token",
        ):
            self.runner().execute()

    def test_execute_requires_installation_token(self):
        self.args.confirm_run = True
        self.args.delivery_token = self.module.RUN_TOKEN
        self.args.allow_network = True
        with self.assertRaisesRegex(
            self.module.DeliveryError,
            "installation-token",
        ):
            self.runner().execute()

    def test_execute_requires_network(self):
        self.args.confirm_run = True
        self.args.delivery_token = self.module.RUN_TOKEN
        self.args.installation_token = (
            self.module.INSTALL_TOKEN
        )
        with self.assertRaisesRegex(
            self.module.DeliveryError,
            "allow-network",
        ):
            self.runner().execute()

    def test_focused_suite_exact_count_passes(self):
        runner = self.runner()
        completed = subprocess.CompletedProcess(
            args=["python"],
            returncode=0,
            stdout="",
            stderr=(
                ".................\n"
                "Ran 17 tests in 0.1s\n\nOK\n"
            ),
        )
        with patch.object(
            runner,
            "run",
            return_value=completed,
        ):
            results = runner.run_focused_suites()
        self.assertEqual(results[0]["actual_tests"], 17)
        self.assertTrue(results[0]["passed"])

    def test_focused_suite_count_mismatch_blocks(self):
        runner = self.runner()
        completed = subprocess.CompletedProcess(
            args=["python"],
            returncode=0,
            stdout="",
            stderr="Ran 16 tests in 0.1s\n\nOK\n",
        )
        with patch.object(
            runner,
            "run",
            return_value=completed,
        ):
            with self.assertRaisesRegex(
                self.module.DeliveryError,
                "expected 17 tests",
            ):
                runner.run_focused_suites()


    def configured_args(self):
        self.args.confirm_run = True
        self.args.delivery_token = self.module.RUN_TOKEN
        self.args.installation_token = self.module.INSTALL_TOKEN
        self.args.allow_network = True
        self.args.workflow_token = "RUN_SUPERVISED_RELEASE_WORKFLOW"
        self.args.git_plan_token = "PLAN_BETA_GIT_OPERATION"
        self.args.git_stage_token = "APPROVE_BETA_GIT_STAGE"
        self.args.git_commit_token = "APPROVE_BETA_GIT_COMMIT"
        self.args.git_push_token = "APPROVE_BETA_GIT_PUSH"
        self.args.tag_create_token = "APPROVE_SUPERVISED_RELEASE_TAG_CREATE"
        self.args.tag_push_token = "APPROVE_SUPERVISED_RELEASE_TAG_PUSH"
        self.args.release_publish_token = "APPROVE_SUPERVISED_RELEASE_PUBLISH"
        self.args.latest_promotion_token = "APPROVE_SUPERVISED_RELEASE_LATEST"
        return self.args

    def test_already_closed_reentry_skips_release_mutations(self):
        module = self.module
        labels = []

        class SimulatedRunner(module.DeliveryRunner):
            def validate_alignment(self):
                return {
                    "installation_path": SCRIPT,
                    "release_path": SCRIPT,
                    "install_tool": SCRIPT,
                    "release_tool": SCRIPT,
                    "checks": {
                        "installation_base": True,
                        "release_base": True,
                        "release_version": True,
                        "public_scope": True,
                    },
                }

            def run(self, label, command, **kwargs):
                labels.append(label)
                if label == "git-head":
                    return subprocess.CompletedProcess(
                        command, 0, stdout="b" * 40 + "\n", stderr=""
                    )
                if label == "pre-release-status":
                    output = Path(command[command.index("--output") + 1])
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_text(
                        json.dumps(
                            {
                                "status_code": "RELEASE_CLOSED",
                                "release_closed": True,
                                "blocked": False,
                                "safe_to_resume": True,
                                "snapshot": {
                                    "release_commit_aligned": True
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return subprocess.CompletedProcess(
                        command, 0, stdout="", stderr=""
                    )
                raise AssertionError(f"unexpected command label: {label}")

        runner = SimulatedRunner(
            ROOT,
            module.validate_plan(self.plan),
            self.configured_args(),
        )
        report = runner.execute()

        self.assertEqual(report["status_code"], "PACKAGE_RELEASE_CLOSED")
        self.assertTrue(report["resume_mode"])
        self.assertEqual(labels, ["git-head", "pre-release-status"])

    def test_partial_aligned_release_resumes_existing_workflow(self):
        module = self.module
        labels = []

        class SimulatedRunner(module.DeliveryRunner):
            def validate_alignment(self):
                return {
                    "installation_path": SCRIPT,
                    "release_path": SCRIPT,
                    "install_tool": SCRIPT,
                    "release_tool": SCRIPT,
                    "checks": {
                        "installation_base": True,
                        "release_base": True,
                        "release_version": True,
                        "public_scope": True,
                    },
                }

            def run(self, label, command, **kwargs):
                labels.append(label)
                if label == "git-head":
                    return subprocess.CompletedProcess(
                        command, 0, stdout="b" * 40 + "\n", stderr=""
                    )

                output = Path(command[command.index("--output") + 1])
                output.parent.mkdir(parents=True, exist_ok=True)

                if label == "pre-release-status":
                    payload = {
                        "status_code": "NEEDS_TAG_PUBLICATION",
                        "release_closed": False,
                        "blocked": False,
                        "safe_to_resume": True,
                        "snapshot": {
                            "release_commit_aligned": True
                        },
                    }
                elif label == "unified-release":
                    payload = {
                        "status_code": "RELEASE_CLOSED",
                        "release_closed": True,
                        "head": "b" * 40,
                    }
                elif label == "release-status":
                    payload = {
                        "status_code": "RELEASE_CLOSED",
                        "release_closed": True,
                    }
                else:
                    raise AssertionError(
                        f"unexpected command label: {label}"
                    )

                output.write_text(
                    json.dumps(payload),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(
                    command, 0, stdout="", stderr=""
                )

        runner = SimulatedRunner(
            ROOT,
            module.validate_plan(self.plan),
            self.configured_args(),
        )
        report = runner.execute()

        self.assertEqual(report["status_code"], "PACKAGE_RELEASE_CLOSED")
        self.assertTrue(report["resume_mode"])
        self.assertEqual(
            labels,
            [
                "git-head",
                "pre-release-status",
                "unified-release",
                "release-status",
            ],
        )

if __name__ == "__main__":
    unittest.main()
