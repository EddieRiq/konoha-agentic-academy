"""Run a Konoha dry-run runtime package through the safe local toolchain.

This CLI is an orchestration runner, not a mission executor.

Allowed behavior:
- prepare a sandbox run directory;
- generate one dry-run runtime package JSON inside that run directory;
- validate the package with the read-only validator API;
- inspect the package with the read-only inspector API;
- write validation, inspection, and run summary reports inside the run directory;
- print a clear PASS/FAIL result.

Blocked behavior:
- shell execution;
- Git operations;
- adapter invocation;
- network access;
- private context access;
- writes outside the declared sandbox root;
- mission execution.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.runtime_builder.create_dry_run_package import (  # noqa: E402
    BuildRequest,
    build_runtime_package,
    default_mission_id,
    default_package_id,
    slugify,
)
from tools.runtime_inspector.inspect_runtime_package import inspect_runtime_package  # noqa: E402
from tools.runtime_validator.validate_runtime_package import validate_runtime_package  # noqa: E402
from tools.sandbox_boundary.prepare_sandbox_run import prepare_sandbox_run  # noqa: E402
from tools.sandbox_boundary.sandbox_guard import (  # noqa: E402
    SandboxBoundaryError,
    ensure_within_root,
    resolve_sandbox_root,
    validate_safe_id,
)


RUNNER_VERSION = "0.14.0"


class RuntimeRunnerError(ValueError):
    """Raised when dry-run runtime orchestration cannot continue safely."""


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp without microseconds."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def json_default(value: Any) -> Any:
    """JSON encoder fallback for dataclasses and Path objects."""
    if isinstance(value, Path):
        return str(value)
    try:
        return asdict(value)
    except TypeError:
        return str(value)


def write_json(path: Path, payload: dict[str, Any], *, root: Path, force: bool = False) -> Path:
    """Write a JSON file inside the sandbox root only."""
    safe_path = ensure_within_root(root, path)

    if safe_path.exists() and not force:
        raise RuntimeRunnerError(f"refusing to overwrite existing artifact without --force: {safe_path}")

    safe_path.parent.mkdir(parents=True, exist_ok=True)
    safe_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=json_default) + "\n",
        encoding="utf-8",
    )
    return safe_path


def validation_result_to_jsonable(result: Any) -> dict[str, Any]:
    """Convert the validator result to a stable report payload."""
    return {
        "schema_version": RUNNER_VERSION,
        "kind": "konoha.runtime_validation_result",
        "passed": bool(result.passed),
        "package_id": result.package_id,
        "mission_id": result.mission_id,
        "mode": result.mode,
        "errors": list(result.errors),
        "warnings": list(result.warnings),
        "safety_boundary": {
            "execution": "blocked",
            "filesystem_mutation": "blocked",
            "git_operations": "blocked",
            "private_context_access": "blocked",
            "adapter_execution": "blocked",
        },
    }


def append_trace_event(package: dict[str, Any], *, event_type: str, summary: str, references: list[str]) -> None:
    """Append a non-executing trace event to the runtime package."""
    trace = package.setdefault("runtime_trace", {})
    events = trace.setdefault("events", [])
    mission_id = str(package.get("mission_id", "unknown"))
    event_id = f"trace-{len(events) + 1:03d}"

    events.append(
        {
            "artifact_type": "runtime_trace_event",
            "event_id": event_id,
            "mission_id": mission_id,
            "event_type": event_type,
            "summary": summary,
            "evidence_references": references,
            "supersedes": None,
            "execution_performed": False,
            "created_at_utc": utc_now(),
        }
    )


def update_package_after_validation(package: dict[str, Any], validation_payload: dict[str, Any]) -> None:
    """Embed validation status into the runtime package without authorizing execution."""
    validated_artifacts = [
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

    package["schema_version"] = RUNNER_VERSION
    package["execution_authorized"] = False

    package["runtime_validation_report"] = {
        "artifact_type": "runtime_validation_report",
        "mission_id": package["mission_id"],
        "validation_outcome": "passed" if validation_payload["passed"] else "failed",
        "validated_at_utc": utc_now(),
        "validated_artifacts": validated_artifacts,
        "errors": validation_payload["errors"],
        "warnings": validation_payload["warnings"],
        "execution_authorized": False,
        "safety_flags": dict(package["safety_flags"]),
    }

    package["runtime_state"]["state"] = "validated" if validation_payload["passed"] else "blocked"
    package["runtime_state"]["current_phase"] = "inspection"
    package["runtime_state"]["open_blockers"] = (
        ["Inspector has not yet completed", "Execution remains unauthorized"]
        if validation_payload["passed"]
        else ["Validation failed", "Execution remains unauthorized"]
    )

    package["runtime_package_manifest"]["package_version"] = RUNNER_VERSION
    package["runtime_package_manifest"]["closure_state"] = (
        "validation_passed" if validation_payload["passed"] else "validation_failed"
    )
    package["runtime_package_manifest"]["execution_authorized"] = False

    append_trace_event(
        package,
        event_type="validation_completed",
        summary="Read-only validator completed. No execution was performed.",
        references=["validation_report.json"],
    )


def update_package_after_inspection(package: dict[str, Any], inspection_payload: dict[str, Any]) -> None:
    """Embed inspection trace/state into the package without authorizing execution."""
    passed = bool(inspection_payload.get("passed"))

    package["runtime_state"]["state"] = "review_ready" if passed else "blocked"
    package["runtime_state"]["current_phase"] = "dry_run_runner_completed"
    package["runtime_state"]["open_blockers"] = (
        ["Human review still required", "Execution remains unauthorized"]
        if passed
        else ["Inspection failed", "Human review required", "Execution remains unauthorized"]
    )

    package["runtime_package_manifest"]["closure_state"] = (
        "review_ready"
        if passed
        else "blocked"
    )

    append_trace_event(
        package,
        event_type="inspection_completed",
        summary="Read-only inspector completed. No execution was performed.",
        references=["inspection_report.json"],
    )


def build_summary(
    *,
    run_id: str,
    run_dir: Path,
    sandbox_root: Path,
    package: dict[str, Any],
    validation_payload: dict[str, Any],
    inspection_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build the runner summary report."""
    passed = bool(validation_payload["passed"]) and bool(inspection_payload["passed"])
    relative_run_dir = run_dir.relative_to(sandbox_root)

    return {
        "schema_version": RUNNER_VERSION,
        "kind": "konoha.dry_run_runtime_runner_summary",
        "runner_version": RUNNER_VERSION,
        "run_id": run_id,
        "package_id": package["package_id"],
        "mission_id": package["mission_id"],
        "mission_title": package["mission_intake"]["mission_title"],
        "mode": "dry_run",
        "status": "passed" if passed else "failed",
        "created_at_utc": utc_now(),
        "sandbox_root": str(sandbox_root),
        "run_directory": str(relative_run_dir).replace("\\", "/"),
        "artifacts": {
            "sandbox_manifest": "sandbox_run_manifest.json",
            "runtime_package": "runtime_package.json",
            "validation_report": "validation_report.json",
            "inspection_report": "inspection_report.json",
            "runtime_run_summary": "runtime_run_summary.json",
        },
        "validation": {
            "passed": bool(validation_payload["passed"]),
            "errors": len(validation_payload["errors"]),
            "warnings": len(validation_payload["warnings"]),
        },
        "inspection": {
            "passed": bool(inspection_payload["passed"]),
            "errors": int(inspection_payload.get("errors", 0)),
            "warnings": int(inspection_payload.get("warnings", 0)),
        },
        "safety_boundary": {
            "execution": "blocked",
            "filesystem_mutation": "sandbox_only",
            "git_operations": "blocked",
            "private_context_access": "blocked",
            "adapter_execution": "blocked",
            "network_access": "blocked",
        },
        "notes": [
            "This runner orchestrates sandbox preparation, package generation, validation, and inspection only.",
            "It does not execute missions or authorize runtime actions.",
            "All generated artifacts are written inside the declared sandbox run directory.",
        ],
    }


def run_dry_run_runtime(
    *,
    title: str,
    scope: str,
    run_id: str,
    sandbox_root: str | Path = "sandbox",
    requested_by: str = "konoha-runtime-runner",
    mission_charter_reference: str = "dry-run-runtime-runner-cli",
    force: bool = False,
) -> dict[str, Any]:
    """Run the safe dry-run runtime orchestration chain.

    Returns a summary dictionary. Raises RuntimeRunnerError or SandboxBoundaryError
    when the run cannot continue safely.
    """
    if not title or not title.strip():
        raise RuntimeRunnerError("title must not be empty")

    if not scope or not scope.strip():
        raise RuntimeRunnerError("scope must not be empty")

    safe_run_id = validate_safe_id(run_id, "run_id")
    root = resolve_sandbox_root(sandbox_root)

    manifest_path = prepare_sandbox_run(
        sandbox_root=root,
        run_id=safe_run_id,
        mission_title=title,
        force=force,
    )

    run_dir = ensure_within_root(root, manifest_path.parent)
    package_path = ensure_within_root(root, run_dir / "runtime_package.json")
    validation_report_path = ensure_within_root(root, run_dir / "validation_report.json")
    inspection_report_path = ensure_within_root(root, run_dir / "inspection_report.json")
    summary_path = ensure_within_root(root, run_dir / "runtime_run_summary.json")

    package_id = default_package_id(safe_run_id)
    mission_id = default_mission_id(package_id)

    request = BuildRequest(
        package_id=package_id,
        mission_id=mission_id,
        mission_title=title.strip(),
        scope=scope.strip(),
        requested_by=requested_by.strip() or "konoha-runtime-runner",
        mission_charter_reference=mission_charter_reference.strip() or "dry-run-runtime-runner-cli",
        output=package_path,
        force=force,
        allow_output_outside_sandbox=False,
    )

    package = build_runtime_package(request)
    package["schema_version"] = RUNNER_VERSION
    package["runtime_state"]["current_phase"] = "validation"
    append_trace_event(
        package,
        event_type="runner_started",
        summary="Dry-run runtime runner started inside sandbox boundary. No execution was performed.",
        references=["sandbox_run_manifest.json"],
    )
    append_trace_event(
        package,
        event_type="package_generated",
        summary="Runtime package generated in memory by the dry-run builder API. No execution was performed.",
        references=["runtime_package.json"],
    )

    initial_validation = validate_runtime_package(package)
    validation_payload = validation_result_to_jsonable(initial_validation)
    update_package_after_validation(package, validation_payload)

    final_validation = validate_runtime_package(package)
    validation_payload = validation_result_to_jsonable(final_validation)
    update_package_after_validation(package, validation_payload)

    inspection = inspect_runtime_package(package)
    inspection_payload = inspection.to_jsonable()
    update_package_after_inspection(package, inspection_payload)

    final_inspection = inspect_runtime_package(package)
    inspection_payload = final_inspection.to_jsonable()

    summary = build_summary(
        run_id=safe_run_id,
        run_dir=run_dir,
        sandbox_root=root,
        package=package,
        validation_payload=validation_payload,
        inspection_payload=inspection_payload,
    )

    write_json(package_path, package, root=root, force=force)
    write_json(validation_report_path, validation_payload, root=root, force=force)
    write_json(inspection_report_path, inspection_payload, root=root, force=force)
    write_json(summary_path, summary, root=root, force=force)

    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Konoha dry-run runtime orchestration without executing mission actions."
    )
    parser.add_argument("--title", required=True, help="Mission title for the dry-run runtime package.")
    parser.add_argument("--scope", required=True, help="Public, generic mission scope for the dry-run package.")
    parser.add_argument("--run-id", required=True, help="Safe run identifier. Single path segment only.")
    parser.add_argument(
        "--sandbox-root",
        default="sandbox",
        help="Sandbox root for generated run artifacts. Default: sandbox",
    )
    parser.add_argument(
        "--requested-by",
        default="konoha-runtime-runner",
        help="Requester label stored in mission intake.",
    )
    parser.add_argument(
        "--mission-charter-reference",
        default="dry-run-runtime-runner-cli",
        help="Reference to the Mission Charter or dry-run source.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite artifacts for this sandbox run.")
    parser.add_argument("--json", action="store_true", help="Emit the runtime run summary as JSON.")
    return parser.parse_args(argv)


def print_text_summary(summary: dict[str, Any]) -> None:
    """Print a stable human-readable summary."""
    status = str(summary["status"]).upper()

    if status == "PASSED":
        print("DRY-RUN RUNTIME PASSED")
    else:
        print("DRY-RUN RUNTIME FAILED")

    print(f"Run: {summary['run_id']}")
    print(f"Package: {summary['package_id']}")
    print(f"Mission: {summary['mission_id']}")
    print(f"Mode: {summary['mode']}")
    print(f"Run directory: {summary['run_directory']}")
    print(f"Validation: {'passed' if summary['validation']['passed'] else 'failed'}")
    print(f"Inspection: {'passed' if summary['inspection']['passed'] else 'failed'}")
    print("Execution: blocked")
    print("Filesystem mutation: sandbox only")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Adapter execution: blocked")
    print("Network access: blocked")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        summary = run_dry_run_runtime(
            title=args.title,
            scope=args.scope,
            run_id=args.run_id,
            sandbox_root=args.sandbox_root,
            requested_by=args.requested_by,
            mission_charter_reference=args.mission_charter_reference,
            force=args.force,
        )
    except (RuntimeRunnerError, SandboxBoundaryError) as exc:
        if args.json:
            print(json.dumps({"passed": False, "status": "failed", "errors": [str(exc)]}, indent=2))
        else:
            print("DRY-RUN RUNTIME FAILED")
            print(f"Reason: {exc}")
        return 1
    except ValueError as exc:
        if args.json:
            print(json.dumps({"passed": False, "status": "error", "errors": [str(exc)]}, indent=2))
        else:
            print("DRY-RUN RUNTIME ERROR")
            print(f"Reason: {exc}")
        return 2

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text_summary(summary)

    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
