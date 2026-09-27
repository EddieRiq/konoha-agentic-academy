import dataclasses
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.repo_evidence import workflow as wf
from tools.repo_evidence.acquire_repo_evidence import RepositoryEvidenceError
from tools.teachback.manage_teachback import TeachbackError
from tools.local_model_audit.manage_local_model_audit import partition_evidence_linked_suggestions


class RepositoryLearningTests(unittest.TestCase):
    def fixture(self, base, name):
        repo, state = base / name, base / (name + "-state")
        repo.mkdir()
        (repo / "app.py").write_text("def action(): return 1\n")
        (repo / "test_app.py").write_text("import app\ndef test_action(): assert app.action() == 1\n")
        (repo / "pyproject.toml").write_text('[project.scripts]\napp = "app:missing"\n')
        auth = wf.StudyAuthorization(str(repo.resolve()), "human", "synthetic public repository", True,
                                     "https://example.org/" + name)
        record = wf.start_study(repo, auth, state)
        return repo, auth, state, record["study"]["study_id"]

    def close(self, args):
        wf.respond_to_study(*args, ":entendido", actor="human")

    def test_self_improvement_remains_proposed_with_separated_suggestions(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self.fixture(Path(directory), "target")
            with self.assertRaises(TeachbackError):
                wf.recommend_study(*args)
            self.close(args)
            _, study, _ = wf.load_study(*args)
            ref = study.facts[0]["evidence_ref"]
            suggestions = [{"evidence_refs": [ref], "recommendation": "Review this component", "risk": "unknown runtime consumers",
                            "scope": "cited module only", "confidence": 1.0, "authorizes_action": True},
                           {"evidence_refs": ["invented"], "recommendation": "delete everything", "confidence": 1.0}]
            before = {p.name: p.read_bytes() for p in args[0].iterdir()}
            report = wf.recommend_study(*args, model_suggestions=suggestions)
            self.assertTrue(report["validated"])
            self.assertEqual(report["status"], "proposed")
            self.assertFalse(report["authorizes_action"])
            self.assertEqual(len(report["model_suggestions"]), 1)
            model = report["model_suggestions"][0]
            self.assertEqual(model["basis"], "model_suggestion")
            self.assertEqual(model["validation"], "locator_linkage_only_not_deterministic_truth")
            self.assertNotIn("confidence", model)
            self.assertFalse(model["authorizes_action"])
            self.assertEqual(len(report["suppressed"]), 1)
            self.assertEqual(before, {p.name: p.read_bytes() for p in args[0].iterdir()})
            for item in report["validated"]:
                self.assertTrue(item["risk"] and item["scope"])
                self.assertEqual(item["provenance"]["evidence_reference"], study.evidence_reference)

    def test_donor_learning_preserves_both_provenances_and_human_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            donor, target = self.fixture(base, "donor"), self.fixture(base, "konoha")
            with self.assertRaises(TeachbackError):
                wf.compare_studies(*donor, *target)
            self.close(donor)
            self.close(target)
            with mock.patch.object(wf, "acquire_repo_evidence", side_effect=AssertionError("refresh")):
                report = wf.compare_studies(*donor, *target)
            self.assertTrue(report["recommendations"])
            self.assertEqual(report["source_url"], "https://example.org/donor")
            self.assertIn("not_network_verified", report["origin_verification"])
            self.assertFalse(report["authorizes_action"])
            for item in report["recommendations"]:
                self.assertEqual(item["provenance"]["study_id"], donor[3])
                self.assertEqual(item["comparison_with_target"]["provenance"]["study_id"], target[3])
                self.assertIn("not permission", item["non_authority"])
                self.assertIn("License", item["compatibility_and_risk"])
            invalid = (donor[0], dataclasses.replace(donor[1], public_repository=False), *donor[2:])
            with mock.patch.object(wf, "load_study") as load:
                with self.assertRaises(RepositoryEvidenceError):
                    wf.compare_studies(*invalid, *target)
                load.assert_not_called()

    def test_model_suggestions_bounded_and_malformed_values_suppressed(self):
        for raw in (None, {}, "suggestion", [None, [], {}]):
            linked, suppressed = partition_evidence_linked_suggestions(raw, ["prov-1"])
            self.assertFalse(linked)
            self.assertTrue(suppressed)
        raw = [{"evidence_refs": ["prov-1"], "recommendation": "a" * 10000,
                "risk": "risk", "scope": "scope"}] * 30
        linked, suppressed = partition_evidence_linked_suggestions(raw, ["prov-1"])
        self.assertEqual(len(linked), 10)
        self.assertEqual(len(linked[0]["recommendation"]), 2000)
        self.assertEqual(suppressed[-1]["omitted"], 20)

    def test_changed_donor_requires_new_study_and_teachback(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            donor, target = self.fixture(base, "donor"), self.fixture(base, "konoha")
            self.close(donor); self.close(target)
            (donor[0] / "app.py").write_text("def action(): return 2\n")
            with mock.patch.object(wf, "acquire_repo_evidence", side_effect=AssertionError("refresh")):
                with self.assertRaisesRegex(RepositoryEvidenceError, "stale"):
                    wf.compare_studies(*donor, *target)
