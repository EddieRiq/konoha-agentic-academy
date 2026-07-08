"""Report listing and UI session report helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_under(root: Path, *parts: str) -> Path:
    root_resolved = Path(root).resolve()
    candidate = root_resolved.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("path escapes root") from exc
    return candidate


def list_reports(sandbox_root: Path) -> list[dict[str, Any]]:
    reports_dir = resolve_under(sandbox_root, "reports")
    if not reports_dir.exists():
        return []
    rows = []
    for path in sorted(reports_dir.glob("*.json"), reverse=True):
        rows.append({"name": path.name, "path": str(path), "size_bytes": path.stat().st_size})
    return rows


def write_ui_session_report(sandbox_root: Path, workspace_root: Path, mission_count: int) -> dict[str, Any]:
    reports_dir = resolve_under(sandbox_root, "reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = utc_now().replace(":", "").replace("+", "Z")
    report = {
        "schema_version": "1.0",
        "report_type": "local_web_ui_session_report",
        "status": "passed",
        "created_at": utc_now(),
        "workspace_root": str(Path(workspace_root).resolve()),
        "mission_count": mission_count,
        "execution": "blocked",
        "filesystem_mutation": "sandbox reports and mission workspace only",
        "repository_apply": "blocked",
        "git_operations": "blocked",
        "private_context_access": "blocked",
        "real_model_invocation": "blocked_from_ui_alpha",
        "network_access": "localhost_ui_only",
        "ui_adds_authority": False,
        "v2_alignment_review_gate": "required before v2.0.0",
    }
    report_path = reports_dir / f"{timestamp}_local_web_ui_session_report.json"
    report["report_path"] = str(report_path)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
