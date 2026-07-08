"""Approval helpers for the Local Web UI Alpha."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.ui_server.services.workspace_service import mission_dir, resolve_under, validate_safe_id


APPROVAL_TOKEN = "APPROVE_MISSION_TRANSITION"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def record_decision(
    workspace_root: Path,
    mission_id: str,
    transition: str,
    decision: str,
    reason: str,
    approval_token: str,
) -> dict[str, Any]:
    validate_safe_id(mission_id, "mission_id")
    if approval_token != APPROVAL_TOKEN:
        raise PermissionError("exact approval token required")

    base = mission_dir(workspace_root, mission_id)
    approvals_dir = resolve_under(base, "approvals")
    reports_dir = resolve_under(base, "reports")
    approvals_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    event = {
        "schema_version": "1.0",
        "event_type": "mission_approval_event",
        "mission_id": mission_id,
        "transition": transition,
        "decision": decision,
        "reason": reason,
        "created_at": utc_now(),
        "recorded_by": "local_web_ui_alpha",
        "token_stored": False,
        "execution": "blocked",
        "repository_apply": "blocked",
        "git_operations": "blocked",
        "private_context_access": "blocked",
        "real_model_invocation": "blocked_from_ui_alpha",
    }

    event_id = event["created_at"].replace(":", "").replace("+", "Z")
    event_path = approvals_dir / f"{event_id}_{transition}.json"
    event_path.write_text(json.dumps(event, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    log_path = approvals_dir / "approval_log.md"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n")
        handle.write(f"## {event['created_at']} — {transition}\n\n")
        handle.write(f"- Decision: {decision}\n")
        handle.write(f"- Reason: {reason}\n")
        handle.write("- Recorded by: local_web_ui_alpha\n")
        handle.write("- Token stored: false\n")

    report_path = reports_dir / f"{event_id}_approval_console_report.json"
    report = {
        "schema_version": "1.0",
        "status": "passed",
        "event": event,
        "report_path": str(report_path),
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def list_approval_events(workspace_root: Path, mission_id: str) -> list[dict[str, Any]]:
    base = mission_dir(workspace_root, mission_id)
    approvals_dir = resolve_under(base, "approvals")
    if not approvals_dir.exists():
        return []
    rows = []
    for path in sorted(approvals_dir.glob("*.json")):
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            rows.append({"path": str(path), "status": "unreadable"})
    return rows
