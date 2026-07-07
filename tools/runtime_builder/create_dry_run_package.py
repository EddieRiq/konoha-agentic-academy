#!/usr/bin/env python3
"""
Konoha Dry-run Package Builder CLI.

Creates a dry-run runtime package JSON file for later validation by the
read-only runtime validator.

This tool is not a runtime executor. It never executes shell commands, never
performs Git operations, never invokes adapters, and never reads private
Village context. It only writes a generated JSON package to an explicit output
location, with guardrails around private and repository-control paths.

Exit codes:
  0 = package generated
  1 = build failed because output already exists or validation guard failed
  2 = CLI/input error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SAFE_FLAGS: dict[str, bool] = {
    "shell_execution": False,
    "filesystem_mutation": False,
    "git_operations": False,
    "adapter_execution": False,
    "private_context_access": False,
    "autonomous_execution": False,
}

PREFERRED_OUTPUT_ROOTS = (
    Path("sandbox/tmp"),
    Path("sandbox/runs"),
    Path("examples/dry_run_packages"),
)

BLOCKED_PATH_PARTS = {
    ".git",
    ".hg",
    ".svn",
    "kirigakure",
    "private-library",
    "vault",
    ".venv",
}

BLOCKED_SUFFIXES = {
    ".env",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
}


class BuildError(ValueError):
    """Raised when the package builder refuses to generate output."""


@dataclass(frozen=True)
class BuildRequest:
    package_id: str
    mission_id: str
    mission_title: str
    scope: str
    requested_by: str
    mission_charter_reference: str
    output: Path
    force: bool = False
    allow_output_outside_sandbox: bool = False


def slugify(value: str) -> str:
    """Return a conservative slug for IDs and path defaults."""
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-._")
    if not normalized:
        raise BuildError("Slug cannot be empty.")
    return normalized


def default_package_id(title: str) -> str:
    return f"{slugify(title)}-dry-run-package"


def default_mission_id(package_id: str) -> str:
    return f"mission-{slugify(package_id)}"


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def validate_output_path(output: Path, allow_output_outside_sandbox: bool) -> None:
    """Validate that output is not targeting private or repository-control paths."""
    parts = {part.lower() for part in output.parts}

    if parts & BLOCKED_PATH_PARTS:
        blocked = ", ".join(sorted(parts & BLOCKED_PATH_PARTS))
        raise BuildError(f"Refusing to write into blocked path component(s): {blocked}.")

    if output.name.lower() in BLOCKED_SUFFIXES or output.suffix.lower() in BLOCKED_SUFFIXES:
        raise BuildError(f"Refusing to write sensitive-looking output path: {output}.")

    if not allow_output_outside_sandbox:
        if not any(is_relative_to(output, root) for root in PREFERRED_OUTPUT_ROOTS):
            allowed = ", ".join(str(root) for root in PREFERRED_OUTPUT_ROOTS)
            raise BuildError(
                f"Output must be under one of [{allowed}] unless "
                "--allow-output-outside-sandbox is provided."
            )


def resolve_output_file(output: Path) -> Path:
    """Resolve a directory or JSON file target into the package JSON path."""
    if output.suffix.lower() == ".json":
        return output
    return output / "runtime_package.json"


def make_step(step_id: str, description: str, action_type: str, evidence: list[str]) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "description": description,
        "action_type": action_type,
        "execution_allowed": False,
        "expected_evidence": evidence,
        "stop_conditions": [
            "Execution requested",
            "Filesystem mutation requested",
            "Git operation requested",
            "Private context required",
            "Adapter invocation requested",
        ],
    }


def build_runtime_package(request: BuildRequest) -> dict[str, Any]:
    """Build a runtime package object without reading external context."""
    package_id = slugify(request.package_id)
    mission_id = slugify(request.mission_id)

    included_artifacts = [
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

    package: dict[str, Any] = {
        "schema_version": "0.11.0",
        "package_id": package_id,
        "mission_id": mission_id,
        "mode": "dry_run",
        "execution_authorized": False,
        "safety_flags": dict(SAFE_FLAGS),
        "mission_intake": {
            "artifact_type": "mission_intake",
            "mission_id": mission_id,
            "mission_title": request.mission_title,
            "requested_by": request.requested_by,
            "mission_charter_reference": request.mission_charter_reference,
            "scope": request.scope,
            "out_of_scope": [
                "Executing shell commands",
                "Mutating repository files",
                "Git operations",
                "Adapter invocation",
                "Private Village context access",
                "Autonomous mission execution",
            ],
            "private_context_required": False,
            "approval_state": "draft",
            "safety_flags": dict(SAFE_FLAGS),
        },
        "dry_run_execution_plan": {
            "artifact_type": "dry_run_execution_plan",
            "mission_id": mission_id,
            "mode": "dry_run",
            "plan_summary": (
                "Generate a dry-run runtime package for review. "
                "No mission execution is authorized or performed."
            ),
            "steps": [
                make_step(
                    "step-001",
                    "Capture public mission scope as a dry-run intake record.",
                    "plan",
                    ["Mission title", "Mission scope", "Out-of-scope boundaries"],
                ),
                make_step(
                    "step-002",
                    "Generate runtime package records with all execution flags blocked.",
                    "package",
                    ["Runtime package JSON", "Safety flags"],
                ),
                make_step(
                    "step-003",
                    "Validate the generated package with the read-only runtime validator.",
                    "validate",
                    ["Validator pass/fail output"],
                ),
            ],
            "safety_flags": dict(SAFE_FLAGS),
        },
        "adapter_invocation_stub": {
            "artifact_type": "adapter_invocation_stub",
            "mission_id": mission_id,
            "adapter_name": "none",
            "stub_mode": "stub_only",
            "invocation_allowed": False,
            "intended_request": {},
            "blocked_capabilities": [
                "adapter execution",
                "shell execution",
                "filesystem mutation",
                "Git operations",
                "private context access",
            ],
            "safety_flags": dict(SAFE_FLAGS),
        },
        "evidence_collection_stub": {
            "artifact_type": "evidence_collection_stub",
            "mission_id": mission_id,
            "collection_mode": "declared_only",
            "automatic_collection_allowed": False,
            "expected_evidence": [
                "Generated runtime package JSON",
                "Runtime validator output",
                "Reviewer decision",
            ],
            "missing_evidence": [
                "Validator output not collected by builder",
                "Reviewer decision not collected by builder",
            ],
            "safety_flags": dict(SAFE_FLAGS),
        },
        "runtime_state": {
            "artifact_type": "runtime_state",
            "mission_id": mission_id,
            "state": "draft",
            "mode": "dry_run",
            "current_phase": "package_generation",
            "open_blockers": [
                "Package has not yet been validated",
                "Package has not yet been reviewed",
                "Execution remains unauthorized",
            ],
            "safety_flags": dict(SAFE_FLAGS),
        },
        "runtime_validation_report": {
            "artifact_type": "runtime_validation_report",
            "mission_id": mission_id,
            "validation_outcome": "not_run",
            "validated_artifacts": [],
            "errors": [],
            "warnings": [
                "Validation report is a placeholder until the read-only validator is run."
            ],
            "execution_authorized": False,
            "safety_flags": dict(SAFE_FLAGS),
        },
        "runtime_trace": {
            "events": [
                {
                    "artifact_type": "runtime_trace_event",
                    "event_id": "trace-001",
                    "mission_id": mission_id,
                    "event_type": "package_generation",
                    "summary": (
                        "Dry-run package generated by builder. "
                        "No execution performed."
                    ),
                    "evidence_references": [
                        "runtime_package.json",
                    ],
                    "supersedes": None,
                    "execution_performed": False,
                }
            ]
        },
        "runtime_package_manifest": {
            "artifact_type": "runtime_package_manifest",
            "package_id": package_id,
            "mission_id": mission_id,
            "package_version": "0.11.0",
            "mode": "dry_run",
            "included_artifacts": included_artifacts,
            "closure_state": "draft",
            "execution_authorized": False,
            "safety_flags": dict(SAFE_FLAGS),
        },
        "runtime_package_index": {
            "artifact_type": "runtime_package_index",
            "package_id": package_id,
            "mission_id": mission_id,
            "artifacts": [
                {"artifact_type": artifact, "reference": artifact, "status": "present"}
                for artifact in included_artifacts
                if artifact != "runtime_trace"
            ] + [
                {
                    "artifact_type": "runtime_trace",
                    "reference": "runtime_trace.events",
                    "status": "present",
                }
            ],
            "trace_references": [
                "runtime_trace.events[0]",
            ],
            "validation_references": [
                "runtime_validation_report",
            ],
        },
    }

    return package


def write_runtime_package(package: dict[str, Any], output_file: Path, force: bool = False) -> Path:
    """Write a package JSON file after checking overwrite rules."""
    if output_file.exists() and not force:
        raise BuildError(f"Output already exists: {output_file}. Use --force to overwrite.")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(package, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return output_file


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a Konoha dry-run runtime package JSON file without "
            "executing mission actions."
        )
    )
    parser.add_argument("--title", required=True, help="Public mission title.")
    parser.add_argument("--scope", required=True, help="Public dry-run mission scope.")
    parser.add_argument("--package-id", help="Package ID. Defaults to a slug from --title.")
    parser.add_argument("--mission-id", help="Mission ID. Defaults to mission-<package-id>.")
    parser.add_argument("--requested-by", default="example-user", help="Requester label.")
    parser.add_argument(
        "--mission-charter-reference",
        default="not-provided",
        help="Reference to a public Mission Charter or dry-run example.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory or .json file. Defaults to sandbox/tmp/<package-id>/runtime_package.json.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing package JSON.")
    parser.add_argument(
        "--allow-output-outside-sandbox",
        action="store_true",
        help=(
            "Allow writing outside sandbox/tmp, sandbox/runs, or examples/dry_run_packages. "
            "Private and repository-control paths remain blocked."
        ),
    )
    return parser.parse_args(argv)


def build_request_from_args(args: argparse.Namespace) -> BuildRequest:
    package_id = slugify(args.package_id or default_package_id(args.title))
    mission_id = slugify(args.mission_id or default_mission_id(package_id))
    output = args.output or Path("sandbox/tmp") / package_id

    return BuildRequest(
        package_id=package_id,
        mission_id=mission_id,
        mission_title=args.title,
        scope=args.scope,
        requested_by=args.requested_by,
        mission_charter_reference=args.mission_charter_reference,
        output=output,
        force=args.force,
        allow_output_outside_sandbox=args.allow_output_outside_sandbox,
    )


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        request = build_request_from_args(args)
        validate_output_path(request.output, request.allow_output_outside_sandbox)
        output_file = resolve_output_file(request.output)
        validate_output_path(output_file, request.allow_output_outside_sandbox)

        package = build_runtime_package(request)
        written = write_runtime_package(package, output_file, force=request.force)

    except BuildError as exc:
        print(f"BUILDER FAILED: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"BUILDER ERROR: {exc}", file=sys.stderr)
        return 2

    print("PACKAGE GENERATED")
    print(f"Package: {package['package_id']}")
    print(f"Mission: {package['mission_id']}")
    print(f"Mode: {package['mode']}")
    print(f"Output: {written}")
    print("Execution: blocked")
    print("Filesystem mutation: package output only")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Adapter execution: blocked")
    print("")
    print("Next validation command:")
    print(f"python tools/runtime_validator/validate_runtime_package.py {written}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
