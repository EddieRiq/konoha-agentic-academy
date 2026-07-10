#!/usr/bin/env python3
"""Read-only terminal operator status for the Hokage Shell."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from mission_continuity import list_missions

SCHEMA_VERSION = "1.0.0"
REPORT_TYPE = "hokage_operator_status_report"

BOUNDARIES = {
    "arbitrary_shell": "blocked",
    "autonomous_background_agents": "blocked",
    "git_operations": "read_only",
    "model_invocation": "blocked",
    "network_access": "blocked",
    "private_memory_read": "blocked",
    "repository_source_mutation": "blocked",
    "workspace_mutation": "blocked",
}


class OperatorStatusError(RuntimeError):
    """Raised when a deterministic status prerequisite is invalid."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        capture_output=True,
        timeout=20,
        shell=False,
        check=False,
    )


def git_stdout(repo_root: Path, *args: str) -> Optional[str]:
    completed = run_git(repo_root, *args)
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def collect_repo_status(repo_root: Path) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        raise OperatorStatusError(f"repository root not found: {repo_root}")

    top_level = git_stdout(repo_root, "rev-parse", "--show-toplevel")
    if top_level is None:
        raise OperatorStatusError(f"not a Git repository: {repo_root}")

    head = git_stdout(repo_root, "rev-parse", "HEAD")
    branch = git_stdout(repo_root, "branch", "--show-current")
    porcelain = git_stdout(
        repo_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    if head is None or porcelain is None:
        raise OperatorStatusError("unable to read repository status")

    changed_lines = [line for line in porcelain.splitlines() if line.strip()]
    upstream = git_stdout(
        repo_root,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
    )

    behind: Optional[int] = None
    ahead: Optional[int] = None
    tracking_synced: Optional[bool] = None
    if upstream:
        counts = git_stdout(
            repo_root,
            "rev-list",
            "--left-right",
            "--count",
            f"{upstream}...HEAD",
        )
        if counts:
            parts = counts.split()
            if len(parts) == 2 and all(part.isdigit() for part in parts):
                behind, ahead = (int(parts[0]), int(parts[1]))
                tracking_synced = behind == 0 and ahead == 0

    latest_tag = git_stdout(repo_root, "describe", "--tags", "--abbrev=0")

    return {
        "repo_root": str(repo_root),
        "top_level": top_level,
        "head": head,
        "head_short": head[:7],
        "branch": branch or "(detached)",
        "working_tree_clean": not changed_lines,
        "changed_path_count": len(changed_lines),
        "upstream": upstream,
        "behind": behind,
        "ahead": ahead,
        "tracking_synced": tracking_synced,
        "latest_tag": latest_tag,
    }


def newest_matching(folder: Path, pattern: str) -> Optional[str]:
    if not folder.exists():
        return None
    matches = sorted(
        (path for path in folder.glob(pattern) if path.is_file()),
        key=lambda path: (path.stat().st_mtime_ns, path.as_posix()),
    )
    return str(matches[-1]) if matches else None


def collect_mission_status(
    workspace_root: Path,
    repo_root: Path,
) -> Dict[str, Any]:
    workspace_root = workspace_root.resolve()
    listing = list_missions(workspace_root, repo_root=repo_root)

    latest = None
    missions = listing.get("missions") or []
    if missions:
        latest = missions[0]

    evidence = {
        "latest_step_report_path": None,
        "latest_audit_json_path": None,
        "latest_patch_plan_path": None,
        "events_path": None,
    }

    if latest:
        mission_id = latest["mission_id"]
        mission_folder = workspace_root / "missions" / mission_id
        evidence = {
            "latest_step_report_path": latest.get(
                "latest_step_report_path"
            ),
            "latest_audit_json_path": newest_matching(
                mission_folder,
                "**/*_repo_consistency_audit.json",
            ),
            "latest_patch_plan_path": newest_matching(
                mission_folder,
                "**/*_repo_patch_plan.json",
            ),
            "events_path": latest.get("events_path"),
        }

    return {
        "workspace_root": str(workspace_root),
        "workspace_exists": workspace_root.exists(),
        "mission_count": listing.get("mission_count", 0),
        "invalid_mission_count": listing.get(
            "invalid_mission_count",
            0,
        ),
        "latest_mission_id": listing.get("latest_mission_id"),
        "latest_mission": latest,
        "evidence": evidence,
    }


def collect_terminal_status(
    *,
    plain_requested: bool = False,
    stdout_tty: Optional[bool] = None,
) -> Dict[str, Any]:
    is_tty = sys.stdout.isatty() if stdout_tty is None else stdout_tty
    terminal_size = shutil.get_terminal_size(fallback=(80, 24))
    viewers = {
        name: shutil.which(name)
        for name in ("glow", "bat", "less")
    }
    preferred = next(
        (name for name in ("glow", "bat", "less") if viewers[name]),
        "plain",
    )

    return {
        "stdout_is_tty": bool(is_tty),
        "plain_requested": bool(plain_requested),
        "term": os.environ.get("TERM"),
        "columns": terminal_size.columns,
        "lines": terminal_size.lines,
        "viewers": viewers,
        "preferred_viewer": preferred,
    }


def choose_next_action(
    repo: Dict[str, Any],
    mission: Dict[str, Any],
) -> str:
    if not repo.get("working_tree_clean"):
        return "Review the working tree before proposing any execution."
    if repo.get("tracking_synced") is False:
        return "Review local and upstream divergence before release work."
    if mission.get("invalid_mission_count", 0):
        return "Inspect invalid local mission sessions before resuming."
    latest = mission.get("latest_mission")
    if latest:
        return (
            latest.get("next_recommended_action")
            or "Review mission evidence and choose the next approved action."
        )
    return "Start a mission only after explicit human approval."


def build_operator_status(
    repo_root: Path,
    workspace_root: Path,
    *,
    plain_requested: bool = False,
    approval_tokens: Optional[Mapping[str, str]] = None,
    stdout_tty: Optional[bool] = None,
) -> Dict[str, Any]:
    repo = collect_repo_status(repo_root)
    mission = collect_mission_status(workspace_root, repo_root.resolve())
    terminal = collect_terminal_status(
        plain_requested=plain_requested,
        stdout_tty=stdout_tty,
    )

    attention_reasons: List[str] = []
    if not repo["working_tree_clean"]:
        attention_reasons.append("working_tree_dirty")
    if repo["tracking_synced"] is False:
        attention_reasons.append("tracking_not_synced")
    if mission["invalid_mission_count"]:
        attention_reasons.append("invalid_mission_sessions")

    operator_state = (
        "attention_required"
        if attention_reasons
        else "ready"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "generated_at": utc_now(),
        "status": "passed",
        "operator_state": operator_state,
        "attention_reasons": attention_reasons,
        "repo": repo,
        "mission": mission,
        "terminal": terminal,
        "approval_tokens": dict(approval_tokens or {}),
        "next_recommended_action": choose_next_action(repo, mission),
        "authority": {
            "status_report_is_evidence_only": True,
            "status_does_not_authorize_execution": True,
            "mission_state_does_not_authorize_execution": True,
            "approval_tokens_are_required_by_sensitive_flows": True,
        },
        "boundaries": BOUNDARIES,
    }


def operator_status_lines(report: Dict[str, Any]) -> List[str]:
    repo = report["repo"]
    mission = report["mission"]
    latest = mission.get("latest_mission")
    evidence = mission.get("evidence") or {}
    terminal = report["terminal"]

    tracking = "not_configured"
    if repo.get("tracking_synced") is True:
        tracking = "synced"
    elif repo.get("tracking_synced") is False:
        tracking = (
            f"behind={repo.get('behind')} ahead={repo.get('ahead')}"
        )

    mission_label = "none"
    mission_state = "n/a"
    if latest:
        mission_label = latest.get("mission_id") or "unknown"
        mission_state = latest.get("state") or "unknown"

    evidence_count = sum(
        1
        for value in (
            evidence.get("latest_step_report_path"),
            evidence.get("latest_audit_json_path"),
            evidence.get("latest_patch_plan_path"),
            evidence.get("events_path"),
        )
        if value
    )

    return [
        f"operator state: {report.get('operator_state')}",
        (
            f"repo: {repo.get('branch')}@{repo.get('head_short')} · "
            f"clean={repo.get('working_tree_clean')} · "
            f"tracking={tracking}"
        ),
        f"latest tag: {repo.get('latest_tag') or 'none'}",
        (
            f"mission: {mission_label} · state={mission_state} · "
            f"invalid={mission.get('invalid_mission_count', 0)}"
        ),
        f"evidence artifacts available: {evidence_count}",
        (
            f"terminal: tty={terminal.get('stdout_is_tty')} · "
            f"columns={terminal.get('columns')} · "
            f"viewer={terminal.get('preferred_viewer')}"
        ),
        f"next: {report.get('next_recommended_action')}",
        "status is evidence only; it does not authorize execution",
    ]


def exit_code_for_report(report: Dict[str, Any]) -> int:
    return 0 if report.get("status") == "passed" else 2
