#!/usr/bin/env python3
"""Read-only Runtime Run Registry CLI.

Lists dry-run runtime runs from a sandbox root.

Safety boundary:
- reads sandbox run manifests and runtime run summaries;
- prints text or JSON reports to stdout;
- does not execute shell commands;
- does not perform Git operations;
- does not invoke adapters;
- does not access private context;
- does not modify files.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


REGISTRY_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    path: str
    state: str
    has_manifest: bool
    has_runtime_package: bool
    has_validation_report: bool
    has_inspection_report: bool
    has_run_summary: bool
    mode: str
    validation: str
    inspection: str
    execution: str
    filesystem_mutation: str
    git_operations: str
    private_context_access: str
    adapter_execution: str
    network_access: str
    blockers: list[str]


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError as exc:
        return None, f"invalid_json:{exc.msg}"
    except OSError as exc:
        return None, f"read_error:{exc.__class__.__name__}"

    if not isinstance(value, dict):
        return None, "invalid_json:not_object"

    return value, None


def _safe_relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _get_first(data: dict[str, Any] | None, keys: list[str], default: str = "unknown") -> str:
    if not data:
        return default

    for key in keys:
        value: Any = data
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                value = None
                break
            value = value[part]
        if value is not None:
            if isinstance(value, bool):
                return "blocked" if value is False else "enabled"
            return str(value)

    return default


def inspect_run(run_dir: Path, sandbox_root: Path) -> RunRecord:
    manifest_path = run_dir / "sandbox_run_manifest.json"
    package_path = run_dir / "runtime_package.json"
    validation_path = run_dir / "validation_report.json"
    inspection_path = run_dir / "inspection_report.json"
    summary_path = run_dir / "runtime_run_summary.json"

    manifest, manifest_error = _load_json(manifest_path)
    summary, summary_error = _load_json(summary_path)

    blockers: list[str] = []
    if manifest_error == "missing":
        blockers.append("missing_sandbox_run_manifest")
    elif manifest_error:
        blockers.append(f"sandbox_run_manifest_{manifest_error}")

    if summary_error == "missing":
        blockers.append("missing_runtime_run_summary")
    elif summary_error:
        blockers.append(f"runtime_run_summary_{summary_error}")

    if not package_path.exists():
        blockers.append("missing_runtime_package")

    if not validation_path.exists():
        blockers.append("missing_validation_report")

    if not inspection_path.exists():
        blockers.append("missing_inspection_report")

    execution = _get_first(
        summary,
        ["safety.execution", "safety_boundary.execution", "execution"],
        default=_get_first(manifest, ["execution"], "unknown"),
    )
    filesystem_mutation = _get_first(
        summary,
        ["safety.filesystem_mutation", "safety_boundary.filesystem_mutation", "filesystem_mutation"],
        default=_get_first(manifest, ["filesystem_mutation"], "unknown"),
    )
    git_operations = _get_first(
        summary,
        ["safety.git_operations", "safety_boundary.git_operations", "git_operations"],
        default=_get_first(manifest, ["git_operations"], "unknown"),
    )
    private_context_access = _get_first(
        summary,
        ["safety.private_context_access", "safety_boundary.private_context_access", "private_context_access"],
        default=_get_first(manifest, ["private_context_access"], "unknown"),
    )
    adapter_execution = _get_first(
        summary,
        ["safety.adapter_execution", "safety_boundary.adapter_execution", "adapter_execution"],
        default=_get_first(manifest, ["adapter_execution"], "unknown"),
    )
    network_access = _get_first(
        summary,
        ["safety.network_access", "safety_boundary.network_access", "network_access"],
        default=_get_first(manifest, ["network_access"], "unknown"),
    )

    for name, value in [
        ("execution", execution),
        ("git_operations", git_operations),
        ("private_context_access", private_context_access),
        ("adapter_execution", adapter_execution),
        ("network_access", network_access),
    ]:
        if value not in {"blocked", "false", "False"}:
            blockers.append(f"{name}_not_blocked")

    if filesystem_mutation not in {"sandbox only", "sandbox_only", "blocked"}:
        blockers.append("filesystem_mutation_not_sandbox_only")

    validation = _get_first(summary, ["validation.status", "validation_status"], "unknown")
    if validation == "unknown":
        validation_passed = _get_first(summary, ["validation.passed"], "unknown")
        if validation_passed == "enabled":
            validation = "passed"
        elif validation_passed == "blocked":
            validation = "failed"

    inspection = _get_first(summary, ["inspection.status", "inspection_status"], "unknown")
    if inspection == "unknown":
        inspection_passed = _get_first(summary, ["inspection.passed"], "unknown")
        if inspection_passed == "enabled":
            inspection = "passed"
        elif inspection_passed == "blocked":
            inspection = "failed"
    mode = _get_first(summary, ["mode"], default=_get_first(manifest, ["mode"], "unknown"))

    if blockers:
        state = "incomplete_or_blocked"
    elif validation.lower() == "passed" and inspection.lower() == "passed":
        state = "passed"
    else:
        state = "review_required"

    return RunRecord(
        run_id=run_dir.name,
        path=_safe_relative_path(run_dir, sandbox_root),
        state=state,
        has_manifest=manifest_path.exists(),
        has_runtime_package=package_path.exists(),
        has_validation_report=validation_path.exists(),
        has_inspection_report=inspection_path.exists(),
        has_run_summary=summary_path.exists(),
        mode=mode,
        validation=validation,
        inspection=inspection,
        execution=execution,
        filesystem_mutation=filesystem_mutation,
        git_operations=git_operations,
        private_context_access=private_context_access,
        adapter_execution=adapter_execution,
        network_access=network_access,
        blockers=blockers,
    )


def list_runs(sandbox_root: Path, include_incomplete: bool = True) -> list[RunRecord]:
    runs_root = sandbox_root / "runs"

    if not runs_root.exists():
        return []

    if not runs_root.is_dir():
        raise ValueError(f"runs path is not a directory: {runs_root}")

    records: list[RunRecord] = []
    for child in sorted(runs_root.iterdir(), key=lambda item: item.name):
        if child.is_dir():
            record = inspect_run(child, sandbox_root)
            if include_incomplete or record.state == "passed":
                records.append(record)

    return records


def build_report(sandbox_root: Path, records: list[RunRecord]) -> dict[str, Any]:
    state_counts: dict[str, int] = {}
    for record in records:
        state_counts[record.state] = state_counts.get(record.state, 0) + 1

    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "tool": "runtime_run_registry",
        "sandbox_root": sandbox_root.as_posix(),
        "run_count": len(records),
        "state_counts": state_counts,
        "runs": [asdict(record) for record in records],
        "safety": {
            "execution": "blocked",
            "filesystem_mutation": "read_only",
            "git_operations": "blocked",
            "private_context_access": "blocked",
            "adapter_execution": "blocked",
            "network_access": "blocked",
        },
    }


def print_text_report(report: dict[str, Any]) -> None:
    print("RUNTIME RUN REGISTRY")
    print(f"Sandbox root: {report['sandbox_root']}")
    print(f"Runs: {report['run_count']}")
    print("Execution: blocked")
    print("Filesystem mutation: read_only")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Adapter execution: blocked")
    print("Network access: blocked")

    runs = report.get("runs", [])
    if not runs:
        print("No runs found.")
        return

    print("")
    for run in runs:
        print(f"- {run['run_id']}: {run['state']} | validation={run['validation']} | inspection={run['inspection']}")
        if run["blockers"]:
            print(f"  blockers: {', '.join(run['blockers'])}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List dry-run runtime runs from a local sandbox.")
    parser.add_argument("--sandbox-root", default="sandbox", help="Sandbox root directory. Default: sandbox")
    parser.add_argument("--json", action="store_true", help="Print JSON report to stdout.")
    parser.add_argument(
        "--passed-only",
        action="store_true",
        help="Only include runs with passed validation and inspection and no blockers.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    sandbox_root = Path(args.sandbox_root).resolve()

    try:
        records = list_runs(sandbox_root, include_incomplete=not args.passed_only)
    except ValueError as exc:
        print("RUNTIME RUN REGISTRY FAILED")
        print(str(exc))
        return 1

    report = build_report(sandbox_root, records)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
