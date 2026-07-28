from __future__ import annotations

import dataclasses
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools.konoha_v4 import executor as executor_module
from tools.konoha_v4.executor import (
    ExecutionAttempt,
    ExecutionStateError,
    MissionLookupError,
    _MissionLock,
    _verify_completed_evidence,
    execute_or_resume_plan,
    expected_approval_command,
    load_persisted_plan,
    plan_identity,
)
from tools.konoha_v4.models import (
    EXECUTION_STATE_SCHEMA_VERSION,
    AgentAssignment,
    AssignmentApproval,
    EvidenceRecord,
    MissionPlan,
)
from tools.konoha_v4.registry import RegistryError


def _assignment(task_id="t1", execution_gate="plan_approval", **overrides):
    fields = dict(
        task_id=task_id,
        family="repository-auditor",
        provider="codex",
        model="codex",
        objective="Inspeccionar sin mutar.",
        inputs=["tools/konoha_v4"],
        expected_output="Evidencia verificable.",
        estimated_input_tokens=10,
        estimated_output_tokens=5,
        estimated_total_tokens=15,
        execution_gate=execution_gate,
    )
    fields.update(overrides)
    return AgentAssignment(**fields)


def _approval_dict(status):
    return {
        "status": status,
        "approved_by": "human" if status == "approved" else None,
        "approved_at": "2026-07-21T00:00:00Z" if status == "approved" else None,
        "feedback": None,
    }


def _plan(assignments, approval_status="approved", **overrides):
    fields = dict(
        mission_id="mission-resume-test",
        understanding="Validar el runtime resumible.",
        explicit_facts=[],
        missing_context=[],
        assumptions_prohibited=[],
        complexity="low",
        assignments=assignments,
        acceptance_criteria=["done"],
        approval_boundaries=["read_only", "mutation", "network", "private_context"],
        estimated_tokens=15 * len(assignments),
        estimated_cost_class="low",
        rationale="test",
        approval=_approval_dict(approval_status),
    )
    fields.update(overrides)
    return MissionPlan(**fields).seal()


def _write_plan(state_dir, plan):
    mission_dir = state_dir / "missions" / plan.mission_id
    mission_dir.mkdir(parents=True, exist_ok=True)
    (mission_dir / "plan.json").write_text(
        json.dumps(dataclasses.asdict(plan), ensure_ascii=False, indent=2), encoding="utf-8",
    )


def _execution_state_path(state_dir, mission_id):
    return state_dir / "missions" / mission_id / "execution_state.json"


def _write_execution_state_raw(state_dir, mission_id, **fields):
    base = dict(
        schema_version=EXECUTION_STATE_SCHEMA_VERSION,
        mission_id=mission_id,
        plan_identity="0" * 64,
        status="in_progress",
        next_assignment_index=0,
        completed_task_ids=[],
        pending_task_id=None,
        pending_execution_gate=None,
        approval_nonce=None,
        active_approval_id=None,
        consumed_approval_ids=[],
        evidence_ids_by_task={},
        executing_task_id=None,
        pause_reason=None,
        diagnostic=None,
        updated_at="2026-07-21T00:00:00Z",
    )
    base.update(fields)
    path = _execution_state_path(state_dir, mission_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")


def _evidence_dir(state_dir, mission_id):
    return state_dir / "missions" / mission_id / "evidence"


def _approval_for(state, **fields_overrides):
    """task_id and approval_text are mandatory, passed via
    fields_overrides like every other field - never as separate positional
    parameters - so a variant overriding either one can never collide with
    an explicit keyword argument of the same name at the call site."""
    required = {"task_id", "approval_text"}
    missing = required - fields_overrides.keys()
    if missing:
        raise ValueError(f"missing approval fields: {sorted(missing)}")

    fields = {
        "mission_id": state.mission_id,
        "execution_gate": "separate_human_approval",
        "plan_identity": state.plan_identity,
        "approval_nonce": state.approval_nonce,
        "approval_source": "interactive_terminal",
        "approved_at": "2026-07-21T00:05:00Z",
    }
    fields.update(fields_overrides)
    return AssignmentApproval(**fields)


class _Registry:
    def agent_family(self, family):
        return {"allowed_task_patterns": ["read-only inspection"]}


class _RegistryUnknownFamily:
    def agent_family(self, family):
        raise RegistryError(f"No existe la familia especializada: {family}")


_COMPLETED_RESULT_TEXT = json.dumps({
    "outcome": "completed",
    "objective_satisfied": True,
    "summary": "ok",
    "diagnostic": None,
    "evidence": [],
    "review_outcome": None,
})


def _patched_invoke():
    return mock.patch(
        "tools.konoha_v4.executor.invoke",
        return_value=SimpleNamespace(
            text=_COMPLETED_RESULT_TEXT, usage={"input": 1, "output": 1}, command=["echo"],
        ),
    )


def _patched_git_status():
    return mock.patch("tools.konoha_v4.executor._git_status", return_value="")


def _fail_after(n, real_fn):
    calls = {"count": 0}

    def _side_effect(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] <= n:
            return real_fn(*args, **kwargs)
        raise OSError("simulated persistence failure")

    return _side_effect


class LoadPersistedPlanTests(unittest.TestCase):
    def test_valid_plan_round_trips(self):
        plan = _plan([_assignment()])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            loaded = load_persisted_plan(state_dir, plan.mission_id)
            self.assertEqual(loaded, plan)

    def test_missing_plan_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with self.assertRaises(MissionLookupError):
                load_persisted_plan(state_dir, "mission-resume-test")

    def test_corrupt_json_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            mission_dir = state_dir / "missions" / "mission-resume-test"
            mission_dir.mkdir(parents=True)
            (mission_dir / "plan.json").write_text("{not json", encoding="utf-8")
            with self.assertRaises(MissionLookupError):
                load_persisted_plan(state_dir, "mission-resume-test")

    def test_non_object_json_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            mission_dir = state_dir / "missions" / "mission-resume-test"
            mission_dir.mkdir(parents=True)
            (mission_dir / "plan.json").write_text("[1, 2, 3]", encoding="utf-8")
            with self.assertRaises(MissionLookupError):
                load_persisted_plan(state_dir, "mission-resume-test")

    def test_missing_field_raises(self):
        plan = _plan([_assignment()])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            raw = dataclasses.asdict(plan)
            del raw["rationale"]
            mission_dir = state_dir / "missions" / plan.mission_id
            mission_dir.mkdir(parents=True)
            (mission_dir / "plan.json").write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(MissionLookupError):
                load_persisted_plan(state_dir, plan.mission_id)

    def test_extra_field_raises(self):
        plan = _plan([_assignment()])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            raw = dataclasses.asdict(plan)
            raw["unexpected_field"] = "x"
            mission_dir = state_dir / "missions" / plan.mission_id
            mission_dir.mkdir(parents=True)
            (mission_dir / "plan.json").write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(MissionLookupError):
                load_persisted_plan(state_dir, plan.mission_id)

    def test_assignments_not_a_list_raises(self):
        plan = _plan([_assignment()])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            raw = dataclasses.asdict(plan)
            raw["assignments"] = "not-a-list"
            mission_dir = state_dir / "missions" / plan.mission_id
            mission_dir.mkdir(parents=True)
            (mission_dir / "plan.json").write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(MissionLookupError):
                load_persisted_plan(state_dir, plan.mission_id)

    def test_assignment_with_incompatible_fields_raises(self):
        plan = _plan([_assignment()])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            raw = dataclasses.asdict(plan)
            raw["assignments"][0]["unexpected"] = "x"
            mission_dir = state_dir / "missions" / plan.mission_id
            mission_dir.mkdir(parents=True)
            (mission_dir / "plan.json").write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(MissionLookupError):
                load_persisted_plan(state_dir, plan.mission_id)

    def test_mission_id_mismatch_raises(self):
        plan = _plan([_assignment()])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            mission_dir = state_dir / "missions" / "mission-other"
            mission_dir.mkdir(parents=True)
            (mission_dir / "plan.json").write_text(
                json.dumps(dataclasses.asdict(plan)), encoding="utf-8",
            )
            with self.assertRaises(MissionLookupError):
                load_persisted_plan(state_dir, "mission-other")


class VerifyCompletedEvidenceTests(unittest.TestCase):
    def test_no_completed_tasks_is_trivially_valid(self):
        plan = _plan([_assignment()])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            state = SimpleNamespace(completed_task_ids=[], evidence_ids_by_task={})
            diagnostic, records = _verify_completed_evidence(state_dir, plan, state)
            self.assertIsNone(diagnostic)
            self.assertEqual(records, [])

    def _completed_state_with_real_evidence(self, state_dir, plan, task):
        record = EvidenceRecord.build(
            mission_id=plan.mission_id, task_id=task.task_id, provider=task.provider,
            model=task.model, status="completed", output="evidencia real",
            token_usage={}, command=[], started_at=0.0, finished_at=1.0,
        )
        out = _evidence_dir(state_dir, plan.mission_id)
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{record.evidence_id}.json").write_text(
            json.dumps(dataclasses.asdict(record), ensure_ascii=False, indent=2), encoding="utf-8",
        )
        state = SimpleNamespace(
            completed_task_ids=[task.task_id],
            evidence_ids_by_task={task.task_id: record.evidence_id},
        )
        return state, record

    def test_valid_evidence_passes(self):
        task = _assignment()
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            state, record = self._completed_state_with_real_evidence(state_dir, plan, task)
            diagnostic, records = _verify_completed_evidence(state_dir, plan, state)
            self.assertIsNone(diagnostic)
            self.assertEqual(records, [record])

    def test_missing_evidence_file_fails(self):
        task = _assignment()
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            state = SimpleNamespace(
                completed_task_ids=[task.task_id],
                evidence_ids_by_task={task.task_id: "evidence-000000000000"},
            )
            diagnostic, records = _verify_completed_evidence(state_dir, plan, state)
            self.assertEqual(diagnostic, "missing_or_corrupt_completed_evidence")
            self.assertEqual(records, [])

    def test_corrupt_json_fails(self):
        task = _assignment()
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            out = _evidence_dir(state_dir, plan.mission_id)
            out.mkdir(parents=True, exist_ok=True)
            (out / "evidence-000000000000.json").write_text("{not json", encoding="utf-8")
            state = SimpleNamespace(
                completed_task_ids=[task.task_id],
                evidence_ids_by_task={task.task_id: "evidence-000000000000"},
            )
            diagnostic, records = _verify_completed_evidence(state_dir, plan, state)
            self.assertEqual(diagnostic, "missing_or_corrupt_completed_evidence")

    def test_hash_mismatch_fails(self):
        task = _assignment()
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            state, record = self._completed_state_with_real_evidence(state_dir, plan, task)
            path = _evidence_dir(state_dir, plan.mission_id) / f"{record.evidence_id}.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["output"] = "output alterado sin recalcular el hash"
            path.write_text(json.dumps(payload), encoding="utf-8")
            diagnostic, records = _verify_completed_evidence(state_dir, plan, state)
            self.assertEqual(diagnostic, "missing_or_corrupt_completed_evidence")

    def test_wrong_status_fails(self):
        task = _assignment()
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            record = EvidenceRecord.build(
                mission_id=plan.mission_id, task_id=task.task_id, provider=task.provider,
                model=task.model, status="failed", output="no completado",
                token_usage={}, command=[], started_at=0.0, finished_at=1.0,
            )
            out = _evidence_dir(state_dir, plan.mission_id)
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{record.evidence_id}.json").write_text(
                json.dumps(dataclasses.asdict(record)), encoding="utf-8",
            )
            state = SimpleNamespace(
                completed_task_ids=[task.task_id],
                evidence_ids_by_task={task.task_id: record.evidence_id},
            )
            diagnostic, records = _verify_completed_evidence(state_dir, plan, state)
            self.assertEqual(diagnostic, "missing_or_corrupt_completed_evidence")

    def test_mission_id_mismatch_fails(self):
        task = _assignment()
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            state, record = self._completed_state_with_real_evidence(state_dir, plan, task)
            path = _evidence_dir(state_dir, plan.mission_id) / f"{record.evidence_id}.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["mission_id"] = "mission-other"
            path.write_text(json.dumps(payload), encoding="utf-8")
            diagnostic, records = _verify_completed_evidence(state_dir, plan, state)
            self.assertEqual(diagnostic, "missing_or_corrupt_completed_evidence")

    def test_evidence_id_path_traversal_rejected(self):
        task = _assignment()
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            state = SimpleNamespace(
                completed_task_ids=[task.task_id],
                evidence_ids_by_task={task.task_id: "../../../etc/passwd"},
            )
            diagnostic, records = _verify_completed_evidence(state_dir, plan, state)
            self.assertEqual(diagnostic, "missing_or_corrupt_completed_evidence")


class ExecuteOrResumePlanGateTests(unittest.TestCase):
    def test_plan_approval_approved_executes(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task], approval_status="approved")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke() as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.diagnostic, "completed")
            self.assertEqual(attempt.state.status, "completed")

    def test_plan_approval_pending_never_mutates_or_invokes(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task], approval_status="pending")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke() as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_not_called()
            self.assertEqual(attempt.diagnostic, "plan_approval_not_satisfied")
            self.assertEqual(attempt.state.status, "in_progress")
            self.assertFalse(_execution_state_path(state_dir, plan.mission_id).exists())

            plan.approval["status"] = "approved"
            _write_plan(state_dir, plan)
            with _patched_invoke() as invoke_mock2, _patched_git_status():
                attempt2 = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock2.assert_called_once()
            self.assertEqual(attempt2.state.status, "completed")

    def test_separate_human_approval_first_call_waits(self):
        task = _assignment(task_id="t1", execution_gate="separate_human_approval")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke() as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_not_called()
            self.assertEqual(attempt.diagnostic, "waiting_for_approval")
            self.assertEqual(attempt.state.status, "waiting_for_approval")
            self.assertIsNotNone(attempt.state.approval_nonce)

    def test_separate_human_approval_valid_executes(self):
        task = _assignment(task_id="t1", execution_gate="separate_human_approval")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(), _patched_git_status():
                waiting = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            state = waiting.state
            text = expected_approval_command(
                plan.mission_id, state.pending_task_id, state.plan_identity, state.approval_nonce,
            )
            approval = _approval_for(state, task_id="t1", approval_text=text)
            with _patched_invoke() as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(
                    Path("."), state_dir, plan.mission_id, _Registry(), approval=approval,
                )
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.state.status, "completed")

    def test_separate_human_approval_invalid_reasons_never_mutate_or_invoke(self):
        task = _assignment(task_id="t1", execution_gate="separate_human_approval")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(), _patched_git_status():
                waiting = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            state = waiting.state
            good_text = expected_approval_command(
                plan.mission_id, state.pending_task_id, state.plan_identity, state.approval_nonce,
            )

            variants = {
                "nonce_mismatch": dict(approval_nonce="0" * 32),
                "unexpected_command_text": dict(approval_text=good_text + " "),
                "task_id_mismatch": dict(task_id="t-other"),
                "mission_id_mismatch": dict(mission_id="mission-other"),
                "gate_mismatch": dict(execution_gate="plan_approval"),
                "plan_identity_mismatch": dict(plan_identity="1" * 64),
                "approval_source_mismatch": dict(approval_source="slack_bot"),
                "approval_missing_fields": dict(approval_text="   "),
            }
            for expected_reason, override in variants.items():
                with self.subTest(reason=expected_reason):
                    approval_fields = {"task_id": "t1", "approval_text": good_text}
                    approval_fields.update(override)
                    bad = _approval_for(state, **approval_fields)
                    with _patched_invoke() as invoke_mock, _patched_git_status():
                        attempt = execute_or_resume_plan(
                            Path("."), state_dir, plan.mission_id, _Registry(), approval=bad,
                        )
                    invoke_mock.assert_not_called()
                    self.assertEqual(attempt.diagnostic, expected_reason)
                    self.assertEqual(attempt.state.status, "waiting_for_approval")
                    self.assertEqual(attempt.state.approval_nonce, state.approval_nonce)

    def test_replay_after_consumption_never_invokes_twice(self):
        task = _assignment(task_id="t1", execution_gate="separate_human_approval")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(), _patched_git_status():
                waiting = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            state = waiting.state
            text = expected_approval_command(
                plan.mission_id, state.pending_task_id, state.plan_identity, state.approval_nonce,
            )
            approval = _approval_for(state, task_id="t1", approval_text=text)
            with _patched_invoke() as invoke_mock, _patched_git_status():
                execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry(), approval=approval)
            invoke_mock.assert_called_once()

            with _patched_invoke() as invoke_mock2, _patched_git_status():
                attempt = execute_or_resume_plan(
                    Path("."), state_dir, plan.mission_id, _Registry(), approval=approval,
                )
            invoke_mock2.assert_not_called()
            self.assertTrue(attempt.diagnostic.startswith("non_resumable_status:"))


class ExecuteOrResumePlanEarlyExitTests(unittest.TestCase):
    def test_unsafe_mission_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with _patched_invoke() as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, "../escape", _Registry())
            invoke_mock.assert_not_called()
            self.assertIsNone(attempt.state)
            self.assertEqual(attempt.diagnostic, "unsafe_mission_id")

    def test_lock_busy(self):
        plan = _plan([_assignment()])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            holder = _MissionLock(state_dir, plan.mission_id)
            self.assertTrue(holder.acquire())
            try:
                with _patched_invoke() as invoke_mock, _patched_git_status():
                    attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
                invoke_mock.assert_not_called()
                self.assertIsNone(attempt.state)
                self.assertEqual(attempt.diagnostic, "lock_busy")
            finally:
                holder.release()

    def test_plan_load_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with _patched_invoke() as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, "mission-resume-test", _Registry())
            invoke_mock.assert_not_called()
            self.assertIsNone(attempt.state)
            self.assertEqual(attempt.diagnostic, "plan_load_error")

    def test_state_load_error(self):
        plan = _plan([_assignment()])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            _write_execution_state_raw(state_dir, plan.mission_id, schema_version="0.9")
            with _patched_invoke() as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_not_called()
            self.assertIsNone(attempt.state)
            self.assertEqual(attempt.diagnostic, "state_load_error")

    def test_empty_plan_assignments(self):
        plan = _plan([])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke() as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_not_called()
            self.assertIsNone(attempt.state)
            self.assertEqual(attempt.diagnostic, "empty_plan_assignments")


class ExecuteOrResumePlanRecoveryTests(unittest.TestCase):
    def test_executing_inherited_becomes_recovery_required_without_invoke(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            _write_execution_state_raw(
                state_dir, plan.mission_id,
                plan_identity=plan_identity(plan),
                status="executing",
                pending_task_id="t1", pending_execution_gate="plan_approval",
                executing_task_id="t1",
            )
            with _patched_invoke() as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_not_called()
            self.assertEqual(attempt.state.status, "recovery_required")
            self.assertEqual(attempt.diagnostic, "interrupted_while_executing")

    def test_corrupt_evidence_becomes_recovery_required_without_invoke(self):
        t1 = _assignment(task_id="t1", execution_gate="plan_approval")
        t2 = _assignment(task_id="t2", execution_gate="plan_approval")
        plan = _plan([t1, t2])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke() as invoke_mock, _patched_git_status():
                first = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(first.state.status, "in_progress")

            evidence_id = first.state.evidence_ids_by_task["t1"]
            path = _evidence_dir(state_dir, plan.mission_id) / f"{evidence_id}.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["output"] = "manipulado"
            path.write_text(json.dumps(payload), encoding="utf-8")

            with _patched_invoke() as invoke_mock2, _patched_git_status():
                second = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock2.assert_not_called()
            self.assertEqual(second.state.status, "recovery_required")
            self.assertEqual(second.diagnostic, "missing_or_corrupt_completed_evidence")

    def test_plan_drift_becomes_recovery_required_without_invoke(self):
        t1 = _assignment(task_id="t1", execution_gate="plan_approval")
        t2 = _assignment(task_id="t2", execution_gate="plan_approval")
        plan = _plan([t1, t2])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke() as invoke_mock, _patched_git_status():
                execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()

            drifted = _plan([t1, t2], understanding="Entendimiento modificado tras el pause.")
            _write_plan(state_dir, drifted)

            with _patched_invoke() as invoke_mock2, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock2.assert_not_called()
            self.assertEqual(attempt.state.status, "recovery_required")
            self.assertEqual(attempt.diagnostic, "plan_drift")

    def test_cursor_exhausted_without_completed_status(self):
        t1 = _assignment(task_id="t1", execution_gate="plan_approval")
        t2 = _assignment(task_id="t2", execution_gate="plan_approval")
        plan = _plan([t1, t2])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(), _patched_git_status():
                execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            with _patched_invoke() as invoke_mock, _patched_git_status():
                completed = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(completed.state.status, "completed")

            path = _execution_state_path(state_dir, plan.mission_id)
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw["status"] = "in_progress"
            path.write_text(json.dumps(raw), encoding="utf-8")

            with _patched_invoke() as invoke_mock2, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock2.assert_not_called()
            self.assertEqual(attempt.state.status, "recovery_required")
            self.assertEqual(attempt.diagnostic, "cursor_exhausted_without_completed_status")


class ExecuteOrResumePlanNonResumableTests(unittest.TestCase):
    def test_terminal_statuses_are_never_touched(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task])
        cases = (
            ("completed", dict(next_assignment_index=1, completed_task_ids=["t1"])),
            ("failed", dict(pending_task_id="t1", pending_execution_gate="plan_approval", diagnostic="boom")),
            ("blocked", dict(pending_task_id="t1", pending_execution_gate="plan_approval", pause_reason="x")),
            ("recovery_required", dict(diagnostic="x")),
        )
        for status, extra in cases:
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory() as tmp:
                    state_dir = Path(tmp)
                    _write_plan(state_dir, plan)
                    _write_execution_state_raw(
                        state_dir, plan.mission_id, plan_identity=plan_identity(plan),
                        status=status, **extra,
                    )
                    with _patched_invoke() as invoke_mock, _patched_git_status():
                        attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
                    invoke_mock.assert_not_called()
                    self.assertEqual(attempt.state.status, status)
                    self.assertEqual(attempt.diagnostic, f"non_resumable_status:{status}")


class ExecuteOrResumePlanPersistenceFailureTests(unittest.TestCase):
    def test_waiting_persist_failed(self):
        task = _assignment(task_id="t1", execution_gate="separate_human_approval")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with mock.patch.object(executor_module, "_save_execution_state", side_effect=OSError("full")):
                with _patched_invoke() as invoke_mock, _patched_git_status():
                    attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_not_called()
            self.assertEqual(attempt.diagnostic, "waiting_persist_failed")
            self.assertFalse(_execution_state_path(state_dir, plan.mission_id).exists())

    def test_executing_persist_failed_plan_approval(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with mock.patch.object(executor_module, "_save_execution_state", side_effect=OSError("full")):
                with _patched_invoke() as invoke_mock, _patched_git_status():
                    attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_not_called()
            self.assertEqual(attempt.diagnostic, "executing_persist_failed")

    def test_executing_persist_failed_separate_human_approval(self):
        task = _assignment(task_id="t1", execution_gate="separate_human_approval")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(), _patched_git_status():
                waiting = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            state = waiting.state
            text = expected_approval_command(
                plan.mission_id, state.pending_task_id, state.plan_identity, state.approval_nonce,
            )
            approval = _approval_for(state, task_id="t1", approval_text=text)
            with mock.patch.object(executor_module, "_save_execution_state", side_effect=OSError("full")):
                with _patched_invoke() as invoke_mock, _patched_git_status():
                    attempt = execute_or_resume_plan(
                        Path("."), state_dir, plan.mission_id, _Registry(), approval=approval,
                    )
            invoke_mock.assert_not_called()
            self.assertEqual(attempt.diagnostic, "executing_persist_failed")

    def test_evidence_persist_failed_then_next_call_sees_interrupted(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with mock.patch.object(executor_module, "_persist", side_effect=OSError("full")):
                with _patched_invoke() as invoke_mock, _patched_git_status():
                    attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.diagnostic, "evidence_persist_failed")

            raw = json.loads(_execution_state_path(state_dir, plan.mission_id).read_text(encoding="utf-8"))
            self.assertEqual(raw["status"], "executing")

            with _patched_invoke() as invoke_mock2, _patched_git_status():
                follow_up = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock2.assert_not_called()
            self.assertEqual(follow_up.diagnostic, "interrupted_while_executing")

    def test_final_transition_persist_failed_then_next_call_sees_interrupted(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task])
        real_save = executor_module._save_execution_state
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with mock.patch.object(
                executor_module, "_save_execution_state", side_effect=_fail_after(1, real_save),
            ):
                with _patched_invoke() as invoke_mock, _patched_git_status():
                    attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.diagnostic, "final_transition_persist_failed")
            self.assertEqual(len(attempt.evidence), 1)

            evidence_dir = _evidence_dir(state_dir, plan.mission_id)
            self.assertEqual(len(list(evidence_dir.glob("*.json"))), 1)

            with _patched_invoke() as invoke_mock2, _patched_git_status():
                follow_up = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock2.assert_not_called()
            self.assertEqual(follow_up.diagnostic, "interrupted_while_executing")

    def test_recovery_persist_failed(self):
        t1 = _assignment(task_id="t1", execution_gate="plan_approval")
        t2 = _assignment(task_id="t2", execution_gate="plan_approval")
        plan = _plan([t1, t2])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke() as invoke_mock, _patched_git_status():
                execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()

            drifted = _plan([t1, t2], understanding="Entendimiento modificado.")
            _write_plan(state_dir, drifted)

            with mock.patch.object(executor_module, "_save_execution_state", side_effect=OSError("full")):
                with _patched_invoke() as invoke_mock2, _patched_git_status():
                    attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock2.assert_not_called()
            self.assertEqual(attempt.diagnostic, "recovery_persist_failed")

    def test_failed_before_execution_persist_failed(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval", family="ghost-family")
        plan = _plan([task])
        real_save = executor_module._save_execution_state
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            # registry.agent_family is now consulted BEFORE "executing" is
            # ever persisted (Git baseline capture and family resolution
            # both happen ahead of that persist), so the
            # failed_before_execution transition is the FIRST save attempt
            # for this scenario, not the second - it must fail immediately.
            with mock.patch.object(
                executor_module, "_save_execution_state", side_effect=_fail_after(0, real_save),
            ):
                with _patched_invoke() as invoke_mock, _patched_git_status():
                    attempt = execute_or_resume_plan(
                        Path("."), state_dir, plan.mission_id, _RegistryUnknownFamily(),
                    )
            invoke_mock.assert_not_called()
            self.assertEqual(attempt.diagnostic, "failed_before_execution_persist_failed")


class ExecuteOrResumePlanLockTests(unittest.TestCase):
    def test_release_success_returns_attempt_unchanged(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(), _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            self.assertEqual(attempt.diagnostic, "completed")
            self.assertFalse(_MissionLock(state_dir, plan.mission_id)._path.exists())

    def test_release_failure_after_normal_return_yields_lock_release_error(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with mock.patch.object(_MissionLock, "release", side_effect=ExecutionStateError("stuck")):
                with _patched_invoke() as invoke_mock, _patched_git_status():
                    attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.diagnostic, "lock_release_error")
            self.assertEqual(attempt.state.status, "completed")
            self.assertEqual(len(attempt.evidence), 1)

    def test_release_failure_after_early_exit_preserves_state_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch.object(_MissionLock, "release", side_effect=ExecutionStateError("stuck")):
                with _patched_invoke() as invoke_mock, _patched_git_status():
                    attempt = execute_or_resume_plan(
                        Path("."), state_dir, "mission-resume-test", _Registry(),
                    )
            invoke_mock.assert_not_called()
            self.assertIsNone(attempt.state)
            self.assertEqual(attempt.diagnostic, "lock_release_error")

    def test_unexpected_exception_still_releases_lock_and_propagates(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with mock.patch.object(executor_module, "_git_status", side_effect=RuntimeError("unexpected bug")):
                with _patched_invoke() as invoke_mock:
                    with self.assertRaises(RuntimeError):
                        execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_not_called()

            with _patched_invoke() as invoke_mock2, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            self.assertNotEqual(attempt.diagnostic, "lock_busy")

    def test_unexpected_exception_and_release_failure_both_observable(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with mock.patch.object(executor_module, "_git_status", side_effect=RuntimeError("unexpected bug")):
                with mock.patch.object(_MissionLock, "release", side_effect=ExecutionStateError("stuck")):
                    with _patched_invoke() as invoke_mock:
                        with self.assertRaises(RuntimeError) as cm:
                            execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_not_called()
            self.assertIsInstance(cm.exception.__cause__, ExecutionStateError)


if __name__ == "__main__":
    unittest.main()
