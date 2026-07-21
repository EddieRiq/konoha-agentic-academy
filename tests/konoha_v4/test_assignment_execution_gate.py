from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools.konoha_v4.executor import execute_plan
from tools.konoha_v4.hokage import approval_summary, validate_plan
from tools.konoha_v4.models import EXECUTION_GATES, AgentAssignment, MissionPlan
from tools.konoha_v4.planner import build_plan
from tools.konoha_v4.registry import CapabilityRegistry


class _Registry:
    def agent_family(self, family: str) -> dict:
        return {"allowed_task_patterns": ["read-only inspection"]}

    def model_allowed(self, provider: str, model: str, family: str) -> bool:
        return True


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


def _approval(status: str) -> dict:
    return {
        "status": status,
        "approved_by": "human" if status == "approved" else None,
        "approved_at": "2026-07-21T00:00:00Z" if status == "approved" else None,
        "feedback": None,
    }


def _plan(assignments: list[AgentAssignment], approval_status: str = "approved") -> MissionPlan:
    return MissionPlan(
        mission_id="mission-gate-test",
        understanding="Validar el gate de ejecución de assignments.",
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
        approval=_approval(approval_status),
    ).seal()


class ExecutorPreflightGateTests(unittest.TestCase):
    def _run(self, assignments: list[AgentAssignment], approval_status: str = "approved"):
        plan = _plan(assignments, approval_status=approval_status)
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch("tools.konoha_v4.executor.invoke") as invoke_mock, \
                 mock.patch("tools.konoha_v4.executor._git_status", return_value="") as git_status_mock:
                invoke_mock.return_value = SimpleNamespace(
                    text="ok", usage={"input": 1, "output": 1}, command=["echo"],
                )
                evidence = execute_plan(Path("."), plan, _Registry(), state_dir)
            return plan, evidence, invoke_mock, git_status_mock

    def test_plan_approval_gate_executes_when_plan_is_fully_approved(self) -> None:
        assignments = [_assignment(task_id="t1", execution_gate="plan_approval")]
        _, evidence, invoke_mock, _ = self._run(assignments, approval_status="approved")

        invoke_mock.assert_called_once()
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].status, "completed")

    def test_separate_human_approval_blocks_even_when_plan_is_approved(self) -> None:
        assignments = [_assignment(task_id="t1", execution_gate="separate_human_approval")]
        _, evidence, invoke_mock, _ = self._run(assignments, approval_status="approved")

        invoke_mock.assert_not_called()
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].status, "blocked")
        self.assertEqual(evidence[0].task_id, "t1")

    def test_atomic_preflight_blocks_first_task_when_second_is_gated(self) -> None:
        assignments = [
            _assignment(task_id="t1", execution_gate="plan_approval"),
            _assignment(task_id="t2", execution_gate="separate_human_approval"),
        ]
        _, evidence, invoke_mock, git_status_mock = self._run(assignments, approval_status="approved")

        invoke_mock.assert_not_called()
        git_status_mock.assert_not_called()
        statuses = {record.task_id: record.status for record in evidence}
        self.assertNotIn("completed", statuses.values())
        self.assertEqual(statuses.get("t2"), "blocked")
        self.assertNotIn("t1", statuses)

    def test_zero_invoke_calls_when_any_assignment_is_blocked(self) -> None:
        assignments = [
            _assignment(task_id="t1", execution_gate="plan_approval"),
            _assignment(task_id="t2", execution_gate=""),
        ]
        _, evidence, invoke_mock, _ = self._run(assignments, approval_status="approved")

        invoke_mock.assert_not_called()

    def test_all_offenders_are_reported(self) -> None:
        assignments = [
            _assignment(task_id="ok", execution_gate="plan_approval"),
            _assignment(task_id="offender-empty", execution_gate=""),
            _assignment(task_id="offender-separate", execution_gate="separate_human_approval"),
        ]
        _, evidence, invoke_mock, _ = self._run(assignments, approval_status="approved")

        invoke_mock.assert_not_called()
        reported_task_ids = {record.task_id for record in evidence}
        self.assertEqual(reported_task_ids, {"offender-empty", "offender-separate"})
        for record in evidence:
            self.assertEqual(record.status, "blocked")

    def test_gate_is_independent_of_mutation_network_private_context(self) -> None:
        assignments = [
            _assignment(
                task_id="t1",
                execution_gate="plan_approval",
                mutation=True,
                network=True,
                private_context=True,
            ),
        ]
        _, evidence, invoke_mock, _ = self._run(assignments, approval_status="approved")

        invoke_mock.assert_called_once()
        self.assertEqual(evidence[0].status, "completed")

    def test_legacy_empty_gate_fails_closed(self) -> None:
        assignments = [_assignment(task_id="t1", execution_gate="")]
        _, evidence, invoke_mock, _ = self._run(assignments, approval_status="approved")

        invoke_mock.assert_not_called()
        self.assertEqual(evidence[0].status, "blocked")

    def test_unknown_execution_gate_fails_closed(self) -> None:
        assignments = [_assignment(task_id="t1", execution_gate="unknown_gate")]
        _, evidence, invoke_mock, _ = self._run(assignments, approval_status="approved")

        invoke_mock.assert_not_called()
        self.assertEqual(evidence[0].status, "blocked")
        self.assertIn("t1", evidence[0].output)
        self.assertIn("unknown_gate", evidence[0].output)

    def test_plan_pending_with_plan_approval_gate_fails_closed(self) -> None:
        assignments = [_assignment(task_id="t1", execution_gate="plan_approval")]
        _, evidence, invoke_mock, _ = self._run(assignments, approval_status="pending")

        invoke_mock.assert_not_called()
        self.assertEqual(evidence[0].status, "blocked")
        self.assertEqual(evidence[0].task_id, "t1")
        self.assertIn("plan_approval", evidence[0].output)

    def test_blocked_evidence_identifies_task_id_and_gate(self) -> None:
        assignments = [_assignment(task_id="needs-human", execution_gate="separate_human_approval")]
        _, evidence, _, _ = self._run(assignments, approval_status="approved")

        self.assertIn("needs-human", evidence[0].output)
        self.assertIn("separate_human_approval", evidence[0].output)

    def test_blocked_evidence_is_persisted(self) -> None:
        assignments = [_assignment(task_id="needs-human", execution_gate="separate_human_approval")]
        plan = _plan(assignments, approval_status="approved")

        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch("tools.konoha_v4.executor.invoke"), \
                 mock.patch("tools.konoha_v4.executor._git_status", return_value=""):
                execute_plan(Path("."), plan, _Registry(), state_dir)

            persisted = list(
                (state_dir / "missions" / plan.mission_id / "evidence").glob("*.json")
            )
            self.assertEqual(len(persisted), 1)
            payload = json.loads(persisted[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "blocked")
            self.assertEqual(payload["task_id"], "needs-human")


class ValidatePlanExecutionGateTests(unittest.TestCase):
    def test_validate_plan_accepts_both_valid_gates(self) -> None:
        plan = _plan(
            [
                _assignment(task_id="t1", execution_gate="plan_approval"),
                _assignment(task_id="t2", execution_gate="separate_human_approval"),
            ],
            approval_status="pending",
        )
        problems = validate_plan(plan, _Registry())
        self.assertFalse(any("execution_gate inválido" in p for p in problems))

    def test_validate_plan_rejects_empty_gate(self) -> None:
        plan = _plan([_assignment(task_id="t1", execution_gate="")], approval_status="pending")
        problems = validate_plan(plan, _Registry())
        matches = [p for p in problems if "execution_gate inválido" in p]
        self.assertEqual(len(matches), 1)
        self.assertIn("t1", matches[0])
        self.assertIn("''", matches[0])
        for gate in sorted(EXECUTION_GATES):
            self.assertIn(gate, matches[0])

    def test_validate_plan_rejects_unknown_gate(self) -> None:
        plan = _plan(
            [_assignment(task_id="t1", execution_gate="unknown_gate")],
            approval_status="pending",
        )
        problems = validate_plan(plan, _Registry())
        matches = [p for p in problems if "execution_gate inválido" in p]
        self.assertEqual(len(matches), 1)
        self.assertIn("t1", matches[0])
        self.assertIn("unknown_gate", matches[0])
        for gate in sorted(EXECUTION_GATES):
            self.assertIn(gate, matches[0])


class ApprovalSummaryExecutionGateTests(unittest.TestCase):
    def test_approval_summary_shows_both_gates(self) -> None:
        plan = _plan(
            [
                _assignment(task_id="t1", execution_gate="plan_approval"),
                _assignment(task_id="t2", execution_gate="separate_human_approval"),
            ],
            approval_status="pending",
        )
        summary = approval_summary(plan)
        self.assertIn("Gate de ejecución: plan_approval", summary)
        self.assertIn("Gate de ejecución: separate_human_approval", summary)

    def test_approval_summary_shows_warning_for_legacy_gate(self) -> None:
        plan = _plan([_assignment(task_id="t1", execution_gate="")], approval_status="pending")
        summary = approval_summary(plan)
        self.assertIn("Gate de ejecución: ⚠ NO DECLARADO", summary)


def _validate_execution_gate(assignment: dict, item_schema: dict) -> list[str]:
    """Mini-validador acotado a required+enum de execution_gate.

    No reemplaza un validador JSON Schema completo (no hay dependencia
    jsonschema instalada en este entorno); sólo cubre la presencia
    obligatoria del campo y la pertenencia al enum declarado.
    """
    problems = []
    if (
        "execution_gate" in item_schema["required"]
        and "execution_gate" not in assignment
    ):
        problems.append("execution_gate ausente")
    elif "execution_gate" in assignment:
        allowed = item_schema["properties"]["execution_gate"]["enum"]
        if assignment["execution_gate"] not in allowed:
            problems.append(
                f"execution_gate desconocido: {assignment['execution_gate']!r}"
            )
    return problems


class SchemaExecutionGateContractTests(unittest.TestCase):
    def setUp(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        schema_path = repo / "schemas" / "runtime" / "konoha_v4_mission_plan.schema.json"
        self.schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.item_schema = self.schema["properties"]["assignments"]["items"]

    def _base_assignment(self, **overrides) -> dict:
        assignment = {
            "task_id": "t1",
            "family": "repository-auditor",
            "provider": "codex",
            "model": "codex",
            "objective": "x",
            "inputs": [],
            "expected_output": "x",
            "dependencies": [],
            "private_context": False,
            "network": False,
            "mutation": False,
            "estimated_input_tokens": 0,
            "estimated_output_tokens": 0,
            "estimated_total_tokens": 0,
            "cost_class": "low",
            "fallback": "stop",
            "stop_condition": "x",
            "execution_gate": "plan_approval",
        }
        assignment.update(overrides)
        return assignment

    def test_schema_accepts_plan_approval(self) -> None:
        assignment = self._base_assignment(execution_gate="plan_approval")
        self.assertEqual(_validate_execution_gate(assignment, self.item_schema), [])

    def test_schema_accepts_separate_human_approval(self) -> None:
        assignment = self._base_assignment(execution_gate="separate_human_approval")
        self.assertEqual(_validate_execution_gate(assignment, self.item_schema), [])

    def test_schema_rejects_unknown_value(self) -> None:
        assignment = self._base_assignment(execution_gate="unknown_gate")
        problems = _validate_execution_gate(assignment, self.item_schema)
        self.assertEqual(len(problems), 1)
        self.assertIn("unknown_gate", problems[0])

    def test_schema_rejects_absent_execution_gate(self) -> None:
        assignment = self._base_assignment()
        del assignment["execution_gate"]
        problems = _validate_execution_gate(assignment, self.item_schema)
        self.assertEqual(problems, ["execution_gate ausente"])


class BuildPlanExecutionGatePropagationTests(unittest.TestCase):
    def test_build_plan_propagates_execution_gate_from_mocked_json(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        registry = CapabilityRegistry(repo)

        raw_plan = {
            "mission_id": "mission-build-plan-gate",
            "understanding": "Propagar execution_gate desde JSON al AgentAssignment.",
            "explicit_facts": [],
            "missing_context": [],
            "assumptions_prohibited": [],
            "complexity": "low",
            "assignments": [
                {
                    "task_id": "propagate-gate",
                    "family": "repository-auditor",
                    "provider": "codex",
                    "model": "codex",
                    "objective": "Verificar propagación del execution_gate.",
                    "inputs": [],
                    "expected_output": "Evidencia.",
                    "dependencies": [],
                    "private_context": False,
                    "network": False,
                    "mutation": False,
                    "estimated_input_tokens": 10,
                    "estimated_output_tokens": 5,
                    "estimated_total_tokens": 15,
                    "cost_class": "low",
                    "fallback": "stop",
                    "stop_condition": "boundary crossing or unavailable required evidence",
                    "execution_gate": "plan_approval",
                }
            ],
            "acceptance_criteria": ["done"],
            "approval_boundaries": ["read_only"],
            "estimated_tokens": 15,
            "estimated_cost_class": "low",
            "rationale": "test",
            "approval": {
                "status": "pending", "approved_by": None, "approved_at": None, "feedback": None,
            },
            "teachback_policy": "disabled",
            "workspace_policy": {
                "workspace_mutation_allowed": False,
                "private_runtime_state_allowed": True,
                "private_state_root": "/tmp/konoha-v4-test-state",
            },
            "budget": {
                "provider_totals": [{"provider": "codex", "total_tokens": 15}],
                "family_totals": [{"family": "repository-auditor", "total_tokens": 15}],
                "replanning_reserve_tokens": 0,
                "maximum_total_tokens": 15,
            },
            "governance": {"conductor": "codex", "constitutional_authority": "hokage"},
        }

        with mock.patch("tools.konoha_v4.planner.invoke_codex") as invoke_codex_mock:
            invoke_codex_mock.return_value = SimpleNamespace(text=json.dumps(raw_plan))
            plan = build_plan(repo, "misión de prueba", {}, registry)

        self.assertEqual(len(plan.assignments), 1)
        self.assertEqual(plan.assignments[0].execution_gate, "plan_approval")


if __name__ == "__main__":
    unittest.main()
