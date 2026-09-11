from __future__ import annotations

from dataclasses import dataclass, field
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools.konoha_v4.conversation import (
    MAX_PLAN_ATTEMPTS,
    _SESSION_EXIT,
    _approval_loop,
    _confirm_feedback,
    _read_approval_input,
    _read_plan_challenge_grant,
)
from tools.konoha_v4.executor import plan_identity as _plan_identity
from tools.konoha_v4.models import AgentAssignment, MissionPlan


@dataclass
class FakePlan:
    mission_id: str
    plan_hash: str
    approval: dict = field(default_factory=lambda: {
        "status": "pending",
        "approved_by": None,
        "approved_at": None,
        "feedback": None,
    })
    missing_context: list = field(default_factory=list)
    assignments: list = field(default_factory=list)


def _real_plan(mission_id: str = "mission-real", **overrides) -> MissionPlan:
    """A real, sealed MissionPlan - needed wherever plan_identity() is
    exercised for real, since FakePlan above isn't shaped for it
    (plan_identity() calls asdict(plan) and reads mission_constraints)."""
    fields = dict(
        mission_id=mission_id,
        understanding="Validar el desafío de aprobación.",
        explicit_facts=[],
        missing_context=[],
        assumptions_prohibited=[],
        complexity="low",
        assignments=[
            AgentAssignment(
                task_id="t1",
                family="repository-auditor",
                provider="codex",
                model="codex",
                objective="Inspeccionar sin mutar.",
                inputs=["tools/konoha_v4"],
                expected_output="Evidencia verificable.",
                estimated_input_tokens=10,
                estimated_output_tokens=5,
                estimated_total_tokens=15,
                execution_gate="plan_approval",
            )
        ],
        acceptance_criteria=["done"],
        approval_boundaries=["read_only", "mutation", "network", "private_context"],
        estimated_tokens=15,
        estimated_cost_class="low",
        rationale="test",
    )
    fields.update(overrides)
    return MissionPlan(**fields).seal()


# --- A/G/H/L: _approval_loop-level behavior --------------------------------


class ApprovalInputStabilizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(".")
        self.registry = Mock()
        self.plan = FakePlan("mission-1", "plan-1")
        self.replanned = FakePlan("mission-1", "plan-2")
        self.store = Mock()
        self.store.planner_context.return_value = {"mission_id": "mission-1"}
        self.store.validate_replanned_plan.return_value = []
        # _approval_loop's human-requested-replan path reads
        # continuity.state.requested_changes_history to build
        # mission_authority_texts (v4.0.1) - a bare Mock() attribute isn't
        # iterable, so it must be a real list here.
        self.store.state.requested_changes_history = []

    def common(self):
        return (
            patch(
                "tools.konoha_v4.conversation.MissionContinuityStore.create",
                return_value=self.store,
            ),
            patch(
                "tools.konoha_v4.conversation._repo_state",
                return_value={"branch": "test", "head": "abc", "status": ""},
            ),
            patch(
                "tools.konoha_v4.conversation.approval_summary",
                return_value="VISIBLE PLAN",
            ),
            patch("tools.konoha_v4.conversation._persist_plan"),
        )

    # --- A: free-form approval input preservation --------------------------

    def test_multiline_feedback_uses_first_line_and_fin(self) -> None:
        with patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value="Primera regla.",
        ), patch(
            "tools.konoha_v4.conversation._read_feedback_from_first_line",
            return_value=("Primera regla.\nSegunda regla.", False),
        ):
            self.assertEqual(
                _read_approval_input(),
                ("feedback", "Primera regla.\nSegunda regla."),
            )

    def test_single_line_cambio_prefix(self) -> None:
        with patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value="cambio: Jounin debe ser independiente.",
        ):
            self.assertEqual(
                _read_approval_input(),
                ("feedback", "Jounin debe ser independiente."),
            )

    def test_exit_is_never_feedback(self) -> None:
        with patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value="salir",
        ):
            self.assertEqual(_read_approval_input(), ("exit", None))

    def test_feedback_first_line_is_not_pre_stripped(self) -> None:
        # BLOCK_4 human-content-preservation contract: a first line that
        # falls through to free-form feedback content must reach
        # _read_feedback_from_first_line exactly as read - unstripped -
        # proving read_exact_line, not read_line, is what backs this path
        # and that no old read_line-based content destruction remains.
        # Control-word matching (the "sí"/"no"/"cambios"/exit checks
        # above) still normalizes its own separate copy internally; this
        # only asserts what reaches the content path.
        with patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value="  indented feedback line  ",
        ), patch(
            "tools.konoha_v4.conversation._read_feedback_from_first_line",
        ) as feedback_mock:
            feedback_mock.return_value = ("  indented feedback line  ", False)
            _read_approval_input()
        feedback_mock.assert_called_once_with("  indented feedback line  ")

    def test_exit_does_not_invoke_or_record(self) -> None:
        create, state, summary, persist = self.common()
        with tempfile.TemporaryDirectory() as tmp, create, state, summary, persist, \
             patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 return_value=("exit", None),
             ), \
             patch("tools.konoha_v4.conversation.build_plan") as build:
            result = _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry
            )
        self.assertIs(result, _SESSION_EXIT)
        build.assert_not_called()
        self.store.record_requested_change.assert_not_called()

    def test_empty_input_does_not_invoke_provider_or_rerender(self) -> None:
        create, state, summary, persist = self.common()
        with tempfile.TemporaryDirectory() as tmp, create, state, summary as show, persist, \
             patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 side_effect=[("pending", None), ("decision", "no")],
             ), \
             patch("tools.konoha_v4.conversation.build_plan") as build:
            result = _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry
            )
        self.assertIsNone(result)
        build.assert_not_called()
        self.assertEqual(show.call_count, 1)

    # --- M: ambiguous "ok" --------------------------------------------------

    def test_ambiguous_ok_leaves_plan_pending_and_requires_explicit_decision(self) -> None:
        # BLOCK_4 FINDING #17: a standalone "ok" decision must neither
        # approve the plan nor be treated as requested changes - it stays
        # pending and Konoha asks again, exactly like classify_approval("ok").
        create, state, summary, persist = self.common()
        with tempfile.TemporaryDirectory() as tmp, create, state, summary as show, persist, \
             patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 side_effect=[("decision", "ok"), ("decision", "no")],
             ), \
             patch("tools.konoha_v4.conversation.build_plan") as build:
            result = _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry
            )
        self.assertIsNone(result)
        build.assert_not_called()
        self.store.record_requested_change.assert_not_called()
        self.assertEqual(show.call_count, 1)

    # --- N: cancelled feedback fail-closed ----------------------------------

    def test_cancelled_feedback_does_not_invoke_or_record(self) -> None:
        create, state, summary, persist = self.common()
        with tempfile.TemporaryDirectory() as tmp, create, state, summary, persist, \
             patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 side_effect=[
                     ("feedback", "change"),
                     ("decision", "no"),
                 ],
             ), \
             patch(
                 "tools.konoha_v4.conversation._confirm_feedback",
                 return_value=False,
             ), \
             patch("tools.konoha_v4.conversation.build_plan") as build:
            _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry
            )
        build.assert_not_called()
        self.store.record_requested_change.assert_not_called()

    # --- F: exact requested-change persistence ------------------------------

    def test_confirmed_multiline_records_exact_text_once(self) -> None:
        feedback = "Primera regla.\nSegunda regla."
        create, state, summary, persist = self.common()
        with tempfile.TemporaryDirectory() as tmp, create, state, summary as show, persist, \
             patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 side_effect=[
                     ("feedback", feedback),
                     ("decision", "no"),
                 ],
             ), \
             patch(
                 "tools.konoha_v4.conversation._confirm_feedback",
                 return_value=True,
             ), \
             patch(
                 "tools.konoha_v4.conversation.build_plan",
                 return_value=self.replanned,
             ) as build, \
             patch(
                 "tools.konoha_v4.conversation.validate_plan",
                 return_value=[],
             ):
            _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry
            )
        # record_requested_change receives exactly the intended feedback
        # text, exactly once, with no prior-turn tail/prefix - the mocked
        # _read_approval_input side_effect is the only source of that
        # string, so any contamination would show up as an inequality
        # here rather than needing private-state inspection.
        build.assert_called_once()
        self.assertEqual(build.call_args.kwargs["feedback"], feedback)
        self.store.record_requested_change.assert_called_once_with(
            feedback, self.plan
        )
        self.assertEqual(show.call_count, 2)

    # --- O: readiness snapshot propagation ----------------------------------

    def test_human_requested_replan_propagates_same_readiness_snapshot(self) -> None:
        # BLOCK_4 FINDING #16 Test G: the validate_plan() call after
        # build_plan() in a human-requested replan must receive the exact
        # same provider_readiness object passed into _approval_loop() -
        # a human-requested replan must never bypass the readiness gate.
        readiness_sentinel = object()
        feedback = "Primera regla.\nSegunda regla."
        create, state, summary, persist = self.common()
        with tempfile.TemporaryDirectory() as tmp, create, state, summary, persist, patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 side_effect=[
                     ("feedback", feedback),
                     ("decision", "no"),
                 ],
             ), patch(
                 "tools.konoha_v4.conversation._confirm_feedback",
                 return_value=True,
             ), patch(
                 "tools.konoha_v4.conversation.build_plan",
                 return_value=self.replanned,
             ), patch(
                 "tools.konoha_v4.conversation.validate_plan",
                 return_value=[],
             ) as validate_plan_mock:
            _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry,
                provider_readiness=readiness_sentinel,
            )
        validate_plan_mock.assert_called_once()
        self.assertIs(
            validate_plan_mock.call_args.kwargs["provider_readiness"], readiness_sentinel,
        )

    # --- P: human replan corrective-retry recording semantics --------------

    def test_human_replan_records_only_final_valid_candidate_as_revision(self) -> None:
        # v4.1.1: a human replan whose first candidate is deterministically
        # invalid must run the bounded corrective retry, record the invalid
        # candidate ONLY as validator-findings evidence (never as a plan
        # revision, and never double-recorded by _approval_loop), and
        # record_plan() only the final validated candidate, once, with
        # reason "human_requested_replan".
        create, state, summary, persist = self.common()
        invalid = FakePlan("mission-1", "plan-bad")
        valid = FakePlan("mission-1", "plan-good")
        with tempfile.TemporaryDirectory() as tmp, create, state, summary, persist, \
             patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 side_effect=[("feedback", "Codex primero."), ("decision", "no")],
             ), \
             patch(
                 "tools.konoha_v4.conversation._confirm_feedback",
                 return_value=True,
             ), \
             patch(
                 "tools.konoha_v4.conversation.build_plan",
                 side_effect=[invalid, valid],
             ), \
             patch(
                 "tools.konoha_v4.conversation.validate_plan",
                 side_effect=[
                     ["mission_constraint_source_not_authorized: mc-012"],
                     [],
                 ],
             ):
            result = _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry,
            )
        # the later explicit "no" rejects the corrected plan
        self.assertIsNone(result)
        reasons = [
            call.kwargs.get("reason")
            for call in self.store.record_plan.call_args_list
        ]
        self.assertEqual(
            reasons, ["initial_pending_approval", "human_requested_replan"],
        )
        human_replan_calls = [
            call for call in self.store.record_plan.call_args_list
            if call.kwargs.get("reason") == "human_requested_replan"
        ]
        self.assertEqual(len(human_replan_calls), 1)
        self.assertIs(human_replan_calls[0].args[0], valid)
        for call in self.store.record_plan.call_args_list:
            self.assertIsNot(call.args[0], invalid)
        # recorded once as deterministic evidence - not double-recorded
        self.store.record_validator_findings.assert_called_once_with(
            ["mission_constraint_source_not_authorized: mc-012"], plan=invalid,
        )

    def test_human_replan_exhaustion_fails_closed_and_records_findings(self) -> None:
        # v4.1.1: MAX_PLAN_ATTEMPTS still bounds a human replan. When every
        # attempt stays deterministically invalid the loop fails closed
        # (returns None, no execution), records each attempt's findings as
        # evidence, and never records a "human_requested_replan" revision.
        create, state, summary, persist = self.common()
        candidates = [
            FakePlan("mission-1", f"plan-{i}")
            for i in range(MAX_PLAN_ATTEMPTS)
        ]
        with tempfile.TemporaryDirectory() as tmp, create, state, summary, persist, \
             patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 side_effect=[("feedback", "Codex primero.")],
             ), \
             patch(
                 "tools.konoha_v4.conversation._confirm_feedback",
                 return_value=True,
             ), \
             patch(
                 "tools.konoha_v4.conversation.build_plan",
                 side_effect=candidates,
             ), \
             patch(
                 "tools.konoha_v4.conversation.validate_plan",
                 return_value=[
                     "mission_constraint_source_not_authorized: mc-013"
                 ],
             ):
            result = _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry,
            )
        self.assertIsNone(result)
        self.assertEqual(
            self.store.record_validator_findings.call_count, MAX_PLAN_ATTEMPTS,
        )
        reasons = [
            call.kwargs.get("reason")
            for call in self.store.record_plan.call_args_list
        ]
        self.assertEqual(reasons, ["initial_pending_approval"])
        self.assertNotIn("human_requested_replan", reasons)

    # --- G: "sí" is intention only, not authority ---------------------------

    def test_yes_approves_only_after_challenge_grant_succeeds(self) -> None:
        create, state, summary, persist = self.common()
        with tempfile.TemporaryDirectory() as tmp, create, state, summary, persist, \
             patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 return_value=("decision", "sí"),
             ), \
             patch(
                 "tools.konoha_v4.conversation._read_plan_challenge_grant",
                 return_value=True,
             ) as grant_mock, \
             patch("tools.konoha_v4.conversation.build_plan") as build:
            result = _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry
            )
        self.assertIs(result, self.plan)
        build.assert_not_called()
        grant_mock.assert_called_once()
        self.assertEqual(
            grant_mock.call_args.kwargs["command_verb"], "aprobar-plan",
        )
        self.assertEqual(self.plan.approval["status"], "approved")
        self.assertEqual(self.plan.approval["approved_by"], "human")
        self.store.record_approval.assert_called_once_with(
            "approved",
            approved_by="human",
            approved_at=self.plan.approval["approved_at"],
        )

    # --- H: failed plan challenge leaves the plan pending -------------------

    def test_failed_plan_challenge_does_not_approve_only_later_explicit_no_rejects(
        self,
    ) -> None:
        # An explicit "sí" is intention only. If the fresh, plan-bound
        # challenge that follows it is not satisfied exactly, the plan
        # must stay pending (never approved, never persisted as approved)
        # and the loop must continue to read a fresh decision - never
        # silently retry the SAME challenge or treat the mismatch as
        # feedback. The later explicit "no" is a separate, legitimate
        # recorded state transition (rejection), which is allowed to
        # happen and must be the ONLY thing ever recorded.
        create, state, summary, persist = self.common()
        with tempfile.TemporaryDirectory() as tmp, create, state, summary, persist, \
             patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 side_effect=[("decision", "sí"), ("decision", "no")],
             ), \
             patch(
                 "tools.konoha_v4.conversation._read_plan_challenge_grant",
                 return_value=False,
             ) as grant_mock, \
             patch("tools.konoha_v4.conversation.build_plan") as build:
            result = _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry
            )
        self.assertIsNone(result)
        build.assert_not_called()
        grant_mock.assert_called_once()
        self.assertEqual(self.plan.approval["status"], "rejected")
        self.assertIsNone(self.plan.approval["approved_by"])
        self.assertIsNone(self.plan.approval["approved_at"])
        # called_once_with("rejected") proves both that the legitimate
        # later rejection was recorded AND that no earlier
        # record_approval("approved") call ever happened - a second call
        # of any kind would fail the "once" cardinality.
        self.store.record_approval.assert_called_once_with("rejected")

    # --- L: plan-only acceptance never becomes execution approval ----------

    def test_plan_only_acceptance_uses_distinct_verb_and_grants_no_execution_authority(
        self,
    ) -> None:
        create, state, summary, persist = self.common()
        with tempfile.TemporaryDirectory() as tmp, create, state, summary, persist, \
             patch(
                 "tools.konoha_v4.conversation._read_approval_input",
                 return_value=("decision", "sí"),
             ), \
             patch(
                 "tools.konoha_v4.conversation._read_plan_challenge_grant",
                 return_value=True,
             ) as grant_mock, \
             patch("tools.konoha_v4.conversation.build_plan") as build:
            result = _approval_loop(
                self.repo, Path(tmp), "mission", self.plan, self.registry,
                plan_only=True,
            )
        self.assertIs(result, self.plan)
        build.assert_not_called()
        grant_mock.assert_called_once()
        self.assertEqual(
            grant_mock.call_args.kwargs["command_verb"], "aceptar-planificacion",
        )
        self.assertNotEqual(
            grant_mock.call_args.kwargs["command_verb"], "aprobar-plan",
        )
        # Constitutional invariant: acceptance-as-planning-artifact only -
        # approval.status is left exactly as build_plan() produced it, and
        # continuity never records an "approved" event, so no execution
        # authority is ever granted or persisted.
        self.assertEqual(self.plan.approval["status"], "pending")
        self.assertIsNone(self.plan.approval["approved_by"])
        self.assertIsNone(self.plan.approval["approved_at"])
        self.store.record_approval.assert_not_called()


# --- B/C/D/E: requested-change confirmation challenge -----------------------


class ConfirmFeedbackChallengeTests(unittest.TestCase):
    """_confirm_feedback's nonce is generated only after the
    requested-change block already ended at ':fin' (proven at the block
    level in test_terminal_input.py); these tests prove the confirmation
    grant itself."""

    def test_pre_pasted_si_after_fin_does_not_confirm(self) -> None:
        with patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value="sí",
        ):
            self.assertFalse(_confirm_feedback("candidate"))

    def test_stale_confirmation_command_does_not_confirm(self) -> None:
        with patch(
            "tools.konoha_v4.conversation.secrets.token_hex",
            return_value="c" * 32,
        ), patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value=":confirmar-cambios " + "d" * 32,
        ):
            self.assertFalse(_confirm_feedback("candidate"))

    def test_exact_fresh_confirmation_command_confirms(self) -> None:
        fixed_nonce = "e" * 32
        with patch(
            "tools.konoha_v4.conversation.secrets.token_hex",
            return_value=fixed_nonce,
        ), patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value=f":confirmar-cambios {fixed_nonce}",
        ):
            self.assertTrue(_confirm_feedback("candidate"))

    def test_eof_does_not_confirm(self) -> None:
        with patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value=None,
        ):
            self.assertFalse(_confirm_feedback("candidate"))

    def test_blank_does_not_confirm(self) -> None:
        with patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value="",
        ):
            self.assertFalse(_confirm_feedback("candidate"))


# --- I/J/K: plan-approval challenge, real plan_identity ---------------------


class PlanApprovalChallengeTests(unittest.TestCase):
    """Exercises the real _read_plan_challenge_grant / plan_identity()
    binding against real, sealed MissionPlan instances - FakePlan above
    isn't shaped for plan_identity(). The production plan_identity
    function is imported and used directly; its algorithm is never
    duplicated here."""

    def test_pre_buffered_si_alone_does_not_grant(self) -> None:
        plan = _real_plan()
        with patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value="sí",
        ):
            self.assertFalse(
                _read_plan_challenge_grant(
                    command_verb="aprobar-plan",
                    grant_label="aprobar este plan",
                    mission_id=plan.mission_id,
                    plan=plan,
                )
            )

    def test_exact_freshly_generated_challenge_grants(self) -> None:
        plan = _real_plan()
        fixed_nonce = "a" * 32
        expected = (
            f":aprobar-plan {plan.mission_id} "
            f"{_plan_identity(plan)} {fixed_nonce}"
        )
        with patch(
            "tools.konoha_v4.conversation.secrets.token_hex",
            return_value=fixed_nonce,
        ), patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value=expected,
        ):
            self.assertTrue(
                _read_plan_challenge_grant(
                    command_verb="aprobar-plan",
                    grant_label="aprobar este plan",
                    mission_id=plan.mission_id,
                    plan=plan,
                )
            )

    def test_plan_identity_drift_invalidates_stale_command(self) -> None:
        # A command built against an earlier plan revision's identity must
        # not authorize a plan that has since drifted (e.g. replanned),
        # even with the same nonce value - proving the identity binding,
        # not just the nonce, is load-bearing, and that stale-revision
        # approval cannot drift forward.
        original = _real_plan()
        drifted = _real_plan(rationale="revisado tras feedback humano")
        self.assertNotEqual(_plan_identity(original), _plan_identity(drifted))

        fixed_nonce = "b" * 32
        stale_command = (
            f":aprobar-plan {original.mission_id} "
            f"{_plan_identity(original)} {fixed_nonce}"
        )
        with patch(
            "tools.konoha_v4.conversation.secrets.token_hex",
            return_value=fixed_nonce,
        ), patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value=stale_command,
        ):
            self.assertFalse(
                _read_plan_challenge_grant(
                    command_verb="aprobar-plan",
                    grant_label="aprobar este plan",
                    mission_id=drifted.mission_id,
                    plan=drifted,
                )
            )

    def test_plan_only_wording_never_uses_execution_verb(self) -> None:
        # A pasted execution-approval command must never satisfy a
        # plan-only acceptance challenge, since the two use distinct
        # command vocabulary.
        plan = _real_plan()
        fixed_nonce = "f" * 32
        execution_command = (
            f":aprobar-plan {plan.mission_id} "
            f"{_plan_identity(plan)} {fixed_nonce}"
        )
        with patch(
            "tools.konoha_v4.conversation.secrets.token_hex",
            return_value=fixed_nonce,
        ), patch(
            "tools.konoha_v4.conversation._TERMINAL_INPUT.read_exact_line",
            return_value=execution_command,
        ):
            self.assertFalse(
                _read_plan_challenge_grant(
                    command_verb="aceptar-planificacion",
                    grant_label="aceptar esta planificación",
                    mission_id=plan.mission_id,
                    plan=plan,
                )
            )


if __name__ == "__main__":
    unittest.main()
