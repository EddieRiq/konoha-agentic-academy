#!/usr/bin/env python3
"""Konoha Mission Workspace manager.

This tool creates and validates mission workspaces under an explicit workspace
root. It does not execute mission actions, call adapters, access private
context, perform Git operations, or use the network.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


VERSION = "1.2.0"

MISSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
REQUIRED_MISSION_DIRS = [
    "inputs",
    "context",
    "plans",
    "outputs",
    "reports",
    "approvals",
    "evidence",
]
REQUIRED_MANIFEST_FIELDS = [
    "schema_version",
    "mission_id",
    "title",
    "scope",
    "status",
    "created_at_utc",
    "workspace_boundary",
    "safety",
]


class MissionWorkspaceError(Exception):
    """Raised when workspace validation or creation fails."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_mission_id(mission_id: str) -> None:
    if not MISSION_ID_PATTERN.fullmatch(mission_id or ""):
        raise MissionWorkspaceError(
            "mission_id must be alphanumeric plus '.', '_' or '-' and may not contain path separators"
        )
    if "/" in mission_id or "\\" in mission_id or ".." in mission_id.split("."):
        raise MissionWorkspaceError("mission_id may not contain path traversal")


def resolve_under(root: Path, child: Path) -> Path:
    root_resolved = root.resolve()
    child_resolved = child.resolve()
    try:
        child_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise MissionWorkspaceError(f"path escapes workspace root: {child}") from exc
    return child_resolved


def mission_root(workspace_root: Path, mission_id: str) -> Path:
    validate_mission_id(mission_id)
    return resolve_under(workspace_root, workspace_root / "missions" / mission_id)


def write_text_file(path: Path, content: str, force: bool = False) -> None:
    if path.exists() and not force:
        raise MissionWorkspaceError(f"file already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json_file(path: Path, payload: Dict[str, object], force: bool = False) -> None:
    write_text_file(path, json.dumps(payload, indent=2, sort_keys=True) + "\n", force=force)


def charter_template(mission_id: str, title: str, scope: str) -> str:
    return f"""# Mission Charter: {title}

## Mission ID

`{mission_id}`

## Scope

{scope}

## Doctrine

- Evidence before action.
- Mission Charter before execution.
- Human approval before sensitive transitions.
- Model inference is never permission.
- Safety overrides autonomy.
- Outputs remain sandbox/local unless explicitly approved.

## Current status

Draft.

## Non-authority boundary

This Mission Workspace does not authorize execution, adapter invocation, repository apply, Git staging, Git commit, Git push, network access, or private context access by itself.
"""


def approval_log_template() -> str:
    return """# Approval Log

No approvals recorded yet.

Approvals must be explicit, scoped, timestamped, and tied to a specific gate.
"""


def readme_template(mission_id: str, title: str) -> str:
    return f"""# Mission Workspace: {title}

Mission ID: `{mission_id}`

This workspace contains mission-local inputs, context, plans, outputs, reports, approvals, and evidence.

The workspace is a container for evidence and review. It is not authority to execute.
"""


def manifest_payload(mission_id: str, title: str, scope: str, workspace_root: Path, root: Path) -> Dict[str, object]:
    return {
        "schema_version": "1.0",
        "mission_id": mission_id,
        "title": title,
        "scope": scope,
        "status": "draft",
        "created_at_utc": utc_now(),
        "workspace_boundary": {
            "workspace_root": str(workspace_root),
            "mission_root": str(root),
            "required_directories": REQUIRED_MISSION_DIRS,
        },
        "safety": {
            "execution": "blocked",
            "filesystem_mutation": "mission workspace only",
            "repository_apply": "blocked",
            "git_operations": "blocked",
            "private_context_access": "blocked",
            "real_adapter_execution": "blocked",
            "network_access": "blocked",
        },
        "review": {
            "requires_human_approval_for_execution": True,
            "requires_human_approval_for_apply": True,
            "requires_human_approval_for_git": True,
            "teachback_required_for_closure": True,
        },
    }


def create_workspace(args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    workspace_root = Path(args.workspace_root)
    root = mission_root(workspace_root, args.mission_id)

    if root.exists() and not args.force:
        raise MissionWorkspaceError(f"mission workspace already exists: {root}")

    root.mkdir(parents=True, exist_ok=True)

    for dirname in REQUIRED_MISSION_DIRS:
        directory = resolve_under(workspace_root, root / dirname)
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("", encoding="utf-8")

    manifest = manifest_payload(args.mission_id, args.title, args.scope, workspace_root, root)

    write_json_file(root / "mission_manifest.json", manifest, force=True)
    write_text_file(root / "charter.md", charter_template(args.mission_id, args.title, args.scope), force=True)
    write_text_file(root / "README.md", readme_template(args.mission_id, args.title), force=True)
    write_text_file(root / "approvals" / "approval_log.md", approval_log_template(), force=True)

    report = report_payload(
        command="create",
        workspace_root=workspace_root,
        mission_id=args.mission_id,
        status="passed",
        blockers=[],
        details={
            "mission_root": str(root),
            "created_files": [
                "mission_manifest.json",
                "charter.md",
                "README.md",
                "approvals/approval_log.md",
            ],
            "created_directories": REQUIRED_MISSION_DIRS,
        },
    )

    write_json_file(root / "reports" / "mission_workspace_report.json", report, force=True)
    return 0, report


def load_manifest(root: Path) -> Dict[str, object]:
    path = root / "mission_manifest.json"
    if not path.exists():
        raise MissionWorkspaceError(f"missing mission_manifest.json: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MissionWorkspaceError(f"invalid mission_manifest.json: {exc}") from exc
    return payload


def validate_workspace(args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    workspace_root = Path(args.workspace_root)
    root = mission_root(workspace_root, args.mission_id)
    blockers: List[str] = []

    if not root.exists():
        blockers.append(f"missing mission root: {root}")
    else:
        try:
            manifest = load_manifest(root)
            for field in REQUIRED_MANIFEST_FIELDS:
                if field not in manifest:
                    blockers.append(f"manifest missing required field: {field}")
            if manifest.get("mission_id") != args.mission_id:
                blockers.append("manifest mission_id does not match requested mission_id")
        except MissionWorkspaceError as exc:
            blockers.append(str(exc))

        for dirname in REQUIRED_MISSION_DIRS:
            if not (root / dirname).is_dir():
                blockers.append(f"missing required directory: {dirname}")

        for filename in ["charter.md", "README.md", "approvals/approval_log.md"]:
            if not (root / filename).exists():
                blockers.append(f"missing required file: {filename}")

    status = "passed" if not blockers else "failed"
    report = report_payload(
        command="validate",
        workspace_root=workspace_root,
        mission_id=args.mission_id,
        status=status,
        blockers=blockers,
        details={"mission_root": str(root)},
    )

    if root.exists():
        reports_dir = root / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        write_json_file(reports_dir / "mission_workspace_validation_report.json", report, force=True)

    return (0 if not blockers else 1), report


def inspect_workspace(args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    workspace_root = Path(args.workspace_root)
    root = mission_root(workspace_root, args.mission_id)
    blockers: List[str] = []

    if not root.exists():
        blockers.append(f"missing mission root: {root}")
        manifest: Dict[str, object] = {}
    else:
        try:
            manifest = load_manifest(root)
        except MissionWorkspaceError as exc:
            blockers.append(str(exc))
            manifest = {}

    details = {
        "mission_root": str(root),
        "manifest": manifest,
        "present_directories": sorted([p.name for p in root.iterdir() if p.is_dir()]) if root.exists() else [],
        "present_files": sorted([p.name for p in root.iterdir() if p.is_file()]) if root.exists() else [],
    }
    report = report_payload(
        command="inspect",
        workspace_root=workspace_root,
        mission_id=args.mission_id,
        status="passed" if not blockers else "failed",
        blockers=blockers,
        details=details,
    )
    return (0 if not blockers else 1), report


def list_workspaces(args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    workspace_root = Path(args.workspace_root)
    missions_dir = workspace_root / "missions"
    missions: List[Dict[str, object]] = []

    if missions_dir.exists():
        for path in sorted(p for p in missions_dir.iterdir() if p.is_dir()):
            try:
                manifest = json.loads((path / "mission_manifest.json").read_text(encoding="utf-8"))
            except Exception:
                manifest = {"mission_id": path.name, "status": "unknown", "title": path.name}
            missions.append(
                {
                    "mission_id": manifest.get("mission_id", path.name),
                    "title": manifest.get("title", path.name),
                    "status": manifest.get("status", "unknown"),
                    "mission_root": str(path),
                }
            )

    report = report_payload(
        command="list",
        workspace_root=workspace_root,
        mission_id=None,
        status="passed",
        blockers=[],
        details={"mission_count": len(missions), "missions": missions},
    )
    return 0, report


def report_payload(
    command: str,
    workspace_root: Path,
    mission_id: Optional[str],
    status: str,
    blockers: List[str],
    details: Dict[str, object],
) -> Dict[str, object]:
    return {
        "schema_version": "1.0",
        "tool": "mission_workspace",
        "command": command,
        "status": status,
        "created_at_utc": utc_now(),
        "workspace_root": str(workspace_root),
        "mission_id": mission_id,
        "checks": {
            "execution": "blocked",
            "filesystem_mutation": "mission workspace only",
            "repository_apply": "blocked",
            "git_operations": "blocked",
            "private_context_access": "blocked",
            "real_adapter_execution": "blocked",
            "network_access": "blocked",
        },
        "blockers": blockers,
        "details": details,
    }


def print_report(report: Dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    command = report.get("command", "unknown")
    status = report.get("status", "unknown")
    heading_status = "PASSED" if status == "passed" else "FAILED"
    print(f"MISSION WORKSPACE {str(command).upper()} {heading_status}")
    if report.get("mission_id"):
        print(f"Mission ID: {report['mission_id']}")
    print(f"Workspace root: {report['workspace_root']}")
    print("Execution: blocked")
    print("Filesystem mutation: mission workspace only")
    print("Repository apply: blocked")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Real adapter execution: blocked")
    print("Network access: blocked")
    for blocker in report.get("blockers", []):
        print(f"Blocker: {blocker}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage Konoha mission workspaces without execution authority."
    )
    parser.add_argument("--version", action="version", version=VERSION)

    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a mission workspace.")
    create.add_argument("--workspace-root", required=True)
    create.add_argument("--mission-id", required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--scope", required=True)
    create.add_argument("--force", action="store_true")
    create.add_argument("--json", action="store_true")

    validate = subparsers.add_parser("validate", help="Validate a mission workspace.")
    validate.add_argument("--workspace-root", required=True)
    validate.add_argument("--mission-id", required=True)
    validate.add_argument("--json", action="store_true")

    inspect_cmd = subparsers.add_parser("inspect", help="Inspect a mission workspace.")
    inspect_cmd.add_argument("--workspace-root", required=True)
    inspect_cmd.add_argument("--mission-id", required=True)
    inspect_cmd.add_argument("--json", action="store_true")

    list_cmd = subparsers.add_parser("list", help="List mission workspaces.")
    list_cmd.add_argument("--workspace-root", required=True)
    list_cmd.add_argument("--json", action="store_true")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "create":
            code, report = create_workspace(args)
        elif args.command == "validate":
            code, report = validate_workspace(args)
        elif args.command == "inspect":
            code, report = inspect_workspace(args)
        elif args.command == "list":
            code, report = list_workspaces(args)
        else:
            raise MissionWorkspaceError(f"unknown command: {args.command}")
    except MissionWorkspaceError as exc:
        workspace_root = Path(getattr(args, "workspace_root", "."))
        mission_id = getattr(args, "mission_id", None)
        report = report_payload(
            command=getattr(args, "command", "unknown"),
            workspace_root=workspace_root,
            mission_id=mission_id,
            status="failed",
            blockers=[str(exc)],
            details={},
        )
        print_report(report, getattr(args, "json", False))
        return 1

    print_report(report, getattr(args, "json", False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
