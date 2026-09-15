from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools.konoha_v4.conversation import (
    _EXIT_COMMANDS,
    _read_exact_command,
    _resolve_pending_plan_approval,
    _run_resumable_execution,
    resume_mission,
    run,
)
from tools.konoha_v4.executor import ExecutionAttempt
from tools.konoha_v4.models import AgentAssignment, EvidenceRecord, ExecutionState, MissionPlan


def _assignment(task_id="t1", execution_gate="separate_human_approval", **overrides):
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


def _plan(assignments=None, approval_status="approved", **overrides):
    fields = dict(
        mission_id="mission-conv-test",
        understanding="Validar el wiring terminal.",
        explicit_facts=[],
        missing_context=[],
        assumptions_prohibited=[],
        complexity="low",
        assignments=assignments if assignments is not None else [_assignment()],
        acceptance_criteria=["done"],
        approval_boundaries=["read_only", "mutation", "network", "private_context"],
        estimated_tokens=15,
        estimated_cost_class="low",
        rationale="test",
        approval={
            "status": approval_status,
            "approved_by": "human" if approval_status == "approved" else None,
            "approved_at": "2026-07-21T00:00:00Z" if approval_status == "approved" else None,
            "feedback": None,
        },
    )
    fields.update(overrides)
    return MissionPlan(**fields).seal()


def _state(**overrides):
    fields = dict(
        schema_version="1.0",
        mission_id="mission-conv-test",
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
    fields.update(overrides)
    return ExecutionState(**fields)


def _attempt(state, diagnostic, evidence=()):
    return ExecutionAttempt(state=state, evidence=tuple(evidence), diagnostic=diagnostic)


def _evidence(task_id="t1", status="completed"):
    return EvidenceRecord.build(
        mission_id="mission-conv-test", task_id=task_id, provider="codex", model="codex",
        status=status, output="evidencia", token_usage={}, command=[],
        started_at=0.0, finished_at=1.0,
    )


class RunResumableExecutionTests(unittest.TestCase):
    def _run(self, attempts, read_decision=None, read_exact=None):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            patches = [
                mock.patch(
                    "tools.konoha_v4.conversation.execute_or_resume_plan", side_effect=attempts,
                ),
            ]
            if read_decision is not None:
                patches.append(
                    mock.patch("tools.konoha_v4.conversation._read_decision", side_effect=read_decision),
                )
            if read_exact is not None:
                patches.append(
                    mock.patch("tools.konoha_v4.conversation._read_exact_command", side_effect=read_exact),
                )
            for p in patches:
                p.start()
            try:
                result = _run_resumable_execution(Path("."), state_dir, "mission-conv-test", mock.Mock())
            finally:
                for p in reversed(patches):
                    p.stop()
            return result

    def test_completed_mission_returns_completed(self):
        state = _state(status="completed", next_assignment_index=1, completed_task_ids=["t1"])
        attempts = [_attempt(state, "completed", evidence=[_evidence()])]
        result = self._run(attempts)
        self.assertEqual(result, "completed")

    def test_state_none_returns_failed(self):
        attempts = [_attempt(None, "plan_load_error")]
        result = self._run(attempts)
        self.assertEqual(result, "failed")

    def test_terminal_status_failed_returns_failed(self):
        state = _state(
            status="failed", pending_task_id="t1", pending_execution_gate="plan_approval",
            diagnostic="boom",
        )
        attempts = [_attempt(state, "workspace_mutation_detected")]
        result = self._run(attempts)
        self.assertEqual(result, "failed")

    def test_recovery_required_returns_failed(self):
        state = _state(status="recovery_required", diagnostic="plan_drift")
        attempts = [_attempt(state, "plan_drift")]
        result = self._run(attempts)
        self.assertEqual(result, "failed")

    # --- security/durability diagnostics always short-circuit, regardless
    # of state.status ---

    def test_lock_release_error_with_completed_status_stops_immediately(self):
        state = _state(status="completed", next_assignment_index=1, completed_task_ids=["t1"])
        attempts = [_attempt(state, "lock_release_error")]
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation.execute_or_resume_plan", side_effect=attempts,
            ) as call:
                result = _run_resumable_execution(Path("."), state_dir, "mission-conv-test", mock.Mock())
            call.assert_called_once()
        self.assertEqual(result, "failed")

    def test_waiting_persist_failed_with_in_progress_status_stops_immediately(self):
        state = _state(status="in_progress")
        attempts = [_attempt(state, "waiting_persist_failed")]
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation.execute_or_resume_plan", side_effect=attempts,
            ) as call:
                result = _run_resumable_execution(Path("."), state_dir, "mission-conv-test", mock.Mock())
            call.assert_called_once()
        self.assertEqual(result, "failed")

    def test_executing_persist_failed_with_in_progress_status_stops_immediately(self):
        state = _state(status="in_progress")
        attempts = [_attempt(state, "executing_persist_failed")]
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation.execute_or_resume_plan", side_effect=attempts,
            ) as call:
                result = _run_resumable_execution(Path("."), state_dir, "mission-conv-test", mock.Mock())
            call.assert_called_once()
        self.assertEqual(result, "failed")

    def test_final_transition_persist_failed_stops_immediately(self):
        state = _state(status="executing", pending_task_id="t1", pending_execution_gate="plan_approval",
                        executing_task_id="t1")
        attempts = [_attempt(state, "final_transition_persist_failed", evidence=[_evidence()])]
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation.execute_or_resume_plan", side_effect=attempts,
            ) as call:
                result = _run_resumable_execution(Path("."), state_dir, "mission-conv-test", mock.Mock())
            call.assert_called_once()
        self.assertEqual(result, "failed")

    # --- v4.0.2: operational readiness diagnostics stop after exactly one
    # attempt regardless of which pending-task status they interrupt, and
    # never trigger an unattended retry loop or automatic fallback ---

    def test_provider_not_ready_in_progress_returns_paused_without_looping(self):
        state = _state(status="in_progress")
        attempts = [_attempt(state, "provider_not_ready:codex")]
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation.execute_or_resume_plan", side_effect=attempts,
            ) as call:
                result = _run_resumable_execution(Path("."), state_dir, "mission-conv-test", mock.Mock())
            call.assert_called_once()
        self.assertEqual(result, "paused")

    def test_model_not_ready_waiting_for_approval_returns_paused_without_looping(self):
        state = _state(
            status="waiting_for_approval", pending_task_id="t1",
            pending_execution_gate="separate_human_approval", approval_nonce="a" * 32,
            pause_reason="esperando",
        )
        attempts = [_attempt(state, "model_not_ready:ollama/llama3:latest")]
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation.execute_or_resume_plan", side_effect=attempts,
            ) as call:
                result = _run_resumable_execution(Path("."), state_dir, "mission-conv-test", mock.Mock())
            call.assert_called_once()
        self.assertEqual(result, "paused")

    def test_readiness_failure_message_confirms_mission_remains_resumable(self):
        state = _state(status="in_progress")
        attempts = [_attempt(state, "provider_not_ready:codex")]
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation.execute_or_resume_plan", side_effect=attempts,
            ), contextlib.redirect_stdout(buffer):
                result = _run_resumable_execution(Path("."), state_dir, "mission-conv-test", mock.Mock())
        self.assertEqual(result, "paused")
        output = buffer.getvalue()
        self.assertIn("resumible", output)
        self.assertIn("--resume mission-conv-test", output)

    # --- waiting_for_approval: exact-match only ---

    def test_waiting_for_approval_exact_match_accepted_and_executes(self):
        waiting_state = _state(
            status="waiting_for_approval", pending_task_id="t1",
            pending_execution_gate="separate_human_approval", approval_nonce="a" * 32,
            pause_reason="esperando",
        )
        completed_state = _state(
            status="completed", next_assignment_index=1, completed_task_ids=["t1"],
        )
        expected = (
            ":aprobar-assignment mission-conv-test t1 separate_human_approval "
            + "0" * 64 + " " + "a" * 32
        )
        attempts = [
            _attempt(waiting_state, "waiting_for_approval"),
            _attempt(completed_state, "completed", evidence=[_evidence()]),
        ]
        result = self._run(attempts, read_exact=[expected])
        self.assertEqual(result, "completed")

    def test_waiting_for_approval_leading_space_rejected(self):
        waiting_state = _state(
            status="waiting_for_approval", pending_task_id="t1",
            pending_execution_gate="separate_human_approval", approval_nonce="a" * 32,
            pause_reason="esperando",
        )
        expected = (
            ":aprobar-assignment mission-conv-test t1 separate_human_approval "
            + "0" * 64 + " " + "a" * 32
        )
        attempts = [
            _attempt(waiting_state, "waiting_for_approval"),
            _attempt(waiting_state, "waiting_for_approval"),
        ]
        result = self._run(attempts, read_exact=[" " + expected, None])
        self.assertEqual(result, "paused")

    def test_waiting_for_approval_trailing_space_rejected(self):
        waiting_state = _state(
            status="waiting_for_approval", pending_task_id="t1",
            pending_execution_gate="separate_human_approval", approval_nonce="a" * 32,
            pause_reason="esperando",
        )
        expected = (
            ":aprobar-assignment mission-conv-test t1 separate_human_approval "
            + "0" * 64 + " " + "a" * 32
        )
        attempts = [
            _attempt(waiting_state, "waiting_for_approval"),
            _attempt(waiting_state, "waiting_for_approval"),
        ]
        result = self._run(attempts, read_exact=[expected + " ", None])
        self.assertEqual(result, "paused")

    def test_waiting_for_approval_case_difference_rejected(self):
        waiting_state = _state(
            status="waiting_for_approval", pending_task_id="t1",
            pending_execution_gate="separate_human_approval", approval_nonce="a" * 32,
            pause_reason="esperando",
        )
        expected = (
            ":aprobar-assignment mission-conv-test t1 separate_human_approval "
            + "0" * 64 + " " + "a" * 32
        )
        attempts = [
            _attempt(waiting_state, "waiting_for_approval"),
            _attempt(waiting_state, "waiting_for_approval"),
        ]
        result = self._run(attempts, read_exact=[expected.upper(), None])
        self.assertEqual(result, "paused")

    def test_waiting_for_approval_partial_command_rejected(self):
        waiting_state = _state(
            status="waiting_for_approval", pending_task_id="t1",
            pending_execution_gate="separate_human_approval", approval_nonce="a" * 32,
            pause_reason="esperando",
        )
        attempts = [
            _attempt(waiting_state, "waiting_for_approval"),
            _attempt(waiting_state, "waiting_for_approval"),
        ]
        result = self._run(attempts, read_exact=[":aprobar-assignment mission-conv-test", None])
        self.assertEqual(result, "paused")

    def test_waiting_for_approval_eof_pauses_without_further_calls(self):
        waiting_state = _state(
            status="waiting_for_approval", pending_task_id="t1",
            pending_execution_gate="separate_human_approval", approval_nonce="a" * 32,
            pause_reason="esperando",
        )
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation.execute_or_resume_plan",
                side_effect=[_attempt(waiting_state, "waiting_for_approval")],
            ) as call:
                with mock.patch(
                    "tools.konoha_v4.conversation._read_exact_command", side_effect=[None],
                ):
                    result = _run_resumable_execution(
                        Path("."), state_dir, "mission-conv-test", mock.Mock(),
                    )
            call.assert_called_once()
        self.assertEqual(result, "paused")

    # --- plan_approval_not_satisfied delegates to _resolve_pending_plan_approval ---

    def test_plan_approval_not_satisfied_approved_continues(self):
        pending_state = _state(status="in_progress")
        completed_state = _state(status="completed", next_assignment_index=1, completed_task_ids=["t1"])
        attempts = [
            _attempt(pending_state, "plan_approval_not_satisfied"),
            _attempt(completed_state, "completed", evidence=[_evidence()]),
        ]
        with mock.patch(
            "tools.konoha_v4.conversation._resolve_pending_plan_approval", return_value="approved",
        ):
            result = self._run(attempts)
        self.assertEqual(result, "completed")

    def test_plan_approval_not_satisfied_paused_returns_paused(self):
        pending_state = _state(status="in_progress")
        attempts = [_attempt(pending_state, "plan_approval_not_satisfied")]
        with mock.patch(
            "tools.konoha_v4.conversation._resolve_pending_plan_approval", return_value="paused",
        ):
            result = self._run(attempts)
        self.assertEqual(result, "paused")

    def test_plan_approval_not_satisfied_rejected_returns_failed(self):
        pending_state = _state(status="in_progress")
        attempts = [_attempt(pending_state, "plan_approval_not_satisfied")]
        with mock.patch(
            "tools.konoha_v4.conversation._resolve_pending_plan_approval", return_value="rejected",
        ):
            result = self._run(attempts)
        self.assertEqual(result, "failed")

    def test_plan_approval_not_satisfied_persist_failed_returns_failed(self):
        pending_state = _state(status="in_progress")
        attempts = [_attempt(pending_state, "plan_approval_not_satisfied")]
        with mock.patch(
            "tools.konoha_v4.conversation._resolve_pending_plan_approval", return_value="persist_failed",
        ):
            result = self._run(attempts)
        self.assertEqual(result, "failed")


class ResolvePendingPlanApprovalTests(unittest.TestCase):
    def _run(self, decisions, plan=None, challenge_grant=True):
        plan = plan or _plan(approval_status="pending")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            mission_dir = state_dir / "missions" / plan.mission_id
            mission_dir.mkdir(parents=True)
            with mock.patch(
                "tools.konoha_v4.conversation.load_persisted_plan", return_value=plan,
            ):
                with mock.patch(
                    "tools.konoha_v4.conversation._read_decision", side_effect=decisions,
                ):
                    with mock.patch(
                        "tools.konoha_v4.conversation.approval_summary", return_value="VISIBLE PLAN",
                    ):
                        # The "approved" branch now requires a fresh,
                        # plan-identity-bound challenge - defaulting to
                        # True here preserves every existing "si"-reaches-
                        # approved test's behavior unchanged; tests that
                        # need to prove the challenge-failure path pass
                        # challenge_grant=False explicitly (or bypass
                        # _run entirely, as the dedicated tests below do).
                        with mock.patch(
                            "tools.konoha_v4.conversation._read_plan_challenge_grant",
                            return_value=challenge_grant,
                        ):
                            result = _resolve_pending_plan_approval(state_dir, plan.mission_id)
            return result, plan

    def test_approved_persists_and_returns_approved(self):
        result, plan = self._run(["si"])
        self.assertEqual(result, "approved")
        self.assertEqual(plan.approval["status"], "approved")

    def test_rejected_persists_and_returns_rejected(self):
        result, plan = self._run(["no"])
        self.assertEqual(result, "rejected")
        self.assertEqual(plan.approval["status"], "rejected")

    def test_paused_on_exit_without_persisting(self):
        plan = _plan(approval_status="pending")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation.load_persisted_plan", return_value=plan,
            ):
                with mock.patch(
                    "tools.konoha_v4.conversation._read_decision", side_effect=["salir"],
                ):
                    with mock.patch(
                        "tools.konoha_v4.conversation.approval_summary", return_value="VISIBLE PLAN",
                    ):
                        with mock.patch(
                            "tools.konoha_v4.conversation._persist_plan",
                        ) as persist_mock:
                            result = _resolve_pending_plan_approval(state_dir, plan.mission_id)
            persist_mock.assert_not_called()
        self.assertEqual(result, "paused")

    def test_pending_reprompts_then_approves(self):
        result, plan = self._run(["", "si"])
        self.assertEqual(result, "approved")

    def test_changes_requested_reprompts_then_approves(self):
        result, plan = self._run(["cambio: algo", "si"])
        self.assertEqual(result, "approved")

    def test_persist_failed_on_approve(self):
        plan = _plan(approval_status="pending")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation.load_persisted_plan", return_value=plan,
            ):
                with mock.patch(
                    "tools.konoha_v4.conversation._read_decision", side_effect=["si"],
                ):
                    with mock.patch(
                        "tools.konoha_v4.conversation.approval_summary", return_value="VISIBLE PLAN",
                    ):
                        with mock.patch(
                            # "si" is intention only; the fresh
                            # plan-identity-bound challenge must succeed
                            # for this test to reach the post-authority
                            # persistence-failure path it exists to prove
                            # - not to exercise challenge failure itself.
                            "tools.konoha_v4.conversation._read_plan_challenge_grant",
                            return_value=True,
                        ):
                            with mock.patch(
                                "tools.konoha_v4.conversation._persist_plan",
                                side_effect=OSError("full"),
                            ):
                                result = _resolve_pending_plan_approval(state_dir, plan.mission_id)
        self.assertEqual(result, "persist_failed")

    def test_persist_failed_on_reject(self):
        plan = _plan(approval_status="pending")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation.load_persisted_plan", return_value=plan,
            ):
                with mock.patch(
                    "tools.konoha_v4.conversation._read_decision", side_effect=["no"],
                ):
                    with mock.patch(
                        "tools.konoha_v4.conversation.approval_summary", return_value="VISIBLE PLAN",
                    ):
                        with mock.patch(
                            "tools.konoha_v4.conversation._persist_plan",
                            side_effect=OSError("full"),
                        ):
                            result = _resolve_pending_plan_approval(state_dir, plan.mission_id)
        self.assertEqual(result, "persist_failed")

    # --- v4.1.1 human-turn-integrity: "si" is intention only, resumed path

    def test_failed_challenge_leaves_plan_pending_pre_buffered_si_is_intention_only(
        self,
    ) -> None:
        # A plain "si" is intention only: if the fresh, plan-identity-bound
        # challenge that follows it is not satisfied exactly, the plan
        # must never become approved and nothing must be persisted from
        # that failed attempt - only the later, legitimate explicit "no"
        # rejection is allowed to persist anything.
        plan = _plan(approval_status="pending")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation.load_persisted_plan", return_value=plan,
            ):
                with mock.patch(
                    "tools.konoha_v4.conversation._read_decision",
                    side_effect=["si", "no"],
                ):
                    with mock.patch(
                        "tools.konoha_v4.conversation.approval_summary", return_value="VISIBLE PLAN",
                    ):
                        with mock.patch(
                            "tools.konoha_v4.conversation._read_plan_challenge_grant",
                            return_value=False,
                        ) as grant_mock:
                            with mock.patch(
                                "tools.konoha_v4.conversation._persist_plan",
                            ) as persist_mock:
                                result = _resolve_pending_plan_approval(
                                    state_dir, plan.mission_id,
                                )
        grant_mock.assert_called_once()
        self.assertEqual(result, "rejected")
        self.assertEqual(plan.approval["status"], "rejected")
        self.assertIsNone(plan.approval["approved_by"])
        self.assertIsNone(plan.approval["approved_at"])
        # Exactly one persist call total, for the later legitimate
        # rejection - the failed challenge itself never wrote anything.
        persist_mock.assert_called_once()

    def test_challenge_uses_reloaded_plan_and_aprobar_plan_verb(self) -> None:
        # The resumed approval path must use the SAME shared
        # _read_plan_challenge_grant helper as normal-mode approval, bound
        # to the exact reloaded persisted plan instance and the execution-
        # authority verb - not a parallel identity/challenge mechanism.
        # Stale/wrong plan_identity rejection itself is already covered at
        # the helper level in test_approval_input_stabilization.py; this
        # only proves the resumed integration path wires the real
        # arguments through.
        plan = _plan(approval_status="pending")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation.load_persisted_plan", return_value=plan,
            ):
                with mock.patch(
                    "tools.konoha_v4.conversation._read_decision", side_effect=["si"],
                ):
                    with mock.patch(
                        "tools.konoha_v4.conversation.approval_summary", return_value="VISIBLE PLAN",
                    ):
                        with mock.patch(
                            "tools.konoha_v4.conversation._read_plan_challenge_grant",
                            return_value=True,
                        ) as grant_mock:
                            result = _resolve_pending_plan_approval(
                                state_dir, plan.mission_id,
                            )
        self.assertEqual(result, "approved")
        grant_mock.assert_called_once_with(
            command_verb="aprobar-plan",
            grant_label=mock.ANY,
            mission_id=plan.mission_id,
            plan=plan,
        )


class ReadExactCommandTests(unittest.TestCase):
    def test_returns_raw_input_without_stripping(self):
        # _read_exact_command now reads through the single-owner
        # TerminalTurnReader (read_exact_line), not raw input() - the
        # exact leading/trailing-whitespace-preserving comparison contract
        # is unchanged, only the read primitive is.
        with mock.patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value="  raw text  ",
        ):
            self.assertEqual(_read_exact_command("Vos> "), "  raw text  ")

    def test_eof_returns_none(self):
        with mock.patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value=None,
        ):
            self.assertIsNone(_read_exact_command("Vos> "))


class RunWiringTests(unittest.TestCase):
    def _run_one_mission(self, execution_result):
        plan = _plan(approval_status="approved")
        acquired = SimpleNamespace(
            provider_readiness={"codex": {"available": True}},
            as_dict=lambda: {},
        )
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch("tools.konoha_v4.conversation.default_state_root", return_value=state_dir), \
                 mock.patch("tools.konoha_v4.conversation.CapabilityRegistry", return_value=mock.Mock()), \
                 mock.patch("tools.konoha_v4.conversation.acquire_context", return_value=acquired), \
                 mock.patch(
                     "tools.konoha_v4.conversation._repo_state",
                     return_value={"branch": "test", "head": "abc", "status": ""},
                 ), \
                 mock.patch(
                     "tools.konoha_v4.conversation._read_turn", side_effect=["hacer algo", "salir"],
                 ), \
                 mock.patch(
                     "tools.konoha_v4.conversation._build_validated_plan",
                     return_value=(plan, [], 1),
                 ), \
                 mock.patch("tools.konoha_v4.conversation._approval_loop", return_value=plan), \
                 mock.patch("tools.konoha_v4.conversation._persist_plan"), \
                 mock.patch(
                     "tools.konoha_v4.conversation._run_resumable_execution",
                     return_value=execution_result,
                 ) as run_mock:
                exit_code = run(Path("."))
        run_mock.assert_called_once()
        return exit_code

    def test_completed_execution_returns_zero(self):
        exit_code = self._run_one_mission("completed")
        self.assertEqual(exit_code, 0)

    def test_wires_acquired_readiness_snapshot_into_both_planning_boundaries(self):
        # BLOCK_4 FINDING #16 Test H: run() must pass the exact same
        # acquired.provider_readiness snapshot into both
        # _build_validated_plan() and _approval_loop() - not a re-probed or
        # re-derived value. Not a provider-execution test: _run_resumable_
        # execution stays fully mocked, same as the rest of this class.
        readiness_sentinel = {"codex": {"available": True}}
        plan = _plan(approval_status="approved")
        acquired = SimpleNamespace(
            provider_readiness=readiness_sentinel,
            as_dict=lambda: {},
        )
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch("tools.konoha_v4.conversation.default_state_root", return_value=state_dir), \
                 mock.patch("tools.konoha_v4.conversation.CapabilityRegistry", return_value=mock.Mock()), \
                 mock.patch("tools.konoha_v4.conversation.acquire_context", return_value=acquired), \
                 mock.patch(
                     "tools.konoha_v4.conversation._repo_state",
                     return_value={"branch": "test", "head": "abc", "status": ""},
                 ), \
                 mock.patch(
                     "tools.konoha_v4.conversation._read_turn", side_effect=["hacer algo", "salir"],
                 ), \
                 mock.patch(
                     "tools.konoha_v4.conversation._build_validated_plan",
                     return_value=(plan, [], 1),
                 ) as build_mock, \
                 mock.patch(
                     "tools.konoha_v4.conversation._approval_loop", return_value=plan,
                 ) as approval_mock, \
                 mock.patch("tools.konoha_v4.conversation._persist_plan"), \
                 mock.patch(
                     "tools.konoha_v4.conversation._run_resumable_execution",
                     return_value="completed",
                 ):
                run(Path("."))

        build_mock.assert_called_once()
        self.assertIs(
            build_mock.call_args.kwargs["provider_readiness"], readiness_sentinel,
        )
        approval_mock.assert_called_once()
        self.assertIs(
            approval_mock.call_args.kwargs["provider_readiness"], readiness_sentinel,
        )

    def test_paused_execution_does_not_report_completed(self):
        exit_code = self._run_one_mission("paused")
        self.assertEqual(exit_code, 0)

    def test_failed_execution_terminal_does_not_report_completed(self):
        exit_code = self._run_one_mission("failed")
        self.assertEqual(exit_code, 0)

    def test_failed_execution_persistence_failure_does_not_report_completed(self):
        # From run()'s perspective a terminal runtime failure and a
        # persistence-failure short-circuit both collapse to the same
        # "failed" result and the same branch - the distinction between the
        # two lives inside _run_resumable_execution (see
        # RunResumableExecutionTests), already covered there.
        exit_code = self._run_one_mission("failed")
        self.assertEqual(exit_code, 0)


class StartupDoesNotScanSourcesTests(unittest.TestCase):
    """BLOCK_4 FINDING #14: conversational startup must reach mission input
    without invoking source_monitor.start_scan on any state_dir/
    source_policy.json roots. source_monitor itself is untouched and stays
    available for future explicitly authorized use - only the automatic
    invocation from run() is removed."""

    def _run_minimal_startup(self):
        acquired = SimpleNamespace(
            provider_readiness={"codex": {"available": True}},
            as_dict=lambda: {},
        )
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.conversation.default_state_root", return_value=state_dir,
            ), mock.patch(
                "tools.konoha_v4.conversation.CapabilityRegistry", return_value=mock.Mock(),
            ), mock.patch(
                "tools.konoha_v4.conversation.acquire_context", return_value=acquired,
            ) as acquire_mock, mock.patch(
                "tools.konoha_v4.source_monitor.start_scan",
            ) as scan_mock, mock.patch(
                "tools.konoha_v4.conversation._read_turn", side_effect=["salir"],
            ) as read_turn_mock:
                exit_code = run(Path("."))
        return exit_code, acquire_mock, scan_mock, read_turn_mock

    def test_startup_does_not_invoke_source_scan(self):
        # Test A: patches the real source_monitor.start_scan entry point
        # (not a conversation-local alias) so this fails immediately if
        # startup ever triggers a source scan again, by any route.
        _, _, scan_mock, _ = self._run_minimal_startup()
        scan_mock.assert_not_called()

    def test_conversation_module_no_longer_binds_start_scan(self):
        import tools.konoha_v4.conversation as conversation_module
        self.assertFalse(hasattr(conversation_module, "start_scan"))

    def test_startup_still_acquires_public_context(self):
        # Test B
        _, acquire_mock, _, _ = self._run_minimal_startup()
        acquire_mock.assert_called_once()

    def test_startup_still_reaches_mission_input(self):
        # Test C: not a full provider-execution test - just proves the
        # conversation reaches _read_turn() and exits cleanly on "salir".
        exit_code, _, _, read_turn_mock = self._run_minimal_startup()
        read_turn_mock.assert_called_once()
        self.assertEqual(exit_code, 0)


class ResumeMissionTests(unittest.TestCase):
    def test_resume_mission_delegates_and_maps_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch("tools.konoha_v4.conversation.default_state_root", return_value=state_dir), \
                 mock.patch("tools.konoha_v4.conversation.CapabilityRegistry", return_value=mock.Mock()), \
                 mock.patch(
                     "tools.konoha_v4.conversation._run_resumable_execution",
                     return_value="completed",
                 ) as run_mock:
                exit_code = resume_mission(Path("."), "mission-conv-test")
        run_mock.assert_called_once()
        self.assertEqual(exit_code, 0)

    def test_resume_mission_paused_maps_to_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch("tools.konoha_v4.conversation.default_state_root", return_value=state_dir), \
                 mock.patch("tools.konoha_v4.conversation.CapabilityRegistry", return_value=mock.Mock()), \
                 mock.patch(
                     "tools.konoha_v4.conversation._run_resumable_execution",
                     return_value="paused",
                 ):
                exit_code = resume_mission(Path("."), "mission-conv-test")
        self.assertEqual(exit_code, 0)

    def test_resume_mission_failed_maps_to_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch("tools.konoha_v4.conversation.default_state_root", return_value=state_dir), \
                 mock.patch("tools.konoha_v4.conversation.CapabilityRegistry", return_value=mock.Mock()), \
                 mock.patch(
                     "tools.konoha_v4.conversation._run_resumable_execution",
                     return_value="failed",
                 ):
                exit_code = resume_mission(Path("."), "mission-conv-test")
        self.assertEqual(exit_code, 1)


class RunTopLevelExitCommandTests(unittest.TestCase):
    """KRR-411A: run()'s top-level mission prompt must exit on every
    canonical _EXIT_COMMANDS control, not a narrower duplicated set."""

    def _run_with_input(self, mission_text):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            acquired = SimpleNamespace(provider_readiness={}, as_dict=lambda: {})
            with mock.patch("tools.konoha_v4.conversation.default_state_root", return_value=state_dir), \
                 mock.patch("tools.konoha_v4.conversation.CapabilityRegistry", return_value=mock.Mock()), \
                 mock.patch("tools.konoha_v4.conversation.acquire_context", return_value=acquired), \
                 mock.patch("tools.konoha_v4.conversation._read_turn", return_value=mission_text), \
                 mock.patch("tools.konoha_v4.conversation._build_validated_plan") as build_mock, \
                 mock.patch("tools.konoha_v4.conversation._run_resumable_execution") as execute_mock, \
                 contextlib.redirect_stdout(io.StringIO()):
                exit_code = run(Path("."))
        return exit_code, build_mock, execute_mock

    def test_every_canonical_exit_command_exits_cleanly_without_planning_or_execution(self):
        for exit_command in sorted(_EXIT_COMMANDS):
            with self.subTest(exit_command=exit_command):
                exit_code, build_mock, execute_mock = self._run_with_input(exit_command)
                self.assertEqual(exit_code, 0)
                build_mock.assert_not_called()
                execute_mock.assert_not_called()

    def test_every_canonical_exit_command_case_insensitive(self):
        for exit_command in sorted(_EXIT_COMMANDS):
            with self.subTest(exit_command=exit_command):
                exit_code, build_mock, execute_mock = self._run_with_input(exit_command.upper())
                self.assertEqual(exit_code, 0)
                build_mock.assert_not_called()
                execute_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
