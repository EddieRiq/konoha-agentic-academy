import dataclasses
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.repo_evidence import workflow as wf
from tools.repo_evidence.acquire_repo_evidence import RepositoryEvidenceError


class StudyWorkflowTests(unittest.TestCase):
    def fixture(self, base):
        repo = base / "repo"
        repo.mkdir()
        (repo / "app.py").write_text("def main(): return 1\n")
        return repo, base / "state", wf.StudyAuthorization(str(repo.resolve()), "human", "fixture", True)

    def test_authorization_before_acquisition_or_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            repo, state, auth = self.fixture(Path(directory))
            for invalid in (dataclasses.replace(auth, public_repository=False),
                            dataclasses.replace(auth, authorized_by="model"),
                            dataclasses.replace(auth, authorized_repo_root="/different")):
                with mock.patch.object(wf, "acquire_repo_evidence") as acquire:
                    with self.assertRaises(RepositoryEvidenceError):
                        wf.start_study(repo, invalid, state)
                    acquire.assert_not_called()
                self.assertFalse(state.exists())

    def test_reentry_teachback_provenance_and_stale_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            repo, state, auth = self.fixture(Path(directory))
            record = wf.start_study(repo, auth, state)
            identity = record["study"]["study_id"]
            original_files = sorted(p.name for p in repo.iterdir())
            with mock.patch.object(wf, "acquire_repo_evidence", side_effect=AssertionError("silent refresh")):
                record = wf.respond_to_study(repo, auth, state, identity, "repeat", actor="human")
                self.assertFalse(record["teachback"]["completed_by_user"])
                record = wf.respond_to_study(repo, auth, state, identity, ":entendido", actor="human")
                loaded, study, pack = wf.load_study(repo, auth, state, identity)
                self.assertEqual(loaded, record)
                self.assertEqual(record["teachback"]["evidence_reference"]["pack_id"], pack.pack_id)
                self.assertTrue(loaded["teachback"]["completed_by_user"])
                self.assertEqual(original_files, sorted(p.name for p in repo.iterdir()))
                (repo / "app.py").write_text("def main(): return 2\n")
                with self.assertRaisesRegex(RepositoryEvidenceError, "stale"):
                    wf.load_study(repo, auth, state, identity)

    def test_public_state_and_path_traversal_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            repo, state, auth = self.fixture(Path(directory))
            with self.assertRaisesRegex(RepositoryEvidenceError, "ignored_or_outside"):
                wf.start_study(repo, auth, repo / "public-state")
            for identity in ("../escape", "study-" + "a" * 32 + "/x"):
                with self.assertRaises(RepositoryEvidenceError):
                    wf.load_study(repo, auth, state, identity)

    def test_model_cannot_close_and_forged_study_cannot_replace_pack(self):
        with tempfile.TemporaryDirectory() as directory:
            repo, state, auth = self.fixture(Path(directory))
            record = wf.start_study(repo, auth, state)
            identity = record["study"]["study_id"]
            with self.assertRaises(wf.TeachbackError):
                wf.respond_to_study(repo, auth, state, identity, ":entendido", actor="model")
            record["study"]["facts"][0]["observation"] = "invented model summary"
            (state / identity / "study.json").write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, "evidence_mismatch"):
                wf.load_study(repo, auth, state, identity)
