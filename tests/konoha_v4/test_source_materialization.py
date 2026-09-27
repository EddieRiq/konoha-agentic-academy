"""Worker delivery must use the exact retained, bounded resolution."""
import dataclasses
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.konoha_v4 import required_sources as rs
from tools.konoha_v4.models import AgentAssignment, EvidenceRecord
from tools.repo_evidence.acquire_repo_evidence import acquire_repo_evidence, Authorization


def context(**kwargs):
    values = dict(plan_approval_status="approved", plan_acceptance_criteria=("done",),
                  user_mission_request="exact human text\n", repo_root=None,
                  repo_evidence_pack=None, family_contracts={"test": {"purpose": "test"}},
                  task_family_by_id={}, evidence_by_task_id={},
                  mission_plan={"mission_id": "mission-test", "understanding": "test"})
    values.update(kwargs)
    return rs.ResolutionContext(**values)


def task(**kwargs):
    values = dict(task_id="t", family="test", provider="codex", model="codex",
                  objective="test", inputs=[], expected_output="evidence")
    values.update(kwargs)
    return AgentAssignment(**values)


class SourceMaterializationTests(unittest.TestCase):
    def test_every_canonical_available_source_has_deliverable_material(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "input.py").write_text("def main(): return 1\n")
            (root / "memory" / "failures").mkdir(parents=True)
            (root / "memory" / "failures" / "failure.md").write_text("Synthetic observed failure")
            rows = []
            for name, material in {"implementation_diff": "locator=input.py:1",
                "test_evidence": "command=synthetic test | result=pass",
                "review_evidence": "verdict=approved", "source_fact_cards": "fact=fixture | locator=input.py:1"}.items():
                rows.extend([{"source": "produced_source", "observation": f"source_id={name}"},
                             {"source": "material:" + name, "observation": material}])
            record = EvidenceRecord.build(mission_id="mission-test", task_id="d", provider="codex", model="codex",
                status="completed", output=json.dumps({"summary": "observed fixture", "evidence": rows}),
                token_usage={}, command=[], started_at=0, finished_at=1)
            ctx = context(repo_root=root, repo_evidence_pack=acquire_repo_evidence(root, Authorization("human", "fixture")),
                failure_log_dir=root / "memory" / "failures", task_family_by_id={"d": "producer"},
                family_contracts={"test": {"purpose": "fixture"}, "producer": {"produces_sources": list(rs._MATERIAL_VALIDATORS)}},
                evidence_by_task_id={"d": record})
            result = rs.resolve_all(list(rs.SOURCE_VOCABULARY), task(inputs=["input.py"], dependencies=["d"]), ctx, enforcing=True)
            for name, resolution in result.items():
                with self.subTest(source=name):
                    self.assertEqual(resolution.availability, rs.SourceAvailability.AVAILABLE, resolution.reason)
                    self.assertTrue(resolution.materialization)
            self.assertEqual(set(rs.materialize_resolved_sources(result)), set(rs.SOURCE_VOCABULARY))

    def test_retained_helpers_are_pure_and_reject_available_without_material(self):
        retained = {"mission_plan": rs.SourceResolution("mission_plan", rs.SourceAvailability.AVAILABLE)}
        self.assertEqual(rs.find_available_sources_without_material(retained), ("mission_plan",))
        with self.assertRaises(ValueError):
            rs.materialize_resolved_sources(retained)
        retained = rs.resolve_all(["mission_plan", "acceptance_criteria", "user_mission_request",
                                   "capability_registry"], task(), context(), enforcing=True)
        with mock.patch.object(rs, "resolve_all", side_effect=AssertionError("second resolve")), \
             mock.patch.object(rs.os, "open", side_effect=AssertionError("filesystem")):
            self.assertEqual(rs.find_available_sources_without_material(retained), ())
            bundle = rs.materialize_resolved_sources(retained)
        self.assertEqual(bundle["user_mission_request"]["text"], "exact human text\n")

    def test_original_request_is_exact_or_fails_closed(self):
        for raw in (None, {}, "", "x" * (rs.MAX_MATERIAL_TEXT_CHARS + 1)):
            with self.subTest(raw_type=type(raw).__name__):
                result = rs.resolve_required_sources("user_mission_request", task(), context(user_mission_request=raw), enforcing=True)
                self.assertEqual(result.availability, rs.SourceAvailability.MISSING)

    def test_input_text_bounded_and_all_selected_inputs_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.py").write_text("a" * 30000)
            ctx = context(repo_root=root)
            result = rs.resolve_required_sources("python_source_files", task(inputs=["a.py"]), ctx, enforcing=True)
            self.assertEqual(result.availability, rs.SourceAvailability.AVAILABLE)
            item = result.materialization["files"]["items"][0]
            self.assertEqual(item["included_bytes"], rs.MAX_MATERIAL_FILE_BYTES)
            self.assertTrue(item["truncated"])
            for inputs in (["a.py", "missing.py"], ["../a.py"], ["/a.py"]):
                result = rs.resolve_required_sources("python_source_files", task(inputs=inputs), ctx, enforcing=True)
                self.assertNotEqual(result.availability, rs.SourceAvailability.AVAILABLE)
            (root / "alias.py").symlink_to(root / "a.py")
            result = rs.resolve_required_sources("python_source_files", task(inputs=["alias.py"]), ctx, enforcing=True)
            self.assertEqual(result.availability, rs.SourceAvailability.UNAUTHORIZED)

    def test_dependency_material_never_contains_raw_output(self):
        payload = {"summary": "s" * 9000, "evidence": [{"source": "a.py:1", "observation": "v" * 5000}] * 60}
        record = EvidenceRecord.build(mission_id="mission-test", task_id="d", provider="codex", model="codex",
            status="completed", output=json.dumps(payload), token_usage={}, command=[], started_at=0, finished_at=1)
        ctx = context(evidence_by_task_id={"d": record})
        result = rs.resolve_required_sources("dependency_evidence_bundle", task(dependencies=["d"]), ctx, enforcing=True)
        # Oversized persisted output is rejected before parsing, never passed through.
        self.assertEqual(result.availability, rs.SourceAvailability.MISSING)
        record.output = json.dumps({"summary": "bounded summary", "evidence": [{"source": "a.py:1", "observation": "fact"}]})
        result = rs.resolve_required_sources("dependency_evidence_bundle", task(dependencies=["d"]), ctx, enforcing=True)
        self.assertEqual(result.availability, rs.SourceAvailability.AVAILABLE)
        self.assertNotIn('"output"', json.dumps(result.materialization))
        for raw in ('[]', '{}', 'null', '{', '[' * 10000, '\ud800'):
            record.output = raw
            result = rs.resolve_required_sources("dependency_evidence_bundle", task(dependencies=["d"]), ctx, enforcing=True)
            self.assertEqual(result.availability, rs.SourceAvailability.MISSING)
