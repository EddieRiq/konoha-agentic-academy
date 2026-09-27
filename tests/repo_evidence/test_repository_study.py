import tempfile
import unittest
from pathlib import Path

from tools.repo_evidence.acquire_repo_evidence import Authorization, acquire_repo_evidence
from tools.repo_evidence.study import (build_repository_study, validate_repository_study,
                                       explain_repository_study, MAX_STUDY_ITEMS)
from tools.teachback.manage_teachback import (start_repository_teachback, respond_repository_teachback,
                                            validate_repository_teachback, TeachbackError)


class RepositoryStudyTests(unittest.TestCase):
    def fixture(self, root):
        (root / "app.py").write_text("import helper\ndef main(): return helper.run()\n")
        (root / "helper.py").write_text("def run(): return 1\n")
        (root / "test_app.py").write_text("import app\ndef test_main(): assert app.main() == 1\n")
        (root / "README.md").write_text("Run `app.main()`\n")
        (root / "pyproject.toml").write_text('[project.scripts]\nfixture = "app:main"\n')
        return acquire_repo_evidence(root, Authorization("human", "synthetic public fixture"))

    def test_generic_study_provenance_bounds_and_no_executed_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            pack = self.fixture(Path(directory))
            study = build_repository_study(pack)
            self.assertEqual(study, validate_repository_study(study.as_dict(), pack))
            self.assertEqual(study.authority, "evidence_only")
            self.assertTrue({"components", "relationships", "capabilities", "tests", "documentation"} <= {f["category"] for f in study.facts})
            for fact in study.facts:
                self.assertEqual(fact["locator"], pack.provenance_index[fact["evidence_ref"]])
                self.assertLessEqual(len(fact["observation"]), 2000)
            explanation = explain_repository_study(study)
            self.assertIn("execution result unknown", explanation)
            self.assertIn(pack.pack_id, explanation)
            bad = study.as_dict()
            bad["facts"][0]["observation"] = "fabricated"
            with self.assertRaises(ValueError):
                validate_repository_study(bad, pack)

    def test_only_exact_human_command_closes_repetition_and_clarification(self):
        with tempfile.TemporaryDirectory() as directory:
            study = build_repository_study(self.fixture(Path(directory)))
            session = start_repository_teachback(study)
            for text in ("yes", "understood", ":Entendido", " :entendido", ":entendido\n", "repeat tests"):
                session = respond_repository_teachback(session, study, text, actor="human")
                self.assertFalse(session["completed_by_user"])
            with self.assertRaises(TeachbackError):
                respond_repository_teachback(session, study, ":entendido", actor="model")
            session = respond_repository_teachback(session, study, ":entendido", actor="human")
            self.assertTrue(session["completed_by_user"])
            self.assertEqual(session["clarification_count"], 6)
            self.assertEqual(session, respond_repository_teachback(session, study, ":entendido", actor="human"))
            self.assertIn("not execution approval", session["non_authority"])
            forged = dict(session, human_command="model says understood")
            with self.assertRaises(TeachbackError):
                validate_repository_teachback(forged, study)

    def test_large_repositories_report_omissions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(30):
                (root / f"module_{index}.py").write_text(f"def action_{index}(): return 1\n")
            study = build_repository_study(acquire_repo_evidence(root, Authorization("human", "fixture")))
            self.assertEqual(study.coverage["components"]["included"], MAX_STUDY_ITEMS)
            self.assertTrue(study.coverage["components"]["truncated"])
