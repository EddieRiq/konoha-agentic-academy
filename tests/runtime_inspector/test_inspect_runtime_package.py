from __future__ import annotations

import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.runtime_inspector.inspect_runtime_package import (  # noqa: E402
    inspect_runtime_package,
    main as inspector_main,
)


def minimal_package() -> dict:
    flags = {
        "shell_execution": False,
        "filesystem_mutation": False,
        "git_operations": False,
        "adapter_execution": False,
        "private_context_access": False,
        "autonomous_execution": False,
    }

    mission_id = "mission-inspector-test"
    package_id = "inspector-test-package"

    return {
        "schema_version": "0.12.0",
        "package_id": package_id,
        "mission_id": mission_id,
        "mode": "dry_run",
        "execution_authorized": False,
        "safety_flags": dict(flags),
        "mission_intake": {
            "artifact_type": "mission_intake",
            "mission_id": mission_id,
            "mission_title": "Inspector test package",
            "requested_by": "unit-test",
            "mission_charter_reference": "tests/runtime_inspector/test_inspect_runtime_package.py",
            "scope": "Inspect a public dry-run package.",
            "out_of_scope": ["Shell execution", "Git operations", "Private context access"],
            "private_context_required": False,
            "approval_state": "approved_for_dry_run",
            "safety_flags": dict(flags),
        },
        "dry_run_execution_plan": {
            "artifact_type": "dry_run_execution_plan",
            "mission_id": mission_id,
            "mode": "dry_run",
            "plan_summary": "Inspect package structure without executing actions.",
            "steps": [
                {
                    "step_id": "step-001",
                    "description": "Inspect structure.",
                    "action_type": "inspect",
                    "execution_allowed": False,
                    "expected_evidence": ["Inspection report"],
                    "stop_conditions": ["Execution requested"],
                }
            ],
            "safety_flags": dict(flags),
        },
        "adapter_invocation_stub": {
            "artifact_type": "adapter_invocation_stub",
            "mission_id": mission_id,
            "adapter_name": "none",
            "stub_mode": "stub_only",
            "invocation_allowed": False,
            "intended_request": {},
            "blocked_capabilities": ["adapter execution"],
            "safety_flags": dict(flags),
        },
        "evidence_collection_stub": {
            "artifact_type": "evidence_collection_stub",
            "mission_id": mission_id,
            "collection_mode": "declared_only",
            "automatic_collection_allowed": False,
            "expected_evidence": ["Inspection report"],
            "missing_evidence": [],
            "safety_flags": dict(flags),
        },
        "runtime_state": {
            "artifact_type": "runtime_state",
            "mission_id": mission_id,
            "state": "review_ready",
            "mode": "dry_run",
            "current_phase": "inspection",
            "open_blockers": [],
            "safety_flags": dict(flags),
        },
        "runtime_validation_report": {
            "artifact_type": "runtime_validation_report",
            "mission_id": mission_id,
            "validation_outcome": "passed",
            "validated_artifacts": [
                "mission_intake",
                "dry_run_execution_plan",
                "adapter_invocation_stub",
                "evidence_collection_stub",
                "runtime_state",
                "runtime_package_manifest",
                "runtime_package_index",
            ],
            "errors": [],
            "warnings": [],
            "execution_authorized": False,
            "safety_flags": dict(flags),
        },
        "runtime_trace": {
            "events": [
                {
                    "artifact_type": "runtime_trace_event",
                    "event_id": "trace-001",
                    "mission_id": mission_id,
                    "event_type": "inspection",
                    "summary": "Package prepared for inspection. No execution performed.",
                    "evidence_references": ["runtime_package.json"],
                    "supersedes": None,
                    "execution_performed": False,
                }
            ]
        },
        "runtime_package_manifest": {
            "artifact_type": "runtime_package_manifest",
            "package_id": package_id,
            "mission_id": mission_id,
            "package_version": "0.12.0",
            "mode": "dry_run",
            "included_artifacts": [
                "mission_intake",
                "dry_run_execution_plan",
                "adapter_invocation_stub",
                "evidence_collection_stub",
                "runtime_state",
                "runtime_validation_report",
                "runtime_trace",
                "runtime_package_manifest",
                "runtime_package_index",
            ],
            "closure_state": "review_ready",
            "execution_authorized": False,
            "safety_flags": dict(flags),
        },
        "runtime_package_index": {
            "artifact_type": "runtime_package_index",
            "package_id": package_id,
            "mission_id": mission_id,
            "artifacts": [
                {"artifact_type": "mission_intake", "reference": "mission_intake", "status": "present"},
                {"artifact_type": "dry_run_execution_plan", "reference": "dry_run_execution_plan", "status": "present"},
                {"artifact_type": "adapter_invocation_stub", "reference": "adapter_invocation_stub", "status": "present"},
                {"artifact_type": "evidence_collection_stub", "reference": "evidence_collection_stub", "status": "present"},
                {"artifact_type": "runtime_state", "reference": "runtime_state", "status": "present"},
                {"artifact_type": "runtime_validation_report", "reference": "runtime_validation_report", "status": "present"},
                {"artifact_type": "runtime_trace", "reference": "runtime_trace.events", "status": "present"},
                {"artifact_type": "runtime_package_manifest", "reference": "runtime_package_manifest", "status": "present"},
                {"artifact_type": "runtime_package_index", "reference": "runtime_package_index", "status": "present"},
            ],
            "trace_references": ["runtime_trace.events[0]"],
            "validation_references": ["runtime_validation_report"],
        },
    }


class ReadOnlyRuntimeInspectorTests(unittest.TestCase):
    def test_minimal_package_passes_inspection(self) -> None:
        report = inspect_runtime_package(minimal_package())

        self.assertTrue(report.passed)
        self.assertEqual(report.errors, 0)
        self.assertEqual(report.summary["present_sections"], 9)

    def test_detects_execution_authorized(self) -> None:
        package = minimal_package()
        package["execution_authorized"] = True

        report = inspect_runtime_package(package)

        self.assertFalse(report.passed)
        self.assertGreaterEqual(report.errors, 1)
        self.assertTrue(any(f.code == "execution_authorized" for f in report.findings))

    def test_detects_missing_required_section(self) -> None:
        package = minimal_package()
        del package["runtime_trace"]

        report = inspect_runtime_package(package)

        self.assertFalse(report.passed)
        self.assertTrue(any(f.code == "required_section_missing" for f in report.findings))

    def test_detects_private_reference(self) -> None:
        package = minimal_package()
        package["mission_intake"]["mission_charter_reference"] = "alliance/kirigakure/private-library/source.md"

        report = inspect_runtime_package(package)

        self.assertFalse(report.passed)
        self.assertTrue(any(f.code == "private_reference_detected" for f in report.findings))

    def test_cli_json_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_path = Path(tmp) / "runtime_package.json"
            package_path.write_text(json.dumps(minimal_package()), encoding="utf-8")

            output = StringIO()
            with redirect_stdout(output):
                exit_code = inspector_main([str(package_path), "--json"])

            self.assertEqual(exit_code, 0)
            parsed = json.loads(output.getvalue())
            self.assertTrue(parsed["passed"])
            self.assertEqual(parsed["summary"]["present_sections"], 9)


if __name__ == "__main__":
    unittest.main()
