from __future__ import annotations

import dataclasses
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools.konoha_v4.executor import (
    ASSIGNMENT_RESULT_SCHEMA_PATH,
    GitStatusError,
    _git_status,
    _validate_assignment_result_payload,
    _validate_assignment_result_rules,
    execute_or_resume_plan,
    execute_plan,
    expected_approval_command,
    plan_identity,
    _task_prompt,
)
from tools.konoha_v4.hokage import validate_plan
from tools.konoha_v4.models import AgentAssignment, AssignmentApproval, MissionPlan


def _assignment(task_id: str = "t1", execution_gate: str = "plan_approval", **overrides) -> AgentAssignment:
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


def _approval_dict(status: str) -> dict:
    return {
        "status": status,
        "approved_by": "human" if status == "approved" else None,
        "approved_at": "2026-07-21T00:00:00Z" if status == "approved" else None,
        "feedback": None,
    }


def _plan(assignments: list[AgentAssignment], approval_status: str = "approved", **overrides) -> MissionPlan:
    fields = dict(
        mission_id="mission-outcome-test",
        understanding="Validar el contrato estructurado de resultado.",
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


def _write_plan(state_dir: Path, plan: MissionPlan) -> None:
    mission_dir = state_dir / "missions" / plan.mission_id
    mission_dir.mkdir(parents=True, exist_ok=True)
    (mission_dir / "plan.json").write_text(
        json.dumps(dataclasses.asdict(plan), ensure_ascii=False, indent=2), encoding="utf-8",
    )


def _execution_state_path(state_dir: Path, mission_id: str) -> Path:
    return state_dir / "missions" / mission_id / "execution_state.json"


def _persisted_state(state_dir: Path, mission_id: str) -> dict:
    return json.loads(_execution_state_path(state_dir, mission_id).read_text(encoding="utf-8"))


class _Registry:
    def agent_family(self, family: str) -> dict:
        return {"allowed_task_patterns": ["read-only inspection"]}

    def model_allowed(self, provider: str, model: str, family: str) -> bool:
        return True


def _result_text(
    outcome: str,
    objective_satisfied: bool,
    *,
    summary: str = "ok",
    diagnostic: str | None = None,
    evidence: list | None = None,
    review_outcome: str | None = None,
) -> str:
    return json.dumps({
        "outcome": outcome,
        "objective_satisfied": objective_satisfied,
        "summary": summary,
        "diagnostic": diagnostic,
        "evidence": evidence if evidence is not None else [],
        "review_outcome": review_outcome,
    })


def _patched_invoke(text: str = None, side_effect=None):
    if side_effect is not None:
        return mock.patch("tools.konoha_v4.executor.invoke", side_effect=side_effect)
    return mock.patch(
        "tools.konoha_v4.executor.invoke",
        return_value=SimpleNamespace(text=text, usage={"input": 1, "output": 1}, command=["codex"]),
    )


def _patched_git_status(return_value: str = ""):
    return mock.patch("tools.konoha_v4.executor._git_status", return_value=return_value)


def _approval_for(state, task_id: str = "t1") -> AssignmentApproval:
    text = expected_approval_command(
        state.mission_id, state.pending_task_id, state.plan_identity, state.approval_nonce,
    )
    return AssignmentApproval(
        mission_id=state.mission_id, task_id=task_id,
        execution_gate="separate_human_approval",
        plan_identity=state.plan_identity, approval_nonce=state.approval_nonce,
        approval_text=text, approval_source="interactive_terminal",
        approved_at="2026-07-21T00:05:00Z",
    )


_COMPLETED_TEXT = _result_text("completed", True)


class OutcomeMappingTests(unittest.TestCase):
    def test_outcome_blocked_blocks_mission(self):
        task = _assignment(task_id="t1")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            text = _result_text("blocked", False)
            with _patched_invoke(text) as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.state.status, "blocked")
            self.assertEqual(attempt.diagnostic, "blocked")
            self.assertEqual(_persisted_state(state_dir, plan.mission_id)["diagnostic"], "blocked")

    def test_outcome_changes_requested_blocks_mission(self):
        task = _assignment(task_id="t1")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            text = _result_text("changes_requested", False)
            with _patched_invoke(text) as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.state.status, "blocked")
            self.assertEqual(attempt.diagnostic, "changes_requested")
            raw = _persisted_state(state_dir, plan.mission_id)
            self.assertEqual(raw["diagnostic"], "changes_requested")
            self.assertEqual(raw["status"], "blocked")

    def test_outcome_failed_produces_assignment_failed_diagnostic(self):
        task = _assignment(task_id="t1")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            text = _result_text("failed", False, review_outcome=None)
            with _patched_invoke(text) as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.evidence[0].status, "failed")
            self.assertEqual(attempt.state.status, "failed")
            self.assertEqual(attempt.diagnostic, "assignment_failed")
            self.assertEqual(_persisted_state(state_dir, plan.mission_id)["diagnostic"], "assignment_failed")

    def test_completed_outcome_with_objective_not_satisfied_fails(self):
        task = _assignment(task_id="t1")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            text = _result_text("completed", False)
            with _patched_invoke(text) as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.state.status, "failed")
            self.assertEqual(attempt.diagnostic, "contradictory_result_fields")

    def test_completed_with_review_outcome_blocked_is_contradiction(self):
        task = _assignment(task_id="t1")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            text = _result_text("completed", True, review_outcome="blocked")
            with _patched_invoke(text) as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.state.status, "failed")
            self.assertEqual(attempt.diagnostic, "contradictory_result_fields")

    def test_invalid_json_fails(self):
        task = _assignment(task_id="t1")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke("not json") as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.state.status, "failed")
            self.assertEqual(attempt.diagnostic, "invalid_result_json")
            self.assertEqual(_persisted_state(state_dir, plan.mission_id)["diagnostic"], "invalid_result_json")

    def test_invalid_schema_fails(self):
        task = _assignment(task_id="t1")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            text = json.dumps({"outcome": "completed"})
            with _patched_invoke(text) as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.state.status, "failed")
            self.assertEqual(attempt.diagnostic, "invalid_result_schema")
            self.assertEqual(_persisted_state(state_dir, plan.mission_id)["diagnostic"], "invalid_result_schema")

    def test_process_failure_fails(self):
        task = _assignment(task_id="t1")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(side_effect=RuntimeError("boom")) as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.state.status, "failed")
            self.assertEqual(attempt.diagnostic, "process_error")
            self.assertEqual(_persisted_state(state_dir, plan.mission_id)["diagnostic"], "process_error")

    def test_completed_valid_preserves_normal_progress(self):
        t1 = _assignment(task_id="t1")
        t2 = _assignment(task_id="t2")
        plan = _plan([t1, t2])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(_COMPLETED_TEXT) as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.state.status, "in_progress")
            self.assertEqual(attempt.diagnostic, "completed")

            with _patched_invoke(_COMPLETED_TEXT) as invoke_mock2, _patched_git_status():
                attempt2 = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock2.assert_called_once()
            self.assertEqual(attempt2.state.status, "completed")

    def test_second_assignment_not_invoked_after_blocked(self):
        t1 = _assignment(task_id="t1")
        t2 = _assignment(task_id="t2")
        plan = _plan([t1, t2])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(_result_text("blocked", False)) as invoke_mock, _patched_git_status():
                execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()

            with _patched_invoke(_COMPLETED_TEXT) as invoke_mock2, _patched_git_status():
                attempt2 = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock2.assert_not_called()
            self.assertEqual(attempt2.diagnostic, "non_resumable_status:blocked")

    def test_second_assignment_not_invoked_after_failed(self):
        t1 = _assignment(task_id="t1")
        t2 = _assignment(task_id="t2")
        plan = _plan([t1, t2])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke("not json") as invoke_mock, _patched_git_status():
                execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()

            with _patched_invoke(_COMPLETED_TEXT) as invoke_mock2, _patched_git_status():
                attempt2 = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock2.assert_not_called()
            self.assertEqual(attempt2.diagnostic, "non_resumable_status:failed")


class UnhashableEnumFieldTests(unittest.TestCase):
    """payload comes from untrusted json.loads() output - outcome/
    review_outcome must never reach `in <set>` before an isinstance(str)
    check, or an unhashable list/dict value raises TypeError instead of
    failing closed."""

    def _base_payload(self, **overrides) -> dict:
        payload = {
            "outcome": "completed",
            "objective_satisfied": True,
            "summary": "ok",
            "diagnostic": None,
            "evidence": [],
            "review_outcome": None,
        }
        payload.update(overrides)
        return payload

    def test_outcome_list_fails_closed_pure(self):
        self.assertEqual(
            _validate_assignment_result_payload(self._base_payload(outcome=[])),
            "invalid_result_schema",
        )

    def test_outcome_dict_fails_closed_pure(self):
        self.assertEqual(
            _validate_assignment_result_payload(self._base_payload(outcome={})),
            "invalid_result_schema",
        )

    def test_review_outcome_list_fails_closed_pure(self):
        self.assertEqual(
            _validate_assignment_result_payload(self._base_payload(review_outcome=[])),
            "invalid_result_schema",
        )

    def test_review_outcome_dict_fails_closed_pure(self):
        self.assertEqual(
            _validate_assignment_result_payload(self._base_payload(review_outcome={})),
            "invalid_result_schema",
        )

    def _assert_end_to_end_fails_closed(self, payload_overrides: dict):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task], approval_status="approved")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            text = json.dumps(self._base_payload(**payload_overrides))
            with _patched_invoke(text) as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.state.status, "failed")
            self.assertNotEqual(attempt.state.status, "recovery_required")
            self.assertEqual(attempt.diagnostic, "invalid_result_schema")
            self.assertEqual(
                _persisted_state(state_dir, plan.mission_id)["diagnostic"], "invalid_result_schema",
            )

    def test_outcome_list_end_to_end(self):
        self._assert_end_to_end_fails_closed({"outcome": []})

    def test_outcome_dict_end_to_end(self):
        self._assert_end_to_end_fails_closed({"outcome": {}})

    def test_review_outcome_list_end_to_end(self):
        self._assert_end_to_end_fails_closed({"review_outcome": []})

    def test_review_outcome_dict_end_to_end(self):
        self._assert_end_to_end_fails_closed({"review_outcome": {}})


class JouninReviewContractTests(unittest.TestCase):
    def _run(self, text: str):
        task = _assignment(task_id="t1", family="jounin-review")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(text) as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            raw = _persisted_state(state_dir, plan.mission_id)
            return attempt, invoke_mock, raw

    def test_jounin_blocked_review_with_outcome_failed_is_contradiction(self):
        text = _result_text("failed", False, review_outcome="blocked")
        attempt, invoke_mock, raw = self._run(text)
        invoke_mock.assert_called_once()
        self.assertEqual(attempt.state.status, "failed")
        self.assertEqual(attempt.diagnostic, "contradictory_result_fields")

    def test_jounin_changes_requested_review_with_outcome_blocked_is_contradiction(self):
        text = _result_text("blocked", False, review_outcome="changes_requested")
        attempt, invoke_mock, raw = self._run(text)
        invoke_mock.assert_called_once()
        self.assertEqual(attempt.state.status, "failed")
        self.assertEqual(attempt.diagnostic, "contradictory_result_fields")

    def test_jounin_with_null_review_outcome_is_contradiction(self):
        text = _result_text("completed", True, review_outcome=None)
        attempt, invoke_mock, raw = self._run(text)
        invoke_mock.assert_called_once()
        self.assertEqual(attempt.state.status, "failed")
        self.assertEqual(attempt.diagnostic, "contradictory_result_fields")

    def test_non_jounin_with_non_null_review_outcome_is_contradiction(self):
        task = _assignment(task_id="t1", family="repository-auditor")
        plan = _plan([task])
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            text = _result_text("completed", True, review_outcome="approved")
            with _patched_invoke(text) as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.state.status, "failed")
            self.assertEqual(attempt.diagnostic, "contradictory_result_fields")

    def test_jounin_approved_with_notes_and_completed_is_valid(self):
        text = _result_text("completed", True, review_outcome="approved_with_notes")
        attempt, invoke_mock, raw = self._run(text)
        invoke_mock.assert_called_once()
        self.assertEqual(attempt.state.status, "completed")
        self.assertEqual(attempt.diagnostic, "completed")

    def test_jounin_blocked_review_with_outcome_blocked_is_valid(self):
        text = _result_text("blocked", False, review_outcome="blocked")
        attempt, invoke_mock, raw = self._run(text)
        invoke_mock.assert_called_once()
        self.assertEqual(attempt.state.status, "blocked")
        self.assertEqual(attempt.diagnostic, "blocked")
        self.assertEqual(raw["diagnostic"], "blocked")

    def test_jounin_changes_requested_review_with_outcome_changes_requested_is_valid(self):
        text = _result_text("changes_requested", False, review_outcome="changes_requested")
        attempt, invoke_mock, raw = self._run(text)
        invoke_mock.assert_called_once()
        self.assertEqual(attempt.state.status, "blocked")
        self.assertEqual(attempt.diagnostic, "changes_requested")
        self.assertEqual(raw["diagnostic"], "changes_requested")

    def test_validate_assignment_result_rules_directly_for_jounin_matrix(self):
        # Fast, direct coverage of the pure rule function alongside the
        # end-to-end assertions above.
        valid = {
            "outcome": "blocked", "objective_satisfied": False,
            "summary": "x", "diagnostic": None, "evidence": [],
            "review_outcome": "blocked",
        }
        self.assertIsNone(_validate_assignment_result_rules(valid, "jounin-review"))

        contradiction = dict(valid, outcome="changes_requested")
        self.assertEqual(
            _validate_assignment_result_rules(contradiction, "jounin-review"),
            "contradictory_result_fields",
        )


class MutationRejectionTests(unittest.TestCase):
    def test_mutation_rejected_before_invoke_plan_approval(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval", mutation=True)
        plan = _plan([task], approval_status="approved")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(_COMPLETED_TEXT) as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_not_called()
            self.assertEqual(attempt.state.status, "blocked")
            self.assertEqual(attempt.diagnostic, "mutation_runtime_not_supported")

    def test_separate_approval_does_not_bypass_mutation_rejection(self):
        task = _assignment(task_id="t1", execution_gate="separate_human_approval", mutation=True)
        plan = _plan([task], approval_status="approved")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)

            approval = AssignmentApproval(
                mission_id=plan.mission_id,
                task_id="t1",
                execution_gate="separate_human_approval",
                plan_identity=plan_identity(plan),
                approval_nonce="0" * 32,
                approval_text=expected_approval_command(plan.mission_id, "t1", plan_identity(plan), "0" * 32),
                approval_source="interactive_terminal",
                approved_at="2026-07-21T00:05:00Z",
            )
            with _patched_invoke(_COMPLETED_TEXT) as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(
                    Path("."), state_dir, plan.mission_id, _Registry(), approval=approval,
                )
            invoke_mock.assert_not_called()
            self.assertEqual(attempt.state.status, "blocked")
            self.assertEqual(attempt.diagnostic, "mutation_runtime_not_supported")
            self.assertEqual(attempt.state.consumed_approval_ids, [])


class HokageMutationValidationTests(unittest.TestCase):
    def test_mutation_rejected_even_when_boundary_is_declared(self):
        task = _assignment(task_id="t1", mutation=True)
        plan = _plan([task], approval_status="pending", approval_boundaries=["mutation"])
        problems = validate_plan(plan, _Registry())
        matches = [p for p in problems if "mutation_runtime_not_supported" in p]
        self.assertEqual(len(matches), 1)
        self.assertIn("t1", matches[0])


class GitStatusRuntimeTests(unittest.TestCase):
    def test_baseline_failure_before_executing_is_failed_not_recovery_required(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task], approval_status="approved")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(_COMPLETED_TEXT) as invoke_mock, \
                 mock.patch(
                     "tools.konoha_v4.executor._git_status",
                     side_effect=GitStatusError("git_status_timeout"),
                 ):
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_not_called()
            self.assertEqual(attempt.state.status, "failed")
            self.assertEqual(attempt.diagnostic, "git_status_timeout")
            self.assertNotEqual(attempt.state.status, "recovery_required")
            self.assertEqual(_persisted_state(state_dir, plan.mission_id)["status"], "failed")

    def test_baseline_failure_with_separate_approval_does_not_consume_it(self):
        task = _assignment(task_id="t1", execution_gate="separate_human_approval")
        plan = _plan([task], approval_status="approved")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(_COMPLETED_TEXT), _patched_git_status():
                waiting = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            approval = _approval_for(waiting.state)
            with _patched_invoke(_COMPLETED_TEXT) as invoke_mock, \
                 mock.patch(
                     "tools.konoha_v4.executor._git_status",
                     side_effect=GitStatusError("git_status_failed"),
                 ):
                attempt = execute_or_resume_plan(
                    Path("."), state_dir, plan.mission_id, _Registry(), approval=approval,
                )
            invoke_mock.assert_not_called()
            self.assertEqual(attempt.state.status, "failed")
            self.assertEqual(attempt.diagnostic, "git_status_failed")
            self.assertEqual(attempt.state.consumed_approval_ids, [])

    def test_post_invoke_git_timeout_produces_failed_evidence_not_exception(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task], approval_status="approved")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(_COMPLETED_TEXT) as invoke_mock, \
                 mock.patch(
                     "tools.konoha_v4.executor._git_status",
                     side_effect=["", GitStatusError("git_status_timeout")],
                 ):
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.state.status, "failed")
            self.assertEqual(attempt.diagnostic, "git_status_timeout")
            self.assertEqual(len(attempt.evidence), 1)
            self.assertEqual(attempt.evidence[0].status, "failed")
            self.assertEqual(_persisted_state(state_dir, plan.mission_id)["diagnostic"], "git_status_timeout")

    def test_post_invoke_git_failed_produces_failed_evidence_not_exception(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task], approval_status="approved")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            _write_plan(state_dir, plan)
            with _patched_invoke(_COMPLETED_TEXT) as invoke_mock, \
                 mock.patch(
                     "tools.konoha_v4.executor._git_status",
                     side_effect=["", GitStatusError("git_status_failed")],
                 ):
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            invoke_mock.assert_called_once()
            self.assertEqual(attempt.state.status, "failed")
            self.assertEqual(attempt.diagnostic, "git_status_failed")
            self.assertEqual(len(attempt.evidence), 1)
            self.assertEqual(attempt.evidence[0].status, "failed")
            self.assertEqual(_persisted_state(state_dir, plan.mission_id)["diagnostic"], "git_status_failed")

    def test_git_status_succeeds_within_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cp = subprocess.CompletedProcess(args=["git"], returncode=0, stdout="", stderr="")
            with mock.patch("tools.konoha_v4.executor.subprocess.run", return_value=cp) as run_mock:
                result = _git_status(repo)
            self.assertEqual(result, "")
            run_mock.assert_called_once()
            args, kwargs = run_mock.call_args
            command = args[0]
            self.assertIn("-c", command)
            self.assertIn("core.fsmonitor=false", command)
            self.assertIn("--short", command)
            self.assertIn("--untracked-files=all", command)
            self.assertGreaterEqual(kwargs.get("timeout"), 120)
            self.assertEqual(kwargs.get("env", {}).get("GIT_OPTIONAL_LOCKS"), "0")

    def test_git_status_timeout_raises_git_status_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with mock.patch(
                "tools.konoha_v4.executor.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd=["git"], timeout=120),
            ):
                with self.assertRaises(GitStatusError) as cm:
                    _git_status(repo)
            self.assertEqual(cm.exception.diagnostic, "git_status_timeout")

    def test_git_status_nonzero_return_code_raises_git_status_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            cp = subprocess.CompletedProcess(
                args=["git"],
                returncode=1,
                stdout="",
                stderr="fatal: boom",
            )
            with mock.patch(
                "tools.konoha_v4.executor.subprocess.run",
                return_value=cp,
            ):
                with self.assertRaises(GitStatusError) as cm:
                    _git_status(repo)
            self.assertEqual(cm.exception.diagnostic, "git_status_failed")


class SchemaOwnershipTests(unittest.TestCase):
    def test_schema_resolves_to_konoha_installation_not_target_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            external_repo = Path(tmp) / "external-public-repo"
            external_repo.mkdir()
            self.assertFalse((external_repo / "schemas").exists())

            task = _assignment(task_id="t1", execution_gate="plan_approval")
            plan = _plan([task], approval_status="approved")
            state_dir = Path(tmp) / "state"
            _write_plan(state_dir, plan)

            with mock.patch(
                "tools.konoha_v4.executor.invoke",
                return_value=SimpleNamespace(text=_COMPLETED_TEXT, usage={}, command=["codex"]),
            ) as invoke_mock, _patched_git_status():
                attempt = execute_or_resume_plan(external_repo, state_dir, plan.mission_id, _Registry())

            invoke_mock.assert_called_once()
            _, kwargs = invoke_mock.call_args
            schema_arg = kwargs["schema"]
            self.assertEqual(schema_arg, ASSIGNMENT_RESULT_SCHEMA_PATH)
            self.assertTrue(schema_arg.is_file())
            self.assertNotIn(str(external_repo), str(schema_arg))
            self.assertEqual(attempt.state.status, "completed")


class ExecutePlanLegacyMutationAndGitTests(unittest.TestCase):
    def test_mutation_on_first_task_stops_with_single_blocked_evidence(self):
        t1 = _assignment(task_id="t1", execution_gate="plan_approval", mutation=True)
        t2 = _assignment(task_id="t2", execution_gate="plan_approval")
        plan = _plan([t1, t2], approval_status="approved")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with _patched_invoke(_COMPLETED_TEXT) as invoke_mock, _patched_git_status():
                evidence = execute_plan(Path("."), plan, _Registry(), state_dir)
            invoke_mock.assert_not_called()
            self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0].task_id, "t1")
            self.assertEqual(evidence[0].status, "blocked")
            self.assertIn("mutation_runtime_not_supported", evidence[0].output)

    def test_git_baseline_failure_produces_exactly_one_failed_evidence(self):
        t1 = _assignment(task_id="t1", execution_gate="plan_approval")
        t2 = _assignment(task_id="t2", execution_gate="plan_approval")
        plan = _plan([t1, t2], approval_status="approved")
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with _patched_invoke(_COMPLETED_TEXT) as invoke_mock, \
                 mock.patch(
                     "tools.konoha_v4.executor._git_status",
                     side_effect=GitStatusError("git_status_failed"),
                 ):
                evidence = execute_plan(Path("."), plan, _Registry(), state_dir)
            invoke_mock.assert_not_called()
            self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0].task_id, "t1")
            self.assertEqual(evidence[0].status, "failed")
            self.assertIn("git_status_failed", evidence[0].output)


class TaskPromptContractTests(unittest.TestCase):
    def _prompt(self):
        task = _assignment(task_id="t1")
        plan = _plan([task])
        return _task_prompt(Path("."), plan, task, {"allowed_task_patterns": ["x"]}, [])

    def test_prompt_no_longer_delegates_git_comparison_to_provider(self):
        payload = json.loads(self._prompt())
        rules_text = " ".join(payload["rules"])
        self.assertNotIn("Compará git status antes y después", rules_text)

    def test_prompt_states_git_integrity_belongs_to_runtime(self):
        payload = json.loads(self._prompt())
        rules_text = " ".join(payload["rules"])
        self.assertIn("La verificación de integridad Git antes/después pertenece al runtime.", rules_text)

    def test_prompt_requires_six_key_json_contract(self):
        payload = json.loads(self._prompt())
        rules_text = " ".join(payload["rules"])
        self.assertIn(
            "outcome, objective_satisfied, summary, diagnostic, evidence, review_outcome",
            rules_text,
        )

    def test_prompt_states_jounin_review_contextual_rule(self):
        payload = json.loads(self._prompt())
        rules_text = " ".join(payload["rules"])
        self.assertIn("jounin-review", rules_text)


if __name__ == "__main__":
    unittest.main()
