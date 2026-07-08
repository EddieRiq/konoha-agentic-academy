#!/usr/bin/env python3
"""
Konoha Product Runtime Bootstrap.

This CLI is the first product-oriented command surface after v1.0.0.
It initializes a local workspace, runs a read-only doctor, creates mission
workspace skeletons, validates public config shape, and delegates dry-run
missions to the existing safe workflow tool.

It does not execute mission actions, invoke real adapters, use network access,
perform Git write operations, access private context, or authorize runtime
actions.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


VERSION = "1.1.0"
DEFAULT_WORKSPACE_ROOT = "sandbox/workspace"
DEFAULT_CONFIG_PATH = "konoha.config.example.json"

SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")

REQUIRED_PUBLIC_PATHS = [
    "README.md",
    "konoha.config.example.json",
    "tools/konoha_cli.py",
    "tools/release_readiness/check_v1_release_readiness.py",
    "tools/mission_workflow/run_dry_run_mission.py",
    "tools/config_validator/validate_konoha_config.py",
    "docs/reference/capability_matrix.md",
    "docs/reference/release_safety_boundaries.md",
]

WORKSPACE_DIRS = [
    "missions",
    "reports",
    "state",
    "tmp",
]

MISSION_DIRS = [
    "inputs",
    "context",
    "plans",
    "outputs",
    "reports",
    "approvals",
]

SAFETY_BOUNDARIES = {
    "execution": "blocked",
    "filesystem_mutation": "workspace and delegated sandbox outputs only",
    "repository_apply": "blocked by bootstrap CLI",
    "git_operations": "read-only or delegated gated tools only",
    "git_write_operations": "blocked by bootstrap CLI",
    "private_context_access": "blocked",
    "adapter_execution": "blocked by bootstrap CLI",
    "real_adapter_execution": "blocked",
    "network_access": "blocked",
}


class KonohaError(Exception):
    """Expected CLI error."""


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_path(repo_root: Path, relative_path: str) -> Path:
    return repo_root / Path(relative_path)


def validate_safe_id(value: str, label: str) -> str:
    if not value:
        raise KonohaError(f"{label} is required")
    if "/" in value or "\\" in value or value in {".", ".."}:
        raise KonohaError(f"{label} must not contain path separators")
    if not SAFE_ID_PATTERN.match(value):
        raise KonohaError(f"{label} must be alphanumeric plus '.', '_' or '-'")
    return value


def resolve_under(root: Path, relative_path: str) -> Path:
    root = root.resolve()
    candidate = (root / Path(relative_path)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise KonohaError(f"path escapes root: {relative_path}") from exc
    return candidate


def read_json_file(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise KonohaError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise KonohaError(f"invalid JSON file: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise KonohaError(f"JSON root must be an object: {path}")
    return data


def write_json(path: Path, data: Dict[str, Any], force: bool = False) -> None:
    if path.exists() and not force:
        raise KonohaError(f"refusing to overwrite existing file without --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str, force: bool = False) -> None:
    if path.exists() and not force:
        raise KonohaError(f"refusing to overwrite existing file without --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_common_report(status: str, command: str) -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "tool": "konoha_product_runtime_bootstrap",
        "tool_version": VERSION,
        "status": status,
        "command": command,
        "generated_at": now_utc(),
        "safety_boundaries": dict(SAFETY_BOUNDARIES),
        "blockers": [],
    }


def doctor_report(repo_root: Path, workspace_root: str, config_path: str) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    report = build_common_report("passed", "doctor")
    report["repo_root"] = str(repo_root)
    report["workspace_root"] = workspace_root
    report["config_path"] = config_path

    missing = [
        item for item in REQUIRED_PUBLIC_PATHS
        if not repo_path(repo_root, item).exists()
    ]

    workspace = resolve_under(repo_root, workspace_root)
    report["required_public_paths"] = {
        "checked": len(REQUIRED_PUBLIC_PATHS),
        "missing": missing,
    }
    report["workspace"] = {
        "path": str(workspace),
        "exists": workspace.exists(),
        "expected_directories": WORKSPACE_DIRS,
    }

    config_result = validate_config_shape(repo_path(repo_root, config_path))
    report["config_validation"] = config_result

    blockers: List[str] = []
    if missing:
        blockers.append("missing required public paths")
    if config_result["status"] != "passed":
        blockers.extend(config_result["blockers"])

    report["blockers"] = blockers
    if blockers:
        report["status"] = "failed"

    return report


def validate_config_shape(config_file: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "status": "passed",
        "config_file": str(config_file),
        "checks": {
            "json_object": False,
            "mentions_sandbox": False,
            "mentions_approval": False,
            "mentions_blocked": False,
        },
        "blockers": [],
    }

    try:
        data = read_json_file(config_file)
    except KonohaError as exc:
        result["status"] = "failed"
        result["blockers"] = [str(exc)]
        return result

    serialized = json.dumps(data, sort_keys=True).lower()
    result["checks"]["json_object"] = True
    result["checks"]["mentions_sandbox"] = "sandbox" in serialized
    result["checks"]["mentions_approval"] = "approval" in serialized
    result["checks"]["mentions_blocked"] = "blocked" in serialized

    for key, passed in result["checks"].items():
        if not passed:
            result["blockers"].append(f"config check failed: {key}")

    if result["blockers"]:
        result["status"] = "failed"
    return result


def init_workspace(repo_root: Path, workspace_root: str, force: bool = False) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    workspace = resolve_under(repo_root, workspace_root)
    report = build_common_report("passed", "init")
    report["repo_root"] = str(repo_root)
    report["workspace_root"] = str(workspace)

    created_dirs: List[str] = []
    for rel in WORKSPACE_DIRS:
        directory = resolve_under(workspace, rel)
        directory.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(directory))

    manifest = {
        "schema_version": "1.0",
        "workspace_type": "konoha_product_runtime_workspace",
        "created_at": now_utc(),
        "tool_version": VERSION,
        "workspace_root": str(workspace),
        "directories": WORKSPACE_DIRS,
        "safety_boundaries": dict(SAFETY_BOUNDARIES),
    }
    manifest_path = workspace / "workspace_manifest.json"
    write_json(manifest_path, manifest, force=force)

    report["created_directories"] = created_dirs
    report["manifest_path"] = str(manifest_path)
    return report


def create_mission(
    repo_root: Path,
    workspace_root: str,
    mission_id: str,
    title: str,
    scope: str,
    force: bool = False,
) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    mission_id = validate_safe_id(mission_id, "mission_id")
    workspace = resolve_under(repo_root, workspace_root)
    missions_root = resolve_under(workspace, "missions")
    mission_dir = resolve_under(missions_root, mission_id)

    report = build_common_report("passed", "mission new")
    report["repo_root"] = str(repo_root)
    report["workspace_root"] = str(workspace)
    report["mission_id"] = mission_id
    report["mission_dir"] = str(mission_dir)

    if mission_dir.exists() and any(mission_dir.iterdir()) and not force:
        raise KonohaError(f"mission already exists; use --force to overwrite generated files: {mission_id}")

    mission_dir.mkdir(parents=True, exist_ok=True)
    for rel in MISSION_DIRS:
        resolve_under(mission_dir, rel).mkdir(parents=True, exist_ok=True)

    charter = f"""# Mission Charter: {title}

## Mission ID

`{mission_id}`

## Scope

{scope}

## Execution boundary

Execution: blocked.

This workspace is for planning, evidence, proposed outputs, approvals, reports, and human review.

## Git boundary

Git operations are blocked by this bootstrap command. Use explicit Git gates only.

## Adapter boundary

Real adapter execution is blocked. Model/provider calls require a later approved gate.

## Private context boundary

Private context access is blocked by default.
"""
    charter_path = mission_dir / "charter.md"
    write_text(charter_path, charter, force=force)

    manifest = {
        "schema_version": "1.0",
        "mission_id": mission_id,
        "title": title,
        "scope": scope,
        "created_at": now_utc(),
        "mission_dir": str(mission_dir),
        "directories": MISSION_DIRS,
        "status": "draft",
        "requires_human_approval": True,
        "safety_boundaries": dict(SAFETY_BOUNDARIES),
    }
    manifest_path = mission_dir / "mission_manifest.json"
    write_json(manifest_path, manifest, force=force)

    report["charter_path"] = str(charter_path)
    report["manifest_path"] = str(manifest_path)
    report["created_directories"] = [str(mission_dir / rel) for rel in MISSION_DIRS]
    return report


def run_delegated_tool(repo_root: Path, script_rel_path: str, args: Sequence[str]) -> int:
    script = repo_path(repo_root.resolve(), script_rel_path)
    if not script.exists():
        raise KonohaError(f"delegated tool not found: {script_rel_path}")

    command = [sys.executable, str(script)] + list(args)
    completed = subprocess.run(command, cwd=str(repo_root.resolve()), shell=False)
    return int(completed.returncode)


def run_dry_run(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    validate_safe_id(args.run_id, "run_id")

    delegated_args = [
        "--title", args.title,
        "--scope", args.scope,
        "--run-id", args.run_id,
        "--repo-root", args.repo_root,
        "--sandbox-root", args.sandbox_root,
    ]
    if args.config:
        delegated_args.extend(["--config", args.config])
    if args.force:
        delegated_args.append("--force")

    return run_delegated_tool(repo_root, "tools/mission_workflow/run_dry_run_mission.py", delegated_args)


def print_report(title: str, report: Dict[str, Any], json_output: bool = False) -> None:
    if json_output:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    status_word = "PASSED" if report.get("status") == "passed" else "FAILED"
    print(f"{title} {status_word}")

    if "workspace_root" in report:
        print(f"Workspace: {report['workspace_root']}")
    if "mission_id" in report:
        print(f"Mission: {report['mission_id']}")
    if "config_path" in report:
        print(f"Config: {report['config_path']}")

    print("Execution: blocked")
    print("Filesystem mutation: workspace and delegated sandbox outputs only")
    print("Repository apply: blocked by bootstrap CLI")
    print("Git operations: read-only or delegated gated tools only")
    print("Git write operations: blocked by bootstrap CLI")
    print("Private context access: blocked")
    print("Adapter execution: blocked by bootstrap CLI")
    print("Real adapter execution: blocked")
    print("Network access: blocked")

    for blocker in report.get("blockers", []):
        print(f"Blocker: {blocker}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="konoha_product",
        description="Konoha Product Runtime Bootstrap CLI",
    )
    parser.add_argument("--version", action="version", version=VERSION)

    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Initialize a local Konoha product workspace")
    init_parser.add_argument("--repo-root", default=".")
    init_parser.add_argument("--workspace-root", default=DEFAULT_WORKSPACE_ROOT)
    init_parser.add_argument("--force", action="store_true")
    init_parser.add_argument("--json", action="store_true")

    doctor_parser = subparsers.add_parser("doctor", help="Run read-only product runtime checks")
    doctor_parser.add_argument("--repo-root", default=".")
    doctor_parser.add_argument("--workspace-root", default=DEFAULT_WORKSPACE_ROOT)
    doctor_parser.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    doctor_parser.add_argument("--json", action="store_true")

    config_parser = subparsers.add_parser("config", help="Config commands")
    config_subparsers = config_parser.add_subparsers(dest="config_command")
    validate_parser = config_subparsers.add_parser("validate", help="Validate public config shape")
    validate_parser.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    validate_parser.add_argument("--json", action="store_true")

    mission_parser = subparsers.add_parser("mission", help="Mission workspace commands")
    mission_subparsers = mission_parser.add_subparsers(dest="mission_command")
    new_parser = mission_subparsers.add_parser("new", help="Create a mission workspace skeleton")
    new_parser.add_argument("--repo-root", default=".")
    new_parser.add_argument("--workspace-root", default=DEFAULT_WORKSPACE_ROOT)
    new_parser.add_argument("--mission-id", required=True)
    new_parser.add_argument("--title", required=True)
    new_parser.add_argument("--scope", required=True)
    new_parser.add_argument("--force", action="store_true")
    new_parser.add_argument("--json", action="store_true")

    run_parser = subparsers.add_parser("run", help="Run delegated product workflows")
    run_subparsers = run_parser.add_subparsers(dest="run_command")
    dry_run_parser = run_subparsers.add_parser("dry-run", help="Delegate to end-to-end dry-run mission workflow")
    dry_run_parser.add_argument("--title", required=True)
    dry_run_parser.add_argument("--scope", required=True)
    dry_run_parser.add_argument("--run-id", required=True)
    dry_run_parser.add_argument("--repo-root", default=".")
    dry_run_parser.add_argument("--sandbox-root", default="sandbox")
    dry_run_parser.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    dry_run_parser.add_argument("--force", action="store_true")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            report = init_workspace(Path(args.repo_root), args.workspace_root, force=args.force)
            print_report("KONOHA PRODUCT RUNTIME INIT", report, json_output=args.json)
            return 0 if report["status"] == "passed" else 1

        if args.command == "doctor":
            report = doctor_report(Path(args.repo_root), args.workspace_root, args.config)
            print_report("KONOHA PRODUCT RUNTIME DOCTOR", report, json_output=args.json)
            return 0 if report["status"] == "passed" else 1

        if args.command == "config" and args.config_command == "validate":
            result = validate_config_shape(Path(args.config))
            report = build_common_report(result["status"], "config validate")
            report["config_validation"] = result
            report["blockers"] = list(result.get("blockers", []))
            print_report("KONOHA CONFIG VALIDATION", report, json_output=args.json)
            return 0 if report["status"] == "passed" else 1

        if args.command == "mission" and args.mission_command == "new":
            report = create_mission(
                Path(args.repo_root),
                args.workspace_root,
                args.mission_id,
                args.title,
                args.scope,
                force=args.force,
            )
            print_report("KONOHA MISSION WORKSPACE", report, json_output=args.json)
            return 0

        if args.command == "run" and args.run_command == "dry-run":
            return run_dry_run(args)

        parser.print_help()
        return 2

    except KonohaError as exc:
        report = build_common_report("failed", args.command or "unknown")
        report["blockers"] = [str(exc)]
        print_report("KONOHA PRODUCT RUNTIME", report, json_output=getattr(args, "json", False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
