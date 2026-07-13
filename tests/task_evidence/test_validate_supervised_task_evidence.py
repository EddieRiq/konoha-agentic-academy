import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT
    / "tools"
    / "task_evidence"
    / "validate_supervised_task_evidence.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "validate_supervised_task_evidence",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256_bytes(payload):
    return sha256(payload).hexdigest()


class SupervisedTaskEvidenceValidatorTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        (self.repo / "sandbox").mkdir()

        self.contract_path = self.repo / "contract.json"
        self.source_path = self.repo / "evidence.json"

        self.contract = {
            "schema_version": "1.0.0",
            "report_type": "supervised_task_contract",
            "contract_id": "contract-001",
            "mission_id": "mission-001",
            "acceptance_criteria": [
                "Inspect the public files.",
                "Record deterministic evidence.",
            ],
            "evidence_requirements": [
                "Record inspected paths.",
                "Record check results and exit codes.",
            ],
            "operations": {
                "allowed": [
                    "inspect_repository",
                    "run_deterministic_checks",
                    "record_external_result",
                ],
                "blocked": [
                    "execute_command",
                    "apply_patch",
                    "git_stage",
                    "git_commit",
                    "git_push",
                    "invoke_local_model",
                    "write_private_memory",
                    "close_mission",
                ],
            },
        }
        self.contract_path.write_text(
            json.dumps(self.contract, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        self.source = {
            "report_type": "test_evidence",
            "inspected_paths": ["README.md"],
            "checks": [{"exit_code": 0, "status": "passed"}],
        }
        self.source_path.write_text(
            json.dumps(self.source, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        contract_hash = self.module.sha256_file(self.contract_path)
        source_hash = self.module.sha256_file(self.source_path)

        self.bundle = {
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
                            "path": "evidence.json",
                            "sha256": source_hash,
                        }
                    ],
                    "related_acceptance_criteria": [0],
                    "related_operations": ["inspect_repository"],
                    "summary": "Inspected paths are recorded.",
                },
                {
                    "evidence_id": "evidence-002",
                    "requirement_index": 1,
                    "requirement_text": "Record check results and exit codes.",
                    "status": "satisfied",
                    "source_refs": [
                        {
                            "source_id": "source-002",
                            "source_type": "command_result",
                            "path": "evidence.json",
                            "sha256": source_hash,
                        }
                    ],
                    "related_acceptance_criteria": [1],
                    "related_operations": [
                        "run_deterministic_checks",
                        "record_external_result",
                    ],
                    "summary": "Check results and exit codes are recorded.",
                },
            ],
            "claims": [
                {
                    "claim_id": "claim-001",
                    "statement": "The required deterministic evidence exists.",
                    "status": "supported",
                    "evidence_ids": ["evidence-001", "evidence-002"],
                }
            ],
            "findings": [
                {
                    "finding_id": "finding-001",
                    "level": "info",
                    "statement": "The bundle maps all evidence requirements.",
                    "evidence_ids": ["evidence-001", "evidence-002"],
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

    def tearDown(self):
        self.tmp.cleanup()

    def write_bundle(self, payload=None):
        path = self.repo / "bundle.json"
        path.write_text(
            json.dumps(payload or self.bundle, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def validate(self, payload=None):
        bundle_path = self.write_bundle(payload)
        return self.module.validate_bundle(
            self.repo,
            bundle_path,
            payload or self.bundle,
        )

    def blocker_codes(self, report):
        return {item["code"] for item in report.get("blockers", [])}

    def test_complete_bundle_ready_for_human_review(self):
        report = self.validate()

        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["evidence_state"], "complete")
        self.assertEqual(
            report["readiness"],
            "ready_for_human_review",
        )
        self.assertEqual(report["summary"]["blocker_count"], 0)
        self.assertTrue(
            report["authority"][
                "ready_for_human_review_is_not_permission"
            ]
        )

    def test_contract_hash_mismatch_blocks(self):
        payload = deepcopy(self.bundle)
        payload["contract_reference"]["sha256"] = "0" * 64

        report = self.validate(payload)

        self.assertIn(
            "contract_sha256_mismatch",
            self.blocker_codes(report),
        )
        self.assertEqual(report["readiness"], "blocked")

    def test_contract_identity_mismatch_blocks(self):
        payload = deepcopy(self.bundle)
        payload["contract_id"] = "different-contract"

        report = self.validate(payload)

        self.assertIn(
            "contract_id_mismatch",
            self.blocker_codes(report),
        )

    def test_missing_requirement_mapping_blocks(self):
        payload = deepcopy(self.bundle)
        payload["evidence_items"] = payload["evidence_items"][:1]
        payload["claims"] = []
        payload["findings"][0]["evidence_ids"] = ["evidence-001"]
        payload["unresolved"] = [
            {
                "unresolved_id": "unresolved-001",
                "statement": "Second requirement lacks evidence.",
                "reason": "No source was recorded.",
                "requirement_indices": [1],
            }
        ]

        report = self.validate(payload)

        self.assertIn(
            "requirement_evidence_missing",
            self.blocker_codes(report),
        )
        self.assertEqual(report["evidence_state"], "incomplete")

    def test_duplicate_requirement_mapping_blocks(self):
        payload = deepcopy(self.bundle)
        payload["evidence_items"][1]["requirement_index"] = 0
        payload["evidence_items"][1][
            "requirement_text"
        ] = "Record inspected paths."

        report = self.validate(payload)

        self.assertIn(
            "requirement_index_duplicate",
            self.blocker_codes(report),
        )

    def test_requirement_text_mismatch_blocks(self):
        payload = deepcopy(self.bundle)
        payload["evidence_items"][0][
            "requirement_text"
        ] = "Invented requirement text."

        report = self.validate(payload)

        self.assertIn(
            "requirement_text_mismatch",
            self.blocker_codes(report),
        )

    def test_source_hash_mismatch_blocks(self):
        payload = deepcopy(self.bundle)
        payload["evidence_items"][0]["source_refs"][0][
            "sha256"
        ] = "f" * 64

        report = self.validate(payload)

        self.assertIn(
            "source_sha256_mismatch",
            self.blocker_codes(report),
        )

    def test_private_source_path_blocks(self):
        payload = deepcopy(self.bundle)
        payload["evidence_items"][0]["source_refs"][0][
            "path"
        ] = "alliance/kirigakure/private-evidence.json"

        report = self.validate(payload)

        self.assertIn(
            "source_path_invalid",
            self.blocker_codes(report),
        )

    def test_supported_claim_requires_satisfied_evidence(self):
        payload = deepcopy(self.bundle)
        payload["evidence_items"][0]["status"] = "unresolved"
        payload["unresolved"] = [
            {
                "unresolved_id": "unresolved-001",
                "statement": "Inspected paths need human confirmation.",
                "reason": "The source meaning is ambiguous.",
                "requirement_indices": [0],
            }
        ]

        report = self.validate(payload)

        self.assertIn(
            "supported_claim_uses_non_satisfied_evidence",
            self.blocker_codes(report),
        )

    def test_contradicted_evidence_sets_contradicted_state(self):
        payload = deepcopy(self.bundle)
        payload["evidence_items"][1]["status"] = "contradicted"
        payload["claims"][0]["status"] = "contradicted"

        report = self.validate(payload)

        self.assertEqual(report["evidence_state"], "contradicted")
        self.assertEqual(report["readiness"], "blocked")
        self.assertNotIn(
            "contradicted_claim_without_contradiction",
            self.blocker_codes(report),
        )

    def test_incomplete_bundle_can_explain_unresolved_evidence(self):
        payload = deepcopy(self.bundle)
        payload["evidence_items"][1]["status"] = "missing"
        payload["evidence_items"][1]["source_refs"] = []
        payload["claims"] = []
        payload["unresolved"] = [
            {
                "unresolved_id": "unresolved-001",
                "statement": "Check results are missing.",
                "reason": "The deterministic check was not recorded.",
                "requirement_indices": [1],
            }
        ]

        report = self.validate(payload)

        self.assertEqual(report["evidence_state"], "incomplete")
        self.assertEqual(report["readiness"], "blocked")
        self.assertNotIn(
            "incomplete_bundle_missing_unresolved_items",
            self.blocker_codes(report),
        )

    def test_cli_exit_codes_and_output_boundary(self):
        complete_path = self.write_bundle()

        complete = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--repo-root",
                str(self.repo),
                "--bundle",
                str(complete_path),
                "--output",
                str(self.repo / "sandbox" / "complete-report.json"),
                "--force",
                "--json",
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(complete.returncode, 0, complete.stderr)
        self.assertEqual(
            json.loads(complete.stdout)["evidence_state"],
            "complete",
        )

        incomplete_payload = deepcopy(self.bundle)
        incomplete_payload["evidence_items"][1]["status"] = "missing"
        incomplete_payload["evidence_items"][1]["source_refs"] = []
        incomplete_payload["claims"] = []
        incomplete_payload["unresolved"] = [
            {
                "unresolved_id": "unresolved-001",
                "statement": "Check evidence is missing.",
                "reason": "No source was recorded.",
                "requirement_indices": [1],
            }
        ]
        incomplete_path = self.write_bundle(incomplete_payload)

        incomplete = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--repo-root",
                str(self.repo),
                "--bundle",
                str(incomplete_path),
                "--json",
            ],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(incomplete.returncode, 1, incomplete.stderr)
        self.assertEqual(
            json.loads(incomplete.stdout)["evidence_state"],
            "incomplete",
        )

        unsafe_output = self.repo / "unsafe-report.json"
        unsafe = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--repo-root",
                str(self.repo),
                "--bundle",
                str(complete_path),
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
