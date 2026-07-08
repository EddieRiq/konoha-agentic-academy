import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "scroll_lifecycle" / "manage_scroll_lifecycle.py"
spec = importlib.util.spec_from_file_location("manage_scroll_lifecycle", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class ScrollLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.workspace = self.root / "workspace"
        self.mission_id = "mission-scroll-test"
        self.mission = self.workspace / "missions" / self.mission_id
        for rel in ["reports", "evidence", "learning_proposals"]:
            (self.mission / rel).mkdir(parents=True, exist_ok=True)
        (self.mission / "evidence" / "finding.md").write_text("# evidence\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, args):
        return module.main(args)

    def proposal_args(self, extra=None):
        args = [
            "propose-learning",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--proposal-id", "proposal-one",
            "--scroll-name", "test-scroll",
            "--learning-summary", "The mission found a repeatable review pattern.",
            "--proposed-behavior-change", "Add a checklist item for that review pattern.",
            "--evidence-path", str(self.mission / "evidence" / "finding.md"),
        ]
        if extra:
            args.extend(extra)
        return args

    def test_preview_does_not_write_proposal(self):
        code = self.run_cli(self.proposal_args())
        self.assertEqual(code, 0)
        self.assertFalse((self.mission / "learning_proposals" / "proposal-one.md").exists())

    def test_confirmed_proposal_writes_markdown_json_and_report(self):
        code = self.run_cli(self.proposal_args([
            "--confirm-proposal",
            "--approval-token", module.PROPOSAL_TOKEN,
            "--actor", "eduardo",
            "--force",
        ]))
        self.assertEqual(code, 0)
        proposal = self.mission / "learning_proposals" / "proposal-one.md"
        report = self.mission / "reports" / "proposal-one_scroll_learning_proposal_report.json"
        self.assertTrue(proposal.exists())
        self.assertTrue(report.exists())
        text = proposal.read_text(encoding="utf-8")
        self.assertIn("This learning proposal is evidence only.", text)
        data = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "passed")
        self.assertTrue(data["authority"]["learning_proposals_are_evidence_only"])

    def test_wrong_proposal_token_fails(self):
        code = self.run_cli(self.proposal_args([
            "--confirm-proposal",
            "--approval-token", "WRONG",
        ]))
        self.assertEqual(code, 1)

    def test_review_requires_existing_proposal(self):
        code = self.run_cli([
            "review-proposal",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--proposal-id", "missing",
            "--decision", "approve_for_experiment",
            "--rationale", "Looks good.",
            "--confirm-review",
            "--approval-token", module.REVIEW_TOKEN,
        ])
        self.assertEqual(code, 1)

    def test_confirmed_review_writes_report(self):
        self.assertEqual(self.run_cli(self.proposal_args([
            "--confirm-proposal",
            "--approval-token", module.PROPOSAL_TOKEN,
            "--force",
        ])), 0)
        code = self.run_cli([
            "review-proposal",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--proposal-id", "proposal-one",
            "--decision", "approve_for_experiment",
            "--rationale", "Safe to experiment inside a mission.",
            "--reviewer", "jounin",
            "--confirm-review",
            "--approval-token", module.REVIEW_TOKEN,
            "--force",
        ])
        self.assertEqual(code, 0)
        report = self.mission / "reports" / "proposal-one_scroll_lifecycle_review_report.json"
        self.assertTrue(report.exists())
        data = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(data["decision"], "approve_for_experiment")
        self.assertTrue(data["authority"]["review_records_do_not_rewrite_doctrine"])

    def test_promotion_plan_requires_prior_review(self):
        self.assertEqual(self.run_cli(self.proposal_args([
            "--confirm-proposal",
            "--approval-token", module.PROPOSAL_TOKEN,
            "--force",
        ])), 0)
        code = self.run_cli([
            "plan-promotion",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--proposal-id", "proposal-one",
            "--target-scroll", "scrolls/test/SKILL.md",
            "--promotion-rationale", "Needed after review.",
            "--confirm-plan",
            "--approval-token", module.PROMOTION_PLAN_TOKEN,
        ])
        self.assertEqual(code, 1)

    def test_index_reports_existing_proposals(self):
        self.assertEqual(self.run_cli(self.proposal_args([
            "--confirm-proposal",
            "--approval-token", module.PROPOSAL_TOKEN,
            "--force",
        ])), 0)
        code = self.run_cli([
            "index",
            "--workspace-root", str(self.workspace),
            "--mission-id", self.mission_id,
            "--write-index",
            "--force",
        ])
        self.assertEqual(code, 0)
        index_path = self.mission / "learning_proposals" / "scroll_learning_proposal_index.json"
        self.assertTrue(index_path.exists())
        data = json.loads(index_path.read_text(encoding="utf-8"))
        self.assertEqual(data["proposal_count"], 1)


if __name__ == "__main__":
    unittest.main()
