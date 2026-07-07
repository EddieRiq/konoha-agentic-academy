"""Prepare a Konoha sandbox run directory.

This CLI creates a dry-run sandbox workspace and a sandbox_run_manifest.json
inside the declared sandbox root.

It is not a mission executor.

Allowed behavior:
- create sandbox subdirectories under the declared sandbox root;
- write one manifest JSON inside the sandbox run directory;
- print a clear summary.

Blocked behavior:
- shell execution;
- Git operations;
- adapter invocation;
- network access;
- private context access;
- writes outside the declared sandbox root.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

try:
    from sandbox_guard import (
        SandboxBoundaryError,
        ensure_within_root,
        resolve_sandbox_root,
        sandbox_subdir,
        validate_safe_id,
    )
except ImportError:  # pragma: no cover - supports package-style execution
    from .sandbox_guard import (
        SandboxBoundaryError,
        ensure_within_root,
        resolve_sandbox_root,
        sandbox_subdir,
        validate_safe_id,
    )


MANIFEST_FILENAME = "sandbox_run_manifest.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_manifest(
    *,
    run_id: str,
    mission_title: str,
    sandbox_root: Path,
    run_dir: Path,
) -> dict[str, Any]:
    """Build a non-executing sandbox manifest."""
    relative_run_dir = run_dir.relative_to(sandbox_root)

    return {
        "schema_version": "0.13.0",
        "kind": "konoha.sandbox_run_manifest",
        "run_id": run_id,
        "mission_title": mission_title.strip(),
        "created_at_utc": utc_now(),
        "sandbox_root": str(sandbox_root),
        "run_directory": str(relative_run_dir).replace("\\", "/"),
        "mode": "dry_run",
        "execution": "blocked",
        "filesystem_mutation": "sandbox_only",
        "git_operations": "blocked",
        "adapter_execution": "blocked",
        "private_context_access": "blocked",
        "network_access": "blocked",
        "created_artifacts": [
            "sandbox_run_manifest.json",
        ],
        "allowed_write_scope": [
            str(relative_run_dir).replace("\\", "/"),
        ],
        "blocked_scopes": [
            "repository_source_files",
            "docs",
            "runtime",
            "adapters",
            "scrolls",
            "alliance/private",
            "git",
            "external_network",
        ],
        "notes": [
            "This manifest records sandbox preparation only.",
            "It does not authorize mission execution.",
            "It does not authorize shell commands, Git operations, adapters, or private context access.",
        ],
    }


def prepare_sandbox_run(
    *,
    sandbox_root: str | Path,
    run_id: str,
    mission_title: str,
    force: bool = False,
) -> Path:
    """Create sandbox run directories and write the manifest.

    Returns the manifest path.
    """
    safe_run_id = validate_safe_id(run_id, "run_id")

    if not mission_title or not mission_title.strip():
        raise SandboxBoundaryError("mission title must not be empty")

    root = resolve_sandbox_root(sandbox_root)
    run_dir = sandbox_subdir(root, "runs", safe_run_id)
    tmp_dir = sandbox_subdir(root, "tmp")
    reports_dir = sandbox_subdir(root, "reports")

    manifest_path = ensure_within_root(root, run_dir / MANIFEST_FILENAME)

    if manifest_path.exists() and not force:
        raise SandboxBoundaryError(
            f"manifest already exists: {manifest_path}. Use --force to overwrite sandbox manifest only."
        )

    # These are the only writes performed by the CLI.
    root.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest(
        run_id=safe_run_id,
        mission_title=mission_title,
        sandbox_root=root,
        run_dir=run_dir,
    )

    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return manifest_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a dry-run-only Konoha sandbox run directory."
    )
    parser.add_argument(
        "--sandbox-root",
        default="sandbox",
        help="Declared sandbox root. Writes are restricted under this root. Default: sandbox",
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Safe run identifier. Single path segment only.",
    )
    parser.add_argument(
        "--mission-title",
        required=True,
        help="Human-readable mission title for the sandbox manifest.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the sandbox_run_manifest.json for this run only.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    try:
        manifest_path = prepare_sandbox_run(
            sandbox_root=args.sandbox_root,
            run_id=args.run_id,
            mission_title=args.mission_title,
            force=args.force,
        )
    except SandboxBoundaryError as exc:
        print("SANDBOX PREPARATION FAILED")
        print(f"Reason: {exc}")
        return 1

    print("SANDBOX RUN PREPARED")
    print(f"Manifest: {manifest_path}")
    print("Mode: dry_run")
    print("Execution: blocked")
    print("Filesystem mutation: sandbox only")
    print("Git operations: blocked")
    print("Adapter execution: blocked")
    print("Private context access: blocked")
    print("Network access: blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
