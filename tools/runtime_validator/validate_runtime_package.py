#!/usr/bin/env python3
"""
Konoha Runtime Validator MVP.

Read-only validator for dry-run runtime packages.

This tool validates JSON package artifacts. It never executes shell commands,
never mutates repository files, never performs Git operations, never invokes
adapters, and never reads private Village context unless the user explicitly
passes a package file located there.

Exit codes:
  0 = validation passed
  1 = validation failed
  2 = input or tool error
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL_SECTIONS = [
    "mission_intake",
    "dry_run_execution_plan",
    "adapter_invocation_stub",
    "evidence_collection_stub",
    "runtime_state",
    "runtime_validation_report",
    "runtime_trace",
    "runtime_package_manifest",
    "runtime_package_index",
]

FORBIDDEN_TRUE_FLAGS = [
    "shell_execution",
    "filesystem_mutation",
    "git_operations",
    "adapter_execution",
    "private_context_access",
    "autonomous_execution",
]

EXPECTED_ARTIFACT_TYPES = {
    "mission_intake": "mission_intake",
    "dry_run_execution_plan": "dry_run_execution_plan",
    "adapter_invocation_stub": "adapter_invocation_stub",
    "evidence_collection_stub": "evidence_collection_stub",
    "runtime_state": "runtime_state",
    "runtime_validation_report": "runtime_validation_report",
    "runtime_package_manifest": "runtime_package_manifest",
    "runtime_package_index": "runtime_package_index",
}


@dataclass
class ValidationResult:
    package_id: str = "unknown"
    mission_id: str = "unknown"
    mode: str = "unknown"
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Input not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def resolve_input_path(path: Path) -> Path:
    """Resolve a file or directory input without writing anything."""
    if path.is_file():
        return path

    if not path.is_dir():
        raise ValueError(f"Input path is neither a file nor a directory: {path}")

    preferred = path / "runtime_package.json"
    if preferred.exists():
        return preferred

    candidates = sorted(path.glob("*.runtime_package.json"))
    if len(candidates) == 1:
        return candidates[0]

    if not candidates:
        raise ValueError(
            f"No runtime package JSON found in directory: {path}. "
            "Expected runtime_package.json or exactly one *.runtime_package.json file."
        )

    raise ValueError(
        f"Multiple *.runtime_package.json files found in directory: {path}. "
        "Pass one explicit file path."
    )


def as_dict(value: Any, section: str, result: ValidationResult) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    result.errors.append(f"{section} must be an object.")
    return {}


def check_false_flag(container: dict[str, Any], field: str, label: str, result: ValidationResult) -> None:
    value = container.get(field)
    if value is not False:
        result.errors.append(f"{label}.{field} must be false; got {value!r}.")


def check_safety_flags(flags: Any, label: str, result: ValidationResult) -> None:
    flags_dict = as_dict(flags, f"{label}.safety_flags", result)
    for flag in FORBIDDEN_TRUE_FLAGS:
        if flag not in flags_dict:
            result.errors.append(f"{label}.safety_flags.{flag} is required and must be false.")
        elif flags_dict[flag] is not False:
            result.errors.append(f"{label}.safety_flags.{flag} must be false; got {flags_dict[flag]!r}.")


def check_artifact_type(section: dict[str, Any], expected: str, label: str, result: ValidationResult) -> None:
    actual = section.get("artifact_type")
    if actual != expected:
        result.errors.append(f"{label}.artifact_type must be {expected!r}; got {actual!r}.")


def validate_runtime_package(package: dict[str, Any]) -> ValidationResult:
    result = ValidationResult(
        package_id=str(package.get("package_id", "unknown")),
        mission_id=str(package.get("mission_id", "unknown")),
        mode=str(package.get("mode", "unknown")),
    )

    if package.get("mode") != "dry_run":
        result.errors.append("Top-level mode must be 'dry_run'.")

    check_false_flag(package, "execution_authorized", "package", result)
    check_safety_flags(package.get("safety_flags"), "package", result)

    for section in REQUIRED_TOP_LEVEL_SECTIONS:
        if section not in package:
            result.errors.append(f"Missing required section: {section}.")

    # Stop early only after collecting missing-section errors.
    if any(f"Missing required section" in err for err in result.errors):
        return result

    for section_key, expected_type in EXPECTED_ARTIFACT_TYPES.items():
        section = as_dict(package.get(section_key), section_key, result)
        check_artifact_type(section, expected_type, section_key, result)

        if "mission_id" in section and str(section.get("mission_id")) != result.mission_id:
            result.errors.append(
                f"{section_key}.mission_id must match top-level mission_id "
                f"{result.mission_id!r}; got {section.get('mission_id')!r}."
            )

        if "safety_flags" in section:
            check_safety_flags(section.get("safety_flags"), section_key, result)

    mission_intake = as_dict(package.get("mission_intake"), "mission_intake", result)
    if mission_intake.get("private_context_required") is True:
        result.errors.append("mission_intake.private_context_required must not be true for public dry-run packages.")
    if mission_intake.get("approval_state") not in {"approved_for_dry_run", "draft", "blocked"}:
        result.errors.append("mission_intake.approval_state must be draft, approved_for_dry_run, or blocked.")

    plan = as_dict(package.get("dry_run_execution_plan"), "dry_run_execution_plan", result)
    if plan.get("mode") != "dry_run":
        result.errors.append("dry_run_execution_plan.mode must be 'dry_run'.")
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        result.errors.append("dry_run_execution_plan.steps must be a non-empty list.")
    else:
        for idx, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                result.errors.append(f"dry_run_execution_plan.steps[{idx}] must be an object.")
                continue
            if step.get("execution_allowed") is not False:
                result.errors.append(f"dry_run_execution_plan.steps[{idx}].execution_allowed must be false.")

    adapter = as_dict(package.get("adapter_invocation_stub"), "adapter_invocation_stub", result)
    if adapter.get("stub_mode") != "stub_only":
        result.errors.append("adapter_invocation_stub.stub_mode must be 'stub_only'.")
    check_false_flag(adapter, "invocation_allowed", "adapter_invocation_stub", result)

    evidence = as_dict(package.get("evidence_collection_stub"), "evidence_collection_stub", result)
    if evidence.get("collection_mode") != "declared_only":
        result.errors.append("evidence_collection_stub.collection_mode must be 'declared_only'.")
    check_false_flag(evidence, "automatic_collection_allowed", "evidence_collection_stub", result)

    state = as_dict(package.get("runtime_state"), "runtime_state", result)
    if state.get("mode") != "dry_run":
        result.errors.append("runtime_state.mode must be 'dry_run'.")

    report = as_dict(package.get("runtime_validation_report"), "runtime_validation_report", result)
    check_false_flag(report, "execution_authorized", "runtime_validation_report", result)

    trace = as_dict(package.get("runtime_trace"), "runtime_trace", result)
    events = trace.get("events")
    if not isinstance(events, list) or not events:
        result.errors.append("runtime_trace.events must be a non-empty list.")
    else:
        for idx, event in enumerate(events, start=1):
            if not isinstance(event, dict):
                result.errors.append(f"runtime_trace.events[{idx}] must be an object.")
                continue
            if event.get("artifact_type") != "runtime_trace_event":
                result.errors.append(f"runtime_trace.events[{idx}].artifact_type must be 'runtime_trace_event'.")
            if str(event.get("mission_id")) != result.mission_id:
                result.errors.append(f"runtime_trace.events[{idx}].mission_id must match top-level mission_id.")
            check_false_flag(event, "execution_performed", f"runtime_trace.events[{idx}]", result)

    manifest = as_dict(package.get("runtime_package_manifest"), "runtime_package_manifest", result)
    if manifest.get("mode") != "dry_run":
        result.errors.append("runtime_package_manifest.mode must be 'dry_run'.")
    check_false_flag(manifest, "execution_authorized", "runtime_package_manifest", result)

    index = as_dict(package.get("runtime_package_index"), "runtime_package_index", result)
    artifacts = index.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        result.errors.append("runtime_package_index.artifacts must be a non-empty list.")

    # Soft completeness warnings.
    if result.passed:
        for section in REQUIRED_TOP_LEVEL_SECTIONS:
            if section not in manifest.get("included_artifacts", []):
                result.warnings.append(f"{section} is present but not listed in runtime_package_manifest.included_artifacts.")

    return result


def print_text_result(result: ValidationResult) -> None:
    if result.passed:
        print("VALIDATION PASSED")
    else:
        print("VALIDATION FAILED")

    print(f"Package: {result.package_id}")
    print(f"Mission: {result.mission_id}")
    print(f"Mode: {result.mode}")
    print("Execution: blocked")
    print("Filesystem mutation: blocked")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Adapter execution: blocked")

    if result.errors:
        print("\nErrors:")
        for err in result.errors:
            print(f"- {err}")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"- {warning}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Konoha dry-run runtime package JSON file without executing actions."
    )
    parser.add_argument("path", help="Path to a runtime package JSON file or directory containing one.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable validation result.")
    args = parser.parse_args(argv)

    try:
        input_path = resolve_input_path(Path(args.path))
        data = load_json(input_path)
        if not isinstance(data, dict):
            raise ValueError("Runtime package root must be a JSON object.")
    except ValueError as exc:
        if args.json:
            print(json.dumps({"passed": False, "errors": [str(exc)]}, indent=2))
        else:
            print(f"VALIDATOR ERROR: {exc}", file=sys.stderr)
        return 2

    result = validate_runtime_package(data)

    if args.json:
        print(json.dumps({
            "passed": result.passed,
            "package_id": result.package_id,
            "mission_id": result.mission_id,
            "mode": result.mode,
            "errors": result.errors,
            "warnings": result.warnings,
            "safety_boundary": {
                "execution": "blocked",
                "filesystem_mutation": "blocked",
                "git_operations": "blocked",
                "private_context_access": "blocked",
                "adapter_execution": "blocked",
            },
        }, indent=2))
    else:
        print_text_result(result)

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
