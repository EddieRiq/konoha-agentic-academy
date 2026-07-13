import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT
    / "tools"
    / "task_contract"
    / "validate_supervised_task_contract.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "validate_supervised_task_contract",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def valid_contract():
    return {
        "schema_version": "1.0.0",
        "report_type": "supervised_task_contract",
        "contract_id": "contract-001",
        "mission_id": "mission-001",
        "title": "Validate public documentation alignment",
        "objective": "Validate public repository documentation without mutation.",
        "non_goals": [
            "Do not invoke models.",
            "Do not modify Git or repository files.",
        ],
        "risk_level": "medium",
        "scope": {
            "allowed_paths": [
                "README.md",
                "CHANGELOG.md",
                "docs/**",
            ],
            "blocked_paths": [
                ".env",
                "alliance/kirigakure/**",
                "sandbox/**",
            ],
        },
        "operations": {
            "allowed": [
                "inspect_repository",
                "read_public_files",
                "run_deterministic_checks",
                "record_external_result",
            ],
            "blocked": [
                "propose_command",
                "invoke_local_model",
                "execute_command",
                "apply_patch",
                "git_stage",
                "git_commit",
                "git_push",
                "write_private_memory",
                "close_mission",
            ],
        },
        "network_policy": "blocked",
        "private_context_policy": "blocked",
        "acceptance_criteria": [
            "All requested public documents are inspected.",
            "Findings include source paths and deterministic evidence.",
        ],
        "evidence_requirements": [
            "Record inspected paths.",
            "Record deterministic check results.",
        ],
        "approval_requirements": [],
        "completion_conditions": [
            "Acceptance criteria are reviewed by a human.",
            "No blocked operation was performed.",
        ],
        "review": {
            "required": True,
            "level": "standard",
            "reviewers": ["human", "jounin"],
        },
        "teachback_required": True,
        "stop_triggers": [
            "Private or company data is discovered.",
            "The requested scope is ambiguous.",
            "A blocked operation appears necessary.",
        ],
        "authority": {
            "contract_is_not_permission": True,
            "validator_output_is_evidence_only": True,
            "mission_state_does_not_authorize_execution": True,
            "approvals_are_operation_specific": True,
        },
    }


class SupervisedTaskContractValidatorTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        (self.repo / "sandbox").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def validate(self, payload):
        return self.module.build_report(
            self.repo / "contract.json",
            payload,
        )

    def test_valid_contract_is_ready(self):
        report = self.validate(valid_contract())

        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["readiness"], "ready")
        self.assertEqual(report["blocker_count"], 0)
        self.assertTrue(
            report["authority"]["ready_does_not_authorize_execution"]
        )

    def test_missing_acceptance_criteria_blocks(self):
        payload = valid_contract()
        payload["acceptance_criteria"] = []

        report = self.validate(payload)

        self.assertEqual(report["readiness"], "blocked")
        self.assertIn(
            "acceptance_criteria_invalid",
            {item["code"] for item in report["blockers"]},
        )

    def test_sensitive_operation_requires_approval(self):
        payload = valid_contract()
        payload["operations"]["allowed"].append("apply_patch")
        payload["operations"]["blocked"].remove("apply_patch")

        report = self.validate(payload)

        self.assertIn(
            "sensitive_operation_without_approval",
            {item["code"] for item in report["blockers"]},
        )

    def test_sensitive_operation_with_approval_is_ready(self):
        payload = valid_contract()
        payload["operations"]["allowed"].append("apply_patch")
        payload["operations"]["blocked"].remove("apply_patch")
        payload["approval_requirements"].append(
            {
                "operation": "apply_patch",
                "approval_token": "APPLY_APPROVED_PATCH",
                "reason": "File mutation requires explicit approval.",
            }
        )

        report = self.validate(payload)

        self.assertEqual(report["readiness"], "ready")
        self.assertEqual(
            report["normalized_contract_summary"]["approval_operations"],
            ["apply_patch"],
        )

    def test_git_push_requires_network_approval_policy(self):
        payload = valid_contract()
        payload["operations"]["allowed"].append("git_push")
        payload["operations"]["blocked"].remove("git_push")
        payload["approval_requirements"].append(
            {
                "operation": "git_push",
                "approval_token": "APPROVE_GIT_PUSH",
                "reason": "Push mutates a remote.",
            }
        )

        report = self.validate(payload)

        self.assertIn(
            "git_push_network_policy_invalid",
            {item["code"] for item in report["blockers"]},
        )

    def test_protected_path_cannot_be_allowed(self):
        payload = valid_contract()
        payload["scope"]["allowed_paths"].append(
            "alliance/kirigakure/memory/obsidian"
        )

        report = self.validate(payload)

        self.assertIn(
            "protected_path_allowed",
            {item["code"] for item in report["blockers"]},
        )

    def test_path_traversal_is_blocked(self):
        payload = valid_contract()
        payload["scope"]["allowed_paths"].append("../outside")

        report = self.validate(payload)

        self.assertIn(
            "repo_path_invalid",
            {item["code"] for item in report["blockers"]},
        )

    def test_high_risk_requires_strict_review(self):
        payload = valid_contract()
        payload["risk_level"] = "high"
        payload["review"]["level"] = "standard"

        report = self.validate(payload)

        self.assertIn(
            "review_level_too_low",
            {item["code"] for item in report["blockers"]},
        )

    def test_teachback_is_mandatory(self):
        payload = valid_contract()
        payload["teachback_required"] = False

        report = self.validate(payload)

        self.assertIn(
            "teachback_not_required",
            {item["code"] for item in report["blockers"]},
        )

    def test_output_must_stay_under_sandbox(self):
        outside = self.repo / "report.json"

        with self.assertRaises(self.module.ContractValidationError):
            self.module.resolve_report_output(
                self.repo,
                str(outside),
            )

    def test_cli_ready_and_blocked_exit_codes(self):
        ready_path = self.repo / "ready.json"
        ready_path.write_text(
            json.dumps(valid_contract()),
            encoding="utf-8",
        )

        blocked = valid_contract()
        blocked["review"]["required"] = False
        blocked_path = self.repo / "blocked.json"
        blocked_path.write_text(
            json.dumps(blocked),
            encoding="utf-8",
        )

        ready_run = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--repo-root",
                str(self.repo),
                "--contract",
                str(ready_path),
                "--json",
            ],
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(ready_run.returncode, 0, ready_run.stderr)
        self.assertEqual(
            json.loads(ready_run.stdout)["readiness"],
            "ready",
        )

        blocked_run = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--repo-root",
                str(self.repo),
                "--contract",
                str(blocked_path),
                "--json",
            ],
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(blocked_run.returncode, 1, blocked_run.stderr)
        self.assertEqual(
            json.loads(blocked_run.stdout)["readiness"],
            "blocked",
        )

    def test_cli_report_output_under_sandbox(self):
        contract_path = self.repo / "contract.json"
        contract_path.write_text(
            json.dumps(valid_contract()),
            encoding="utf-8",
        )
        output = self.repo / "sandbox" / "reports" / "validation.json"

        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--repo-root",
                str(self.repo),
                "--contract",
                str(contract_path),
                "--output",
                str(output),
                "--force",
                "--json",
            ],
            text=True,
            capture_output=True,
            timeout=30,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(output.exists())
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["readiness"], "ready")


if __name__ == "__main__":
    unittest.main()
