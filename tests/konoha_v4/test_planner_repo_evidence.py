"""Focused tests for Gate C1: RepositoryEvidencePack integration into
tools/konoha_v4/planner.py's build_plan, and the two new
tools/konoha_v4/conversation.py helpers that acquire it before the planner
provider is invoked.

build_plan itself never touches the terminal or spawns a subprocess - only
invoke_codex is mocked here, so these tests are safe to run in-process.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.konoha_v4.conversation import (
    _acquire_repo_evidence_for_planning,
    _repository_state_unavailable_reason,
)
from tools.konoha_v4.planner import build_plan
from tools.konoha_v4.registry import CapabilityRegistry
from tools.repo_evidence.acquire_repo_evidence import (
    Authorization,
    RepositoryEvidencePack,
    acquire_repo_evidence,
)

REPO = Path(__file__).resolve().parents[2]


def _minimal_raw_plan(assignments: list[dict]) -> dict:
    """A minimal, schema-shaped MissionPlan dict - the same fixture shape
    already used by tests/konoha_v4/test_assignment_execution_gate.py,
    parameterized only by assignments/acceptance_criteria for this file's
    purposes."""
    return {
        "mission_id": "mission-repo-evidence-test",
        "understanding": "test",
        "explicit_facts": [],
        "missing_context": [],
        "assumptions_prohibited": [],
        "complexity": "low",
        "assignments": assignments,
        "acceptance_criteria": ["done"],
        "approval_boundaries": ["read_only"],
        "estimated_tokens": sum(a["estimated_total_tokens"] for a in assignments),
        "estimated_cost_class": "low",
        "rationale": "test",
        "approval": {"status": "pending", "approved_by": None, "approved_at": None, "feedback": None},
        "teachback_policy": "disabled",
        "workspace_policy": {
            "workspace_mutation_allowed": False,
            "private_runtime_state_allowed": True,
            "private_state_root": "/tmp/konoha-v4-test-state",
        },
        "budget": {
            "provider_totals": [{"provider": "codex", "total_tokens": sum(a["estimated_total_tokens"] for a in assignments)}],
            "family_totals": _family_totals(assignments),
            "replanning_reserve_tokens": 0,
            "maximum_total_tokens": sum(a["estimated_total_tokens"] for a in assignments),
        },
        "governance": {"conductor": "codex", "constitutional_authority": "hokage"},
        "mission_constraints": [],
    }


def _family_totals(assignments: list[dict]) -> list[dict]:
    totals: dict[str, int] = {}
    for a in assignments:
        totals[a["family"]] = totals.get(a["family"], 0) + a["estimated_total_tokens"]
    return [{"family": f, "total_tokens": t} for f, t in totals.items()]


def _assignment(task_id: str, family: str, *, dependencies: list[str] | None = None,
                 inputs: list[str] | None = None) -> dict:
    return {
        "task_id": task_id, "family": family, "provider": "codex", "model": "provider_default",
        "objective": "obj", "inputs": inputs or [], "expected_output": "out",
        "dependencies": dependencies or [], "private_context": False, "network": False, "mutation": False,
        "estimated_input_tokens": 5, "estimated_output_tokens": 5, "estimated_total_tokens": 10,
        "cost_class": "low", "fallback": "stop",
        "stop_condition": "boundary crossing or unavailable required evidence",
        "execution_gate": "plan_approval",
    }


def _make_temp_git_repo() -> tempfile.TemporaryDirectory:
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init"],
        cwd=root, check=True,
    )
    return td


class BuildPlanRepositoryEvidenceContextTest(unittest.TestCase):
    """context["repository_evidence"] embedding - the one materialization
    path, never a second serializer inside planner.py."""

    def setUp(self):
        self.registry = CapabilityRegistry(REPO)

    def _invoke_and_capture_context(self, repo_evidence) -> dict:
        raw_plan = _minimal_raw_plan([_assignment("t1", "python-static-review", inputs=["docs/x.md"])])
        captured = {}

        def fake_invoke_codex(prompt, cwd, schema):
            marker = "CONTEXTO ESTRUCTURADO:\n"
            captured["context"] = json.loads(prompt.split(marker, 1)[1])
            return mock.Mock(text=json.dumps(raw_plan))

        with mock.patch("tools.konoha_v4.planner.invoke_codex", side_effect=fake_invoke_codex):
            build_plan(REPO, "mision de prueba", {}, self.registry, repo_evidence=repo_evidence)
        return captured["context"]

    def test_repository_evidence_embedded_when_pack_given(self):
        with _make_temp_git_repo() as td:
            pack = acquire_repo_evidence(Path(td), Authorization(authorized_by="t", authorization_note="t"))
            context = self._invoke_and_capture_context(pack)
        self.assertIsNotNone(context["repository_evidence"])
        self.assertEqual(pack.pack_id, context["repository_evidence"]["pack_id"])
        # The embedded view must itself be the bounded shape, not a raw dump.
        self.assertIn("total", context["repository_evidence"]["modules"])
        self.assertIn("truncated", context["repository_evidence"]["modules"])

    def test_repository_evidence_none_when_no_pack_given(self):
        context = self._invoke_and_capture_context(None)
        self.assertIsNone(context["repository_evidence"])


class BuildPlanRequiredSourcesPreviewTest(unittest.TestCase):
    """The assignment-level required_sources preview folded into
    plan.missing_context - MISSING/UNAUTHORIZED only, never PENDING_PRODUCER."""

    def setUp(self):
        self.registry = CapabilityRegistry(REPO)

    def _build(self, assignments: list[dict]):
        raw_plan = _minimal_raw_plan(assignments)
        with mock.patch("tools.konoha_v4.planner.invoke_codex") as invoke_codex_mock:
            invoke_codex_mock.return_value = mock.Mock(text=json.dumps(raw_plan))
            return build_plan(REPO, "mision de prueba", {}, self.registry)

    def test_genuine_missing_required_source_reaches_missing_context(self):
        # python_coding_rules is task-input based; no inputs declared -> MISSING.
        plan = self._build([_assignment("t1", "python-static-review", inputs=[])])
        joined = " ".join(plan.missing_context)
        self.assertIn("python_source_files", joined)
        self.assertIn("t1", joined)

    def test_unauthorized_required_source_is_distinguishable(self):
        plan = self._build([_assignment("t1", "source-extraction", inputs=["private-library/secret.md"])])
        joined = " ".join(plan.missing_context)
        self.assertIn("unauthorized", joined)
        self.assertIn("authorized_local_source", joined)

    def test_pending_producer_with_identified_producer_is_not_missing_context(self):
        assignments = [
            _assignment("impl-1", "python-implementation", inputs=["docs/rules.md"]),
            _assignment("review-1", "python-review", dependencies=["impl-1"], inputs=["docs/rules.md"]),
        ]
        plan = self._build(assignments)
        joined = " ".join(plan.missing_context)
        self.assertNotIn("implementation_diff", joined)
        self.assertNotIn("test_evidence", joined)

    def test_unresolvable_family_is_skipped_not_raised(self):
        # Mirrors test_assignment_execution_gate.py's synthetic
        # "repository-auditor" family - build_plan must never raise on an
        # unregistered family; hokage.validate_plan reports that separately.
        plan = self._build([_assignment("t1", "totally-unregistered-family")])
        self.assertEqual(len(plan.assignments), 1)


class AcquireRepoEvidenceForPlanningTest(unittest.TestCase):
    def test_returns_a_real_pack_for_a_valid_repo(self):
        with _make_temp_git_repo() as td:
            pack = _acquire_repo_evidence_for_planning(Path(td))
        self.assertIsInstance(pack, RepositoryEvidencePack)

    def test_returns_none_on_genuine_acquisition_failure(self):
        with tempfile.TemporaryDirectory() as td:
            not_a_dir = Path(td) / "does_not_exist"
            pack = _acquire_repo_evidence_for_planning(not_a_dir)
        self.assertIsNone(pack)


class RepositoryStateUnavailableReasonTest(unittest.TestCase):
    def test_none_when_pack_is_current(self):
        with _make_temp_git_repo() as td:
            root = Path(td)
            pack = acquire_repo_evidence(root, Authorization(authorized_by="t", authorization_note="t"))
            reason = _repository_state_unavailable_reason(root, "mision", pack)
        self.assertIsNone(reason)

    def test_reason_when_pack_is_none(self):
        with _make_temp_git_repo() as td:
            reason = _repository_state_unavailable_reason(Path(td), "mision", None)
        self.assertIsNotNone(reason)

    def test_reason_when_pack_is_stale(self):
        with _make_temp_git_repo() as td:
            root = Path(td)
            pack = acquire_repo_evidence(root, Authorization(authorized_by="t", authorization_note="t"))
            (root / "a.py").write_text("VALUE = 2\n", encoding="utf-8")  # dirty, no new commit
            reason = _repository_state_unavailable_reason(root, "mision", pack)
        self.assertEqual("repository_evidence_stale", reason)


if __name__ == "__main__":
    unittest.main()
