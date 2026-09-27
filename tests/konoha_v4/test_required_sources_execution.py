import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.konoha_v4 import executor as ex
from tools.konoha_v4.continuity import MissionContinuityStore
from test_execute_or_resume_plan import (_plan, _assignment, _write_plan, _approval_for,
                                         _patched_invoke)


class Registry:
    def agent_family(self, name):
        return {"required_sources": ["mission_plan", "user_mission_request", "acceptance_criteria"]}


class RequiredSourcesExecutionTests(unittest.TestCase):
    def test_request_symlink_fails_closed_without_reading_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = _plan([_assignment()])
            _write_plan(root, plan)
            target = root / "other.json"
            target.write_text(json.dumps({"schema_version": "1.0", "mission_id": plan.mission_id, "original_request": "unauthorized alias"}))
            (root / "missions" / plan.mission_id / "continuity.json").symlink_to(target)
            with mock.patch.object(ex, "invoke") as invoke:
                result = ex.execute_or_resume_plan(root, root, plan.mission_id, Registry())
            self.assertTrue(result.diagnostic.startswith("required_sources:user_mission_request:"))
            invoke.assert_not_called()

    def test_missing_request_resumable_without_readiness_git_or_invoke(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = _plan([_assignment()])
            _write_plan(root, plan)
            for raw in (None, "[]", "{", '{"mission_id":"wrong", "original_request":"invented"}'):
                path = root / "missions" / plan.mission_id / "continuity.json"
                if raw is not None:
                    path.write_text(raw)
                with mock.patch.object(ex, "_readiness_diagnostic") as ready, \
                     mock.patch.object(ex, "_git_status") as git, mock.patch.object(ex, "invoke") as invoke:
                    result = ex.execute_or_resume_plan(root, root, plan.mission_id, Registry())
                    self.assertEqual(result.diagnostic, "required_sources:user_mission_request:user_mission_request_empty")
                    self.assertEqual(result.state.status, "in_progress")
                    self.assertEqual(result.evidence, ())
                    ready.assert_not_called(); git.assert_not_called(); invoke.assert_not_called()
                self.assertFalse((path.parent / "execution_state.json").exists())
                self.assertFalse((path.parent / "evidence").exists())

    def test_exact_request_and_single_resolve_delivered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = _plan([_assignment()])
            _write_plan(root, plan)
            original = "  original request\nsecond line  "
            MissionContinuityStore.create(root, plan.mission_id, original, {})
            with mock.patch.object(ex, "resolve_all", wraps=ex.resolve_all) as resolve, \
                 mock.patch.object(ex, "_readiness_diagnostic", return_value=None), \
                 mock.patch.object(ex, "_git_status", return_value=""), _patched_invoke() as invoke:
                result = ex.execute_or_resume_plan(root, root, plan.mission_id, Registry())
            self.assertEqual(result.diagnostic, "completed")
            resolve.assert_called_once()
            self.assertTrue(resolve.call_args.kwargs["enforcing"])
            payload = json.loads(invoke.call_args.args[1])
            self.assertEqual(payload["resolved_source_bundle"]["user_mission_request"]["text"], original)
            self.assertNotIn("dependency_evidence", payload)

    def test_missing_source_does_not_consume_separate_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = _plan([_assignment(execution_gate="separate_human_approval")])
            _write_plan(root, plan)
            first = ex.execute_or_resume_plan(root, root, plan.mission_id, Registry())
            state_path = root / "missions" / plan.mission_id / "execution_state.json"
            before = state_path.read_bytes()
            command = ex.expected_approval_command(plan.mission_id, "t1", first.state.plan_identity, first.state.approval_nonce)
            approval = _approval_for(first.state, task_id="t1", approval_text=command)
            with mock.patch.object(ex, "invoke") as invoke:
                result = ex.execute_or_resume_plan(root, root, plan.mission_id, Registry(), approval)
            self.assertTrue(result.diagnostic.startswith("required_sources:"))
            self.assertEqual(before, state_path.read_bytes())
            invoke.assert_not_called()
            self.assertEqual(result.state.consumed_approval_ids, [])

    def test_legacy_cannot_bypass_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = _plan([_assignment()])
            with mock.patch.object(ex, "_git_status") as git, mock.patch.object(ex, "invoke") as invoke:
                with self.assertRaisesRegex(ex.RequiredSourcesError, "required_sources:user_mission_request"):
                    ex.execute_plan(root, plan, Registry(), root)
            git.assert_not_called(); invoke.assert_not_called()
            self.assertFalse((root / "missions").exists())
