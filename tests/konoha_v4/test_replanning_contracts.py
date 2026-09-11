from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tools.konoha_v4.conversation import (
    MAX_PLAN_ATTEMPTS,
    _build_validated_plan,
)
from tools.konoha_v4.continuity import plan_payload


def _planner_context(**overrides) -> dict:
    """A realistic continuity.planner_context() shape for the human-replan
    tests: every field the real store returns, so the tests can prove the
    corrective retry engine carries them through unchanged."""
    context = {
        "schema_version": "1.0",
        "mission_id": "mission-1",
        "original_request": "misión original",
        "repo_baseline": {"branch": "main", "head": "abc"},
        "requested_changes_history": [{"revision": 1, "text": "Codex primero."}],
        "validator_findings_history": [],
        "previous_plan": {"plan_hash": "plan-0"},
        "approval": {"status": "pending", "approved_by": None, "approved_at": None},
        "execution": {"started": False, "completed": False, "tools_executed": []},
        "provider_sessions": {},
    }
    context.update(overrides)
    return context


def _candidate(plan_hash: str) -> SimpleNamespace:
    return SimpleNamespace(
        missing_context=[], mission_id="mission-1", plan_hash=plan_hash,
    )


class ReplanningContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Mock()
        self.registry = Mock()
        self.state = {"branch": "test"}
        self.mission = "Inspeccionar el runtime en modo read-only."

    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_replans_once_after_deterministic_failure(
        self,
        build_plan: Mock,
        validate_plan: Mock,
    ) -> None:
        first = SimpleNamespace(missing_context=[])
        corrected = SimpleNamespace(missing_context=[])

        build_plan.side_effect = [first, corrected]
        validate_plan.side_effect = [
            [
                "estimated_tokens debe coincidir con "
                "budget.maximum_total_tokens."
            ],
            [],
        ]

        plan, problems, attempts = _build_validated_plan(
            self.repo,
            self.mission,
            self.state,
            self.registry,
        )

        self.assertIs(plan, corrected)
        self.assertEqual(problems, [])
        self.assertEqual(attempts, 2)
        self.assertEqual(build_plan.call_count, 2)

        first_feedback = build_plan.call_args_list[0].kwargs["feedback"]
        second_feedback = build_plan.call_args_list[1].kwargs["feedback"]

        self.assertIsNone(first_feedback)
        self.assertIn(
            "estimated_tokens debe coincidir",
            second_feedback,
        )
        self.assertIn(
            "Conservá la misión",
            second_feedback,
        )

    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_missing_context_does_not_trigger_replanning(
        self,
        build_plan: Mock,
        validate_plan: Mock,
    ) -> None:
        plan_with_missing_context = SimpleNamespace(
            missing_context=["Se requiere autorización humana."],
        )
        build_plan.return_value = plan_with_missing_context
        validate_plan.return_value = [
            "Falta contexto explícito: Se requiere autorización humana."
        ]

        plan, problems, attempts = _build_validated_plan(
            self.repo,
            self.mission,
            self.state,
            self.registry,
        )

        self.assertIs(plan, plan_with_missing_context)
        self.assertEqual(attempts, 1)
        self.assertEqual(build_plan.call_count, 1)
        self.assertTrue(problems)

    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_propagates_same_readiness_snapshot_across_replanning_attempts(
        self,
        build_plan: Mock,
        validate_plan: Mock,
    ) -> None:
        # BLOCK_4 FINDING #16 Test F: a distinctive sentinel object proves
        # identity (not merely equal contents) is threaded unchanged into
        # every validate_plan() call across automatic deterministic
        # replanning attempts - the snapshot is never refreshed mid-loop.
        readiness_sentinel = object()
        first = SimpleNamespace(missing_context=[])
        corrected = SimpleNamespace(missing_context=[])

        build_plan.side_effect = [first, corrected]
        validate_plan.side_effect = [
            [
                "estimated_tokens debe coincidir con "
                "budget.maximum_total_tokens."
            ],
            [],
        ]

        plan, problems, attempts = _build_validated_plan(
            self.repo,
            self.mission,
            self.state,
            self.registry,
            provider_readiness=readiness_sentinel,
        )

        self.assertIs(plan, corrected)
        self.assertEqual(attempts, 2)
        self.assertEqual(validate_plan.call_count, 2)
        for call in validate_plan.call_args_list:
            self.assertIs(call.kwargs["provider_readiness"], readiness_sentinel)

    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_stops_after_maximum_attempts(
        self,
        build_plan: Mock,
        validate_plan: Mock,
    ) -> None:
        plans = [
            SimpleNamespace(missing_context=[])
            for _ in range(MAX_PLAN_ATTEMPTS)
        ]
        build_plan.side_effect = plans
        validate_plan.return_value = ["Presupuesto inconsistente."]

        plan, problems, attempts = _build_validated_plan(
            self.repo,
            self.mission,
            self.state,
            self.registry,
        )

        self.assertIs(plan, plans[-1])
        self.assertEqual(attempts, MAX_PLAN_ATTEMPTS)
        self.assertEqual(build_plan.call_count, MAX_PLAN_ATTEMPTS)
        self.assertEqual(problems, ["Presupuesto inconsistente."])


class HumanRequestedReplanEngineTests(unittest.TestCase):
    """v4.1.1: human-requested replanning runs the SAME bounded
    build/validate/deterministic-corrective-retry engine as initial
    planning. These exercise that engine directly through its human-replan
    extension points."""

    def setUp(self) -> None:
        self.repo = Mock()
        self.registry = Mock()
        self.state = {"branch": "test", "head": "abc", "status": ""}
        self.mission = "misión original"
        self.authority = [self.mission, "Codex primero."]

    def _run(self, *, build_plan, validate_plan, **kwargs):
        defaults = dict(
            mission_authority_texts=self.authority,
            first_attempt_feedback="Codex primero.",
            base_continuity=_planner_context(),
            extra_validate=lambda _plan: [],
        )
        defaults.update(kwargs)
        return _build_validated_plan(
            self.repo, self.mission, self.state, self.registry, **defaults,
        )

    # 1. first invalid plan -> deterministic corrective retry -> valid plan
    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_corrective_retry_reaches_valid_plan(
        self, build_plan: Mock, validate_plan: Mock,
    ) -> None:
        invalid = _candidate("plan-bad")
        valid = _candidate("plan-good")
        build_plan.side_effect = [invalid, valid]
        validate_plan.side_effect = [
            ["mission_constraint_source_not_authorized: mc-012"],
            [],
        ]
        record_invalid = Mock()

        plan, problems, attempts = self._run(
            build_plan=build_plan,
            validate_plan=validate_plan,
            on_invalid_attempt=record_invalid,
        )

        self.assertIs(plan, valid)
        self.assertEqual(problems, [])
        self.assertEqual(attempts, 2)
        self.assertEqual(build_plan.call_count, 2)
        # attempt 1 receives the confirmed human feedback verbatim
        self.assertEqual(
            build_plan.call_args_list[0].kwargs["feedback"], "Codex primero.",
        )
        # the corrective retry receives deterministic validator feedback on
        # the requested_changes channel - never as authority
        second_feedback = build_plan.call_args_list[1].kwargs["feedback"]
        self.assertIn("validación determinística", second_feedback)
        self.assertIn(
            "mission_constraint_source_not_authorized: mc-012", second_feedback,
        )
        record_invalid.assert_called_once_with(
            invalid, ["mission_constraint_source_not_authorized: mc-012"],
        )

    # 2. MAX_PLAN_ATTEMPTS is enforced for human replanning
    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_max_plan_attempts_is_enforced(
        self, build_plan: Mock, validate_plan: Mock,
    ) -> None:
        build_plan.side_effect = [
            _candidate(f"plan-{i}") for i in range(MAX_PLAN_ATTEMPTS)
        ]
        validate_plan.return_value = [
            "mission_constraint_source_not_authorized: mc-013"
        ]
        record_invalid = Mock()

        plan, problems, attempts = self._run(
            build_plan=build_plan,
            validate_plan=validate_plan,
            on_invalid_attempt=record_invalid,
        )

        self.assertEqual(attempts, MAX_PLAN_ATTEMPTS)
        self.assertEqual(build_plan.call_count, MAX_PLAN_ATTEMPTS)
        self.assertEqual(
            problems, ["mission_constraint_source_not_authorized: mc-013"],
        )
        # every invalid candidate recorded exactly once, final one included
        self.assertEqual(record_invalid.call_count, MAX_PLAN_ATTEMPTS)

    # 3. same provider_readiness object is passed on every retry
    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_same_readiness_snapshot_across_attempts(
        self, build_plan: Mock, validate_plan: Mock,
    ) -> None:
        readiness_sentinel = object()
        build_plan.side_effect = [_candidate(f"plan-{i}") for i in range(3)]
        validate_plan.side_effect = [["f1"], ["f2"], []]

        self._run(
            build_plan=build_plan,
            validate_plan=validate_plan,
            provider_readiness=readiness_sentinel,
        )

        self.assertEqual(validate_plan.call_count, 3)
        for call in validate_plan.call_args_list:
            self.assertIs(
                call.kwargs["provider_readiness"], readiness_sentinel,
            )

    # 4. mission_authority_texts remain mission + confirmed human history on
    #    every retry; validator feedback is never added as authority
    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_authority_texts_are_constant_and_exclude_validator_feedback(
        self, build_plan: Mock, validate_plan: Mock,
    ) -> None:
        build_plan.side_effect = [_candidate(f"plan-{i}") for i in range(3)]
        validate_plan.side_effect = [
            ["deterministic finding A"],
            ["deterministic finding B"],
            [],
        ]

        self._run(build_plan=build_plan, validate_plan=validate_plan)

        self.assertEqual(validate_plan.call_count, 3)
        for call in validate_plan.call_args_list:
            self.assertEqual(
                call.kwargs["mission_authority_texts"],
                [self.mission, "Codex primero."],
            )
        # the validator findings did surface - on the requested_changes
        # channel of the corrective retries, never in authority
        self.assertIn(
            "deterministic finding A",
            build_plan.call_args_list[1].kwargs["feedback"],
        )

    # continuity.validate_replanned_plan must run on every human-replan attempt
    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_extra_validate_runs_on_every_attempt(
        self, build_plan: Mock, validate_plan: Mock,
    ) -> None:
        build_plan.side_effect = [_candidate(f"plan-{i}") for i in range(3)]
        validate_plan.side_effect = [["f1"], ["f2"], []]
        extra_validate = Mock(return_value=[])

        self._run(
            build_plan=build_plan,
            validate_plan=validate_plan,
            extra_validate=extra_validate,
        )

        self.assertEqual(extra_validate.call_count, 3)

    # 5. the corrective retry receives the first invalid replan as ephemeral
    #    previous_plan context plus validator findings, and preserves every
    #    other planner_context() field unchanged
    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_corrective_context_is_ephemeral_and_preserves_planner_context(
        self, build_plan: Mock, validate_plan: Mock,
    ) -> None:
        invalid = _candidate("plan-bad")
        valid = _candidate("plan-good")
        build_plan.side_effect = [invalid, valid]
        validate_plan.side_effect = [["new deterministic finding"], []]
        base = _planner_context(
            validator_findings_history=[{"revision": 1, "findings": ["older"]}],
        )

        self._run(
            build_plan=build_plan,
            validate_plan=validate_plan,
            base_continuity=base,
        )

        context = build_plan.call_args_list[1].kwargs["continuity"]
        # previous_plan is the immediately preceding invalid candidate
        self.assertEqual(context["previous_plan"], plan_payload(invalid))
        # validator_findings_history = existing history + this sequence's
        # deterministic findings
        self.assertEqual(
            context["validator_findings_history"][0],
            {"revision": 1, "findings": ["older"]},
        )
        self.assertEqual(
            context["validator_findings_history"][-1]["findings"],
            ["new deterministic finding"],
        )
        # every other planner_context() field carried through unchanged -
        # never flattened into the reduced initial-planning synthetic shape
        for key in (
            "schema_version",
            "mission_id",
            "original_request",
            "repo_baseline",
            "requested_changes_history",
            "approval",
            "execution",
            "provider_sessions",
        ):
            self.assertEqual(context[key], base[key])

    # 6/8 boundary: missing_context still fails closed on a human replan and
    #    records the failing candidate as evidence
    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_missing_context_fails_closed_and_records_evidence(
        self, build_plan: Mock, validate_plan: Mock,
    ) -> None:
        blocked = SimpleNamespace(
            missing_context=["Se requiere autorización humana nueva."],
            mission_id="mission-1",
            plan_hash="plan-blocked",
        )
        build_plan.return_value = blocked
        validate_plan.return_value = [
            "Falta contexto explícito: Se requiere autorización humana nueva."
        ]
        record_invalid = Mock()

        plan, problems, attempts = self._run(
            build_plan=build_plan,
            validate_plan=validate_plan,
            on_invalid_attempt=record_invalid,
        )

        self.assertIs(plan, blocked)
        self.assertEqual(attempts, 1)
        self.assertEqual(build_plan.call_count, 1)
        self.assertTrue(problems)
        record_invalid.assert_called_once_with(blocked, problems)


if __name__ == "__main__":
    unittest.main()
