#!/usr/bin/env python3
"""Read-only validator for Konoha project configuration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any

EXPECTED_APPLY_TOKEN = "APPLY_SANDBOX_PLAN"
EXPECTED_STAGE_TOKEN = "STAGE_ALLOWLISTED_FILES"

REQUIRED_TOP_LEVEL = {
    "config_type",
    "schema_version",
    "project",
    "sandbox",
    "paths",
    "safety",
    "approvals",
    "tools",
}

REQUIRED_SAFETY_FLAGS = {
    "execution_blocked": True,
    "filesystem_mutation_default": "blocked",
    "sandbox_writes_allowed": True,
    "repository_apply_requires_approval": True,
    "git_staging_requires_approval": True,
    "git_commit_blocked": True,
    "git_push_blocked": True,
    "adapter_execution_blocked": True,
    "private_context_access_blocked": True,
    "network_access_blocked": True,
}

PRIVATE_PATH_MARKERS = (
    "alliance/kirigakure",
    "private-library",
    "/vault",
    "/memory/local",
    ".env",
    "secrets",
    "credentials",
)


def as_posix(value: str) -> str:
    return value.replace("\\", "/").strip("/")


def is_safe_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    raw = value.replace("\\", "/")
    path = PurePosixPath(raw)
    if raw.startswith("/") or Path(raw).is_absolute():
        return False
    if any(part in ("..", "") for part in path.parts):
        return False
    if ":" in raw:
        return False
    return True


def path_has_private_marker(value: str) -> bool:
    normalized = as_posix(value).lower()
    return any(marker.lower() in normalized for marker in PRIVATE_PATH_MARKERS)


def validate_config(config: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    missing = sorted(REQUIRED_TOP_LEVEL - set(config))
    if missing:
        errors.append(f"missing top-level fields: {', '.join(missing)}")

    if config.get("config_type") != "konoha_project_config":
        errors.append("config_type must be 'konoha_project_config'")

    if not isinstance(config.get("schema_version"), str) or not config.get("schema_version"):
        errors.append("schema_version must be a non-empty string")

    project = config.get("project", {})
    if not isinstance(project, dict):
        errors.append("project must be an object")
    else:
        if not project.get("name"):
            errors.append("project.name is required")
        if project.get("mode") != "local_first":
            errors.append("project.mode must be 'local_first'")

    sandbox = config.get("sandbox", {})
    if not isinstance(sandbox, dict):
        errors.append("sandbox must be an object")
    else:
        for key in ("root", "runs_dir", "tmp_dir", "reports_dir"):
            if not is_safe_relative_path(sandbox.get(key)):
                errors.append(f"sandbox.{key} must be a safe repo-relative path")
        root = as_posix(str(sandbox.get("root", "")))
        for key in ("runs_dir", "tmp_dir", "reports_dir"):
            value = as_posix(str(sandbox.get(key, "")))
            if root and value and not (value == root or value.startswith(root + "/")):
                errors.append(f"sandbox.{key} must be inside sandbox.root")

    paths = config.get("paths", {})
    if not isinstance(paths, dict):
        errors.append("paths must be an object")
    else:
        for key in ("allowed_apply_destinations", "allowed_staging_paths", "blocked_private_paths"):
            values = paths.get(key)
            if not isinstance(values, list) or not values:
                errors.append(f"paths.{key} must be a non-empty list")
                continue
            for value in values:
                if not is_safe_relative_path(value):
                    errors.append(f"paths.{key} contains unsafe path: {value!r}")
        for key in ("allowed_apply_destinations", "allowed_staging_paths"):
            values = paths.get(key, [])
            if isinstance(values, list):
                for value in values:
                    if isinstance(value, str) and path_has_private_marker(value):
                        errors.append(f"paths.{key} must not allow private path: {value!r}")
        blocked = paths.get("blocked_private_paths", [])
        if isinstance(blocked, list):
            blocked_text = "\n".join(str(item).lower() for item in blocked)
            if "alliance/kirigakure" not in blocked_text:
                warnings.append("blocked_private_paths does not explicitly include alliance/kirigakure")

    safety = config.get("safety", {})
    if not isinstance(safety, dict):
        errors.append("safety must be an object")
    else:
        for key, expected in REQUIRED_SAFETY_FLAGS.items():
            if safety.get(key) != expected:
                errors.append(f"safety.{key} must be {expected!r}")

    approvals = config.get("approvals", {})
    if not isinstance(approvals, dict):
        errors.append("approvals must be an object")
    else:
        if approvals.get("apply_plan_token") != EXPECTED_APPLY_TOKEN:
            errors.append("approvals.apply_plan_token must match the required explicit apply token")
        if approvals.get("git_staging_token") != EXPECTED_STAGE_TOKEN:
            errors.append("approvals.git_staging_token must match the required explicit staging token")

    tools = config.get("tools", {})
    if not isinstance(tools, dict) or not tools:
        errors.append("tools must be a non-empty object")
    else:
        for name, value in tools.items():
            if not isinstance(value, str) or not value:
                errors.append(f"tools.{name} must be a non-empty repo-relative path")
            elif not is_safe_relative_path(value):
                errors.append(f"tools.{name} contains unsafe path: {value!r}")
            elif path_has_private_marker(value):
                errors.append(f"tools.{name} must not reference private context: {value!r}")

    return errors, warnings


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("config root must be a JSON object")
    return data


def build_report(path: Path, config: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "report_type": "konoha_project_config_validation",
        "config_path": str(path),
        "schema_version": config.get("schema_version"),
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "warnings": warnings,
        "safety": {
            "execution": "blocked",
            "filesystem_mutation": "blocked_by_default",
            "sandbox_writes": "allowed_by_policy",
            "repository_apply": "approval_required",
            "git_staging": "approval_required",
            "git_commit": "blocked",
            "git_push": "blocked",
            "adapter_execution": "blocked",
            "private_context_access": "blocked",
            "network_access": "blocked",
        },
    }


def print_text_report(report: dict[str, Any]) -> None:
    print("CONFIG VALIDATION PASSED" if report["status"] == "passed" else "CONFIG VALIDATION FAILED")
    print("Execution: blocked")
    print("Filesystem mutation: blocked by default")
    print("Sandbox writes: allowed by policy")
    print("Repository apply: approval required")
    print("Git staging: approval required")
    print("Git commit: blocked")
    print("Git push: blocked")
    print("Private context access: blocked")
    print("Adapter execution: blocked")
    print("Network access: blocked")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}")
    for error in report["errors"]:
        print(f"ERROR: {error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Konoha project config file.")
    parser.add_argument("config_path", help="Path to konoha.config.json or konoha.config.example.json")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args(argv)

    config_path = Path(args.config_path)
    try:
        config = load_config(config_path)
        errors, warnings = validate_config(config)
        report = build_report(config_path, config, errors, warnings)
    except Exception as exc:
        report = {
            "report_type": "konoha_project_config_validation",
            "config_path": str(config_path),
            "status": "failed",
            "errors": [str(exc)],
            "warnings": [],
            "safety": {"execution": "blocked", "filesystem_mutation": "blocked_by_default", "private_context_access": "blocked"},
        }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
