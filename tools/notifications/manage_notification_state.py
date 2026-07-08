#!/usr/bin/env python3
"""Manage mission notification state for Konoha.

This CLI writes mission-local notification state only under an explicit
Mission Workspace. It does not execute mission actions, run shell commands,
use network access, perform Git operations, invoke models/adapters, or access
private context.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


APPROVAL_TOKEN = "UPDATE_NOTIFICATION_STATE"

ALLOWED_STATES = {
    "created",
    "running",
    "waiting_user_input",
    "waiting_approval",
    "blocked",
    "ready_for_review",
    "ready_for_teachback",
    "closed",
}

ALLOWED_SEVERITIES = {
    "info",
    "attention",
    "blocked",
    "urgent",
}

BOUNDARIES = {
    "execution": "blocked",
    "repository_apply": "blocked",
    "git_operations": "blocked",
    "private_context_access": "blocked",
    "real_model_invocation": "blocked",
    "network_access": "blocked",
    "background_agents": "blocked",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_id(value: str, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} is required")
    if "/" in value or "\\" in value or ".." in value:
        raise ValueError(f"{field_name} must not contain path separators or traversal")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
        raise ValueError(f"{field_name} must be alphanumeric plus '.', '_' or '-'")


def resolve_under(root: Path, *parts: str) -> Path:
    root_resolved = root.resolve()
    candidate = root_resolved.joinpath(*parts).resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError(f"path escapes root: {candidate}")
    return candidate


def mission_dir(workspace_root: Path, mission_id: str) -> Path:
    validate_id(mission_id, "mission_id")
    path = resolve_under(workspace_root, "missions", mission_id)
    if not path.exists():
        raise ValueError(f"mission workspace does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"mission path is not a directory: {path}")
    return path


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Dict[str, Any], force: bool = False) -> None:
    if path.exists() and not force:
        raise ValueError(f"output already exists: {path}; use --force")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_notification_log(path: Path, event: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = (
        f"- {event['created_at']} | state={event['state']} | "
        f"severity={event['severity']} | actor={event['actor']} | "
        f"reason={event['reason']}\n"
    )
    if not path.exists():
        path.write_text("# Notification Log\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)


def base_report(
    command: str,
    mission_id: str,
    state: Optional[str],
    status: str,
    invocation: str,
    blockers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "report_type": "mission_notification_state_report",
        "schema_version": "1.0.0",
        "command": command,
        "mission_id": mission_id,
        "state": state,
        "status": status,
        "invocation": invocation,
        "generated_at": utc_now(),
        "blockers": blockers or [],
        "boundaries": dict(BOUNDARIES),
        "authority": {
            "notification_state_is_evidence_only": True,
            "state_change_does_not_authorize_execution": True,
            "state_change_does_not_close_mission": True,
        },
    }


def print_report(report: Dict[str, Any], as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    status = report["status"]
    command = report["command"]
    if status == "passed" and report["invocation"] == "preview_only":
        print("MISSION NOTIFICATION STATE PREVIEW")
    elif status == "passed":
        print("MISSION NOTIFICATION STATE PASSED")
    else:
        print("MISSION NOTIFICATION STATE FAILED")

    print(f"Command: {command}")
    print(f"Mission: {report['mission_id']}")
    if report.get("state"):
        print(f"State: {report['state']}")
    print(f"Invocation: {report['invocation']}")
    print("Execution: blocked")
    print("Repository apply: blocked")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Real model invocation: blocked")
    print("Network access: blocked")
    print("Background agents: blocked")

    for blocker in report.get("blockers", []):
        print(f"Blocker: {blocker}")


def build_event(args: argparse.Namespace) -> Dict[str, Any]:
    if args.state not in ALLOWED_STATES:
        raise ValueError(f"invalid state: {args.state}")
    if args.severity not in ALLOWED_SEVERITIES:
        raise ValueError(f"invalid severity: {args.severity}")
    if not args.reason.strip():
        raise ValueError("reason is required")
    return {
        "event_type": "mission_notification_state_update",
        "schema_version": "1.0.0",
        "mission_id": args.mission_id,
        "state": args.state,
        "severity": args.severity,
        "reason": args.reason.strip(),
        "required_human_action": args.required_human_action.strip(),
        "actor": args.actor.strip() or "unknown",
        "created_at": utc_now(),
        "boundaries": dict(BOUNDARIES),
    }


def set_state(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace_root)
    try:
        mdir = mission_dir(workspace_root, args.mission_id)
        event = build_event(args)
        report = base_report(
            command="set",
            mission_id=args.mission_id,
            state=args.state,
            status="passed",
            invocation="confirmed" if args.confirm_state_update else "preview_only",
        )

        if not args.confirm_state_update:
            print_report(report, args.json)
            return 0

        if args.approval_token != APPROVAL_TOKEN:
            raise ValueError(f"approval token must be {APPROVAL_TOKEN}")

        state_path = mdir / "mission_notification_state.json"
        log_path = mdir / "notifications" / "notification_log.md"
        reports_dir = mdir / "reports"

        payload = {
            "schema_version": "1.0.0",
            "mission_id": args.mission_id,
            "current_state": args.state,
            "severity": args.severity,
            "reason": event["reason"],
            "required_human_action": event["required_human_action"],
            "updated_by": event["actor"],
            "updated_at": event["created_at"],
            "history_log": str(log_path),
            "boundaries": dict(BOUNDARIES),
        }

        write_json(state_path, payload, force=args.force)
        append_notification_log(log_path, event)

        report["state_path"] = str(state_path)
        report["notification_log_path"] = str(log_path)
        report_path = reports_dir / f"{args.event_id}_mission_notification_state_report.json"
        report["report_path"] = str(report_path)
        write_json(report_path, report, force=args.force)

        print_report(report, args.json)
        return 0

    except Exception as exc:
        report = base_report(
            command="set",
            mission_id=args.mission_id,
            state=getattr(args, "state", None),
            status="failed",
            invocation="blocked",
            blockers=[str(exc)],
        )
        print_report(report, args.json)
        return 1


def inspect_state(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace_root)
    try:
        mdir = mission_dir(workspace_root, args.mission_id)
        state_path = mdir / "mission_notification_state.json"
        if not state_path.exists():
            raise ValueError("mission notification state does not exist")
        payload = read_json(state_path)
        report = base_report(
            command="inspect",
            mission_id=args.mission_id,
            state=payload.get("current_state"),
            status="passed",
            invocation="read_only",
        )
        report["state_payload"] = payload
        print_report(report, args.json)
        return 0
    except Exception as exc:
        report = base_report(
            command="inspect",
            mission_id=args.mission_id,
            state=None,
            status="failed",
            invocation="blocked",
            blockers=[str(exc)],
        )
        print_report(report, args.json)
        return 1


def list_states(args: argparse.Namespace) -> int:
    payload = {
        "allowed_states": sorted(ALLOWED_STATES),
        "allowed_severities": sorted(ALLOWED_SEVERITIES),
        "approval_token": APPROVAL_TOKEN,
        "boundaries": dict(BOUNDARIES),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("MISSION NOTIFICATION STATES")
        for state in payload["allowed_states"]:
            print(f"- {state}")
        print("Severities:")
        for severity in payload["allowed_severities"]:
            print(f"- {severity}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage mission notification state for Konoha Mission Workspaces."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    set_parser = sub.add_parser("set", help="Preview or write mission notification state.")
    set_parser.add_argument("--workspace-root", required=True)
    set_parser.add_argument("--mission-id", required=True)
    set_parser.add_argument("--event-id", default="notification-state-update")
    set_parser.add_argument("--state", required=True, choices=sorted(ALLOWED_STATES))
    set_parser.add_argument("--severity", default="attention", choices=sorted(ALLOWED_SEVERITIES))
    set_parser.add_argument("--reason", required=True)
    set_parser.add_argument("--required-human-action", default="")
    set_parser.add_argument("--actor", default="konoha")
    set_parser.add_argument("--confirm-state-update", action="store_true")
    set_parser.add_argument("--approval-token", default="")
    set_parser.add_argument("--force", action="store_true")
    set_parser.add_argument("--json", action="store_true")
    set_parser.set_defaults(func=set_state)

    inspect_parser = sub.add_parser("inspect", help="Inspect existing mission notification state.")
    inspect_parser.add_argument("--workspace-root", required=True)
    inspect_parser.add_argument("--mission-id", required=True)
    inspect_parser.add_argument("--json", action="store_true")
    inspect_parser.set_defaults(func=inspect_state)

    states_parser = sub.add_parser("states", help="List allowed states and severities.")
    states_parser.add_argument("--json", action="store_true")
    states_parser.set_defaults(func=list_states)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
