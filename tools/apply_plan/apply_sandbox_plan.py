#!/usr/bin/env python3
"""Human-approved sandbox apply plan prototype for Konoha dry-run workflows.

This tool reads an apply_plan.json from:

    <sandbox-root>/runs/<run-id>/apply_plan.json

It can preview planned changes or, with explicit human confirmation, copy
proposed artifacts from:

    <sandbox-root>/runs/<run-id>/proposed_outputs/

to allowlisted repository paths.

It does not execute shell commands, invoke adapters, use the network, access
private Village context, or perform repository version-control operations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SAFE_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
APPROVAL_TOKEN = "APPLY_SANDBOX_PLAN"
ALLOWED_DESTINATION_PREFIXES = (
    "docs/",
    "examples/",
    "runtime/templates/",
    "schemas/runtime/",
    "scrolls/",
    "alliance/templates/",
    "sandbox/tmp/",
)
ALLOWED_SUFFIXES = {".md", ".json", ".txt"}
BLOCKED_DESTINATION_PARTS = {
    ".git",
    ".github",
    "kirigakure",
    "private-library",
    "private",
    "vault",
    "secrets",
    "secret",
    "credentials",
    "credential",
    "memory",
    ".env",
}
BLOCKED_FILENAMES = {".env"}


class ApplyPlanError(Exception):
    """Raised when an apply plan cannot be previewed or applied safely."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str) -> int:
    print("SANDBOX APPLY PLAN FAILED")
    print(message)
    return 1


def require_safe_run_id(run_id: str) -> None:
    if not SAFE_RUN_ID_RE.fullmatch(run_id):
        raise ApplyPlanError(
            "Unsafe run_id. Use only letters, numbers, dots, underscores, and hyphens; "
            "do not use path separators or traversal."
        )


def ensure_under(parent: Path, child: Path, label: str) -> None:
    try:
        child.relative_to(parent)
    except ValueError as exc:
        raise ApplyPlanError(f"{label} escapes allowed boundary: {child}") from exc


def normalize_relative_path(raw_path: str, *, label: str) -> str:
    if not raw_path or not isinstance(raw_path, str):
        raise ApplyPlanError(f"{label} must be a non-empty relative path.")

    path = Path(raw_path)
    if path.is_absolute():
        raise ApplyPlanError(f"{label} must not be absolute.")

    parts = path.parts
    if any(part in {"", ".", ".."} for part in parts):
        raise ApplyPlanError(f"{label} must not contain empty parts, '.', or '..' traversal.")

    normalized = path.as_posix()
    if normalized.startswith("/"):
        raise ApplyPlanError(f"{label} must be relative.")

    return normalized


def validate_destination_path(relative_path: str) -> None:
    normalized = normalize_relative_path(relative_path, label="intended_repo_path")

    suffix = Path(normalized).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        allowed = ", ".join(sorted(ALLOWED_SUFFIXES))
        raise ApplyPlanError(f"Destination suffix '{suffix}' is not allowed. Allowed: {allowed}")

    if not normalized.startswith(ALLOWED_DESTINATION_PREFIXES):
        allowed = ", ".join(ALLOWED_DESTINATION_PREFIXES)
        raise ApplyPlanError(f"Destination path is outside allowlist: {normalized}. Allowed: {allowed}")

    parts_lower = {part.lower() for part in Path(normalized).parts}
    if parts_lower & BLOCKED_DESTINATION_PARTS:
        blocked = ", ".join(sorted(parts_lower & BLOCKED_DESTINATION_PARTS))
        raise ApplyPlanError(f"Destination path contains blocked private or unsafe segment(s): {blocked}")

    if Path(normalized).name in BLOCKED_FILENAMES:
        raise ApplyPlanError("Destination filename is blocked.")


def resolve_paths(sandbox_root_arg: str, repo_root_arg: str, run_id: str) -> dict[str, Path]:
    require_safe_run_id(run_id)

    sandbox_root = Path(sandbox_root_arg).resolve()
    repo_root = Path(repo_root_arg).resolve()
    runs_root = (sandbox_root / "runs").resolve()
    run_dir = (runs_root / run_id).resolve()
    proposed_outputs = (run_dir / "proposed_outputs").resolve()
    apply_plan_path = run_dir / "apply_plan.json"
    report_path = run_dir / "human_approved_apply_report.json"

    ensure_under(sandbox_root, runs_root, "runs_root")
    ensure_under(runs_root, run_dir, "run_dir")
    ensure_under(run_dir, proposed_outputs, "proposed_outputs")
    ensure_under(run_dir, report_path, "report_path")

    return {
        "sandbox_root": sandbox_root,
        "repo_root": repo_root,
        "runs_root": runs_root,
        "run_dir": run_dir,
        "proposed_outputs": proposed_outputs,
        "apply_plan_path": apply_plan_path,
        "report_path": report_path,
    }


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ApplyPlanError(f"Missing {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ApplyPlanError(f"Invalid JSON in {label}: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ApplyPlanError(f"{label} must contain a JSON object.")
    return data


def validate_plan_boundaries(plan: dict[str, Any], run_id: str) -> None:
    if plan.get("run_id") != run_id:
        raise ApplyPlanError(f"apply_plan.json run_id mismatch. Expected '{run_id}'.")

    if plan.get("mode") != "dry_run":
        raise ApplyPlanError("apply_plan.json must keep mode as dry_run.")

    if plan.get("execution") != "blocked":
        raise ApplyPlanError("apply_plan.json must keep execution blocked.")

    if plan.get("git_operations") != "blocked":
        raise ApplyPlanError("apply_plan.json must keep version-control operations blocked.")

    if plan.get("adapter_execution") != "blocked":
        raise ApplyPlanError("apply_plan.json must keep adapter execution blocked.")

    if plan.get("private_context_access") != "blocked":
        raise ApplyPlanError("apply_plan.json must keep private context access blocked.")

    if plan.get("network_access") != "blocked":
        raise ApplyPlanError("apply_plan.json must keep network access blocked.")

    changes = plan.get("planned_changes")
    if not isinstance(changes, list) or not changes:
        raise ApplyPlanError("apply_plan.json must contain at least one planned change.")


def validate_change(change: dict[str, Any]) -> None:
    if not isinstance(change, dict):
        raise ApplyPlanError("Each planned change must be a JSON object.")

    if change.get("operation") != "propose_file":
        raise ApplyPlanError("Only propose_file planned changes are supported.")

    if change.get("requires_human_approval") is not True:
        raise ApplyPlanError("Each planned change must require human approval.")

    if change.get("apply_status") not in {"not_applied", "blocked"}:
        raise ApplyPlanError("Only not_applied or blocked planned changes can be previewed or applied.")

    sandbox_artifact_path = normalize_relative_path(
        change.get("sandbox_artifact_path", ""), label="sandbox_artifact_path"
    )
    if not sandbox_artifact_path.startswith("proposed_outputs/"):
        raise ApplyPlanError("sandbox_artifact_path must start with proposed_outputs/.")

    intended_repo_path = normalize_relative_path(
        change.get("intended_repo_path", ""), label="intended_repo_path"
    )
    validate_destination_path(intended_repo_path)


def build_change_result(
    *,
    change: dict[str, Any],
    proposed_outputs: Path,
    repo_root: Path,
    confirm_apply: bool,
    allow_overwrite: bool,
) -> dict[str, Any]:
    validate_change(change)

    sandbox_artifact_rel = normalize_relative_path(
        change["sandbox_artifact_path"], label="sandbox_artifact_path"
    )
    artifact_rel_under_outputs = sandbox_artifact_rel.removeprefix("proposed_outputs/")
    intended_repo_path = normalize_relative_path(change["intended_repo_path"], label="intended_repo_path")

    source_path = (proposed_outputs / artifact_rel_under_outputs).resolve()
    destination_path = (repo_root / intended_repo_path).resolve()

    ensure_under(proposed_outputs, source_path, "source artifact")
    ensure_under(repo_root, destination_path, "destination path")

    if not source_path.exists() or not source_path.is_file():
        raise ApplyPlanError(f"Source artifact is missing or is not a file: {source_path}")

    if destination_path.exists() and not allow_overwrite:
        raise ApplyPlanError(
            f"Destination already exists and overwrite is not allowed: {destination_path}"
        )

    checksum = sha256_file(source_path)
    status = "would_apply"
    if confirm_apply:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        destination_path.write_bytes(source_path.read_bytes())
        status = "applied"

    return {
        "change_id": change.get("change_id", "UNASSIGNED"),
        "operation": "copy_proposed_file",
        "source_sandbox_artifact_path": sandbox_artifact_rel,
        "destination_repo_path": intended_repo_path,
        "status": status,
        "artifact_kind": change.get("artifact_kind", "UNASSIGNED"),
        "source_sha256": checksum,
        "destination_existed_before": destination_path.exists() and status == "would_apply",
        "overwrite_allowed": allow_overwrite,
        "requires_human_approval": True,
    }


def build_report(
    *,
    run_id: str,
    plan: dict[str, Any],
    repo_root: Path,
    sandbox_root: Path,
    confirm_apply: bool,
    allow_overwrite: bool,
    approval_token_provided: bool,
    applied_changes: list[dict[str, Any]],
) -> dict[str, Any]:
    status = "applied" if confirm_apply else "preview"
    return {
        "$schema": "../../schemas/runtime/human_approved_apply_report.schema.json",
        "schema_version": "0.1",
        "run_id": run_id,
        "plan_id": plan.get("plan_id", "UNASSIGNED"),
        "mode": "human_approved_apply_plan",
        "status": status,
        "created_at": utc_now(),
        "repo_root": str(repo_root),
        "sandbox_root": str(sandbox_root),
        "confirm_apply": confirm_apply,
        "approval_token_provided": approval_token_provided,
        "allow_overwrite": allow_overwrite,
        "execution": "blocked",
        "filesystem_mutation": "repo_allowlist_only" if confirm_apply else "preview_only",
        "repository_apply": "applied" if confirm_apply else "preview_only",
        "git_operations": "blocked",
        "adapter_execution": "blocked",
        "private_context_access": "blocked",
        "network_access": "blocked",
        "applied_changes": applied_changes,
        "notes": [
            "This report records a human-approved apply plan preview or apply operation.",
            "It does not authorize mission execution or repository version-control operations.",
        ],
    }


def apply_sandbox_plan(
    *,
    sandbox_root: str,
    run_id: str,
    repo_root: str,
    confirm_apply: bool,
    approval_token: str,
    allow_overwrite: bool,
    write_report: bool,
) -> dict[str, Any]:
    if confirm_apply and approval_token != APPROVAL_TOKEN:
        raise ApplyPlanError(
            f"Applying requires --approval-token {APPROVAL_TOKEN!r}. "
            "Run without --confirm-apply to preview only."
        )

    if allow_overwrite and not confirm_apply:
        raise ApplyPlanError("--allow-overwrite is only valid with --confirm-apply.")

    paths = resolve_paths(sandbox_root, repo_root, run_id)

    if not paths["run_dir"].exists():
        raise ApplyPlanError(f"Run directory does not exist: {paths['run_dir']}")

    plan = load_json_object(paths["apply_plan_path"], "apply_plan.json")
    validate_plan_boundaries(plan, run_id)

    changes = plan["planned_changes"]
    applied_changes = [
        build_change_result(
            change=change,
            proposed_outputs=paths["proposed_outputs"],
            repo_root=paths["repo_root"],
            confirm_apply=confirm_apply,
            allow_overwrite=allow_overwrite,
        )
        for change in changes
    ]

    report = build_report(
        run_id=run_id,
        plan=plan,
        repo_root=paths["repo_root"],
        sandbox_root=paths["sandbox_root"],
        confirm_apply=confirm_apply,
        allow_overwrite=allow_overwrite,
        approval_token_provided=bool(approval_token),
        applied_changes=applied_changes,
    )

    if write_report:
        paths["report_path"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    return {
        "report": report,
        "report_path": paths["report_path"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or apply a Konoha sandbox apply plan with explicit human approval."
    )
    parser.add_argument("--sandbox-root", required=True, help="Sandbox root path.")
    parser.add_argument("--run-id", required=True, help="Existing sandbox run id.")
    parser.add_argument("--repo-root", default=".", help="Repository root path.")
    parser.add_argument(
        "--confirm-apply",
        action="store_true",
        help="Actually copy proposed files to allowlisted repository paths.",
    )
    parser.add_argument(
        "--approval-token",
        default="",
        help=f"Required for --confirm-apply. Exact value: {APPROVAL_TOKEN}",
    )
    parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="Allow overwriting existing destination files. Requires --confirm-apply.",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Do not write human_approved_apply_report.json inside the sandbox run.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report to stdout.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = apply_sandbox_plan(
            sandbox_root=args.sandbox_root,
            run_id=args.run_id,
            repo_root=args.repo_root,
            confirm_apply=args.confirm_apply,
            approval_token=args.approval_token,
            allow_overwrite=args.allow_overwrite,
            write_report=not args.no_report,
        )
    except ApplyPlanError as exc:
        return fail(str(exc))

    report = result["report"]
    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    if args.confirm_apply:
        print("SANDBOX APPLY PLAN APPLIED")
    else:
        print("SANDBOX APPLY PLAN PREVIEW")
    print(f"Run ID: {args.run_id}")
    print(f"Status: {report['status']}")
    print(f"Changes: {len(report['applied_changes'])}")
    print(f"Report: {result['report_path']}")
    print("Execution: blocked")
    print(f"Filesystem mutation: {report['filesystem_mutation']}")
    print(f"Repository apply: {report['repository_apply']}")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Adapter execution: blocked")
    print("Network access: blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
