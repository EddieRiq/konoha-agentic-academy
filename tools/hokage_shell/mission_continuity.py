#!/usr/bin/env python3
"""Read-only mission continuity helpers for the Hokage Shell."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"
REPORT_TYPE = "hokage_mission_continuity_report"
MISSION_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")

BOUNDARIES = {
    "arbitrary_shell": "blocked",
    "autonomous_background_agents": "blocked",
    "git_operations": "blocked",
    "model_invocation": "blocked",
    "network_access": "blocked",
    "private_memory_read": "blocked",
    "repository_source_mutation": "blocked",
    "workspace_mutation": "blocked",
}


class MissionContinuityError(RuntimeError):
    """Configuration, path, or mission integrity error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_mission_id(mission_id: str) -> str:
    if not MISSION_ID_RE.fullmatch(mission_id):
        raise MissionContinuityError(
            "mission id must match ^[a-z0-9][a-z0-9._-]{0,79}$"
        )
    return mission_id


def resolve_under(root: Path, candidate: Path) -> Path:
    root = root.resolve()
    candidate = candidate.resolve()
    if candidate != root and root not in candidate.parents:
        raise MissionContinuityError(f"path escapes workspace root: {candidate}")
    return candidate


def missions_root(workspace_root: Path) -> Path:
    return (workspace_root.resolve() / "missions").resolve()


def mission_dir(workspace_root: Path, mission_id: str) -> Path:
    validate_mission_id(mission_id)
    root = missions_root(workspace_root)
    return resolve_under(root, root / mission_id)


def mission_session_path(workspace_root: Path, mission_id: str) -> Path:
    return mission_dir(workspace_root, mission_id) / "hokage_shell_session.json"


def parse_timestamp(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def timestamp_sort_key(value: Any) -> float:
    parsed = parse_timestamp(value)
    return parsed.timestamp() if parsed is not None else float("-inf")


def read_json_object(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MissionContinuityError(f"session file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MissionContinuityError(
            f"session JSON is invalid at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(payload, dict):
        raise MissionContinuityError("session JSON must be an object")
    return payload


def validate_session_payload(
    payload: Dict[str, Any],
    directory_mission_id: str,
) -> None:
    required = {
        "schema_version",
        "report_type",
        "mission_id",
        "task",
        "state",
        "created_at",
        "updated_at",
        "repo_root",
        "workspace_root",
        "next_recommended_action",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise MissionContinuityError(
            "session is missing required fields: " + ", ".join(missing)
        )
    if payload.get("report_type") != "hokage_shell_session":
        raise MissionContinuityError(
            "session report_type must be hokage_shell_session"
        )
    if payload.get("mission_id") != directory_mission_id:
        raise MissionContinuityError(
            "session mission_id does not match its directory"
        )
    validate_mission_id(str(payload.get("mission_id")))
    if parse_timestamp(payload.get("created_at")) is None:
        raise MissionContinuityError("session created_at is invalid")
    if parse_timestamp(payload.get("updated_at")) is None:
        raise MissionContinuityError("session updated_at is invalid")
    if not isinstance(payload.get("task"), str) or not payload["task"].strip():
        raise MissionContinuityError("session task must be non-empty text")
    if not isinstance(payload.get("state"), str) or not payload["state"].strip():
        raise MissionContinuityError("session state must be non-empty text")


def read_event_summary(events_path: Path) -> Dict[str, Any]:
    if not events_path.exists():
        return {
            "events_path": str(events_path),
            "event_count": 0,
            "invalid_event_count": 0,
            "latest_event_type": None,
            "latest_event_at": None,
        }

    event_count = 0
    invalid_event_count = 0
    latest_event_type = None
    latest_event_at = None
    latest_event_key = float("-inf")

    for raw in events_path.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines():
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            invalid_event_count += 1
            continue
        if not isinstance(event, dict):
            invalid_event_count += 1
            continue
        event_count += 1
        event_key = timestamp_sort_key(event.get("created_at"))
        if event_key >= latest_event_key:
            latest_event_key = event_key
            latest_event_type = event.get("event_type")
            latest_event_at = event.get("created_at")

    return {
        "events_path": str(events_path),
        "event_count": event_count,
        "invalid_event_count": invalid_event_count,
        "latest_event_type": latest_event_type,
        "latest_event_at": latest_event_at,
    }


def latest_step_report_path(mission_path: Path) -> Optional[str]:
    folder = mission_path / "step_reports"
    if not folder.exists():
        return None
    reports = sorted(
        (path for path in folder.glob("*.md") if path.is_file()),
        key=lambda item: (item.stat().st_mtime_ns, item.name),
    )
    return str(reports[-1]) if reports else None


def session_summary(
    workspace_root: Path,
    directory: Path,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    directory = resolve_under(missions_root(workspace_root), directory)
    mission_id = validate_mission_id(directory.name)
    session_path = directory / "hokage_shell_session.json"
    payload = read_json_object(session_path)
    validate_session_payload(payload, mission_id)

    event_summary = read_event_summary(directory / "events.ndjson")
    current_repo = repo_root.resolve() if repo_root is not None else None
    recorded_repo = Path(str(payload["repo_root"])).resolve()
    recorded_workspace = Path(str(payload["workspace_root"])).resolve()

    task = payload["task"].strip().replace("\n", " ")
    summary = {
        "mission_id": mission_id,
        "state": payload["state"],
        "task_preview": task[:160],
        "created_at": payload["created_at"],
        "updated_at": payload["updated_at"],
        "next_recommended_action": payload["next_recommended_action"],
        "session_path": str(session_path),
        "latest_step_report_path": latest_step_report_path(directory),
        "repo_root": str(recorded_repo),
        "workspace_root": str(recorded_workspace),
        "repo_root_matches": (
            recorded_repo == current_repo if current_repo is not None else None
        ),
        "workspace_root_matches": recorded_workspace == workspace_root.resolve(),
        **event_summary,
    }
    summary["continuity_status"] = (
        "ready"
        if summary["workspace_root_matches"]
        else "workspace_root_mismatch"
    )
    return summary


def candidate_directories(workspace_root: Path) -> Iterable[Path]:
    root = missions_root(workspace_root)
    if not root.exists():
        return []
    return sorted(
        (
            path
            for path in root.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        ),
        key=lambda item: item.name,
    )


def list_missions(
    workspace_root: Path,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    workspace_root = workspace_root.resolve()
    valid: List[Dict[str, Any]] = []
    invalid: List[Dict[str, Any]] = []

    for directory in candidate_directories(workspace_root):
        try:
            valid.append(
                session_summary(
                    workspace_root,
                    directory,
                    repo_root=repo_root,
                )
            )
        except MissionContinuityError as exc:
            invalid.append(
                {
                    "mission_id": directory.name,
                    "mission_path": str(directory),
                    "status": "invalid",
                    "blocker": str(exc),
                }
            )

    valid.sort(
        key=lambda item: (
            timestamp_sort_key(item.get("updated_at")),
            timestamp_sort_key(item.get("created_at")),
            item["mission_id"],
        ),
        reverse=True,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "generated_at": utc_now(),
        "status": "passed",
        "mode": "list",
        "workspace_root": str(workspace_root),
        "repo_root": str(repo_root.resolve()) if repo_root else None,
        "mission_count": len(valid),
        "invalid_mission_count": len(invalid),
        "latest_mission_id": valid[0]["mission_id"] if valid else None,
        "missions": valid,
        "invalid_missions": invalid,
        "boundaries": BOUNDARIES,
        "authority": {
            "continuity_report_is_evidence_only": True,
            "resume_does_not_authorize_execution": True,
            "memory_is_not_read": True,
        },
    }


def select_mission(
    listing: Dict[str, Any],
    mission_id: Optional[str] = None,
    latest: bool = False,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if latest and mission_id:
        raise MissionContinuityError(
            "choose mission_id or latest, not both"
        )
    if not latest and not mission_id:
        raise MissionContinuityError(
            "mission_id or latest is required"
        )

    if latest:
        selected_id = listing.get("latest_mission_id")
        if selected_id is None:
            return None, "no valid local missions were found"
    else:
        selected_id = validate_mission_id(str(mission_id))

    for mission in listing.get("missions", []):
        if mission.get("mission_id") == selected_id:
            return mission, None

    for invalid in listing.get("invalid_missions", []):
        if invalid.get("mission_id") == selected_id:
            return None, invalid.get("blocker") or "mission is invalid"

    return None, f"mission not found: {selected_id}"


def build_resume_report(
    workspace_root: Path,
    repo_root: Optional[Path] = None,
    mission_id: Optional[str] = None,
    latest: bool = False,
) -> Dict[str, Any]:
    listing = list_missions(workspace_root, repo_root=repo_root)
    mission, blocker = select_mission(
        listing,
        mission_id=mission_id,
        latest=latest,
    )

    if mission is None:
        return {
            "schema_version": SCHEMA_VERSION,
            "report_type": REPORT_TYPE,
            "generated_at": utc_now(),
            "status": "blocked",
            "mode": "resume",
            "mission_id": mission_id,
            "latest_requested": latest,
            "mission": None,
            "blocker": blocker,
            "boundaries": BOUNDARIES,
            "authority": {
                "continuity_report_is_evidence_only": True,
                "resume_does_not_authorize_execution": True,
                "memory_is_not_read": True,
            },
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "generated_at": utc_now(),
        "status": "passed",
        "mode": "resume",
        "mission_id": mission["mission_id"],
        "latest_requested": latest,
        "mission": mission,
        "continuity": {
            "active_state": mission["state"],
            "last_event_type": mission["latest_event_type"],
            "last_event_at": mission["latest_event_at"],
            "event_count": mission["event_count"],
            "invalid_event_count": mission["invalid_event_count"],
            "latest_step_report_path": mission["latest_step_report_path"],
            "next_recommended_action": mission["next_recommended_action"],
            "repo_root_matches": mission["repo_root_matches"],
            "workspace_root_matches": mission["workspace_root_matches"],
        },
        "boundaries": BOUNDARIES,
        "authority": {
            "continuity_report_is_evidence_only": True,
            "resume_does_not_authorize_execution": True,
            "memory_is_not_read": True,
        },
    }


def exit_code_for_report(report: Dict[str, Any]) -> int:
    if report.get("status") == "passed":
        return 0
    blocker = str(report.get("blocker") or "")
    if blocker.startswith("mission not found") or blocker.startswith(
        "no valid local missions"
    ):
        return 1
    return 2
