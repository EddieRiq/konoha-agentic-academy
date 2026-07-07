#!/usr/bin/env python3
"""Controlled sandbox artifact writer for Konoha dry-run workflows.

This tool writes proposed artifacts only inside:

    <sandbox-root>/runs/<run-id>/proposed_outputs/

It also writes dry-run planning metadata inside the same run folder:

    apply_plan.json
    artifact_write_report.json

It does not execute shell commands, perform Git operations, invoke adapters,
access private Village context, use the network, or apply artifacts to the repo.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SAFE_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ALLOWED_SUFFIXES = {".md", ".json", ".txt"}


class ArtifactWriterError(Exception):
    """Raised when sandbox artifact writing is blocked."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fail(message: str) -> int:
    print("SANDBOX ARTIFACT WRITE FAILED")
    print(message)
    return 1


def require_safe_run_id(run_id: str) -> None:
    if not SAFE_RUN_ID_RE.fullmatch(run_id):
        raise ArtifactWriterError(
            "Unsafe run_id. Use only letters, numbers, dots, underscores, and hyphens; "
            "do not use path separators or traversal."
        )


def ensure_under(parent: Path, child: Path, label: str) -> None:
    try:
        child.relative_to(parent)
    except ValueError as exc:
        raise ArtifactWriterError(f"{label} escapes allowed sandbox boundary: {child}") from exc


def resolve_run_paths(sandbox_root_arg: str, run_id: str) -> dict[str, Path]:
    require_safe_run_id(run_id)

    sandbox_root = Path(sandbox_root_arg).resolve()
    runs_root = (sandbox_root / "runs").resolve()
    run_dir = (runs_root / run_id).resolve()

    ensure_under(sandbox_root, runs_root, "runs_root")
    ensure_under(runs_root, run_dir, "run_dir")

    manifest_path = run_dir / "sandbox_run_manifest.json"
    outputs_root = (run_dir / "proposed_outputs").resolve()
    apply_plan_path = run_dir / "apply_plan.json"
    report_path = run_dir / "artifact_write_report.json"

    return {
        "sandbox_root": sandbox_root,
        "runs_root": runs_root,
        "run_dir": run_dir,
        "manifest_path": manifest_path,
        "outputs_root": outputs_root,
        "apply_plan_path": apply_plan_path,
        "report_path": report_path,
    }


def resolve_artifact_path(outputs_root: Path, artifact_rel_arg: str) -> tuple[Path, str]:
    artifact_rel = Path(artifact_rel_arg)

    if artifact_rel.is_absolute():
        raise ArtifactWriterError("artifact-path must be relative to proposed_outputs.")

    if any(part in {"..", ""} for part in artifact_rel.parts):
        raise ArtifactWriterError("artifact-path must not contain empty parts or '..' traversal.")

    suffix = artifact_rel.suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        allowed = ", ".join(sorted(ALLOWED_SUFFIXES))
        raise ArtifactWriterError(f"Unsupported artifact extension '{suffix}'. Allowed: {allowed}")

    artifact_path = (outputs_root / artifact_rel).resolve()
    ensure_under(outputs_root, artifact_path, "artifact_path")

    normalized_rel = artifact_rel.as_posix()
    return artifact_path, normalized_rel


def load_json_file(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ArtifactWriterError(f"Required file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArtifactWriterError(f"Invalid JSON file: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ArtifactWriterError(f"JSON file must contain an object: {path}")

    return data


def validate_manifest(manifest_path: Path, run_id: str) -> None:
    manifest = load_json_file(manifest_path)
    manifest_run_id = manifest.get("run_id")
    if manifest_run_id != run_id:
        raise ArtifactWriterError(
            f"Manifest run_id mismatch. Expected '{run_id}', found '{manifest_run_id}'."
        )

    if manifest.get("execution") != "blocked":
        raise ArtifactWriterError("Sandbox manifest must keep execution blocked.")

    if manifest.get("git_operations") != "blocked":
        raise ArtifactWriterError("Sandbox manifest must keep Git operations blocked.")

    if manifest.get("adapter_execution") != "blocked":
        raise ArtifactWriterError("Sandbox manifest must keep adapter execution blocked.")

    if manifest.get("private_context_access") != "blocked":
        raise ArtifactWriterError("Sandbox manifest must keep private context access blocked.")


def validate_content_for_suffix(content: str, suffix: str) -> None:
    if suffix.lower() == ".json":
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ArtifactWriterError(f"Artifact content is not valid JSON: {exc}") from exc
        if not isinstance(parsed, (dict, list)):
            raise ArtifactWriterError("JSON artifact content must be an object or array.")


def read_existing_apply_plan(path: Path, run_id: str) -> dict[str, Any]:
    if not path.exists():
        return {
            "$schema": "../../schemas/runtime/sandbox_apply_plan.schema.json",
            "schema_version": "0.1",
            "plan_id": f"apply-plan-{run_id}",
            "mode": "dry_run",
            "run_id": run_id,
            "status": "proposed",
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "execution": "blocked",
            "filesystem_mutation": "sandbox_only",
            "git_operations": "blocked",
            "adapter_execution": "blocked",
            "private_context_access": "blocked",
            "network_access": "blocked",
            "planned_changes": [],
            "notes": [
                "This apply plan is a dry-run proposal only.",
                "It does not authorize applying files to the repository.",
            ],
        }

    plan = load_json_file(path)
    if plan.get("run_id") != run_id:
        raise ArtifactWriterError(f"Existing apply_plan.json run_id does not match '{run_id}'.")
    if plan.get("status") not in {"proposed", "draft"}:
        raise ArtifactWriterError("Existing apply_plan.json is not editable by this dry-run writer.")
    if not isinstance(plan.get("planned_changes"), list):
        raise ArtifactWriterError("Existing apply_plan.json must contain planned_changes list.")
    return plan


def update_apply_plan(
    plan: dict[str, Any],
    run_id: str,
    artifact_rel: str,
    artifact_kind: str,
    intended_repo_path: str,
) -> dict[str, Any]:
    planned_changes = [
        item
        for item in plan.get("planned_changes", [])
        if item.get("sandbox_artifact_path") != f"proposed_outputs/{artifact_rel}"
    ]

    change_id = f"change-{len(planned_changes) + 1:03d}"
    planned_changes.append(
        {
            "change_id": change_id,
            "operation": "propose_file",
            "artifact_kind": artifact_kind,
            "sandbox_artifact_path": f"proposed_outputs/{artifact_rel}",
            "intended_repo_path": intended_repo_path or "UNASSIGNED",
            "apply_status": "not_applied",
            "requires_human_approval": True,
            "execution": "blocked",
            "git_operations": "blocked",
            "notes": [
                "This record proposes an artifact only.",
                "Applying it to the repository requires a future human-approved apply plan gate.",
            ],
        }
    )

    plan["planned_changes"] = planned_changes
    plan["updated_at"] = utc_now()
    return plan


def build_report(
    run_id: str,
    artifact_rel: str,
    artifact_kind: str,
    artifact_path: Path,
    apply_plan_path: Path,
    force: bool,
) -> dict[str, Any]:
    return {
        "$schema": "../../schemas/runtime/sandbox_artifact_write_report.schema.json",
        "schema_version": "0.1",
        "run_id": run_id,
        "status": "written",
        "created_at": utc_now(),
        "artifact_kind": artifact_kind,
        "sandbox_artifact_path": f"proposed_outputs/{artifact_rel}",
        "artifact_absolute_path": str(artifact_path),
        "apply_plan_path": str(apply_plan_path),
        "force_used": force,
        "execution": "blocked",
        "filesystem_mutation": "sandbox_only",
        "git_operations": "blocked",
        "adapter_execution": "blocked",
        "private_context_access": "blocked",
        "network_access": "blocked",
        "repository_apply": "blocked",
        "requires_human_approval_to_apply": True,
    }


def write_sandbox_artifact(
    *,
    sandbox_root: str,
    run_id: str,
    artifact_path_arg: str,
    content: str,
    artifact_kind: str,
    intended_repo_path: str,
    force: bool,
) -> dict[str, Any]:
    paths = resolve_run_paths(sandbox_root, run_id)
    run_dir = paths["run_dir"]

    if not run_dir.exists():
        raise ArtifactWriterError(f"Run directory does not exist: {run_dir}")

    validate_manifest(paths["manifest_path"], run_id)

    artifact_path, artifact_rel = resolve_artifact_path(paths["outputs_root"], artifact_path_arg)
    validate_content_for_suffix(content, artifact_path.suffix)

    if artifact_path.exists() and not force:
        raise ArtifactWriterError(
            f"Artifact already exists: {artifact_path}. Re-run with --force to overwrite."
        )

    paths["outputs_root"].mkdir(parents=True, exist_ok=True)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(content, encoding="utf-8")

    plan = read_existing_apply_plan(paths["apply_plan_path"], run_id)
    plan = update_apply_plan(plan, run_id, artifact_rel, artifact_kind, intended_repo_path)
    paths["apply_plan_path"].write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")

    report = build_report(
        run_id=run_id,
        artifact_rel=artifact_rel,
        artifact_kind=artifact_kind,
        artifact_path=artifact_path,
        apply_plan_path=paths["apply_plan_path"],
        force=force,
    )
    paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    return {
        "artifact_path": artifact_path,
        "artifact_rel": artifact_rel,
        "apply_plan_path": paths["apply_plan_path"],
        "report_path": paths["report_path"],
        "report": report,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a proposed artifact inside a Konoha sandbox run."
    )
    parser.add_argument("--sandbox-root", required=True, help="Sandbox root path.")
    parser.add_argument("--run-id", required=True, help="Existing sandbox run id.")
    parser.add_argument(
        "--artifact-path",
        required=True,
        help="Relative path under proposed_outputs, e.g. docs/proposed_note.md.",
    )
    parser.add_argument("--content", required=True, help="Artifact content to write.")
    parser.add_argument(
        "--artifact-kind",
        default="markdown",
        choices=["markdown", "json", "text", "report"],
        help="Artifact classification for the apply plan.",
    )
    parser.add_argument(
        "--intended-repo-path",
        default="UNASSIGNED",
        help="Optional future repo path. This tool does not apply it.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing sandbox artifact.")
    parser.add_argument("--json", action="store_true", help="Print JSON report to stdout.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = write_sandbox_artifact(
            sandbox_root=args.sandbox_root,
            run_id=args.run_id,
            artifact_path_arg=args.artifact_path,
            content=args.content,
            artifact_kind=args.artifact_kind,
            intended_repo_path=args.intended_repo_path,
            force=args.force,
        )
    except ArtifactWriterError as exc:
        return fail(str(exc))

    if args.json:
        print(json.dumps(result["report"], indent=2))
        return 0

    print("SANDBOX ARTIFACT WRITTEN")
    print(f"Run ID: {args.run_id}")
    print(f"Artifact: {result['artifact_path']}")
    print(f"Apply plan: {result['apply_plan_path']}")
    print(f"Report: {result['report_path']}")
    print("Execution: blocked")
    print("Filesystem mutation: sandbox only")
    print("Repository apply: blocked")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Adapter execution: blocked")
    print("Network access: blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
