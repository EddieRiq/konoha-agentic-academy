#!/usr/bin/env python3
"""
Human Approval Console CLI for Konoha mission workspaces.

This tool records human approval/rejection events inside an explicit mission
workspace. It is not a mission executor, does not invoke adapters, does not
perform Git operations, and does not access private context.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


APPROVE_TOKEN = "APPROVE_MISSION_TRANSITION"
REJECT_TOKEN = "REJECT_MISSION_TRANSITION"
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
SAFE_TRANSITION_RE = re.compile(r"^[A-Za-z0-9._:/ -]+$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fail(message: str, *, command: str = "APPROVAL CONSOLE") -> int:
    print(f"{command} FAILED")
    print("Execution: blocked")
    print("Filesystem mutation: mission approvals only")
    print("Repository apply: blocked")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Real adapter execution: blocked")
    print("Network access: blocked")
    print(f"Blocker: {message}")
    return 1


def safe_id(value: str, label: str) -> str:
    if not value or not SAFE_ID_RE.match(value):
        raise ValueError(f"{label} must be alphanumeric plus '.', '_' or '-' and may not contain path separators")
    if "/" in value or "\\" in value or value in {".", ".."}:
        raise ValueError(f"{label} may not contain path separators or traversal values")
    return value


def safe_transition(value: str) -> str:
    if not value or not SAFE_TRANSITION_RE.match(value):
        raise ValueError("transition contains unsupported characters")
    if ".." in value:
        raise ValueError("transition may not contain traversal-like patterns")
    return value.strip()


def resolve_under(root: Path, *parts: str) -> Path:
    root_resolved = root.resolve()
    candidate = root_resolved.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"path escapes root: {candidate}") from exc
    return candidate


def mission_dir(workspace_root: Path, mission_id: str) -> Path:
    mission_id = safe_id(mission_id, "mission_id")
    return resolve_under(workspace_root, "missions", mission_id)


def required_paths(mission_path: Path) -> List[Path]:
    return [
        mission_path / "charter.md",
        mission_path / "mission_manifest.json",
        mission_path / "README.md",
        mission_path / "inputs",
        mission_path / "context",
        mission_path / "plans",
        mission_path / "outputs",
        mission_path / "reports",
        mission_path / "approvals",
        mission_path / "approvals" / "approval_log.md",
        mission_path / "evidence",
    ]


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line.rstrip("\n") + "\n")


def events_path(mission_path: Path) -> Path:
    return mission_path / "approvals" / "approval_events.jsonl"


def log_path(mission_path: Path) -> Path:
    return mission_path / "approvals" / "approval_log.md"


def read_events(mission_path: Path) -> List[Dict[str, Any]]:
    path = events_path(mission_path)
    if not path.exists():
        return []

    events: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                events.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid approval event JSON at line {line_number}") from exc
    return events


def mission_exists(mission_path: Path) -> bool:
    return mission_path.exists() and mission_path.is_dir()


def workspace_report(workspace_root: Path, mission_id: str) -> Dict[str, Any]:
    mission_path = mission_dir(workspace_root, mission_id)
    required = required_paths(mission_path)
    missing = [str(path.relative_to(mission_path)) for path in required if not path.exists()]
    events = read_events(mission_path) if mission_exists(mission_path) else []
    last_event = events[-1] if events else None

    status = "pending_review"
    if last_event:
        status = "approved" if last_event.get("event_type") == "approval" else "rejected"

    manifest: Dict[str, Any] = {}
    manifest_path = mission_path / "mission_manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)

    report = {
        "schema_version": "1.0",
        "tool": "human_approval_console_cli",
        "mission_id": mission_id,
        "mission_path": str(mission_path),
        "workspace_root": str(workspace_root.resolve()),
        "mission_exists": mission_exists(mission_path),
        "workspace_valid": mission_exists(mission_path) and not missing,
        "missing_required_paths": missing,
        "status": status,
        "approval_event_count": len(events),
        "last_event": last_event,
        "manifest": manifest,
        "safety_boundaries": safety_boundaries(filesystem_mutation="blocked"),
    }
    return report


def safety_boundaries(*, filesystem_mutation: str) -> Dict[str, str]:
    return {
        "execution": "blocked",
        "filesystem_mutation": filesystem_mutation,
        "repository_apply": "blocked",
        "git_operations": "blocked",
        "private_context_access": "blocked",
        "real_adapter_execution": "blocked",
        "network_access": "blocked",
        "runtime_authority": "blocked",
    }


def ensure_mission_ready(mission_path: Path) -> None:
    if not mission_exists(mission_path):
        raise ValueError(f"mission workspace does not exist: {mission_path}")

    missing = [str(path.relative_to(mission_path)) for path in required_paths(mission_path) if not path.exists()]
    if missing:
        raise ValueError("mission workspace missing required paths: " + ", ".join(missing))


def print_report(report: Dict[str, Any], *, title: str, as_json: bool = False) -> int:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print(title)
    print(f"Mission: {report['mission_id']}")
    print(f"Status: {report['status']}")
    print(f"Workspace valid: {str(report['workspace_valid']).lower()}")
    print(f"Approval events: {report['approval_event_count']}")
    print("Execution: blocked")
    print("Filesystem mutation: blocked")
    print("Repository apply: blocked")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Real adapter execution: blocked")
    print("Network access: blocked")

    if report["missing_required_paths"]:
        print("Missing required paths:")
        for item in report["missing_required_paths"]:
            print(f"- {item}")
    return 0


def command_status(args: argparse.Namespace) -> int:
    try:
        report = workspace_report(Path(args.workspace_root), args.mission_id)
        if not report["mission_exists"]:
            return fail("mission workspace does not exist", command="MISSION STATUS")
        return print_report(report, title="MISSION STATUS", as_json=args.json)
    except Exception as exc:
        return fail(str(exc), command="MISSION STATUS")


def command_inspect(args: argparse.Namespace) -> int:
    try:
        report = workspace_report(Path(args.workspace_root), args.mission_id)
        if not report["mission_exists"]:
            return fail("mission workspace does not exist", command="MISSION INSPECT")
        return print_report(report, title="MISSION INSPECT", as_json=args.json)
    except Exception as exc:
        return fail(str(exc), command="MISSION INSPECT")


def event_payload(
    *,
    mission_id: str,
    event_type: str,
    transition: str,
    decision: str,
    reason: str,
    actor: str,
) -> Dict[str, Any]:
    now = utc_now()
    return {
        "schema_version": "1.0",
        "tool": "human_approval_console_cli",
        "event_id": f"{mission_id}-{event_type}-{now.replace(':', '').replace('-', '')}",
        "mission_id": mission_id,
        "event_type": event_type,
        "transition": transition,
        "decision": decision,
        "reason": reason,
        "actor": actor,
        "created_at_utc": now,
        "approval_token_verified": True,
        "review_required_after_event": event_type == "approval",
        "safety_boundaries": safety_boundaries(filesystem_mutation="mission approvals only"),
    }


def write_event(mission_path: Path, payload: Dict[str, Any]) -> None:
    approvals_dir = mission_path / "approvals"
    approvals_dir.mkdir(parents=True, exist_ok=True)
    append_line(events_path(mission_path), json.dumps(payload, sort_keys=True))

    log_line = (
        f"- {payload['created_at_utc']} | {payload['event_type']} | "
        f"{payload['transition']} | {payload['decision']} | actor={payload['actor']} | "
        f"reason={payload['reason']}"
    )
    if not log_path(mission_path).exists():
        append_line(log_path(mission_path), "# Approval log")
        append_line(log_path(mission_path), "")
    append_line(log_path(mission_path), log_line)


def write_console_report(mission_path: Path, payload: Dict[str, Any]) -> Path:
    report_path = mission_path / "reports" / "mission_approval_console_report.json"
    write_json(
        report_path,
        {
            "schema_version": "1.0",
            "tool": "human_approval_console_cli",
            "mission_id": payload["mission_id"],
            "latest_event": payload,
            "approval_event_count": len(read_events(mission_path)),
            "report_created_at_utc": utc_now(),
            "safety_boundaries": safety_boundaries(filesystem_mutation="mission approvals only"),
        },
    )
    return report_path


def command_approve(args: argparse.Namespace) -> int:
    try:
        if args.approval_token != APPROVE_TOKEN:
            return fail("invalid approval token", command="MISSION APPROVAL")
        transition = safe_transition(args.transition)
        mission_id = safe_id(args.mission_id, "mission_id")
        path = mission_dir(Path(args.workspace_root), mission_id)
        ensure_mission_ready(path)

        payload = event_payload(
            mission_id=mission_id,
            event_type="approval",
            transition=transition,
            decision=args.decision,
            reason=args.reason,
            actor=args.actor,
        )
        write_event(path, payload)
        report_path = write_console_report(path, payload)

        if args.json:
            print(json.dumps({"event": payload, "report_path": str(report_path)}, indent=2, sort_keys=True))
        else:
            print("MISSION APPROVAL PASSED")
            print(f"Mission: {mission_id}")
            print(f"Transition: {transition}")
            print(f"Decision: {args.decision}")
            print(f"Report: {report_path}")
            print("Execution: blocked")
            print("Filesystem mutation: mission approvals only")
            print("Repository apply: blocked")
            print("Git operations: blocked")
            print("Private context access: blocked")
            print("Real adapter execution: blocked")
            print("Network access: blocked")
        return 0
    except Exception as exc:
        return fail(str(exc), command="MISSION APPROVAL")


def command_reject(args: argparse.Namespace) -> int:
    try:
        if args.approval_token != REJECT_TOKEN:
            return fail("invalid rejection token", command="MISSION REJECTION")
        transition = safe_transition(args.transition)
        mission_id = safe_id(args.mission_id, "mission_id")
        path = mission_dir(Path(args.workspace_root), mission_id)
        ensure_mission_ready(path)

        payload = event_payload(
            mission_id=mission_id,
            event_type="rejection",
            transition=transition,
            decision=args.decision,
            reason=args.reason,
            actor=args.actor,
        )
        write_event(path, payload)
        report_path = write_console_report(path, payload)

        if args.json:
            print(json.dumps({"event": payload, "report_path": str(report_path)}, indent=2, sort_keys=True))
        else:
            print("MISSION REJECTION PASSED")
            print(f"Mission: {mission_id}")
            print(f"Transition: {transition}")
            print(f"Decision: {args.decision}")
            print(f"Report: {report_path}")
            print("Execution: blocked")
            print("Filesystem mutation: mission approvals only")
            print("Repository apply: blocked")
            print("Git operations: blocked")
            print("Private context access: blocked")
            print("Real adapter execution: blocked")
            print("Network access: blocked")
        return 0
    except Exception as exc:
        return fail(str(exc), command="MISSION REJECTION")


def command_approvals_list(args: argparse.Namespace) -> int:
    try:
        mission_id = safe_id(args.mission_id, "mission_id")
        path = mission_dir(Path(args.workspace_root), mission_id)
        ensure_mission_ready(path)
        events = read_events(path)

        if args.json:
            print(json.dumps({"mission_id": mission_id, "events": events}, indent=2, sort_keys=True))
            return 0

        print("MISSION APPROVAL EVENTS")
        print(f"Mission: {mission_id}")
        print(f"Events: {len(events)}")
        for event in events:
            print(f"- {event.get('created_at_utc')} | {event.get('event_type')} | {event.get('transition')} | {event.get('decision')}")
        return 0
    except Exception as exc:
        return fail(str(exc), command="MISSION APPROVAL EVENTS")


def list_files_under(root: Path) -> List[str]:
    if not root.exists():
        return []
    results: List[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            results.append(str(path.relative_to(root)))
    return results


def command_file_list(args: argparse.Namespace, *, folder: str, title: str) -> int:
    try:
        mission_id = safe_id(args.mission_id, "mission_id")
        path = mission_dir(Path(args.workspace_root), mission_id)
        ensure_mission_ready(path)
        items = list_files_under(path / folder)

        if args.json:
            print(json.dumps({"mission_id": mission_id, folder: items}, indent=2, sort_keys=True))
            return 0

        print(title)
        print(f"Mission: {mission_id}")
        print(f"Files: {len(items)}")
        for item in items:
            print(f"- {item}")
        return 0
    except Exception as exc:
        return fail(str(exc), command=title)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Human Approval Console CLI for Konoha mission workspaces."
    )
    parser.add_argument("--version", action="version", version="1.3.0")

    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_workspace_args(command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument("--workspace-root", required=True)
        command_parser.add_argument("--mission-id", required=True)
        command_parser.add_argument("--json", action="store_true")

    status = subparsers.add_parser("status", help="Show mission approval status.")
    add_workspace_args(status)
    status.set_defaults(func=command_status)

    inspect = subparsers.add_parser("inspect", help="Inspect mission approval state.")
    add_workspace_args(inspect)
    inspect.set_defaults(func=command_inspect)

    approve = subparsers.add_parser("approve", help="Record a human approval event.")
    approve.add_argument("--workspace-root", required=True)
    approve.add_argument("--mission-id", required=True)
    approve.add_argument("--transition", required=True)
    approve.add_argument("--decision", required=True)
    approve.add_argument("--reason", required=True)
    approve.add_argument("--actor", default="human")
    approve.add_argument("--approval-token", required=True)
    approve.add_argument("--json", action="store_true")
    approve.set_defaults(func=command_approve)

    reject = subparsers.add_parser("reject", help="Record a human rejection event.")
    reject.add_argument("--workspace-root", required=True)
    reject.add_argument("--mission-id", required=True)
    reject.add_argument("--transition", required=True)
    reject.add_argument("--decision", required=True)
    reject.add_argument("--reason", required=True)
    reject.add_argument("--actor", default="human")
    reject.add_argument("--approval-token", required=True)
    reject.add_argument("--json", action="store_true")
    reject.set_defaults(func=command_reject)

    approvals = subparsers.add_parser("approvals", help="Approval event operations.")
    approvals_sub = approvals.add_subparsers(dest="approvals_command", required=True)
    approvals_list = approvals_sub.add_parser("list", help="List approval events.")
    add_workspace_args(approvals_list)
    approvals_list.set_defaults(func=command_approvals_list)

    evidence = subparsers.add_parser("evidence", help="Evidence operations.")
    evidence_sub = evidence.add_subparsers(dest="evidence_command", required=True)
    evidence_list = evidence_sub.add_parser("list", help="List mission evidence files.")
    add_workspace_args(evidence_list)
    evidence_list.set_defaults(
        func=lambda args: command_file_list(args, folder="evidence", title="MISSION EVIDENCE")
    )

    reports = subparsers.add_parser("reports", help="Report operations.")
    reports_sub = reports.add_subparsers(dest="reports_command", required=True)
    reports_list = reports_sub.add_parser("list", help="List mission report files.")
    add_workspace_args(reports_list)
    reports_list.set_defaults(
        func=lambda args: command_file_list(args, folder="reports", title="MISSION REPORTS")
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
