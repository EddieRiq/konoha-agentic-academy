import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "teachback" / "manage_teachback.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "manage_teachback_test",
        TOOL,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ManageTeachbackTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp.name) / "workspace"
        self.mission_id = "teachback-test"
        self.mission = (
            self.workspace / "missions" / self.mission_id
        )
        (self.mission / "reports").mkdir(
            parents=True,
            exist_ok=True,
        )
        (self.mission / "evidence").mkdir(
            parents=True,
            exist_ok=True,
        )
        (self.mission / "charter.md").write_text(
            "# Charter\n",
            encoding="utf-8",
        )
        self.write_manifest(
            required=True,
            level=2,
            risk="medium",
            skip_allowed=False,
        )
        (self.mission / "evidence" / "execution.json").write_text(
            '{"status":"passed"}\n',
            encoding="utf-8",
        )
        (self.mission / "reports" / "review.json").write_text(
            '{"status":"passed","reviewed_by":"human"}\n',
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def write_manifest(
        self,
        *,
        required,
        level,
        risk,
        skip_allowed,
    ):
        (self.mission / "mission_manifest.json").write_text(
            json.dumps(
                {
                    "mission_id": self.mission_id,
                    "risk_level": risk,
                    "teachback": {
                        "required": required,
                        "required_level": level,
                        "skip_allowed": skip_allowed,
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def passed_args(self, teachback_id="passed"):
        return [
            "record",
            "--workspace-root",
            str(self.workspace),
            "--mission-id",
            self.mission_id,
            "--teachback-id",
            teachback_id,
            "--result",
            "passed",
            "--achieved-level",
            "2",
            "--completed-by-user",
            "--summary",
            (
                "The user can explain operation, validation, "
                "risks and recovery."
            ),
            "--human-evidence",
            (
                "User explanation covers inputs, outputs, "
                "validation and common failures."
            ),
            "--source-execution",
            "evidence/execution.json",
            "--source-review",
            "reports/review.json",
        ]

    def test_prepare_uses_manifest_policy(self):
        self.assertEqual(
            self.module.main(
                [
                    "prepare",
                    "--workspace-root",
                    str(self.workspace),
                    "--mission-id",
                    self.mission_id,
                ]
            ),
            0,
        )

    def test_passed_record_is_written(self):
        code = self.module.main(
            self.passed_args()
            + [
                "--confirm-record",
                "--approval-token",
                "RECORD_TEACHBACK_EVIDENCE",
            ]
        )
        self.assertEqual(code, 0)
        record = (
            self.mission
            / "reports"
            / "passed_teachback_record.json"
        )
        payload = json.loads(record.read_text(encoding="utf-8"))
        self.assertEqual(payload["result"], "passed")
        self.assertTrue(payload["completed_by_user"])

    def test_wrong_token_does_not_write(self):
        code = self.module.main(
            self.passed_args("wrong-token")
            + [
                "--confirm-record",
                "--approval-token",
                "WRONG",
            ]
        )
        self.assertEqual(code, 1)
        self.assertFalse(
            (
                self.mission
                / "reports"
                / "wrong-token_teachback_record.json"
            ).exists()
        )

    def test_passed_level_below_required_blocks(self):
        args = self.passed_args("low-level")
        args[args.index("--achieved-level") + 1] = "1"
        code = self.module.main(
            args
            + [
                "--confirm-record",
                "--approval-token",
                "RECORD_TEACHBACK_EVIDENCE",
            ]
        )
        self.assertEqual(code, 1)

    def test_needs_clarification_is_recordable_not_complete(self):
        code = self.module.main(
            [
                "record",
                "--workspace-root",
                str(self.workspace),
                "--mission-id",
                self.mission_id,
                "--teachback-id",
                "clarify",
                "--result",
                "needs_clarification",
                "--achieved-level",
                "1",
                "--summary",
                "The user understands setup but not rollback.",
                "--gap",
                "Rollback is not understood.",
                "--next-explanation-needed",
                "Explain rollback with a concrete example.",
                "--source-execution",
                "evidence/execution.json",
                "--source-review",
                "reports/review.json",
                "--confirm-record",
                "--approval-token",
                "RECORD_TEACHBACK_EVIDENCE",
            ]
        )
        self.assertEqual(code, 0)
        payload = json.loads(
            (
                self.mission
                / "reports"
                / "clarify_teachback_record.json"
            ).read_text(encoding="utf-8")
        )
        self.assertFalse(payload["completed_by_user"])

    def test_skip_blocks_when_manifest_requires_teachback(self):
        code = self.module.main(
            [
                "record",
                "--workspace-root",
                str(self.workspace),
                "--mission-id",
                self.mission_id,
                "--teachback-id",
                "skip",
                "--result",
                "skipped",
                "--achieved-level",
                "0",
                "--summary",
                "Teachback skipped by charter.",
                "--skip-reason",
                "Conversation-only mission.",
                "--confirm-record",
                "--approval-token",
                "RECORD_TEACHBACK_EVIDENCE",
            ]
        )
        self.assertEqual(code, 1)

    def test_skip_allowed_only_for_explicit_low_risk_policy(self):
        self.write_manifest(
            required=False,
            level=0,
            risk="low",
            skip_allowed=True,
        )
        code = self.module.main(
            [
                "record",
                "--workspace-root",
                str(self.workspace),
                "--mission-id",
                self.mission_id,
                "--teachback-id",
                "skip-low",
                "--result",
                "skipped",
                "--achieved-level",
                "0",
                "--completed-by-user",
                "--summary",
                "No reusable deliverable was produced.",
                "--skip-reason",
                "Conversation-only mission.",
                "--confirm-record",
                "--approval-token",
                "RECORD_TEACHBACK_EVIDENCE",
            ]
        )
        self.assertEqual(code, 0)

    def test_conflicting_reentry_blocks(self):
        args = self.passed_args("conflict") + [
            "--confirm-record",
            "--approval-token",
            "RECORD_TEACHBACK_EVIDENCE",
        ]
        self.assertEqual(self.module.main(args), 0)

        changed = list(args)
        index = changed.index("--summary") + 1
        changed[index] = (
            "A different human explanation changes evidence."
        )
        self.assertEqual(self.module.main(changed), 1)

    def test_status_marks_passed_record_close_eligible(self):
        args = self.passed_args("status") + [
            "--confirm-record",
            "--approval-token",
            "RECORD_TEACHBACK_EVIDENCE",
        ]
        self.assertEqual(self.module.main(args), 0)
        self.assertEqual(
            self.module.main(
                [
                    "status",
                    "--workspace-root",
                    str(self.workspace),
                    "--mission-id",
                    self.mission_id,
                    "--teachback-record",
                    "reports/status_teachback_record.json",
                ]
            ),
            0,
        )

    def test_source_path_traversal_blocks(self):
        outside = Path(self.tmp.name) / "outside.json"
        outside.write_text('{"status":"passed"}\n', encoding="utf-8")
        args = self.passed_args("escape")
        index = args.index("--source-execution") + 1
        args[index] = str(outside)
        code = self.module.main(
            args
            + [
                "--confirm-record",
                "--approval-token",
                "RECORD_TEACHBACK_EVIDENCE",
            ]
        )
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
