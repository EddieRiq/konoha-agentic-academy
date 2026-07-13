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
    / "action_proposal"
    / "validate_supervised_action_proposal.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "validate_supervised_action_proposal",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SupervisedActionProposalValidatorTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        (self.repo / "sandbox").mkdir()
        (self.repo / "docs").mkdir()

        for relative, content in {
            "README.md": "# README\n",
            "CHANGELOG.md": "# CHANGELOG\n",
            "docs/roadmap.md": "# Roadmap\n",
        }.items():
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        self.contract_path = self.repo / "contract.json"
        self.source_path = self.repo / "source.json"
        self.evidence_path = self.repo / "evidence.json"

        self.contract = {
            "schema_version": "1.0.0",
            "report_type": "supervised_task_contract",
            "contract_id": "contract-001",
            "mission_id": "mission-001",
            "title": "Review documentation",
            "objective": "Review public documentation without mutation.",
            "non_goals": ["Do not mutate repository state."],
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
                    "memory/local/**",
                    "vault/**",
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
                "Inspect public documentation.",
                "Record deterministic evidence.",
            ],
            "evidence_requirements": [
                "Record inspected paths.",
                "Record deterministic check results.",
            ],
            "approval_requirements": [],
            "completion_conditions": [
                "A human reviewer confirms the evidence."
            ],
            "review": {
                "required": True,
                "level": "standard",
                "reviewers": ["human", "jounin"],
            },
            "teachback_required": True,
            "stop_triggers": [
                "Private data appears.",
                "A blocked operation becomes necessary.",
            ],
            "authority": {
                "contract_is_not_permission": True,
                "validator_output_is_evidence_only": True,
                "mission_state_does_not_authorize_execution": True,
                "approvals_are_operation_specific": True,
            },
        }
        self.contract_path.write_text(
            json.dumps(self.contract, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        self.source = {
            "report_type": "test_source",
            "paths": ["README.md", "docs/roadmap.md"],
            "checks": [{"argv": ["grep", "-n", "test"], "exit_code": 0}],
        }
        self.source_path.write_text(
            json.dumps(self.source, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        contract_hash = self.module.sha256_file(self.contract_path)
        source_hash = self.module.sha256_file(self.source_path)

        self.evidence = {
            "schema_version": "1.0.0",
            "report_type": "supervised_task_evidence_bundle",
            "bundle_id": "bundle-001",
            "contract_reference": {
                "path": "contract.json",
                "sha256": contract_hash,
            },
            "contract_id": "contract-001",
            "mission_id": "mission-001",
            "evidence_items": [
                {
                    "evidence_id": "evidence-001",
                    "requirement_index": 0,
                    "requirement_text": "Record inspected paths.",
                    "status": "satisfied",
                    "source_refs": [
                        {
                            "source_id": "source-001",
                            "source_type": "report",
                            "path": "source.json",
                            "sha256": source_hash,
                        }
                    ],
                    "related_acceptance_criteria": [0],
                    "related_operations": ["inspect_repository"],
                    "summary": "Public paths are recorded.",
                },
                {
                    "evidence_id": "evidence-002",
                    "requirement_index": 1,
                    "requirement_text": "Record deterministic check results.",
                    "status": "satisfied",
                    "source_refs": [
                        {
                            "source_id": "source-002",
                            "source_type": "command_result",
                            "path": "source.json",
                            "sha256": source_hash,
                        }
                    ],
                    "related_acceptance_criteria": [1],
                    "related_operations": [
                        "run_deterministic_checks",
                        "record_external_result",
                    ],
                    "summary": "Deterministic results are recorded.",
                },
            ],
            "claims": [
                {
                    "claim_id": "claim-001",
                    "statement": "Required evidence is recorded.",
                    "status": "supported",
                    "evidence_ids": ["evidence-001", "evidence-002"],
                }
            ],
            "findings": [
                {
                    "finding_id": "finding-001",
                    "level": "info",
                    "statement": "No mutation is authorized.",
                    "evidence_ids": ["evidence-001"],
                }
            ],
            "unresolved": [],
            "authority": {
                "bundle_is_evidence_only": True,
                "evidence_does_not_authorize_execution": True,
                "hashes_do_not_prove_truth": True,
                "human_review_required": True,
            },
        }
        self.evidence_path.write_text(
            json.dumps(self.evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        evidence_hash = self.module.sha256_file(self.evidence_path)

        self.proposal = {
            "schema_version": "1.0.0",
            "report_type": "supervised_action_proposal",
            "proposal_id": "proposal-001",
            "contract_reference": {
                "path": "contract.json",
                "sha256": contract_hash,
            },
            "evidence_bundle_reference": {
                "path": "evidence.json",
                "sha256": evidence_hash,
            },
            "contract_id": "contract-001",
            "bundle_id": "bundle-001",
            "mission_id": "mission-001",
            "title": "Review public documentation",
            "rationale": "Complete evidence supports a bounded read-only review.",
            "risk_level": "medium",
            "affected_paths": [
                "README.md",
                "CHANGELOG.md",
                "docs/roadmap.md",
            ],
            "proposed_actions": [
                {
                    "action_id": "inspect-docs",
                    "operation": "inspect_repository",
                    "purpose": "Inspect declared public paths.",
                    "expected_effect": "Identify public documentation markers.",
                    "risk_level": "low",
                    "affected_paths": [
                        "README.md",
                        "docs/roadmap.md",
                    ],
                    "evidence_ids": ["evidence-001"],
                    "acceptance_criteria": [0],
                    "working_directory": ".",
                    "requires_approval": False,
                    "destructive": False,
                    "irreversible": False,
                    "execution_status": "proposed_only",
                },
                {
                    "action_id": "check-docs",
                    "operation": "run_deterministic_checks",
                    "purpose": "Propose a deterministic read-only check.",
                    "expected_effect": "Return public marker matches.",
                    "risk_level": "low",
                    "affected_paths": [
                        "README.md",
                        "CHANGELOG.md",
                        "docs/roadmap.md",
                    ],
                    "evidence_ids": ["evidence-002"],
                    "acceptance_criteria": [0, 1],
                    "command_argv": [
                        "grep",
                        "-n",
                        "test",
                        "README.md",
                        "CHANGELOG.md",
                        "docs/roadmap.md",
                    ],
                    "working_directory": ".",
                    "requires_approval": False,
                    "destructive": False,
                    "irreversible": False,
                    "execution_status": "proposed_only",
                },
            ],
            "approval_requirements": [],
            "rollback_plan": {
                "mode": "not_required",
                "affected_state": ["No state change is proposed."],
                "pre_action_evidence": ["Contract and evidence hashes."],
                "success_checks": ["No repository mutation."],
                "failure_signals": ["A blocked path is required."],
                "recovery_steps": ["Stop without changing state."],
                "rollback_commands": [],
                "irreversible_actions": [],
                "residual_risk": "Human interpretation may still be wrong.",
                "approval_owner": "human",
                "authority": {
                    "rollback_is_not_authorized": True,
                    "rollback_commands_are_data_only": True,
                },
            },
            "acceptance_criteria_links": [0, 1],
            "stop_trigger_links": [0, 1],
            "review": {
                "required": True,
                "level": "standard",
                "reviewers": ["human", "jounin"],
            },
            "authority": {
                "proposal_is_not_permission": True,
                "commands_are_data_only": True,
                "approvals_are_not_consumed": True,
                "evidence_does_not_authorize_action": True,
                "human_review_required": True,
                "mission_state_does_not_authorize_execution": True,
            },
        }

    def tearDown(self):
        self.tmp.cleanup()

    def rewrite_contract_and_references(self, proposal):
        self.contract_path.write_text(
            json.dumps(self.contract, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        contract_hash = self.module.sha256_file(self.contract_path)
        proposal["contract_reference"]["sha256"] = contract_hash
        self.evidence["contract_reference"]["sha256"] = contract_hash

        self.evidence_path.write_text(
            json.dumps(self.evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        proposal["evidence_bundle_reference"][
            "sha256"
        ] = self.module.sha256_file(self.evidence_path)

    def write_proposal(self, payload=None):
        path = self.repo / "proposal.json"
        path.write_text(
            json.dumps(payload or self.proposal, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        return path

    def validate(self, payload=None):
        proposal = payload or self.proposal
        path = self.write_proposal(proposal)
        return self.module.validate_proposal(self.repo, path, proposal)

    @staticmethod
    def blocker_codes(report):
        return {item["code"] for item in report.get("blockers", [])}

    def test_valid_proposal_is_ready_for_approval_review(self):
        report = self.validate()

        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["proposal_state"], "proposed")
        self.assertEqual(
            report["readiness"],
            "ready_for_approval_review",
        )
        self.assertEqual(report["summary"]["blocker_count"], 0)
        self.assertFalse(
            report["summary"]["state_changing_operation_present"]
        )
        self.assertTrue(
            report["authority"][
                "ready_for_approval_review_is_not_approval"
            ]
        )

    def test_contract_hash_mismatch_blocks(self):
        payload = deepcopy(self.proposal)
        payload["contract_reference"]["sha256"] = "0" * 64

        report = self.validate(payload)

        self.assertIn(
            "reference_sha256_mismatch",
            self.blocker_codes(report),
        )

    def test_evidence_hash_mismatch_blocks(self):
        payload = deepcopy(self.proposal)
        payload["evidence_bundle_reference"]["sha256"] = "f" * 64

        report = self.validate(payload)

        self.assertIn(
            "reference_sha256_mismatch",
            self.blocker_codes(report),
        )

    def test_identity_mismatch_blocks(self):
        payload = deepcopy(self.proposal)
        payload["contract_id"] = "other-contract"
        payload["bundle_id"] = "other-bundle"
        payload["mission_id"] = "other-mission"

        report = self.validate(payload)
        codes = self.blocker_codes(report)

        self.assertIn("proposal_contract_id_mismatch", codes)
        self.assertIn("proposal_bundle_id_mismatch", codes)
        self.assertIn("proposal_mission_id_mismatch", codes)

    def test_incomplete_evidence_blocks(self):
        payload = deepcopy(self.proposal)
        self.evidence["evidence_items"][1]["status"] = "missing"
        self.evidence["evidence_items"][1]["source_refs"] = []
        self.evidence["unresolved"] = [
            {
                "unresolved_id": "missing-result",
                "statement": "Check result is missing.",
                "reason": "No source was recorded.",
                "requirement_indices": [1],
            }
        ]
        self.rewrite_contract_and_references(payload)

        report = self.validate(payload)
        codes = self.blocker_codes(report)

        self.assertIn("evidence_not_satisfied", codes)
        self.assertIn("evidence_has_unresolved_items", codes)

    def test_unsupported_evidence_claim_blocks(self):
        payload = deepcopy(self.proposal)
        self.evidence["claims"][0]["status"] = "unsupported"
        self.rewrite_contract_and_references(payload)

        report = self.validate(payload)

        self.assertIn(
            "evidence_claim_not_supported",
            self.blocker_codes(report),
        )

    def test_operation_not_allowed_by_contract_blocks(self):
        payload = deepcopy(self.proposal)
        action = payload["proposed_actions"][0]
        action["operation"] = "apply_patch"
        action["command_argv"] = ["python", "patch.py"]
        action["requires_approval"] = True

        report = self.validate(payload)
        codes = self.blocker_codes(report)

        self.assertIn("action_operation_not_allowed", codes)
        self.assertIn("action_operation_blocked", codes)

    def test_path_outside_contract_scope_blocks(self):
        payload = deepcopy(self.proposal)
        payload["affected_paths"].append("tools/unsafe.py")
        payload["proposed_actions"][0]["affected_paths"].append(
            "tools/unsafe.py"
        )

        report = self.validate(payload)
        codes = self.blocker_codes(report)

        self.assertIn("proposal_path_outside_contract", codes)
        self.assertIn("action_path_outside_contract", codes)

    def test_private_path_blocks(self):
        payload = deepcopy(self.proposal)
        payload["affected_paths"].append("vault/private.json")
        payload["proposed_actions"][0]["affected_paths"].append(
            "vault/private.json"
        )

        report = self.validate(payload)
        codes = self.blocker_codes(report)

        self.assertIn("proposal_private_path_blocked", codes)
        self.assertIn("action_private_path_blocked", codes)

    def test_shell_composition_token_blocks(self):
        payload = deepcopy(self.proposal)
        payload["proposed_actions"][1]["command_argv"] = [
            "grep",
            "-n",
            "test",
            "README.md",
            "&&",
            "git",
            "status",
        ]

        report = self.validate(payload)

        self.assertIn(
            "shell_composition_blocked",
            self.blocker_codes(report),
        )

    def test_sensitive_state_change_needs_approval_and_rollback(self):
        payload = deepcopy(self.proposal)

        self.contract["operations"]["allowed"].append("execute_command")
        self.contract["operations"]["blocked"].remove("execute_command")

        action = payload["proposed_actions"][0]
        action["operation"] = "execute_command"
        action["command_argv"] = ["python", "mutate.py"]
        action["requires_approval"] = True
        action["destructive"] = True

        self.rewrite_contract_and_references(payload)

        report = self.validate(payload)
        codes = self.blocker_codes(report)

        self.assertIn("operation_without_declared_approval", codes)
        self.assertIn("rollback_required_for_state_change", codes)
        self.assertTrue(
            report["summary"]["state_changing_operation_present"]
        )

    def test_cli_exit_codes_and_output_boundary(self):
        proposal_path = self.write_proposal()

        ready = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--repo-root",
                str(self.repo),
                "--proposal",
                str(proposal_path),
                "--output",
                str(self.repo / "sandbox" / "ready.json"),
                "--force",
                "--json",
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(ready.returncode, 0, ready.stderr)
        self.assertEqual(
            json.loads(ready.stdout)["proposal_state"],
            "proposed",
        )

        blocked_payload = deepcopy(self.proposal)
        blocked_payload["proposed_actions"][0][
            "operation"
        ] = "apply_patch"
        blocked_payload["proposed_actions"][0][
            "command_argv"
        ] = ["python", "patch.py"]
        blocked_path = self.write_proposal(blocked_payload)

        blocked = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--repo-root",
                str(self.repo),
                "--proposal",
                str(blocked_path),
                "--json",
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(blocked.returncode, 1, blocked.stderr)
        self.assertEqual(
            json.loads(blocked.stdout)["proposal_state"],
            "blocked",
        )

        unsafe_output = self.repo / "unsafe.json"
        unsafe = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--repo-root",
                str(self.repo),
                "--proposal",
                str(proposal_path),
                "--output",
                str(unsafe_output),
                "--force",
                "--json",
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(unsafe.returncode, 2, unsafe.stderr)
        self.assertFalse(unsafe_output.exists())


if __name__ == "__main__":
    unittest.main()
