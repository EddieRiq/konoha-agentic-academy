"""Mission Workspace helpers for the Local Web UI Alpha.

These helpers only read/write under an explicit workspace root.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")

REQUIRED_DIRS = [
    "inputs",
    "context",
    "plans",
    "outputs",
    "reports",
    "approvals",
    "evidence",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_safe_id(value: str, label: str = "id") -> str:
    if not value or not SAFE_ID_RE.match(value) or "/" in value or "\\" in value:
        raise ValueError(f"{label} must be alphanumeric plus '.', '_' or '-'")
    if value in {".", ".."}:
        raise ValueError(f"{label} may not be '.' or '..'")
    return value


def resolve_under(root: Path, *parts: str) -> Path:
    root_resolved = Path(root).resolve()
    candidate = root_resolved.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("path escapes workspace root") from exc
    return candidate


def missions_dir(workspace_root: Path) -> Path:
    return resolve_under(workspace_root, "missions")


def mission_dir(workspace_root: Path, mission_id: str) -> Path:
    validate_safe_id(mission_id, "mission_id")
    return resolve_under(workspace_root, "missions", mission_id)


def create_mission_workspace(
    workspace_root: Path,
    mission_id: str,
    title: str,
    scope: str,
    force: bool = False,
) -> dict[str, Any]:
    validate_safe_id(mission_id, "mission_id")
    target = mission_dir(workspace_root, mission_id)
    if target.exists() and not force:
        raise FileExistsError(f"mission workspace already exists: {target}")

    target.mkdir(parents=True, exist_ok=True)
    for dirname in REQUIRED_DIRS:
        resolve_under(target, dirname).mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": "1.0",
        "mission_id": mission_id,
        "title": title,
        "scope": scope,
        "created_at": utc_now(),
        "status": "draft",
        "review_required": True,
        "execution": "blocked",
        "repository_apply": "blocked",
        "git_operations": "blocked",
        "private_context_access": "blocked",
        "real_model_invocation": "blocked_from_ui_alpha",
        "network_access": "localhost_ui_only",
    }

    charter = f"""# Mission Charter: {title}

## Mission ID

`{mission_id}`

## Scope

{scope}

## Safety boundary

- Execution: blocked.
- Repository apply: blocked.
- Git operations: blocked.
- Private context access: blocked.
- Real model invocation from UI: blocked in v1.7 alpha.
- Network access: localhost UI only.

## Human review

Mission transitions require explicit human review.
"""

    readme = f"""# {mission_id}

Mission Workspace created by Local Web UI Alpha.

This workspace is evidence-only until an explicit human-approved gate performs a bounded transition.
"""

    approval_log = f"""# Approval Log: {mission_id}

Approval events recorded by Konoha tools and UI alpha appear here.

The UI does not store or autofill approval tokens.
"""

    (target / "mission_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (target / "charter.md").write_text(charter, encoding="utf-8")
    (target / "README.md").write_text(readme, encoding="utf-8")
    (target / "approvals" / "approval_log.md").write_text(approval_log, encoding="utf-8")
    return manifest


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def inspect_mission(workspace_root: Path, mission_id: str) -> dict[str, Any]:
    target = mission_dir(workspace_root, mission_id)
    manifest_path = target / "mission_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"mission manifest not found: {manifest_path}")

    manifest = read_json(manifest_path)
    return {
        "mission_id": mission_id,
        "path": str(target),
        "manifest": manifest,
        "charter": (target / "charter.md").read_text(encoding="utf-8")
        if (target / "charter.md").exists()
        else "",
        "plans": sorted(p.name for p in (target / "plans").glob("*") if p.is_file()),
        "reports": sorted(p.name for p in (target / "reports").glob("*") if p.is_file()),
        "evidence": sorted(p.name for p in (target / "evidence").glob("*") if p.is_file()),
        "approvals": sorted(p.name for p in (target / "approvals").glob("*") if p.is_file()),
    }


def list_missions(workspace_root: Path) -> list[dict[str, Any]]:
    base = missions_dir(workspace_root)
    if not base.exists():
        return []
    rows = []
    for child in sorted(base.iterdir()):
        if not child.is_dir():
            continue
        manifest_path = child / "mission_manifest.json"
        if manifest_path.exists():
            try:
                manifest = read_json(manifest_path)
            except Exception:
                manifest = {"mission_id": child.name, "status": "unreadable"}
        else:
            manifest = {"mission_id": child.name, "status": "missing_manifest"}
        rows.append(
            {
                "mission_id": manifest.get("mission_id", child.name),
                "title": manifest.get("title", ""),
                "status": manifest.get("status", ""),
                "created_at": manifest.get("created_at", ""),
                "path": str(child),
            }
        )
    return rows
