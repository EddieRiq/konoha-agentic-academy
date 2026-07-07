"""Path guard utilities for Konoha local sandbox boundaries.

This module is intentionally small and dependency-free.

Safety boundary:
- no shell execution;
- no Git operations;
- no network access;
- no adapter invocation;
- no private context access;
- no writes outside the declared sandbox root.

The guard only normalizes paths and rejects path traversal. It does not grant
permission to execute a mission.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable


SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class SandboxBoundaryError(ValueError):
    """Raised when a requested sandbox path violates the boundary."""


def validate_safe_id(value: str, field_name: str = "id") -> str:
    """Validate a safe identifier used as a path segment.

    The identifier must be a single segment. Slashes, backslashes, empty
    values, relative traversal, drive prefixes, and shell-like separators are
    rejected by construction.
    """
    if not isinstance(value, str):
        raise SandboxBoundaryError(f"{field_name} must be a string")

    cleaned = value.strip()
    if not cleaned:
        raise SandboxBoundaryError(f"{field_name} must not be empty")

    if cleaned in {".", ".."}:
        raise SandboxBoundaryError(f"{field_name} must not be a traversal segment")

    if "/" in cleaned or "\\" in cleaned:
        raise SandboxBoundaryError(f"{field_name} must be a single path segment")

    if ":" in cleaned:
        raise SandboxBoundaryError(f"{field_name} must not contain drive or URI separators")

    if not SAFE_ID_PATTERN.match(cleaned):
        raise SandboxBoundaryError(
            f"{field_name} must match {SAFE_ID_PATTERN.pattern}"
        )

    return cleaned


def resolve_sandbox_root(sandbox_root: str | Path) -> Path:
    """Resolve the declared sandbox root.

    The caller chooses the sandbox root. Every generated path must then remain
    under this root. The function does not require the path to already exist.
    """
    root = Path(sandbox_root).expanduser().resolve()
    if str(root).strip() == "":
        raise SandboxBoundaryError("sandbox root must not be empty")
    return root


def ensure_within_root(root: Path, target: Path) -> Path:
    """Return resolved target if it stays under root, otherwise raise."""
    resolved_root = root.resolve()
    resolved_target = target.resolve()

    try:
        resolved_target.relative_to(resolved_root)
    except ValueError as exc:
        raise SandboxBoundaryError(
            f"target path escapes sandbox root: {resolved_target}"
        ) from exc

    return resolved_target


def sandbox_subdir(root: Path, *segments: str) -> Path:
    """Build and validate a sandbox path from safe segments."""
    safe_segments: Iterable[str] = (
        validate_safe_id(segment, f"path segment {idx}")
        for idx, segment in enumerate(segments, start=1)
    )
    target = root.joinpath(*safe_segments)
    return ensure_within_root(root, target)
