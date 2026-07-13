import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = (
    REPO_ROOT
    / "tools"
    / "mission_closure"
    / "close_mission.py"
)
TEACHBACK_PATH = (
    REPO_ROOT
    / "tools"
    / "teachback"
    / "manage_teachback.py"
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def create_mission(
    workspace_root: Path,
    mission_id: str,
) -> Path:
    mission = workspace_root / "missions" / mission_id
    for relative in [
        "reports",
        "plans",
        "approvals",
        "evidence",
        "inputs",
        "context",
        "outputs",
    ]:
        (mission / relative).mkdir(
            parents=True,
            exist_ok=True,
        )

    (mission / "charter.md").write_text(
        (
            "# Charter\n\n"
            "risk_level: medium\n"
            "teachback_required: true\n"
            "teachback_required_level: 2\n"
        ),
        encoding="utf-8",
    )
    (mission / "mission_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "mission_id": mission_id,
                "title": "Test mission",
                "risk_level": "medium",
                "teachback": {
                    "required": True,
                    "required_level": 2,
                    "skip_allowed": False,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (mission / "evidence" / "execution.json").write_text(
        json.dumps(
            {
                "report_type": "task_execution_result",
                "status": "passed",
                "exit_code": 0,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (mission / "reports" / "review.json").write_text(
        json.dumps(
            {
                "report_type": "konoha_human_review_record",
                "status": "passed",
                "review_decision": "approved",
                "human_approval": True,
                "reviewed_by": "eduardo",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return mission


class MissionClosureTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module(
            TOOL_PATH,
            "close_mission_module",
        )
        self.teachback = load_module(
            TEACHBACK_PATH,
            "teachback_test_module",
        )
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.workspace = self.root / "workspace"
        self.memory = self.root / "memory" / "vault"
        self.mission_id = "mission-close-test"
        self.mission = create_mission(
            self.workspace,
            self.mission_id,
        )
        self.record_teachback()

    def tearDown(self):
        self.tmp.cleanup()

    def record_teachback(
        self,
        *,
        teachback_id="close-test",
        result="passed",
        achieved_level=2,
        completed=True,
        gaps=None,
        next_needed=None,
    ):
        args = [
            "record",
            "--workspace-root",
            str(self.workspace),
            "--mission-id",
            self.mission_id,
            "--teachback-id",
            teachback_id,
            "--result",
            result,
            "--achieved-level",
            str(achieved_level),
            "--summary",
            (
                "I can explain the implementation, operation, "
                "validation and remaining limitations."
            ),
            "--human-actor",
            "eduardo",
            "--source-execution",
            "evidence/execution.json",
            "--source-review",
            "reports/review.json",
            "--confirm-record",
            "--approval-token",
            "RECORD_TEACHBACK_EVIDENCE",
        ]
        if completed:
            args.append("--completed-by-user")
        if result == "passed":
            args.extend(
                [
                    "--human-evidence",
                    (
                        "The user explained the purpose, operation, "
                        "validation and failure modes in their own words."
                    ),
                ]
            )
        for gap in gaps or []:
            args.extend(["--gap", gap])
        if next_needed:
            args.extend(
                [
                    "--next-explanation-needed",
                    next_needed,
                ]
            )
        return self.teachback.main(args)

    def base_args(self, teachback_id="close-test"):
        return [
            "--workspace-root",
            str(self.workspace),
            "--mission-id",
            self.mission_id,
            "--memory-root",
            str(self.memory),
            "--closure-id",
            "close-test",
            "--execution-evidence",
            "evidence/execution.json",
            "--review-evidence",
            "reports/review.json",
            "--teachback-record",
            (
                "reports/"
                f"{teachback_id}_teachback_record.json"
            ),
            "--closure-reason",
            "Mission reviewed and ready for closure.",
            "--human-actor",
            "eduardo",
        ]

    def test_preview_does_not_write_outputs(self):
        code = self.module.main(self.base_args())
        self.assertEqual(code, 0)
        self.assertFalse(
            (
                self.mission
                / "reports"
                / "close-test_mission_closure_report.json"
            ).exists()
        )

    def test_confirmed_close_writes_reports_and_memory(self):
        code = self.module.main(
            self.base_args()
            + [
                "--confirm-close",
                "--approval-token",
                "CLOSE_MISSION_WITH_TEACHBACK",
            ]
        )
        self.assertEqual(code, 0)

        report = (
            self.mission
            / "reports"
            / "close-test_mission_closure_report.json"
        )
        self.assertTrue(report.exists())
        self.assertTrue(
            (
                self.mission
                / "reports"
                / "close-test_notification_state.json"
            ).exists()
        )
        self.assertTrue(
            (self.mission / "mission_status.json").exists()
        )

        status = json.loads(
            (self.mission / "mission_status.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(status["status"], "closed")
        self.assertEqual(
            status["teachback_status"],
            "passed",
        )

        self.assertTrue(
            (
                self.memory
                / "10-missions"
                / f"{self.mission_id}.md"
            ).exists()
        )
        self.assertTrue(
            (
                self.memory
                / "20-decisions"
                / f"{self.mission_id}_closure_decision.md"
            ).exists()
        )

    def test_rejects_wrong_approval_token(self):
        code = self.module.main(
            self.base_args()
            + [
                "--confirm-close",
                "--approval-token",
                "WRONG",
            ]
        )
        self.assertEqual(code, 1)

    def test_needs_clarification_blocks_closure(self):
        self.record_teachback(
            teachback_id="clarify",
            result="needs_clarification",
            achieved_level=1,
            completed=False,
            gaps=["Cannot yet explain rollback."],
            next_needed="Explain rollback and recovery.",
        )
        code = self.module.main(
            self.base_args("clarify")
            + [
                "--confirm-close",
                "--approval-token",
                "CLOSE_MISSION_WITH_TEACHBACK",
            ]
        )
        self.assertEqual(code, 1)

    def test_changes_requested_review_blocks_closure(self):
        (self.mission / "reports" / "review.json").write_text(
            json.dumps(
                {
                    "status": "passed",
                    "review_decision": "changes_requested",
                    "human_approval": False,
                    "reviewed_by": "eduardo",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        code = self.module.main(self.base_args())
        self.assertEqual(code, 1)

    def test_failed_execution_blocks_closure(self):
        (
            self.mission
            / "evidence"
            / "execution.json"
        ).write_text(
            json.dumps(
                {
                    "status": "failed",
                    "exit_code": 1,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        code = self.module.main(self.base_args())
        self.assertEqual(code, 1)

    def test_identical_reentry_is_idempotent(self):
        args = self.base_args() + [
            "--confirm-close",
            "--approval-token",
            "CLOSE_MISSION_WITH_TEACHBACK",
        ]
        self.assertEqual(self.module.main(args), 0)
        report_path = (
            self.mission
            / "reports"
            / "close-test_mission_closure_report.json"
        )
        before = report_path.read_bytes()

        self.assertEqual(self.module.main(args), 0)
        self.assertEqual(report_path.read_bytes(), before)

    def test_conflicting_reentry_blocks_even_with_force(self):
        args = self.base_args() + [
            "--confirm-close",
            "--approval-token",
            "CLOSE_MISSION_WITH_TEACHBACK",
        ]
        self.assertEqual(self.module.main(args), 0)

        conflict = self.base_args()
        index = conflict.index("--closure-reason") + 1
        conflict[index] = (
            "A different human closure reason is supplied."
        )
        conflict.extend(
            [
                "--confirm-close",
                "--approval-token",
                "CLOSE_MISSION_WITH_TEACHBACK",
                "--force",
            ]
        )
        self.assertEqual(self.module.main(conflict), 1)

    def test_rejects_path_traversal_mission_id(self):
        args = self.base_args()
        args[
            args.index("--mission-id") + 1
        ] = "../escape"
        self.assertEqual(self.module.main(args), 1)

    def test_markdown_frontmatter_contains_type(self):
        content = self.module.markdown_frontmatter(
            {
                "type": "mission_memory",
                "mission_id": "m1",
            },
            "# Body",
        )
        self.assertIn("---", content)
        self.assertIn("type:", content)
        self.assertIn("# Body", content)


if __name__ == "__main__":
    unittest.main()
