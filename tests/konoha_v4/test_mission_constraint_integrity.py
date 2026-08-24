from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tools.konoha_v4.conversation import _approval_loop, _build_validated_plan
from tools.konoha_v4.executor import (
    _validate_execution_state_invariants,
    execute_or_resume_plan,
    load_persisted_plan,
    plan_identity,
)
from tools.konoha_v4.hokage import approval_summary, validate_plan
from tools.konoha_v4.models import (
    EXECUTION_STATE_SCHEMA_VERSION,
    AgentAssignment,
    ExecutionState,
    MissionPlan,
)


class _Registry:
    def agent_family(self, family: str) -> dict:
        return {"allowed_task_patterns": ["read-only inspection"]}

    def model_allowed(self, provider: str, model: str, family: str) -> bool:
        return True


MISSION_TEXT = (
    "Ejecutá Codex primero y después Claude, sin superar 275 tokens en total."
)


def _assignments() -> list[AgentAssignment]:
    return [
        AgentAssignment(
            task_id="codex-first",
            family="repository-auditor",
            provider="codex",
            model="codex",
            objective="Inspeccionar el runtime sin modificar archivos.",
            inputs=["tools/konoha_v4"],
            expected_output="Evidencia verificable.",
            dependencies=[],
            estimated_input_tokens=100,
            estimated_output_tokens=50,
            estimated_total_tokens=150,
            execution_gate="plan_approval",
        ),
        AgentAssignment(
            task_id="claude-second",
            family="repository-auditor",
            provider="claude",
            model="claude",
            objective="Revisar los hallazgos de Codex.",
            inputs=["tools/konoha_v4"],
            expected_output="Evidencia verificable.",
            dependencies=["codex-first"],
            estimated_input_tokens=80,
            estimated_output_tokens=20,
            estimated_total_tokens=100,
            execution_gate="plan_approval",
        ),
    ]


def _plan(mission_constraints: list[dict] | None = None) -> MissionPlan:
    return MissionPlan(
        mission_id="mission-constraint-contract",
        understanding="Validar el manifiesto estructurado de restricciones de misión.",
        explicit_facts=["Codex va primero; Claude va segundo."],
        missing_context=[],
        assumptions_prohibited=["No inferir autorización."],
        complexity="medium",
        assignments=_assignments(),
        acceptance_criteria=["No hubo mutación."],
        approval_boundaries=["read_only"],
        estimated_tokens=275,
        estimated_cost_class="low",
        rationale="Validación constitucional read-only.",
        budget={
            "provider_totals": [
                {"provider": "codex", "total_tokens": 150},
                {"provider": "claude", "total_tokens": 100},
            ],
            "family_totals": [
                {"family": "repository-auditor", "total_tokens": 250},
            ],
            "replanning_reserve_tokens": 25,
            "maximum_total_tokens": 275,
        },
        mission_constraints=mission_constraints,
    ).seal()


def _constraint(**overrides) -> dict:
    base = {
        "constraint_id": "constraint-1",
        "source_text": "Codex primero",
        "scope": "assignment",
        "assignment_index": 0,
        "field": "provider",
        "operator": "equals",
        "value": "codex",
    }
    base.update(overrides)
    return base


class LegacyIdentityCompatibilityTests(unittest.TestCase):
    """Test 1."""

    def test_legacy_none_plan_identity_matches_pre_v401_algorithm(self) -> None:
        plan = _plan(mission_constraints=None)

        raw = asdict(plan)
        raw.pop("approval", None)
        raw.pop("plan_hash", None)
        raw.pop("mission_constraints", None)
        canonical = json.dumps(
            raw, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        )
        expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        self.assertEqual(plan_identity(plan), expected)


class LegacySealHashCompatibilityTests(unittest.TestCase):
    """Optional/high-value: MissionPlan.seal()'s plan_hash for a legacy
    (mission_constraints=None) plan must reproduce the exact pre-v4.0.1
    16-hex-char algorithm, independently of plan_identity()."""

    def test_legacy_none_plan_hash_matches_pre_v401_seal_algorithm(self) -> None:
        plan = _plan(mission_constraints=None)

        raw = asdict(plan)
        raw["plan_hash"] = ""
        raw.pop("mission_constraints", None)
        canonical = json.dumps(raw, sort_keys=True, ensure_ascii=False)
        expected = hashlib.sha256(canonical.encode()).hexdigest()[:16]

        self.assertEqual(plan.plan_hash, expected)


class PersistedLegacyPlanLoadTests(unittest.TestCase):
    """Test 2."""

    def test_legacy_plan_json_without_mission_constraints_loads_as_none(self) -> None:
        plan = _plan(mission_constraints=None)
        raw = asdict(plan)
        raw.pop("mission_constraints", None)

        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            mission_dir = state_dir / "missions" / plan.mission_id
            mission_dir.mkdir(parents=True)
            (mission_dir / "plan.json").write_text(
                json.dumps(raw, ensure_ascii=False), encoding="utf-8",
            )
            loaded = load_persisted_plan(state_dir, plan.mission_id)

        self.assertIsNone(loaded.mission_constraints)


class LegacyExecutionStateCompatibilityTests(unittest.TestCase):
    """Test 3: persisted legacy v4.0.0 plan.json (no mission_constraints)
    round-trips through load_persisted_plan(), reproduces the exact legacy
    plan_identity, and still satisfies the existing resume invariant check
    against a persisted ExecutionState recorded under that legacy identity."""

    def test_legacy_persisted_plan_and_execution_state_remain_resumable(self) -> None:
        plan = _plan(mission_constraints=None)
        legacy_identity = plan_identity(plan)

        raw = asdict(plan)
        raw.pop("mission_constraints", None)

        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            mission_dir = state_dir / "missions" / plan.mission_id
            mission_dir.mkdir(parents=True)
            (mission_dir / "plan.json").write_text(
                json.dumps(raw, ensure_ascii=False), encoding="utf-8",
            )
            loaded = load_persisted_plan(state_dir, plan.mission_id)

        self.assertIsNone(loaded.mission_constraints)
        self.assertEqual(plan_identity(loaded), legacy_identity)

        state = ExecutionState(
            schema_version=EXECUTION_STATE_SCHEMA_VERSION,
            mission_id=plan.mission_id,
            plan_identity=legacy_identity,
            status="in_progress",
            next_assignment_index=0,
        )

        self.assertIsNone(_validate_execution_state_invariants(loaded, state))


class ReadinessGateCompatibilityTests(unittest.TestCase):
    """Tests 15 and 16: the v4.0.2 pre-invocation readiness gate is
    orthogonal to mission_constraints entirely - it must not require, read,
    or invent any mission_constraints-related field, for either the exact
    legacy v4.0.0 persisted shape (mission_constraints key entirely absent,
    loading as None) or the v4.0.1 shape ([] or populated)."""

    _COMPLETED_RESULT_TEXT = json.dumps({
        "outcome": "completed", "objective_satisfied": True, "summary": "ok",
        "diagnostic": None, "evidence": [], "review_outcome": None,
    })

    def _approved(self, mission_constraints):
        plan = _plan(mission_constraints=mission_constraints)
        plan.approval["status"] = "approved"
        plan.approval["approved_by"] = "human"
        return plan

    def _write_plan(self, state_dir, plan, *, legacy_v400=False):
        mission_dir = state_dir / "missions" / plan.mission_id
        mission_dir.mkdir(parents=True, exist_ok=True)

        payload = asdict(plan)

        if legacy_v400:
            self.assertIsNone(plan.mission_constraints)
            payload.pop("mission_constraints", None)

        (mission_dir / "plan.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _run(self, plan, *, available, legacy_v400=False):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            self._write_plan(state_dir, plan, legacy_v400=legacy_v400)
            readiness = SimpleNamespace(available=available, models=[])
            with patch(
                "tools.konoha_v4.executor.probe_provider_readiness", return_value=readiness,
            ), patch(
                "tools.konoha_v4.executor.invoke",
                return_value=SimpleNamespace(
                    text=self._COMPLETED_RESULT_TEXT, usage={}, command=["echo"],
                ),
            ) as invoke_mock, patch(
                "tools.konoha_v4.executor._git_status", return_value="",
            ):
                attempt = execute_or_resume_plan(Path("."), state_dir, plan.mission_id, _Registry())
            return attempt, invoke_mock

    def test_v400_legacy_plan_without_manifest_executes_when_provider_ready(self):
        plan = self._approved(None)
        attempt, invoke_mock = self._run(plan, available=True, legacy_v400=True)
        invoke_mock.assert_called_once()
        self.assertEqual(attempt.diagnostic, "completed")

    def test_v400_legacy_plan_without_manifest_blocks_when_provider_not_ready(self):
        plan = self._approved(None)
        attempt, invoke_mock = self._run(plan, available=False, legacy_v400=True)
        invoke_mock.assert_not_called()
        self.assertEqual(attempt.diagnostic, "provider_not_ready:codex")

    def test_v400_legacy_plan_without_manifest_loads_as_none(self):
        plan = self._approved(None)
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            self._write_plan(state_dir, plan, legacy_v400=True)
            loaded = load_persisted_plan(state_dir, plan.mission_id)
        self.assertIsNone(loaded.mission_constraints)

    def test_v401_empty_manifest_executes_when_provider_ready(self):
        attempt, invoke_mock = self._run(self._approved([]), available=True)
        invoke_mock.assert_called_once()
        self.assertEqual(attempt.diagnostic, "completed")

    def test_v401_populated_manifest_blocks_when_provider_not_ready(self):
        constraint = _constraint(source_text="Codex primero")
        attempt, invoke_mock = self._run(self._approved([constraint]), available=False)
        invoke_mock.assert_not_called()
        self.assertEqual(attempt.diagnostic, "provider_not_ready:codex")


class ManifestIdentityParticipationTests(unittest.TestCase):
    """Tests 4 and 5."""

    def test_empty_manifest_differs_from_legacy_none(self) -> None:
        legacy = _plan(mission_constraints=None)
        new_format = _plan(mission_constraints=[])

        self.assertNotEqual(plan_identity(legacy), plan_identity(new_format))

    def test_changing_manifest_changes_identity(self) -> None:
        constraint_a = _constraint()
        constraint_b = dict(constraint_a, value="claude")

        plan_a = _plan(mission_constraints=[constraint_a])
        plan_b = _plan(mission_constraints=[constraint_b])

        self.assertNotEqual(plan_identity(plan_a), plan_identity(plan_b))


class ShapeAndAuthorityTests(unittest.TestCase):
    """Tests 6, 7, 8, 9, plus empty-manifest and malformed-container
    fail-closed coverage."""

    def test_duplicate_constraint_id_fails(self) -> None:
        c1 = _constraint(constraint_id="dup", assignment_index=0, value="codex")
        c2 = _constraint(constraint_id="dup", assignment_index=1, value="claude")
        plan = _plan(mission_constraints=[c1, c2])

        problems = validate_plan(
            plan, _Registry(), mission_authority_texts=[MISSION_TEXT],
        )

        self.assertTrue(
            any(
                p.startswith("mission_constraint_invalid:") and "duplicado" in p
                for p in problems
            )
        )

    def test_unauthorized_paraphrased_source_text_fails(self) -> None:
        c = _constraint(source_text="Empezá con Codex")
        plan = _plan(mission_constraints=[c])

        problems = validate_plan(
            plan, _Registry(), mission_authority_texts=[MISSION_TEXT],
        )

        self.assertTrue(
            any(p.startswith("mission_constraint_source_not_authorized:") for p in problems)
        )

    def test_exact_verbatim_source_text_succeeds(self) -> None:
        c = _constraint(source_text="Codex primero")
        plan = _plan(mission_constraints=[c])

        problems = validate_plan(
            plan, _Registry(), mission_authority_texts=[MISSION_TEXT],
        )

        self.assertEqual(problems, [])

    def test_missing_authority_texts_fails_closed(self) -> None:
        c = _constraint(source_text="Codex primero")
        plan = _plan(mission_constraints=[c])

        problems = validate_plan(plan, _Registry())

        self.assertTrue(
            any(p.startswith("mission_constraint_source_not_authorized:") for p in problems)
        )

    def test_empty_new_manifest_without_authority_fails_closed(self) -> None:
        # [] is still new-format (only None is legacy), so it must still
        # require mission_authority_texts even though there is nothing to
        # check a source_text against.
        plan = _plan(mission_constraints=[])

        problems = validate_plan(plan, _Registry())

        self.assertTrue(
            any(p.startswith("mission_constraint_source_not_authorized:") for p in problems)
        )

    def test_malformed_non_list_manifest_container_fails_closed(self) -> None:
        # MissionPlan's type hints are not runtime-enforced; a manually
        # malformed object must still fail closed with a deterministic
        # diagnostic rather than raising.
        plan = _plan(mission_constraints=[])
        plan.mission_constraints = "not-a-list"

        problems = validate_plan(
            plan, _Registry(), mission_authority_texts=[MISSION_TEXT],
        )

        self.assertTrue(any(p.startswith("mission_constraint_invalid:") for p in problems))


class PlanScopeStructuralTests(unittest.TestCase):
    """Tests 10, 11, 17, 18."""

    def test_assignment_count_equals_mismatch_fails(self) -> None:
        c = _constraint(
            constraint_id="constraint-count",
            source_text="Codex primero y después Claude",
            scope="plan",
            assignment_index=None,
            field="assignment_count",
            operator="equals",
            value=5,
        )
        problems = validate_plan(
            _plan(mission_constraints=[c]), _Registry(),
            mission_authority_texts=[MISSION_TEXT],
        )
        self.assertTrue(any(p.startswith("mission_constraint_mismatch:") for p in problems))

    def test_assignment_count_at_most_violation_fails(self) -> None:
        c = _constraint(
            constraint_id="constraint-count-max",
            source_text="Codex primero y después Claude",
            scope="plan",
            assignment_index=None,
            field="assignment_count",
            operator="at_most",
            value=1,
        )
        problems = validate_plan(
            _plan(mission_constraints=[c]), _Registry(),
            mission_authority_texts=[MISSION_TEXT],
        )
        self.assertTrue(any(p.startswith("mission_constraint_mismatch:") for p in problems))

    def test_maximum_total_tokens_at_most_violation_fails(self) -> None:
        c = _constraint(
            constraint_id="constraint-max-tokens",
            source_text="sin superar 275 tokens en total",
            scope="plan",
            assignment_index=None,
            field="maximum_total_tokens",
            operator="at_most",
            value=100,
        )
        problems = validate_plan(
            _plan(mission_constraints=[c]), _Registry(),
            mission_authority_texts=[MISSION_TEXT],
        )
        self.assertTrue(any(p.startswith("mission_constraint_mismatch:") for p in problems))

    def test_replanning_reserve_tokens_mismatch_fails(self) -> None:
        c = _constraint(
            constraint_id="constraint-reserve",
            source_text="Codex primero",
            scope="plan",
            assignment_index=None,
            field="replanning_reserve_tokens",
            operator="equals",
            value=999,
        )
        problems = validate_plan(
            _plan(mission_constraints=[c]), _Registry(),
            mission_authority_texts=[MISSION_TEXT],
        )
        self.assertTrue(any(p.startswith("mission_constraint_mismatch:") for p in problems))


class AssignmentScopeStructuralTests(unittest.TestCase):
    """Tests 12, 13, 14, 15."""

    def test_provider_by_position_mismatch_fails(self) -> None:
        c = _constraint(field="provider", operator="equals", value="claude")
        problems = validate_plan(
            _plan(mission_constraints=[c]), _Registry(),
            mission_authority_texts=[MISSION_TEXT],
        )
        self.assertTrue(any(p.startswith("mission_constraint_mismatch:") for p in problems))

    def test_model_mismatch_fails(self) -> None:
        c = _constraint(field="model", operator="equals", value="not-codex")
        problems = validate_plan(
            _plan(mission_constraints=[c]), _Registry(),
            mission_authority_texts=[MISSION_TEXT],
        )
        self.assertTrue(any(p.startswith("mission_constraint_mismatch:") for p in problems))

    def test_family_mismatch_fails(self) -> None:
        c = _constraint(field="family", operator="equals", value="mission-conductor")
        problems = validate_plan(
            _plan(mission_constraints=[c]), _Registry(),
            mission_authority_texts=[MISSION_TEXT],
        )
        self.assertTrue(any(p.startswith("mission_constraint_mismatch:") for p in problems))

    def test_network_mismatch_fails(self) -> None:
        c = _constraint(field="network", operator="equals", value=True)
        problems = validate_plan(
            _plan(mission_constraints=[c]), _Registry(),
            mission_authority_texts=[MISSION_TEXT],
        )
        self.assertTrue(any(p.startswith("mission_constraint_mismatch:") for p in problems))

    def test_private_context_mismatch_fails(self) -> None:
        c = _constraint(field="private_context", operator="equals", value=True)
        problems = validate_plan(
            _plan(mission_constraints=[c]), _Registry(),
            mission_authority_texts=[MISSION_TEXT],
        )
        self.assertTrue(any(p.startswith("mission_constraint_mismatch:") for p in problems))

    def test_mutation_mismatch_fails(self) -> None:
        c = _constraint(field="mutation", operator="equals", value=True)
        problems = validate_plan(
            _plan(mission_constraints=[c]), _Registry(),
            mission_authority_texts=[MISSION_TEXT],
        )
        self.assertTrue(any(p.startswith("mission_constraint_mismatch:") for p in problems))

    def test_execution_gate_mismatch_fails(self) -> None:
        c = _constraint(field="execution_gate", operator="equals", value="separate_human_approval")
        problems = validate_plan(
            _plan(mission_constraints=[c]), _Registry(),
            mission_authority_texts=[MISSION_TEXT],
        )
        self.assertTrue(any(p.startswith("mission_constraint_mismatch:") for p in problems))


class DependencyPositionResolutionTests(unittest.TestCase):
    """Test 16."""

    def test_correct_dependency_positions_resolve_and_pass(self) -> None:
        c = _constraint(
            constraint_id="constraint-deps-ok",
            source_text="Claude depende de Codex",
            assignment_index=1,
            field="dependencies",
            operator="equals",
            value=[0],
        )
        problems = validate_plan(
            _plan(mission_constraints=[c]), _Registry(),
            mission_authority_texts=[MISSION_TEXT, "Claude depende de Codex"],
        )
        self.assertEqual(problems, [])

    def test_wrong_dependency_positions_fail(self) -> None:
        c = _constraint(
            constraint_id="constraint-deps-bad",
            source_text="Claude depende de Codex",
            assignment_index=1,
            field="dependencies",
            operator="equals",
            value=[],
        )
        problems = validate_plan(
            _plan(mission_constraints=[c]), _Registry(),
            mission_authority_texts=[MISSION_TEXT, "Claude depende de Codex"],
        )
        self.assertTrue(any(p.startswith("mission_constraint_mismatch:") for p in problems))


class MalformedConstraintShapeTests(unittest.TestCase):
    """Test 19."""

    def test_malformed_combinations_fail_closed(self) -> None:
        cases = {
            "unknown_field": _constraint(field="not_a_real_field"),
            "unknown_operator": _constraint(operator="greater_than"),
            "at_most_on_string_field": _constraint(operator="at_most"),
            "assignment_index_present_for_plan_scope": _constraint(
                scope="plan", field="assignment_count", assignment_index=0, value=1,
            ),
            "assignment_index_missing_for_assignment_scope": _constraint(
                assignment_index=None,
            ),
            "assignment_index_out_of_range": _constraint(assignment_index=99),
            "wrong_value_type_for_int_field": _constraint(
                field="estimated_input_tokens", operator="equals", value="100",
            ),
            "wrong_value_type_for_bool_field": _constraint(
                field="network", operator="equals", value="true",
            ),
            "wrong_value_type_for_list_field": _constraint(
                field="dependencies", operator="equals", value="0",
            ),
            "dependency_position_out_of_range": _constraint(
                field="dependencies", operator="equals", value=[99],
            ),
            "missing_key": {k: v for k, v in _constraint().items() if k != "value"},
            "unknown_key": dict(_constraint(), extra_field="nope"),
            "empty_constraint_id": _constraint(constraint_id=""),
            "scope_field_relationship_violated": _constraint(
                scope="plan", field="provider", assignment_index=None,
            ),
        }
        for label, constraint in cases.items():
            with self.subTest(label=label):
                problems = validate_plan(
                    _plan(mission_constraints=[constraint]), _Registry(),
                    mission_authority_texts=[MISSION_TEXT],
                )
                self.assertTrue(
                    any(p.startswith("mission_constraint_invalid:") for p in problems),
                    f"expected mission_constraint_invalid for {label}, got: {problems}",
                )


class ApprovalSummaryDisplayTests(unittest.TestCase):
    """Tests 20, 21."""

    def test_new_format_manifest_is_displayed_with_source_text(self) -> None:
        c1 = _constraint(
            constraint_id="constraint-provider-1",
            source_text="Codex primero",
        )
        c2 = _constraint(
            constraint_id="constraint-count",
            source_text="Codex primero y después Claude",
            scope="plan",
            assignment_index=None,
            field="assignment_count",
            operator="equals",
            value=2,
        )
        summary = approval_summary(_plan(mission_constraints=[c1, c2]))

        self.assertIn("Restricciones estructurales extraídas:", summary)
        self.assertIn("constraint-provider-1", summary)
        self.assertIn('assignment[0].provider equals "codex"', summary)
        self.assertIn("Codex primero", summary)
        self.assertIn("constraint-count", summary)
        self.assertIn("plan.assignment_count equals 2", summary)
        self.assertIn("Codex primero y después Claude", summary)
        self.assertIn(
            "La completitud semántica de la extracción de "
            "mission_constraints requiere revisión humana.",
            summary,
        )

    def test_empty_manifest_shows_explicit_none_extracted_message(self) -> None:
        summary = approval_summary(_plan(mission_constraints=[]))

        self.assertIn(
            "Ninguna restricción estructural representable fue extraída.", summary,
        )

    def test_legacy_plan_marks_no_structured_manifest(self) -> None:
        summary = approval_summary(_plan(mission_constraints=None))

        self.assertIn(
            "Restricciones estructurales: plan legacy v4.0.0 sin manifest estructurado.",
            summary,
        )
        self.assertNotIn("Restricciones estructurales extraídas:", summary)


class AutomaticReplanningAuthorityTests(unittest.TestCase):
    """Test 22."""

    @patch("tools.konoha_v4.conversation.validate_plan")
    @patch("tools.konoha_v4.conversation.build_plan")
    def test_automatic_corrective_replanning_never_uses_validator_feedback_as_authority(
        self, build_plan: Mock, validate_plan_mock: Mock,
    ) -> None:
        mission_text = "Inspeccionar el runtime en modo read-only."
        first = SimpleNamespace(missing_context=[])
        corrected = SimpleNamespace(missing_context=[])
        build_plan.side_effect = [first, corrected]
        validate_plan_mock.side_effect = [
            ["estimated_tokens debe coincidir con budget.maximum_total_tokens."],
            [],
        ]

        _build_validated_plan(Mock(), mission_text, {"branch": "test"}, Mock())

        self.assertEqual(validate_plan_mock.call_count, 2)
        for call in validate_plan_mock.call_args_list:
            self.assertEqual(call.kwargs["mission_authority_texts"], [mission_text])


@dataclass
class _FakePlan:
    mission_id: str
    plan_hash: str
    approval: dict = field(default_factory=lambda: {
        "status": "pending", "approved_by": None, "approved_at": None, "feedback": None,
    })
    missing_context: list = field(default_factory=list)
    assignments: list = field(default_factory=list)


class HumanRequestedChangeAuthorityTests(unittest.TestCase):
    """Test 23."""

    def test_confirmed_requested_change_becomes_authority_source(self) -> None:
        plan = _FakePlan("mission-1", "plan-1")
        replanned = _FakePlan("mission-1", "plan-2")
        store = Mock()
        store.planner_context.return_value = {"mission_id": "mission-1"}
        store.validate_replanned_plan.return_value = []
        store.state.requested_changes_history = []

        def _record(text, _plan):
            store.state.requested_changes_history.append({"text": text})

        store.record_requested_change.side_effect = _record

        feedback = "Codex debe ir primero."
        mission_text = "misión original"

        with tempfile.TemporaryDirectory() as tmp, patch(
            "tools.konoha_v4.conversation.MissionContinuityStore.create",
            return_value=store,
        ), patch(
            "tools.konoha_v4.conversation._repo_state",
            return_value={"branch": "t", "head": "h", "status": ""},
        ), patch(
            "tools.konoha_v4.conversation.approval_summary",
            return_value="VISIBLE PLAN",
        ), patch("tools.konoha_v4.conversation._persist_plan"), patch(
            "tools.konoha_v4.conversation._read_approval_input",
            side_effect=[("feedback", feedback), ("decision", "no")],
        ), patch(
            "tools.konoha_v4.conversation._confirm_feedback", return_value=True,
        ), patch(
            "tools.konoha_v4.conversation.build_plan", return_value=replanned,
        ), patch(
            "tools.konoha_v4.conversation.validate_plan", return_value=[],
        ) as validate_plan_mock:
            _approval_loop(Path("."), Path(tmp), mission_text, plan, Mock())

        validate_plan_mock.assert_called_once()
        authority_texts = validate_plan_mock.call_args.kwargs["mission_authority_texts"]
        self.assertEqual(authority_texts, [mission_text, feedback])


if __name__ == "__main__":
    unittest.main()
