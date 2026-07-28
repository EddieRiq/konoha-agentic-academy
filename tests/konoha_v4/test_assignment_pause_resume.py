from __future__ import annotations

import copy
import dataclasses
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.konoha_v4.executor import (
    ExecutionAttempt,
    ExecutionStateError,
    MissionLookupError,
    _MissionLock,
    _approval_id,
    _new_execution_state,
    _recovery_result,
    _state_with_timestamp,
    _transition_after_blocked_assignment,
    _transition_after_completed_assignment,
    _transition_after_failed_assignment,
    _transition_to_blocked,
    _transition_to_executing,
    _transition_to_failed_before_execution,
    _transition_to_waiting,
    _validate_assignment_approval,
    _validate_execution_state_invariants,
    expected_approval_command,
    plan_identity,
)
from tools.konoha_v4.models import (
    EXECUTION_STATE_SCHEMA_VERSION,
    AgentAssignment,
    AssignmentApproval,
    EvidenceRecord,
    ExecutionState,
    MissionPlan,
)


def _assignment(task_id: str = "t1", execution_gate: str = "separate_human_approval", **overrides) -> AgentAssignment:
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


def _plan(assignments: list[AgentAssignment]) -> MissionPlan:
    return MissionPlan(
        mission_id="mission-pause-resume-test",
        understanding="Validar aprobación de assignment.",
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
    )


def _state(plan: MissionPlan, task: AgentAssignment, nonce: str = "nonce-1", **overrides) -> ExecutionState:
    fields = dict(
        schema_version="1.0",
        mission_id=plan.mission_id,
        plan_identity=plan_identity(plan),
        status="waiting_for_approval",
        next_assignment_index=0,
        pending_task_id=task.task_id,
        pending_execution_gate="separate_human_approval",
        approval_nonce=nonce,
        updated_at="2026-07-21T00:00:00Z",
    )
    fields.update(overrides)
    return ExecutionState(**fields)


def _approval(plan: MissionPlan, task: AgentAssignment, state: ExecutionState, **overrides) -> AssignmentApproval:
    fields = dict(
        mission_id=plan.mission_id,
        task_id=task.task_id,
        execution_gate="separate_human_approval",
        plan_identity=plan_identity(plan),
        approval_nonce=state.approval_nonce,
        approval_text=expected_approval_command(
            plan.mission_id, task.task_id, plan_identity(plan), state.approval_nonce,
        ),
        approval_source="interactive_terminal",
        approved_at="2026-07-21T00:05:00Z",
    )
    fields.update(overrides)
    return AssignmentApproval(**fields)


class AssignmentApprovalValidationTests(unittest.TestCase):
    def _fixture(self):
        task = _assignment()
        plan = _plan([task])
        state = _state(plan, task)
        approval = _approval(plan, task, state)
        return plan, state, task, approval

    def test_valid_approval_passes(self):
        plan, state, task, approval = self._fixture()
        valid, approval_id, reason = _validate_assignment_approval(approval, plan, state, task)
        self.assertTrue(valid)
        self.assertIsNotNone(approval_id)
        self.assertIsNone(reason)

    def test_approval_id_stable_across_approved_at(self):
        plan, state, task, approval = self._fixture()
        other = _approval(plan, task, state, approved_at="2099-01-01T00:00:00Z")
        self.assertEqual(_approval_id(approval), _approval_id(other))

    def test_approval_id_changes_with_any_authoritative_field(self):
        plan, state, task, approval = self._fixture()
        base_id = _approval_id(approval)
        variants = {
            "mission_id": "mission-other",
            "task_id": "t-other",
            "execution_gate": "plan_approval",
            "plan_identity": "0" * 64,
            "approval_nonce": "nonce-other",
            "approval_text": approval.approval_text + " ",
            "approval_source": "other_source",
        }
        for field_name, value in variants.items():
            with self.subTest(field=field_name):
                other = _approval(plan, task, state, **{field_name: value})
                self.assertNotEqual(_approval_id(other), base_id)

    def test_no_approval_provided(self):
        plan, state, task, _ = self._fixture()
        valid, approval_id, reason = _validate_assignment_approval(None, plan, state, task)
        self.assertFalse(valid)
        self.assertIsNone(approval_id)
        self.assertEqual(reason, "no_approval_provided")

    def test_each_field_whitespace_only(self):
        plan, state, task, approval = self._fixture()
        for field_name in (
            "mission_id", "task_id", "execution_gate", "plan_identity",
            "approval_nonce", "approval_text", "approval_source", "approved_at",
        ):
            with self.subTest(field=field_name):
                bad = _approval(plan, task, state, **{field_name: "   "})
                valid, approval_id, reason = _validate_assignment_approval(bad, plan, state, task)
                self.assertFalse(valid)
                self.assertIsNone(approval_id)
                self.assertEqual(reason, "approval_missing_fields")

    def test_unknown_source(self):
        plan, state, task, approval = self._fixture()
        bad = _approval(plan, task, state, approval_source="slack_bot")
        valid, approval_id, reason = _validate_assignment_approval(bad, plan, state, task)
        self.assertFalse(valid)
        self.assertIsNone(approval_id)
        self.assertEqual(reason, "approval_source_mismatch")

    def test_wrong_mission_in_approval(self):
        plan, state, task, approval = self._fixture()
        bad = _approval(plan, task, state, mission_id="mission-other")
        valid, approval_id, reason = _validate_assignment_approval(bad, plan, state, task)
        self.assertFalse(valid)
        self.assertIsNone(approval_id)
        self.assertEqual(reason, "mission_id_mismatch")

    def test_wrong_mission_in_state(self):
        plan, state, task, approval = self._fixture()
        bad_state = _state(plan, task, mission_id="mission-other")
        valid, approval_id, reason = _validate_assignment_approval(approval, plan, bad_state, task)
        self.assertFalse(valid)
        self.assertIsNone(approval_id)
        self.assertEqual(reason, "mission_id_mismatch")

    def test_wrong_task_id(self):
        plan, state, task, approval = self._fixture()
        bad = _approval(plan, task, state, task_id="t-other")
        valid, approval_id, reason = _validate_assignment_approval(bad, plan, state, task)
        self.assertFalse(valid)
        self.assertIsNone(approval_id)
        self.assertEqual(reason, "task_id_mismatch")

    def test_wrong_pending_task(self):
        plan, state, task, approval = self._fixture()
        bad_state = _state(plan, task, pending_task_id="t-other")
        valid, approval_id, reason = _validate_assignment_approval(approval, plan, bad_state, task)
        self.assertFalse(valid)
        self.assertIsNone(approval_id)
        self.assertEqual(reason, "task_id_mismatch")

    def test_status_not_waiting(self):
        plan, state, task, approval = self._fixture()
        bad_state = _state(plan, task, status="in_progress")
        valid, approval_id, reason = _validate_assignment_approval(approval, plan, bad_state, task)
        self.assertFalse(valid)
        self.assertIsNone(approval_id)
        self.assertEqual(reason, "no_pending_approval")

    def test_wrong_gate_on_approval(self):
        plan, state, task, approval = self._fixture()
        bad = _approval(plan, task, state, execution_gate="plan_approval")
        valid, approval_id, reason = _validate_assignment_approval(bad, plan, state, task)
        self.assertFalse(valid)
        self.assertIsNone(approval_id)
        self.assertEqual(reason, "gate_mismatch")

    def test_wrong_real_task_gate(self):
        plan, state, task, approval = self._fixture()
        other_task = _assignment(execution_gate="plan_approval")
        valid, approval_id, reason = _validate_assignment_approval(approval, plan, state, other_task)
        self.assertFalse(valid)
        self.assertIsNone(approval_id)
        self.assertEqual(reason, "gate_mismatch")

    def test_wrong_pending_gate(self):
        plan, state, task, approval = self._fixture()
        bad_state = _state(plan, task, pending_execution_gate="plan_approval")
        valid, approval_id, reason = _validate_assignment_approval(approval, plan, bad_state, task)
        self.assertFalse(valid)
        self.assertIsNone(approval_id)
        self.assertEqual(reason, "gate_mismatch")

    def test_wrong_identity_in_approval(self):
        plan, state, task, approval = self._fixture()
        bad = _approval(plan, task, state, plan_identity="0" * 64)
        valid, approval_id, reason = _validate_assignment_approval(bad, plan, state, task)
        self.assertFalse(valid)
        self.assertIsNone(approval_id)
        self.assertEqual(reason, "plan_identity_mismatch")

    def test_wrong_identity_in_state(self):
        plan, state, task, approval = self._fixture()
        bad_state = _state(plan, task, plan_identity="0" * 64)
        valid, approval_id, reason = _validate_assignment_approval(approval, plan, bad_state, task)
        self.assertFalse(valid)
        self.assertIsNone(approval_id)
        self.assertEqual(reason, "plan_identity_mismatch")

    def test_wrong_nonce(self):
        plan, state, task, approval = self._fixture()
        bad = _approval(plan, task, state, approval_nonce="nonce-wrong")
        valid, approval_id, reason = _validate_assignment_approval(bad, plan, state, task)
        self.assertFalse(valid)
        self.assertIsNone(approval_id)
        self.assertEqual(reason, "nonce_mismatch")

    def test_approximate_text_rejected(self):
        plan, state, task, approval = self._fixture()
        bad = _approval(plan, task, state, approval_text=approval.approval_text + " ")
        valid, approval_id, reason = _validate_assignment_approval(bad, plan, state, task)
        self.assertFalse(valid)
        self.assertIsNone(approval_id)
        self.assertEqual(reason, "unexpected_command_text")

    def test_expected_approval_command_format(self):
        text = expected_approval_command("mission-x", "t1", "abc123", "nonce-1")
        self.assertEqual(
            text,
            ":aprobar-assignment mission-x t1 separate_human_approval abc123 nonce-1",
        )

    def test_replay_already_consumed(self):
        plan, state, task, approval = self._fixture()
        consumed_id = _approval_id(approval)
        state_with_replay = _state(
            plan, task, consumed_approval_ids=[consumed_id],
        )
        valid, approval_id, reason = _validate_assignment_approval(approval, plan, state_with_replay, task)
        self.assertFalse(valid)
        self.assertEqual(approval_id, consumed_id)
        self.assertEqual(reason, "approval_already_consumed")

    def test_state_unchanged_before_and_after(self):
        plan, state, task, approval = self._fixture()
        before = copy.deepcopy(state)
        _validate_assignment_approval(approval, plan, state, task)
        self.assertEqual(state, before)

        bad = _approval(plan, task, state, approval_nonce="nonce-wrong")
        before_invalid = copy.deepcopy(state)
        _validate_assignment_approval(bad, plan, state, task)
        self.assertEqual(state, before_invalid)


class ExecutionStateInvariantTests(unittest.TestCase):
    def _plan_one(self, gate: str = "separate_human_approval") -> MissionPlan:
        return _plan([_assignment(task_id="t1", execution_gate=gate)])

    def _plan_two(
        self, gate1: str = "separate_human_approval", gate2: str = "plan_approval",
    ) -> MissionPlan:
        return _plan([
            _assignment(task_id="t1", execution_gate=gate1),
            _assignment(task_id="t2", execution_gate=gate2),
        ])

    def _es(self, plan: MissionPlan, **overrides) -> ExecutionState:
        fields = dict(
            schema_version="1.0",
            mission_id=plan.mission_id,
            plan_identity=plan_identity(plan),
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
        fields.update(overrides)
        return ExecutionState(**fields)

    def test_valid_in_progress(self):
        plan = self._plan_one()
        state = self._es(plan, status="in_progress")
        self.assertIsNone(_validate_execution_state_invariants(plan, state))

    def test_valid_waiting_for_approval(self):
        plan = self._plan_one(gate="separate_human_approval")
        state = self._es(
            plan,
            status="waiting_for_approval",
            pending_task_id="t1",
            pending_execution_gate="separate_human_approval",
            approval_nonce="a" * 32,
            pause_reason="esperando aprobación",
        )
        self.assertIsNone(_validate_execution_state_invariants(plan, state))

    def test_valid_executing_plan_approval(self):
        plan = self._plan_one(gate="plan_approval")
        state = self._es(
            plan,
            status="executing",
            pending_task_id="t1",
            pending_execution_gate="plan_approval",
            executing_task_id="t1",
        )
        self.assertIsNone(_validate_execution_state_invariants(plan, state))

    def test_valid_executing_separate_human_approval(self):
        plan = self._plan_one(gate="separate_human_approval")
        state = self._es(
            plan,
            status="executing",
            pending_task_id="t1",
            pending_execution_gate="separate_human_approval",
            executing_task_id="t1",
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
        )
        self.assertIsNone(_validate_execution_state_invariants(plan, state))

    def test_valid_completed(self):
        plan = self._plan_two()
        state = self._es(
            plan,
            status="completed",
            next_assignment_index=2,
            completed_task_ids=["t1", "t2"],
        )
        self.assertIsNone(_validate_execution_state_invariants(plan, state))

    def test_valid_failed(self):
        plan = self._plan_one()
        state = self._es(
            plan,
            status="failed",
            pending_task_id="t1",
            pending_execution_gate="separate_human_approval",
            diagnostic="proveedor no disponible",
        )
        self.assertIsNone(_validate_execution_state_invariants(plan, state))

    def test_valid_blocked(self):
        plan = self._plan_one()
        state = self._es(
            plan,
            status="blocked",
            pending_task_id="t1",
            pending_execution_gate="separate_human_approval",
            pause_reason="bloqueado por gate",
        )
        self.assertIsNone(_validate_execution_state_invariants(plan, state))

    def test_valid_recovery_required(self):
        plan = self._plan_one()
        state = self._es(plan, status="recovery_required", diagnostic="evidencia corrupta")
        self.assertIsNone(_validate_execution_state_invariants(plan, state))

    def test_empty_plan_rejected(self):
        plan = _plan([])
        state = self._es(plan, status="in_progress")
        self.assertEqual(
            _validate_execution_state_invariants(plan, state), "empty_plan_assignments"
        )

    def test_mission_mismatch(self):
        plan = self._plan_one()
        state = self._es(plan, mission_id="mission-other")
        self.assertEqual(_validate_execution_state_invariants(plan, state), "mission_id_mismatch")

    def test_plan_drift(self):
        plan = self._plan_one()
        state = self._es(plan, plan_identity="0" * 64)
        self.assertEqual(_validate_execution_state_invariants(plan, state), "plan_drift")

    def test_cursor_negative(self):
        plan = self._plan_one()
        state = self._es(plan, next_assignment_index=-1)
        self.assertEqual(_validate_execution_state_invariants(plan, state), "cursor_out_of_range")

    def test_cursor_beyond_total(self):
        plan = self._plan_one()
        state = self._es(plan, next_assignment_index=2)
        self.assertEqual(_validate_execution_state_invariants(plan, state), "cursor_out_of_range")

    def test_completed_not_a_prefix(self):
        plan = self._plan_two()
        state = self._es(plan, next_assignment_index=1, completed_task_ids=["t2"])
        self.assertEqual(
            _validate_execution_state_invariants(plan, state),
            "completed_task_ids_not_a_prefix",
        )

    def test_cursor_prefix_length_mismatch(self):
        plan = self._plan_two()
        state = self._es(plan, next_assignment_index=0, completed_task_ids=["t1"])
        self.assertEqual(
            _validate_execution_state_invariants(plan, state), "cursor_index_mismatch"
        )

    def test_unknown_pending_task(self):
        plan = self._plan_one()
        state = self._es(plan, pending_task_id="ghost")
        self.assertEqual(
            _validate_execution_state_invariants(plan, state), "unknown_referenced_task"
        )

    def test_unknown_executing_task(self):
        plan = self._plan_one()
        state = self._es(plan, executing_task_id="ghost")
        self.assertEqual(
            _validate_execution_state_invariants(plan, state), "unknown_referenced_task"
        )

    def test_unknown_evidence_task(self):
        plan = self._plan_one()
        state = self._es(plan, evidence_ids_by_task={"ghost": "evidence-000000000000"})
        self.assertEqual(
            _validate_execution_state_invariants(plan, state), "unknown_referenced_task"
        )

    def test_invalid_nonce_format(self):
        plan = self._plan_one(gate="separate_human_approval")
        state = self._es(
            plan,
            status="waiting_for_approval",
            pending_task_id="t1",
            pending_execution_gate="separate_human_approval",
            approval_nonce="not-a-valid-nonce",
            pause_reason="esperando aprobación",
        )
        self.assertEqual(
            _validate_execution_state_invariants(plan, state), "invalid_approval_nonce"
        )

    def test_active_approval_already_consumed(self):
        plan = self._plan_one(gate="separate_human_approval")
        approval_id = "1" * 64
        state = self._es(
            plan,
            status="executing",
            pending_task_id="t1",
            pending_execution_gate="separate_human_approval",
            executing_task_id="t1",
            approval_nonce="a" * 32,
            active_approval_id=approval_id,
            consumed_approval_ids=[approval_id],
        )
        self.assertEqual(
            _validate_execution_state_invariants(plan, state),
            "active_approval_id_already_consumed",
        )

    def test_waiting_without_nonce(self):
        plan = self._plan_one(gate="separate_human_approval")
        state = self._es(
            plan,
            status="waiting_for_approval",
            pending_task_id="t1",
            pending_execution_gate="separate_human_approval",
            pause_reason="esperando aprobación",
        )
        self.assertEqual(
            _validate_execution_state_invariants(plan, state),
            "invalid_state_for_waiting_for_approval",
        )

    def test_waiting_on_wrong_gate_task(self):
        plan = self._plan_one(gate="plan_approval")
        state = self._es(
            plan,
            status="waiting_for_approval",
            pending_task_id="t1",
            pending_execution_gate="plan_approval",
            approval_nonce="a" * 32,
            pause_reason="esperando aprobación",
        )
        self.assertEqual(
            _validate_execution_state_invariants(plan, state),
            "invalid_state_for_waiting_for_approval",
        )

    def test_executing_separate_without_active_approval(self):
        plan = self._plan_one(gate="separate_human_approval")
        state = self._es(
            plan,
            status="executing",
            pending_task_id="t1",
            pending_execution_gate="separate_human_approval",
            executing_task_id="t1",
            approval_nonce="a" * 32,
        )
        self.assertEqual(
            _validate_execution_state_invariants(plan, state), "invalid_state_for_executing"
        )

    def test_executing_plan_approval_with_active_approval(self):
        plan = self._plan_one(gate="plan_approval")
        state = self._es(
            plan,
            status="executing",
            pending_task_id="t1",
            pending_execution_gate="plan_approval",
            executing_task_id="t1",
            active_approval_id="1" * 64,
        )
        self.assertEqual(
            _validate_execution_state_invariants(plan, state), "invalid_state_for_executing"
        )

    def test_completed_incomplete(self):
        plan = self._plan_two()
        state = self._es(
            plan,
            status="completed",
            next_assignment_index=1,
            completed_task_ids=["t1"],
        )
        self.assertEqual(
            _validate_execution_state_invariants(plan, state), "invalid_state_for_completed"
        )

    def test_failed_without_diagnostic(self):
        plan = self._plan_one()
        state = self._es(
            plan,
            status="failed",
            pending_task_id="t1",
            pending_execution_gate="separate_human_approval",
        )
        self.assertEqual(
            _validate_execution_state_invariants(plan, state), "invalid_state_for_failed"
        )

    def test_blocked_with_nonce(self):
        plan = self._plan_one()
        state = self._es(
            plan,
            status="blocked",
            pending_task_id="t1",
            pending_execution_gate="separate_human_approval",
            pause_reason="bloqueado",
            approval_nonce="a" * 32,
        )
        self.assertEqual(
            _validate_execution_state_invariants(plan, state), "invalid_state_for_blocked"
        )

    def test_recovery_required_without_diagnostic(self):
        plan = self._plan_one()
        state = self._es(plan, status="recovery_required")
        self.assertEqual(
            _validate_execution_state_invariants(plan, state),
            "invalid_state_for_recovery_required",
        )

    def test_valid_case_does_not_mutate_state_or_plan(self):
        plan = self._plan_one()
        state = self._es(plan, status="in_progress")
        plan_before = copy.deepcopy(plan)
        state_before = copy.deepcopy(state)
        _validate_execution_state_invariants(plan, state)
        self.assertEqual(plan, plan_before)
        self.assertEqual(state, state_before)

    def test_invalid_case_does_not_mutate_state_or_plan(self):
        plan = self._plan_one()
        state = self._es(plan, next_assignment_index=-1)
        plan_before = copy.deepcopy(plan)
        state_before = copy.deepcopy(state)
        _validate_execution_state_invariants(plan, state)
        self.assertEqual(plan, plan_before)
        self.assertEqual(state, state_before)


class MissionLockTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state_dir = Path(self._tmp.name)
        self.mission_id = "mission-lock-test"

    def _lock(self) -> _MissionLock:
        return _MissionLock(self.state_dir, self.mission_id)

    def _lock_path(self) -> Path:
        return self.state_dir / "missions" / self.mission_id / "execution.lock"

    def test_first_acquire_returns_true(self):
        lock = self._lock()
        self.assertTrue(lock.acquire())
        self.assertTrue(self._lock_path().is_file())
        self.assertTrue(lock._held)
        lock.release()

    def test_second_instance_cannot_acquire(self):
        first = self._lock()
        self.assertTrue(first.acquire())
        second = self._lock()
        self.assertFalse(second.acquire())
        self.assertFalse(second._held)
        self.assertTrue(self._lock_path().is_file())
        first.release()

    def test_release_allows_reacquire(self):
        first = self._lock()
        self.assertTrue(first.acquire())
        first.release()
        second = self._lock()
        self.assertTrue(second.acquire())
        second.release()

    def test_double_release_is_safe(self):
        lock = self._lock()
        self.assertTrue(lock.acquire())
        lock.release()
        lock.release()
        self.assertFalse(self._lock_path().exists())
        self.assertFalse(lock._held)

    def test_non_holder_does_not_remove_foreign_lock(self):
        holder = self._lock()
        self.assertTrue(holder.acquire())
        contender = self._lock()
        self.assertFalse(contender.acquire())
        contender.release()
        self.assertTrue(self._lock_path().is_file())
        self.assertTrue(holder._held)
        holder.release()

    def test_unsafe_mission_id_is_rejected(self):
        with self.assertRaises(MissionLookupError):
            _MissionLock(self.state_dir, "../escape")
        self.assertEqual(list(self.state_dir.rglob("*")), [])

    def test_lock_path_is_mission_scoped(self):
        lock = self._lock()
        expected = (self.state_dir / "missions" / self.mission_id / "execution.lock").resolve()
        self.assertEqual(lock._path.resolve(), expected)

    def test_lock_mode_is_restrictive(self):
        if os.name != "posix":
            self.skipTest("modo de archivo restrictivo sólo verificable en POSIX")
        lock = self._lock()
        self.assertTrue(lock.acquire())
        mode = stat.S_IMODE(self._lock_path().stat().st_mode)
        self.assertEqual(mode, 0o600)
        lock.release()

    def test_mkdir_oserror_becomes_execution_state_error(self):
        lock = self._lock()
        with mock.patch.object(Path, "mkdir", side_effect=OSError("disk full")):
            with self.assertRaises(ExecutionStateError):
                lock.acquire()
        self.assertFalse(lock._held)
        self.assertFalse(self._lock_path().exists())

    def test_open_oserror_becomes_execution_state_error(self):
        lock = self._lock()
        with mock.patch(
            "tools.konoha_v4.executor.os.open", side_effect=PermissionError("denied")
        ):
            with self.assertRaises(ExecutionStateError):
                lock.acquire()
        self.assertFalse(lock._held)
        self.assertFalse(self._lock_path().exists())

    def test_close_oserror_removes_only_own_partial_lock(self):
        lock = self._lock()
        real_close = os.close

        def close_then_fail(fd):
            real_close(fd)
            raise OSError("simulated close failure")

        with mock.patch(
            "tools.konoha_v4.executor.os.close", side_effect=close_then_fail
        ):
            with self.assertRaises(ExecutionStateError):
                lock.acquire()
        self.assertFalse(lock._held)
        self.assertFalse(self._lock_path().exists())

    def test_unlink_oserror_keeps_held_true(self):
        lock = self._lock()
        self.assertTrue(lock.acquire())
        with mock.patch(
            "tools.konoha_v4.executor.os.unlink", side_effect=PermissionError("denied")
        ):
            with self.assertRaises(ExecutionStateError):
                lock.release()
        self.assertTrue(lock._held)
        lock.release()

    def test_release_can_retry_after_transient_unlink_failure(self):
        lock = self._lock()
        self.assertTrue(lock.acquire())
        with mock.patch(
            "tools.konoha_v4.executor.os.unlink", side_effect=PermissionError("denied")
        ):
            with self.assertRaises(ExecutionStateError):
                lock.release()
        self.assertTrue(lock._held)
        lock.release()
        self.assertFalse(lock._held)
        self.assertFalse(self._lock_path().exists())

    def test_filenotfound_during_release_clears_held(self):
        lock = self._lock()
        self.assertTrue(lock.acquire())
        self._lock_path().unlink()
        lock.release()
        self.assertFalse(lock._held)

    def test_preexisting_lock_is_never_removed(self):
        lock_path = self._lock_path()
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text("sentinel", encoding="utf-8")
        contender = self._lock()
        self.assertFalse(contender.acquire())
        self.assertTrue(lock_path.is_file())
        self.assertEqual(lock_path.read_text(encoding="utf-8"), "sentinel")
        lock_path.unlink()

    def test_no_automatic_stale_lock_recovery(self):
        lock_path = self._lock_path()
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text("stale", encoding="utf-8")
        successor = self._lock()
        self.assertFalse(successor.acquire())
        self.assertTrue(lock_path.is_file())
        self.assertEqual(lock_path.read_text(encoding="utf-8"), "stale")
        lock_path.unlink()


class PureTransitionTests(unittest.TestCase):
    def _plan_two(
        self, gate1: str = "separate_human_approval", gate2: str = "plan_approval",
    ) -> MissionPlan:
        return _plan([
            _assignment(task_id="t1", execution_gate=gate1),
            _assignment(task_id="t2", execution_gate=gate2),
        ])

    def _es(self, plan: MissionPlan, **overrides) -> ExecutionState:
        fields = dict(
            schema_version=EXECUTION_STATE_SCHEMA_VERSION,
            mission_id=plan.mission_id,
            plan_identity=plan_identity(plan),
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
        fields.update(overrides)
        return ExecutionState(**fields)

    def _evidence(
        self,
        task: AgentAssignment,
        plan: MissionPlan,
        status: str = "completed",
        **overrides,
    ) -> EvidenceRecord:
        fields = dict(
            mission_id=plan.mission_id,
            task_id=task.task_id,
            provider=task.provider,
            model=task.model,
            status=status,
            output="evidencia de prueba",
            token_usage={},
            command=[],
            started_at=0.0,
            finished_at=1.0,
        )
        fields.update(overrides)
        return EvidenceRecord.build(**fields)

    def test_execution_attempt_fields_are_exactly_state_evidence_diagnostic(self):
        names = tuple(f.name for f in dataclasses.fields(ExecutionAttempt))
        self.assertEqual(names, ("state", "evidence", "diagnostic"))

    def test_execution_attempt_evidence_field_is_tuple(self):
        evidence_field = next(
            f for f in dataclasses.fields(ExecutionAttempt)
            if f.name == "evidence"
        )
        self.assertIn("tuple", str(evidence_field.type))

        attempt = ExecutionAttempt(state=None, evidence=(), diagnostic="ok")
        self.assertIsInstance(attempt.evidence, tuple)

    def test_execution_attempt_is_frozen(self):
        attempt = ExecutionAttempt(state=None, evidence=(), diagnostic="ok")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            attempt.diagnostic = "changed"

    def test_new_execution_state_sets_in_progress_and_zero_cursor(self):
        plan = self._plan_two()
        state = _new_execution_state(plan, "2026-07-21T00:00:00Z")
        self.assertEqual(state.status, "in_progress")
        self.assertEqual(state.next_assignment_index, 0)

    def test_new_execution_state_uses_plan_identity_and_mission_id(self):
        plan = self._plan_two()
        state = _new_execution_state(plan, "2026-07-21T00:00:00Z")
        self.assertEqual(state.mission_id, plan.mission_id)
        self.assertEqual(state.plan_identity, plan_identity(plan))

    def test_new_execution_state_all_optional_fields_none_or_empty(self):
        plan = self._plan_two()
        state = _new_execution_state(plan, "2026-07-21T00:00:00Z")
        self.assertEqual(state.schema_version, EXECUTION_STATE_SCHEMA_VERSION)
        self.assertEqual(state.completed_task_ids, [])
        self.assertIsNone(state.pending_task_id)
        self.assertIsNone(state.pending_execution_gate)
        self.assertIsNone(state.approval_nonce)
        self.assertIsNone(state.active_approval_id)
        self.assertEqual(state.consumed_approval_ids, [])
        self.assertEqual(state.evidence_ids_by_task, {})
        self.assertIsNone(state.executing_task_id)
        self.assertIsNone(state.pause_reason)
        self.assertIsNone(state.diagnostic)
        self.assertEqual(state.updated_at, "2026-07-21T00:00:00Z")

    def test_new_execution_state_with_empty_assignments_fails_invariants_without_disk_access(self):
        plan = _plan([])
        state = _new_execution_state(plan, "2026-07-21T00:00:00Z")
        self.assertEqual(
            _validate_execution_state_invariants(plan, state), "empty_plan_assignments"
        )

    def test_state_with_timestamp_applies_updated_at_and_changes(self):
        plan = self._plan_two()
        state = self._es(plan)
        new_state = _state_with_timestamp(
            state,
            "2026-07-22T00:00:00Z",
            status="blocked",
            diagnostic="boom",
        )
        self.assertEqual(new_state.updated_at, "2026-07-22T00:00:00Z")
        self.assertEqual(new_state.status, "blocked")
        self.assertEqual(new_state.diagnostic, "boom")

    def test_state_with_timestamp_does_not_mutate_input_state(self):
        plan = self._plan_two()
        state = self._es(plan)
        before = copy.deepcopy(state)
        _state_with_timestamp(state, "2026-07-22T00:00:00Z", status="blocked")
        self.assertEqual(state, before)

    def test_transition_to_blocked_sets_status_and_diagnostic_reason(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
            executing_task_id=task.task_id,
        )
        new_state = _transition_to_blocked(state, task, "motivo de bloqueo", "2026-07-22T00:00:00Z")
        self.assertEqual(new_state.status, "blocked")
        self.assertEqual(new_state.diagnostic, "motivo de bloqueo")
        self.assertEqual(new_state.pause_reason, "motivo de bloqueo")
        self.assertEqual(new_state.pending_task_id, task.task_id)
        self.assertEqual(new_state.pending_execution_gate, task.execution_gate)
        self.assertIsNone(new_state.approval_nonce)
        self.assertIsNone(new_state.active_approval_id)
        self.assertIsNone(new_state.executing_task_id)

    def test_transition_to_blocked_preserves_cursor_and_completed(self):
        plan = self._plan_two()
        task = plan.assignments[1]
        state = self._es(
            plan,
            next_assignment_index=1,
            completed_task_ids=["t1"],
        )
        new_state = _transition_to_blocked(state, task, "motivo", "2026-07-22T00:00:00Z")
        self.assertEqual(new_state.next_assignment_index, 1)
        self.assertEqual(new_state.completed_task_ids, ["t1"])

    def test_transition_to_waiting_sets_nonce_and_pending_task(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(plan)
        new_state = _transition_to_waiting(
            state, task, "a" * 32, "esperando aprobación", "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.status, "waiting_for_approval")
        self.assertEqual(new_state.pending_task_id, task.task_id)
        self.assertEqual(new_state.pending_execution_gate, task.execution_gate)
        self.assertEqual(new_state.approval_nonce, "a" * 32)
        self.assertEqual(new_state.pause_reason, "esperando aprobación")

    def test_transition_to_waiting_clears_active_approval_and_executing(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="executing",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            active_approval_id="1" * 64,
            diagnostic="diagnóstico obsoleto",
        )
        new_state = _transition_to_waiting(
            state, task, "a" * 32, "esperando aprobación", "2026-07-22T00:00:00Z",
        )
        self.assertIsNone(new_state.active_approval_id)
        self.assertIsNone(new_state.executing_task_id)
        self.assertIsNone(new_state.diagnostic)

    def test_transition_to_executing_sets_executing_task_id_and_active_approval_id(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="waiting_for_approval",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            approval_nonce="a" * 32,
            pause_reason="esperando aprobación",
        )
        new_state = _transition_to_executing(state, task, "1" * 64, "2026-07-22T00:00:00Z")
        self.assertEqual(new_state.status, "executing")
        self.assertEqual(new_state.executing_task_id, task.task_id)
        self.assertEqual(new_state.active_approval_id, "1" * 64)

    def test_transition_to_executing_preserves_nonce_for_separate_human_approval(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="waiting_for_approval",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            approval_nonce="a" * 32,
            pause_reason="esperando aprobación",
        )
        new_state = _transition_to_executing(state, task, "1" * 64, "2026-07-22T00:00:00Z")
        self.assertEqual(new_state.approval_nonce, "a" * 32)

    def test_transition_to_executing_none_active_approval_id_for_plan_approval(self):
        plan = self._plan_two(gate1="plan_approval")
        task = plan.assignments[0]
        state = self._es(
            plan,
            approval_nonce="a" * 32,
            active_approval_id="2" * 64,
        )
        new_state = _transition_to_executing(state, task, "1" * 64, "2026-07-22T00:00:00Z")
        self.assertIsNone(new_state.approval_nonce)
        self.assertIsNone(new_state.active_approval_id)

    def test_transition_after_completed_assignment_advances_cursor_and_records_evidence(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="executing",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
        )
        evidence = self._evidence(task, plan, status="completed")
        new_state = _transition_after_completed_assignment(
            state, plan, task, evidence, "1" * 64, "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.next_assignment_index, 1)
        self.assertEqual(new_state.completed_task_ids, ["t1"])
        self.assertEqual(new_state.evidence_ids_by_task[task.task_id], evidence.evidence_id)

    def test_transition_after_completed_assignment_returns_to_in_progress_when_tasks_remain(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="executing",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
        )
        evidence = self._evidence(task, plan, status="completed")
        new_state = _transition_after_completed_assignment(
            state, plan, task, evidence, "1" * 64, "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.status, "in_progress")

    def test_transition_after_completed_assignment_reaches_completed_on_last_task(self):
        plan = self._plan_two()
        task = plan.assignments[1]
        state = self._es(
            plan,
            status="executing",
            next_assignment_index=1,
            completed_task_ids=["t1"],
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            evidence_ids_by_task={"t1": "evidence-000000000000"},
        )
        evidence = self._evidence(task, plan, status="completed")
        new_state = _transition_after_completed_assignment(
            state, plan, task, evidence, None, "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.status, "completed")
        self.assertEqual(new_state.next_assignment_index, 2)
        self.assertEqual(new_state.completed_task_ids, ["t1", "t2"])

    def test_transition_after_completed_assignment_consumes_approval_exactly_once(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="executing",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
            consumed_approval_ids=[],
        )
        evidence = self._evidence(task, plan, status="completed")
        new_state = _transition_after_completed_assignment(
            state, plan, task, evidence, "1" * 64, "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.consumed_approval_ids.count("1" * 64), 1)

    def test_transition_after_completed_assignment_clears_active_approval_and_nonce(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="executing",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
            pause_reason="obsoleto",
            diagnostic="obsoleto",
        )
        evidence = self._evidence(task, plan, status="completed")
        new_state = _transition_after_completed_assignment(
            state, plan, task, evidence, "1" * 64, "2026-07-22T00:00:00Z",
        )
        self.assertIsNone(new_state.active_approval_id)
        self.assertIsNone(new_state.approval_nonce)
        self.assertIsNone(new_state.executing_task_id)
        self.assertIsNone(new_state.pending_task_id)
        self.assertIsNone(new_state.pending_execution_gate)
        self.assertIsNone(new_state.pause_reason)
        self.assertIsNone(new_state.diagnostic)

    def test_transition_after_failed_assignment_keeps_cursor_at_current_task(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="executing",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
        )
        evidence = self._evidence(task, plan, status="failed")
        new_state = _transition_after_failed_assignment(
            state, plan, task, evidence, "1" * 64, "assignment_failed", "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.next_assignment_index, 0)
        self.assertEqual(new_state.completed_task_ids, [])
        self.assertEqual(new_state.pending_task_id, task.task_id)

    def test_transition_after_failed_assignment_sets_diagnostic_from_explicit_param(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="executing",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
        )
        evidence = self._evidence(task, plan, status="failed")
        new_state = _transition_after_failed_assignment(
            state, plan, task, evidence, "1" * 64, "invalid_result_json", "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.status, "failed")
        self.assertEqual(new_state.diagnostic, "invalid_result_json")
        self.assertNotEqual(new_state.diagnostic, evidence.status)
        self.assertIsNone(new_state.pause_reason)

    def test_transition_after_failed_assignment_consumes_approval_exactly_once(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="executing",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
            consumed_approval_ids=[],
        )
        evidence = self._evidence(task, plan, status="failed")
        new_state = _transition_after_failed_assignment(
            state, plan, task, evidence, "1" * 64, "assignment_failed", "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.consumed_approval_ids.count("1" * 64), 1)

    def test_transition_after_failed_assignment_does_not_record_evidence_id(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="executing",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
        )
        evidence = self._evidence(task, plan, status="failed")
        new_state = _transition_after_failed_assignment(
            state, plan, task, evidence, "1" * 64, "assignment_failed", "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.evidence_ids_by_task, {})

    def test_transition_after_blocked_assignment_sets_status_and_diagnostic(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="executing",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
        )
        evidence = self._evidence(task, plan, status="blocked")
        new_state = _transition_after_blocked_assignment(
            state, plan, task, evidence, "1" * 64, "changes_requested", "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.status, "blocked")
        self.assertEqual(new_state.diagnostic, "changes_requested")
        self.assertEqual(new_state.pause_reason, "changes_requested")
        self.assertEqual(new_state.pending_task_id, task.task_id)
        self.assertEqual(new_state.pending_execution_gate, task.execution_gate)
        self.assertIsNone(new_state.executing_task_id)
        self.assertIsNone(new_state.active_approval_id)
        self.assertIsNone(new_state.approval_nonce)

    def test_transition_after_blocked_assignment_keeps_cursor_and_completed(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="executing",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
        )
        evidence = self._evidence(task, plan, status="blocked")
        new_state = _transition_after_blocked_assignment(
            state, plan, task, evidence, None, "blocked", "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.next_assignment_index, 0)
        self.assertEqual(new_state.completed_task_ids, [])
        self.assertEqual(new_state.evidence_ids_by_task, {})

    def test_transition_after_blocked_assignment_consumes_approval_exactly_once(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="executing",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
            consumed_approval_ids=[],
        )
        evidence = self._evidence(task, plan, status="blocked")
        new_state = _transition_after_blocked_assignment(
            state, plan, task, evidence, "1" * 64, "blocked", "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.consumed_approval_ids.count("1" * 64), 1)

    def test_transition_to_failed_before_execution_preserves_cursor_and_pending_task(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(plan, status="in_progress")
        new_state = _transition_to_failed_before_execution(
            state, task, "unknown_agent_family", None, "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.next_assignment_index, 0)
        self.assertEqual(new_state.pending_task_id, task.task_id)
        self.assertEqual(new_state.pending_execution_gate, task.execution_gate)
        self.assertEqual(new_state.status, "failed")
        self.assertEqual(new_state.diagnostic, "unknown_agent_family")

    def test_transition_to_failed_before_execution_consumes_approval_when_given(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(plan, status="in_progress", consumed_approval_ids=[])
        new_state = _transition_to_failed_before_execution(
            state, task, "unknown_agent_family", "1" * 64, "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.consumed_approval_ids.count("1" * 64), 1)

    def test_transition_to_failed_before_execution_no_approval_consumed_when_none(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(plan, status="in_progress", consumed_approval_ids=[])
        new_state = _transition_to_failed_before_execution(
            state, task, "unknown_agent_family", None, "2026-07-22T00:00:00Z",
        )
        self.assertEqual(new_state.consumed_approval_ids, [])

    def test_recovery_result_sets_recovery_required_and_diagnostic(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="executing",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
        )
        new_state = _recovery_result(state, "evidencia corrupta", "2026-07-22T00:00:00Z")
        self.assertEqual(new_state.status, "recovery_required")
        self.assertEqual(new_state.diagnostic, "evidencia corrupta")

    def test_recovery_result_preserves_executing_task_id_and_active_approval_id(self):
        plan = self._plan_two()
        task = plan.assignments[0]
        state = self._es(
            plan,
            status="executing",
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
        )
        new_state = _recovery_result(state, "evidencia corrupta", "2026-07-22T00:00:00Z")
        self.assertEqual(new_state.executing_task_id, task.task_id)
        self.assertEqual(new_state.active_approval_id, "1" * 64)
        self.assertEqual(new_state.approval_nonce, "a" * 32)
        self.assertEqual(new_state.pending_task_id, task.task_id)
        self.assertEqual(new_state.pending_execution_gate, task.execution_gate)

    def test_recovery_result_preserves_cursor_completed_and_evidence_map(self):
        plan = self._plan_two()
        task = plan.assignments[1]
        state = self._es(
            plan,
            status="executing",
            next_assignment_index=1,
            completed_task_ids=["t1"],
            pending_task_id=task.task_id,
            pending_execution_gate=task.execution_gate,
            executing_task_id=task.task_id,
            evidence_ids_by_task={"t1": "evidence-000000000000"},
            consumed_approval_ids=["2" * 64],
        )
        new_state = _recovery_result(state, "evidencia corrupta", "2026-07-22T00:00:00Z")
        self.assertEqual(new_state.next_assignment_index, 1)
        self.assertEqual(new_state.completed_task_ids, ["t1"])
        self.assertEqual(new_state.evidence_ids_by_task, {"t1": "evidence-000000000000"})
        self.assertEqual(new_state.consumed_approval_ids, ["2" * 64])

    def test_all_transitions_echo_supplied_updated_at_exactly(self):
        plan = self._plan_two()
        t1, t2 = plan.assignments

        fresh = _new_execution_state(plan, "ts-0")
        self.assertEqual(fresh.updated_at, "ts-0")

        state0 = self._es(plan, status="in_progress")

        stamped = _state_with_timestamp(state0, "ts-stamp")
        self.assertEqual(stamped.updated_at, "ts-stamp")

        waiting = _transition_to_waiting(state0, t1, "a" * 32, "esperando aprobación", "ts-1")
        self.assertEqual(waiting.updated_at, "ts-1")

        executing1 = _transition_to_executing(waiting, t1, "1" * 64, "ts-2")
        self.assertEqual(executing1.updated_at, "ts-2")

        evidence1 = self._evidence(t1, plan, status="completed")
        completed1 = _transition_after_completed_assignment(
            executing1, plan, t1, evidence1, "1" * 64, "ts-3",
        )
        self.assertEqual(completed1.updated_at, "ts-3")

        executing2 = _transition_to_executing(completed1, t2, None, "ts-4")
        self.assertEqual(executing2.updated_at, "ts-4")

        evidence2 = self._evidence(t2, plan, status="completed")
        completed2 = _transition_after_completed_assignment(
            executing2, plan, t2, evidence2, None, "ts-5",
        )
        self.assertEqual(completed2.updated_at, "ts-5")

        blocked = _transition_to_blocked(state0, t1, "motivo", "ts-6")
        self.assertEqual(blocked.updated_at, "ts-6")

        failed = _transition_after_failed_assignment(
            executing1, plan, t1, self._evidence(t1, plan, status="failed"),
            "1" * 64, "assignment_failed", "ts-7",
        )
        self.assertEqual(failed.updated_at, "ts-7")

        failed_before = _transition_to_failed_before_execution(
            state0, t1, "unknown_agent_family", None, "ts-8",
        )
        self.assertEqual(failed_before.updated_at, "ts-8")

        recovery = _recovery_result(executing1, "evidencia corrupta", "ts-9")
        self.assertEqual(recovery.updated_at, "ts-9")

    def test_all_transitions_produce_states_that_satisfy_existing_invariants(self):
        plan = self._plan_two()
        t1, t2 = plan.assignments
        in_progress = self._es(plan, status="in_progress")
        self.assertIsNone(_validate_execution_state_invariants(plan, in_progress))

        waiting_t1 = _transition_to_waiting(
            in_progress, t1, "a" * 32, "esperando aprobación", "ts-1",
        )
        self.assertIsNone(_validate_execution_state_invariants(plan, waiting_t1))

        executing_t1 = _transition_to_executing(waiting_t1, t1, "1" * 64, "ts-2")
        self.assertIsNone(_validate_execution_state_invariants(plan, executing_t1))

        evidence_t1 = self._evidence(t1, plan, status="completed")
        completed_t1 = _transition_after_completed_assignment(
            executing_t1, plan, t1, evidence_t1, "1" * 64, "ts-3",
        )
        self.assertIsNone(_validate_execution_state_invariants(plan, completed_t1))

        executing_t2 = _transition_to_executing(completed_t1, t2, None, "ts-4")
        self.assertIsNone(_validate_execution_state_invariants(plan, executing_t2))

        evidence_t2 = self._evidence(t2, plan, status="completed")
        completed_total = _transition_after_completed_assignment(
            executing_t2, plan, t2, evidence_t2, None, "ts-5",
        )
        self.assertIsNone(_validate_execution_state_invariants(plan, completed_total))
        self.assertEqual(completed_total.status, "completed")

        failed_t1 = _transition_after_failed_assignment(
            executing_t1, plan, t1, self._evidence(t1, plan, status="failed"),
            "1" * 64, "assignment_failed", "ts-6",
        )
        self.assertIsNone(_validate_execution_state_invariants(plan, failed_t1))

        blocked_t1 = _transition_after_blocked_assignment(
            executing_t1, plan, t1, self._evidence(t1, plan, status="blocked"),
            "1" * 64, "changes_requested", "ts-6b",
        )
        self.assertIsNone(_validate_execution_state_invariants(plan, blocked_t1))

        recovery_t1 = _recovery_result(executing_t1, "evidencia corrupta", "ts-7")
        self.assertIsNone(_validate_execution_state_invariants(plan, recovery_t1))

        failed_before = _transition_to_failed_before_execution(
            in_progress, t1, "unknown_agent_family", None, "ts-8",
        )
        self.assertIsNone(_validate_execution_state_invariants(plan, failed_before))

    def test_transitions_never_mutate_their_inputs(self):
        plan = self._plan_two()
        t1, t2 = plan.assignments
        plan_before = copy.deepcopy(plan)
        task_before = copy.deepcopy(t1)

        state = self._es(
            plan,
            status="executing",
            pending_task_id=t1.task_id,
            pending_execution_gate=t1.execution_gate,
            executing_task_id=t1.task_id,
            approval_nonce="a" * 32,
            active_approval_id="1" * 64,
        )
        state_before = copy.deepcopy(state)

        completed_evidence = self._evidence(t1, plan, status="completed")
        completed_evidence_before = copy.deepcopy(completed_evidence)
        failed_evidence = self._evidence(t1, plan, status="failed")
        failed_evidence_before = copy.deepcopy(failed_evidence)

        _new_execution_state(plan, "ts-new")
        _transition_after_completed_assignment(
            state, plan, t1, completed_evidence, "1" * 64, "ts-1",
        )
        _transition_after_failed_assignment(
            state, plan, t1, failed_evidence, "1" * 64, "assignment_failed", "ts-2",
        )
        blocked_evidence = self._evidence(t1, plan, status="blocked")
        blocked_evidence_before = copy.deepcopy(blocked_evidence)
        _transition_after_blocked_assignment(
            state, plan, t1, blocked_evidence, "1" * 64, "changes_requested", "ts-2b",
        )
        _transition_to_waiting(state, t1, "a" * 32, "motivo", "ts-3")
        _transition_to_executing(state, t1, "1" * 64, "ts-4")
        _transition_to_blocked(state, t1, "motivo", "ts-5")
        _transition_to_failed_before_execution(state, t1, "diagnostico", "1" * 64, "ts-6")
        _recovery_result(state, "diagnostico", "ts-7")
        _state_with_timestamp(state, "ts-8")

        self.assertEqual(plan, plan_before)
        self.assertEqual(t1, task_before)
        self.assertEqual(state, state_before)
        self.assertEqual(completed_evidence, completed_evidence_before)
        self.assertEqual(failed_evidence, failed_evidence_before)
        self.assertEqual(blocked_evidence, blocked_evidence_before)


if __name__ == "__main__":
    unittest.main()
