import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.konoha_v4 import executor as ex
from tools.repo_evidence.acquire_repo_evidence import Authorization, acquire_repo_evidence, is_evidence_current
from tools.repo_evidence.persistence import evidence_reference, persist_evidence_pack
from test_execute_or_resume_plan import _plan, _assignment, _write_plan, _patched_invoke


class Registry:
    def agent_family(self, name):
        return {"required_sources": ["repository_state"]}


class ApprovedEvidenceTests(unittest.TestCase):
    def test_resume_after_completed_assignment_rechecks_same_pack(self):
        with tempfile.TemporaryDirectory() as directory:
            repo, state, plan, pack = self.setup_fixture(Path(directory))
            plan.assignments.append(_assignment(task_id="t2", dependencies=["t1"]))
            plan.seal()
            _write_plan(state, plan)
            with mock.patch.object(ex, "_readiness_diagnostic", return_value=None), \
                 mock.patch.object(ex, "_git_status", return_value=""), _patched_invoke() as invoke:
                first = ex.execute_or_resume_plan(repo, state, plan.mission_id, Registry())
            self.assertEqual(first.state.completed_task_ids, ["t1"])
            invoke.assert_called_once()
            state_path = state / "missions" / plan.mission_id / "execution_state.json"
            before = state_path.read_bytes()
            (repo / "app.py").write_text("def main(): return 99\n")
            with mock.patch.object(ex, "invoke") as invoke, \
                 mock.patch("tools.repo_evidence.acquire_repo_evidence.acquire_repo_evidence", side_effect=AssertionError("refresh")):
                resumed = ex.execute_or_resume_plan(repo, state, plan.mission_id, Registry())
            self.assertIn("repository_evidence_stale", resumed.diagnostic)
            self.assertEqual(resumed.state.completed_task_ids, ["t1"])
            self.assertEqual(resumed.state.next_assignment_index, 1)
            self.assertEqual(before, state_path.read_bytes())
            invoke.assert_not_called()

    def setup_fixture(self, base):
        repo, state = base / "repo", base / "state"
        repo.mkdir()
        (repo / "app.py").write_text("def main():\n    return 1\n")
        pack = acquire_repo_evidence(repo, Authorization("human", "fixture authorized"))
        plan = _plan([_assignment()], repository_evidence=evidence_reference(pack))
        _write_plan(state, plan)
        persist_evidence_pack(state / "missions" / plan.mission_id, pack)
        return repo, state, plan, pack

    def test_exact_pack_reused_after_reload_without_acquisition(self):
        with tempfile.TemporaryDirectory() as directory:
            repo, state, plan, pack = self.setup_fixture(Path(directory))
            with mock.patch("tools.repo_evidence.acquire_repo_evidence.acquire_repo_evidence", side_effect=AssertionError("refresh")), \
                 mock.patch.object(ex, "_readiness_diagnostic", return_value=None), \
                 mock.patch.object(ex, "_git_status", return_value=""), _patched_invoke() as invoke:
                result = ex.execute_or_resume_plan(repo, state, plan.mission_id, Registry())
            self.assertEqual(result.diagnostic, "completed")
            payload = json.loads(invoke.call_args.args[1])
            self.assertEqual(payload["resolved_source_bundle"]["repository_state"]["pack_id"], pack.pack_id)

    def test_stale_corrupt_missing_and_wrong_root_fail_without_refresh(self):
        for change in ("stale", "corrupt", "missing", "wrong_root"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                repo, state, plan, pack = self.setup_fixture(base)
                path = next((state / "missions" / plan.mission_id).glob("repository-evidence-*.json"))
                if change == "stale":
                    (repo / "app.py").write_text("def main():\n    return 2\n")
                elif change == "corrupt":
                    path.write_text(path.read_text().replace('"main"', '"fake"'))
                elif change == "missing":
                    path.unlink()
                else:
                    repo = base / "other"
                    repo.mkdir()
                    (repo / "app.py").write_text("def main():\n    return 1\n")
                with mock.patch.object(ex, "_readiness_diagnostic") as ready, \
                     mock.patch.object(ex, "_git_status") as git, mock.patch.object(ex, "invoke") as invoke, \
                     mock.patch("tools.repo_evidence.acquire_repo_evidence.acquire_repo_evidence", side_effect=AssertionError("refresh")):
                    result = ex.execute_or_resume_plan(repo, state, plan.mission_id, Registry())
                self.assertTrue(result.diagnostic.startswith("required_sources:repository_state:"), result)
                self.assertEqual(result.state.status, "in_progress")
                ready.assert_not_called(); git.assert_not_called(); invoke.assert_not_called()

    def test_reference_is_part_of_operative_plan_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            _, _, plan, _ = self.setup_fixture(Path(directory))
            before = ex.plan_identity(plan)
            plan.repository_evidence["sha256"] = "0" * 64
            self.assertNotEqual(before, ex.plan_identity(plan))

    def test_unbound_legacy_plan_cannot_acquire_required_repository_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = _plan([_assignment()])
            _write_plan(root, plan)
            with mock.patch.object(ex, "invoke") as invoke:
                result = ex.execute_or_resume_plan(root, root, plan.mission_id, Registry())
            self.assertEqual(result.diagnostic, "required_sources:repository_state:repository_evidence_not_acquired")
            invoke.assert_not_called()
