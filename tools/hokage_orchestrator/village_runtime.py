"""Supervised private village initialization for Konoha."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable


SCHEMA_VERSION = "1.0.0"
DEFAULT_VILLAGE_NAME = "kirigakure"
REQUIRED_DIRS = (
    "state",
    "memory",
    "telemetry",
    "budgets",
    "handoffs",
    "reports",
    "evals",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def safe_village_name(value: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError("Village name is required.")
    if normalized in {".", ".."}:
        raise ValueError("Unsafe village name.")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if normalized[0] not in set("abcdefghijklmnopqrstuvwxyz0123456789"):
        raise ValueError("Village name must start with a letter or digit.")
    if any(char not in allowed for char in normalized):
        raise ValueError("Village name contains unsupported characters.")
    if "/" in normalized or "\\" in normalized:
        raise ValueError("Village name may not contain path separators.")
    return normalized[:48]


def git_ignored(repo_root: Path, village_root: Path) -> bool:
    try:
        relative = village_root.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    # A trailing-slash ignore rule such as ``alliance/*/`` does not match
    # a non-existent directory when Git receives the path without a slash.
    # Village initialization must verify the future directory before creating
    # it, so preserve directory semantics explicitly.
    candidate = relative.as_posix().rstrip("/") + "/"
    completed = subprocess.run(
        ["git", "check-ignore", "-q", "--", candidate],
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        shell=False,
        timeout=20,
    )
    return completed.returncode == 0


class VillageInitializer:
    """Inspects and initializes one ignored private village."""

    def __init__(
        self,
        *,
        repo_root: Path,
        village_name: str = DEFAULT_VILLAGE_NAME,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.village_name = safe_village_name(village_name)
        self.village_root = (
            self.repo_root / "alliance" / self.village_name
        ).resolve()
        self.manifest_path = (
            self.village_root / "state" / "village_manifest.json"
        )

    @property
    def approval_phrase(self) -> str:
        return f"APROBAR ALDEA PRIVADA {self.village_name}"

    def inspect(self) -> Dict[str, Any]:
        ignored = git_ignored(self.repo_root, self.village_root)
        existing = self.village_root.is_dir()
        missing_dirs = [
            name for name in REQUIRED_DIRS
            if not (self.village_root / name).is_dir()
        ]
        return {
            "schema_version": SCHEMA_VERSION,
            "report_type": "private_village_status",
            "village_name": self.village_name,
            "village_root": str(self.village_root),
            "exists": existing,
            "git_ignored": ignored,
            "ready": existing and ignored and not missing_dirs,
            "missing_directories": missing_dirs,
            "approval_phrase": self.approval_phrase,
            "authority": {
                "inspection_is_evidence_only": True,
                "creation_requires_exact_human_approval": True,
                "village_does_not_authorize_execution": True,
            },
        }

    def initialize(self, approval: str) -> Dict[str, Any]:
        status = self.inspect()
        if approval != self.approval_phrase:
            raise PermissionError("Exact village approval phrase required.")
        if not status["git_ignored"]:
            raise RuntimeError(
                f"{self.village_root} is not ignored by Git."
            )
        for name in REQUIRED_DIRS:
            (self.village_root / name).mkdir(
                parents=True,
                exist_ok=True,
            )
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "report_type": "private_village_manifest",
            "village_name": self.village_name,
            "village_root": str(self.village_root),
            "created_at": utc_now(),
            "directories": list(REQUIRED_DIRS),
            "authority": {
                "private_only": True,
                "manifest_is_evidence_only": True,
                "manifest_does_not_authorize_execution": True,
            },
        }
        write_json(self.manifest_path, manifest)
        result = self.inspect()
        result["manifest_path"] = str(self.manifest_path)
        result["created"] = True
        return result
