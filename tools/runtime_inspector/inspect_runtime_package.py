#!/usr/bin/env python3
"""
Konoha Read-only Runtime Inspector CLI.

Inspects a dry-run runtime package JSON file for internal consistency,
traceability, and safety-boundary signals.

This tool is not a runtime executor and not an auto-fixer. It reads one JSON
package, reports findings, and exits. It never executes shell commands, never
performs Git operations, never invokes adapters, never reads private Village
context, and never modifies inspected files.

Exit codes:
  0 = inspection completed with no errors
  1 = inspection found one or more errors
  2 = CLI/input error
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable


SAFE_FLAG_KEYS = (
    "shell_execution",
    "filesystem_mutation",
    "git_operations",
    "adapter_execution",
    "private_context_access",
    "autonomous_execution",
)

REQUIRED_SECTIONS = (
    "mission_intake",
    "dry_run_execution_plan",
    "adapter_invocation_stub",
    "evidence_collection_stub",
    "runtime_state",
    "runtime_validation_report",
    "runtime_trace",
    "runtime_package_manifest",
    "runtime_package_index",
)

BOOLEAN_BLOCK_FIELDS = {
    "execution_authorized",
    "execution_allowed",
    "invocation_allowed",
    "automatic_collection_allowed",
    "private_context_required",
    "execution_performed",
    "shell_execution",
    "filesystem_mutation",
    "git_operations",
    "adapter_execution",
    "private_context_access",
    "autonomous_execution",
}

PRIVATE_REFERENCE_FRAGMENTS = (
    "alliance/kirigakure",
    "alliance\\kirigakure",
    "kirienv",
    "effective-python-brett-slatkin",
    "brett slatkin",
    "praise for effective python",
    "private-library",
    ".venv",
)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class InspectionReport:
    passed: bool
    package_id: str
    mission_id: str
    mode: str
    errors: int
    warnings: int
    findings: list[Finding]
    summary: dict[str, Any]

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "package_id": self.package_id,
            "mission_id": self.mission_id,
            "mode": self.mode,
            "errors": self.errors,
            "warnings": self.warnings,
            "findings": [asdict(finding) for finding in self.findings],
            "summary": self.summary,
            "safety_boundary": {
                "execution": "blocked",
                "filesystem_mutation": "blocked",
                "git_operations": "blocked",
                "private_context_access": "blocked",
                "adapter_execution": "blocked",
            },
        }


def resolve_input_path(path: Path) -> Path:
    """Resolve a JSON file path or directory containing runtime_package.json."""
    if path.is_dir():
        candidate = path / "runtime_package.json"
        if candidate.exists():
            return candidate
        raise ValueError(f"Directory does not contain runtime_package.json: {path}")

    if not path.exists():
        raise ValueError(f"Input path does not exist: {path}")

    if path.suffix.lower() != ".json":
        raise ValueError(f"Runtime inspector expects a JSON file: {path}")

    return path


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Runtime package root must be a JSON object.")

    return data


def add(findings: list[Finding], severity: str, code: str, path: str, message: str) -> None:
    findings.append(Finding(severity=severity, code=code, path=path, message=message))


def iter_values(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value

    if isinstance(value, dict):
        for key, item in value.items():
            yield from iter_values(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from iter_values(item, f"{path}[{index}]")


def check_safety_flags(flags: Any, path: str, findings: list[Finding]) -> None:
    if not isinstance(flags, dict):
        add(findings, "error", "safety_flags_missing", path, "Safety flags must be an object.")
        return

    for flag in SAFE_FLAG_KEYS:
        if flag not in flags:
            add(findings, "error", "safety_flag_missing", f"{path}.{flag}", "Required safety flag is missing.")
        elif flags[flag] is not False:
            add(
                findings,
                "error",
                "safety_flag_not_blocked",
                f"{path}.{flag}",
                "Safety flag must be false for dry-run packages.",
            )


def check_root_contract(package: dict[str, Any], findings: list[Finding]) -> None:
    package_id = package.get("package_id")
    mission_id = package.get("mission_id")

    if not package.get("schema_version"):
        add(findings, "error", "schema_version_missing", "$.schema_version", "schema_version is required.")

    if not isinstance(package_id, str) or not package_id:
        add(findings, "error", "package_id_missing", "$.package_id", "package_id is required.")

    if not isinstance(mission_id, str) or not mission_id:
        add(findings, "error", "mission_id_missing", "$.mission_id", "mission_id is required.")

    if package.get("mode") != "dry_run":
        add(findings, "error", "mode_not_dry_run", "$.mode", "Runtime package mode must be dry_run.")

    if package.get("execution_authorized") is not False:
        add(
            findings,
            "error",
            "execution_authorized",
            "$.execution_authorized",
            "execution_authorized must be false.",
        )

    check_safety_flags(package.get("safety_flags"), "$.safety_flags", findings)


def check_required_sections(package: dict[str, Any], findings: list[Finding]) -> None:
    root_mission_id = package.get("mission_id")

    for section in REQUIRED_SECTIONS:
        if section not in package:
            add(findings, "error", "required_section_missing", f"$.{section}", "Required runtime section is missing.")
            continue

        value = package[section]
        if not isinstance(value, dict):
            add(findings, "error", "required_section_not_object", f"$.{section}", "Required section must be an object.")
            continue

        section_mission_id = value.get("mission_id")
        if section_mission_id and root_mission_id and section_mission_id != root_mission_id:
            add(
                findings,
                "error",
                "mission_id_mismatch",
                f"$.{section}.mission_id",
                "Section mission_id does not match root mission_id.",
            )

        if isinstance(value.get("safety_flags"), dict):
            check_safety_flags(value.get("safety_flags"), f"$.{section}.safety_flags", findings)


def check_boolean_boundaries(package: dict[str, Any], findings: list[Finding]) -> None:
    for path, value in iter_values(package):
        key = path.rsplit(".", 1)[-1]
        if key in BOOLEAN_BLOCK_FIELDS and value is True:
            add(
                findings,
                "error",
                "blocked_boolean_true",
                path,
                f"{key} must not be true in a dry-run package.",
            )


def check_trace(package: dict[str, Any], findings: list[Finding]) -> None:
    trace = package.get("runtime_trace")
    if not isinstance(trace, dict):
        return

    events = trace.get("events")
    if not isinstance(events, list) or not events:
        add(findings, "error", "trace_events_missing", "$.runtime_trace.events", "Trace must include at least one event.")
        return

    seen_event_ids: set[str] = set()

    for index, event in enumerate(events):
        event_path = f"$.runtime_trace.events[{index}]"
        if not isinstance(event, dict):
            add(findings, "error", "trace_event_not_object", event_path, "Trace event must be an object.")
            continue

        event_id = event.get("event_id")
        if not event_id:
            add(findings, "warning", "trace_event_id_missing", f"{event_path}.event_id", "Trace event has no event_id.")
        elif event_id in seen_event_ids:
            add(findings, "warning", "trace_event_id_duplicate", f"{event_path}.event_id", "Trace event_id is duplicated.")
        else:
            seen_event_ids.add(str(event_id))

        if event.get("execution_performed") is not False:
            add(
                findings,
                "error",
                "trace_execution_performed",
                f"{event_path}.execution_performed",
                "Trace event must not report execution_performed=true.",
            )


def check_manifest(package: dict[str, Any], findings: list[Finding]) -> None:
    manifest = package.get("runtime_package_manifest")
    if not isinstance(manifest, dict):
        return

    included = manifest.get("included_artifacts")
    if not isinstance(included, list):
        add(
            findings,
            "error",
            "manifest_included_artifacts_missing",
            "$.runtime_package_manifest.included_artifacts",
            "Manifest must include included_artifacts list.",
        )
        return

    included_set = {str(item) for item in included}

    for section in REQUIRED_SECTIONS:
        if section not in included_set:
            add(
                findings,
                "warning",
                "manifest_artifact_not_listed",
                "$.runtime_package_manifest.included_artifacts",
                f"{section} is present in the contract but not listed in the manifest.",
            )

    if manifest.get("execution_authorized") is not False:
        add(
            findings,
            "error",
            "manifest_execution_authorized",
            "$.runtime_package_manifest.execution_authorized",
            "Manifest must not authorize execution.",
        )

    closure_state = str(manifest.get("closure_state", "")).lower()
    if "execut" in closure_state and closure_state not in {"execution_blocked", "not_executed"}:
        add(
            findings,
            "warning",
            "closure_state_mentions_execution",
            "$.runtime_package_manifest.closure_state",
            "Closure state mentions execution; reviewer should verify that it is framed as blocked or not executed.",
        )


def check_index(package: dict[str, Any], findings: list[Finding]) -> None:
    index = package.get("runtime_package_index")
    if not isinstance(index, dict):
        return

    artifacts = index.get("artifacts")
    if not isinstance(artifacts, list):
        add(
            findings,
            "error",
            "index_artifacts_missing",
            "$.runtime_package_index.artifacts",
            "Package index must include artifacts list.",
        )
        return

    indexed_types: set[str] = set()

    for idx, item in enumerate(artifacts):
        item_path = f"$.runtime_package_index.artifacts[{idx}]"
        if not isinstance(item, dict):
            add(findings, "warning", "index_artifact_not_object", item_path, "Index artifact entry should be an object.")
            continue

        artifact_type = item.get("artifact_type")
        status = item.get("status")

        if artifact_type:
            indexed_types.add(str(artifact_type))
        else:
            add(findings, "warning", "index_artifact_type_missing", f"{item_path}.artifact_type", "Index artifact type is missing.")

        if status not in {"present", "declared", "placeholder", "review_ready"}:
            add(
                findings,
                "warning",
                "index_artifact_status_unusual",
                f"{item_path}.status",
                "Index artifact status should explain whether the artifact is present, declared, placeholder, or review_ready.",
            )

    for section in REQUIRED_SECTIONS:
        if section not in indexed_types:
            add(
                findings,
                "warning",
                "index_section_not_listed",
                "$.runtime_package_index.artifacts",
                f"{section} is not listed as an index artifact.",
            )


def check_validation_report(package: dict[str, Any], findings: list[Finding]) -> None:
    report = package.get("runtime_validation_report")
    if not isinstance(report, dict):
        return

    outcome = str(report.get("validation_outcome", "")).lower()

    if outcome in {"failed", "blocked", "error", "invalid"}:
        add(
            findings,
            "error",
            "validation_report_failed",
            "$.runtime_validation_report.validation_outcome",
            "Validation report outcome indicates failure or blocking.",
        )
    elif outcome in {"", "not_run", "pending"}:
        add(
            findings,
            "warning",
            "validation_report_not_run",
            "$.runtime_validation_report.validation_outcome",
            "Validation report is not marked as passed; run the read-only validator before release.",
        )

    errors = report.get("errors")
    if isinstance(errors, list) and errors:
        add(
            findings,
            "error",
            "validation_report_errors_present",
            "$.runtime_validation_report.errors",
            "Validation report contains errors.",
        )

    if report.get("execution_authorized") is not False:
        add(
            findings,
            "error",
            "validation_report_authorizes_execution",
            "$.runtime_validation_report.execution_authorized",
            "Validation report must not authorize execution.",
        )


def check_private_references(package: dict[str, Any], findings: list[Finding]) -> None:
    for path, value in iter_values(package):
        if not isinstance(value, str):
            continue

        lower_value = value.lower()
        for fragment in PRIVATE_REFERENCE_FRAGMENTS:
            if fragment in lower_value:
                add(
                    findings,
                    "error",
                    "private_reference_detected",
                    path,
                    f"Package contains blocked private/local reference fragment: {fragment}",
                )


def inspect_runtime_package(package: dict[str, Any]) -> InspectionReport:
    findings: list[Finding] = []

    check_root_contract(package, findings)
    check_required_sections(package, findings)
    check_boolean_boundaries(package, findings)
    check_trace(package, findings)
    check_manifest(package, findings)
    check_index(package, findings)
    check_validation_report(package, findings)
    check_private_references(package, findings)

    errors = sum(1 for finding in findings if finding.severity == "error")
    warnings = sum(1 for finding in findings if finding.severity == "warning")

    present_sections = [section for section in REQUIRED_SECTIONS if isinstance(package.get(section), dict)]
    missing_sections = [section for section in REQUIRED_SECTIONS if section not in present_sections]

    summary = {
        "required_sections": len(REQUIRED_SECTIONS),
        "present_sections": len(present_sections),
        "missing_sections": missing_sections,
        "trace_events": len(package.get("runtime_trace", {}).get("events", []))
        if isinstance(package.get("runtime_trace"), dict)
        else 0,
        "safety_flags": "blocked" if errors == 0 else "review_required",
    }

    return InspectionReport(
        passed=errors == 0,
        package_id=str(package.get("package_id", "unknown")),
        mission_id=str(package.get("mission_id", "unknown")),
        mode=str(package.get("mode", "unknown")),
        errors=errors,
        warnings=warnings,
        findings=findings,
        summary=summary,
    )


def print_text_report(report: InspectionReport) -> None:
    if report.passed and report.warnings:
        print("INSPECTION PASSED WITH WARNINGS")
    elif report.passed:
        print("INSPECTION PASSED")
    else:
        print("INSPECTION FAILED")

    print(f"Package: {report.package_id}")
    print(f"Mission: {report.mission_id}")
    print(f"Mode: {report.mode}")
    print(f"Required sections: {report.summary['present_sections']}/{report.summary['required_sections']}")
    print(f"Trace events: {report.summary['trace_events']}")
    print(f"Errors: {report.errors}")
    print(f"Warnings: {report.warnings}")
    print("Execution: blocked")
    print("Filesystem mutation: blocked")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Adapter execution: blocked")

    if report.findings:
        print("\nFindings:")
        for finding in report.findings:
            print(f"- [{finding.severity}] {finding.code} at {finding.path}: {finding.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a Konoha dry-run runtime package JSON file without executing actions."
    )
    parser.add_argument("path", help="Path to a runtime package JSON file or directory containing runtime_package.json.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable inspection report to stdout.")
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Return exit code 1 when warnings are present, even without errors.",
    )
    args = parser.parse_args(argv)

    try:
        input_path = resolve_input_path(Path(args.path))
        package = load_json(input_path)
    except ValueError as exc:
        if args.json:
            print(json.dumps({"passed": False, "errors": [str(exc)]}, indent=2))
        else:
            print(f"INSPECTOR ERROR: {exc}", file=sys.stderr)
        return 2

    report = inspect_runtime_package(package)

    if args.json:
        print(json.dumps(report.to_jsonable(), indent=2))
    else:
        print_text_report(report)

    if not report.passed:
        return 1

    if args.strict_warnings and report.warnings:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
