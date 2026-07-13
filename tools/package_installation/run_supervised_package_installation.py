#!/usr/bin/env python3
"""Supervised package installation scope guard for Konoha.

The guard separates package files written directly by ZIP extraction from
public index files changed by an idempotent helper. It validates the exact
union before and after helper execution.

It does not stage, commit, push, create tags, access network, invoke models,
or read private context.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

SCHEMA_VERSION = "1.0.0"
MANIFEST_REPORT_TYPE = "supervised_package_installation_manifest"
REPORT_TYPE = "supervised_package_installation_report"
INSTALL_TOKEN = "APPLY_SUPERVISED_PACKAGE_INSTALLATION"

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")
TOKEN_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")

PRIVATE_PREFIXES = (
    ".env",
    "alliance/kirigakure",
    "memory/local",
    "vault",
    "sandbox",
)

BOUNDARIES = {
    "git_stage": "blocked",
    "git_commit": "blocked",
    "git_push": "blocked",
    "tag_mutation": "blocked",
    "release_mutation": "blocked",
    "network_access": "blocked",
    "model_invocation": "blocked",
    "private_context_access": "blocked",
    "arbitrary_shell": "blocked",
    "helper_execution": "explicit_install_token_only",
    "report_output": "sandbox_only",
}


class InstallationError(RuntimeError):
    """Invalid manifest, unsafe scope, or failed bounded helper."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def normalize_relative_path(raw: Any) -> Optional[str]:
    if not isinstance(raw, str):
        return None

    value = raw.strip().replace("\\", "/")
    if not value or value.startswith("/") or re.match(r"^[A-Za-z]:/", value):
        return None

    while value.startswith("./"):
        value = value[2:]

    if value == ".":
        return "."

    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None

    return value


def is_private_path(relative: str) -> bool:
    lowered = relative.lower()
    parts = lowered.split("/")

    if lowered == ".env" or lowered.startswith(".env."):
        return True

    for prefix in PRIVATE_PREFIXES:
        normalized = prefix.lower()
        if lowered == normalized or lowered.startswith(normalized + "/"):
            return True

    if len(parts) >= 3 and parts[0] == "alliance":
        if parts[2] in {"private-library", "memory"}:
            return True

    return False


def read_json_object(path: Path, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InstallationError(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise InstallationError(
            f"{label} JSON invalid at line {exc.lineno}, column {exc.colno}"
        ) from exc

    if not isinstance(payload, dict):
        raise InstallationError(f"{label} JSON must be an object")

    return payload


def resolve_output(repo_root: Path, raw: str) -> Path:
    sandbox_root = (repo_root / "sandbox").resolve()
    output = Path(raw)
    if not output.is_absolute():
        output = repo_root / output
    output = output.resolve()

    if not is_relative_to(output, sandbox_root):
        raise InstallationError(
            "installation output must stay under <repo-root>/sandbox"
        )

    return output


def write_json(path: Path, payload: Mapping[str, Any], force: bool) -> None:
    if path.exists() and not force:
        raise InstallationError(f"output exists; use --force: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def git_read(repo_root: Path, *args: str, timeout: int = 120) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            text=True,
            capture_output=True,
            shell=False,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise InstallationError(
            f"git {' '.join(args)} timed out"
        ) from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise InstallationError(
            f"git {' '.join(args)} failed: {detail or 'no output'}"
        )

    return completed.stdout.strip()


def normalize_manifest_paths(
    value: Any,
    field: str,
    *,
    allow_sandbox: bool = False,
) -> List[str]:
    if not isinstance(value, list) or not value:
        raise InstallationError(f"{field} must be a non-empty list")

    result: List[str] = []
    for index, raw in enumerate(value):
        normalized = normalize_relative_path(raw)
        if normalized is None or normalized == ".":
            raise InstallationError(f"{field}[{index}] is invalid")

        if is_private_path(normalized) and not (
            allow_sandbox and normalized.startswith("sandbox/")
        ):
            raise InstallationError(
                f"{field}[{index}] points to blocked context: {normalized}"
            )

        result.append(normalized)

    if len(result) != len(set(result)):
        raise InstallationError(f"{field} contains duplicate paths")

    return sorted(result)


def validate_manifest(payload: Mapping[str, Any]) -> Dict[str, Any]:
    required = {
        "schema_version",
        "report_type",
        "installation_id",
        "expected_base_commit",
        "expected_branch",
        "tracking_ref",
        "direct_repo_paths",
        "helper_modified_paths",
        "expected_public_paths",
        "helper_path",
        "helper_approval_token",
        "authority",
    }

    missing = sorted(required - set(payload))
    if missing:
        raise InstallationError(
            "manifest missing fields: " + ", ".join(missing)
        )

    if payload.get("schema_version") != SCHEMA_VERSION:
        raise InstallationError(
            f"manifest schema_version must be {SCHEMA_VERSION}"
        )

    if payload.get("report_type") != MANIFEST_REPORT_TYPE:
        raise InstallationError(
            f"manifest report_type must be {MANIFEST_REPORT_TYPE}"
        )

    installation_id = payload.get("installation_id")
    if (
        not isinstance(installation_id, str)
        or not SAFE_ID_RE.fullmatch(installation_id)
    ):
        raise InstallationError("installation_id is invalid")

    base = payload.get("expected_base_commit")
    if not isinstance(base, str) or not COMMIT_RE.fullmatch(base):
        raise InstallationError(
            "expected_base_commit must be 40 lowercase hex characters"
        )

    for field in ("expected_branch", "tracking_ref"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise InstallationError(f"{field} must be non-empty text")

    direct = normalize_manifest_paths(
        payload.get("direct_repo_paths"),
        "direct_repo_paths",
    )
    helper_modified = normalize_manifest_paths(
        payload.get("helper_modified_paths"),
        "helper_modified_paths",
    )
    expected_public = normalize_manifest_paths(
        payload.get("expected_public_paths"),
        "expected_public_paths",
    )

    overlap = sorted(set(direct) & set(helper_modified))
    if overlap:
        raise InstallationError(
            "direct_repo_paths and helper_modified_paths overlap: "
            + ", ".join(overlap)
        )

    union = sorted(set(direct) | set(helper_modified))
    if union != expected_public:
        raise InstallationError(
            "expected_public_paths must equal the exact union of "
            "direct_repo_paths and helper_modified_paths"
        )

    helper_path = normalize_relative_path(payload.get("helper_path"))
    if (
        helper_path is None
        or helper_path == "."
        or not helper_path.startswith("sandbox/")
    ):
        raise InstallationError(
            "helper_path must be a repository-relative path under sandbox"
        )

    helper_token = payload.get("helper_approval_token")
    if (
        not isinstance(helper_token, str)
        or not TOKEN_RE.fullmatch(helper_token)
    ):
        raise InstallationError("helper_approval_token is invalid")

    authority = payload.get("authority")
    required_authority = {
        "manifest_is_not_permission": True,
        "install_token_required": True,
        "helper_is_bounded": True,
        "git_operations_blocked": True,
        "network_access_blocked": True,
        "private_context_blocked": True,
    }

    if not isinstance(authority, dict):
        raise InstallationError("manifest authority must be an object")

    for key, expected in required_authority.items():
        if authority.get(key) is not expected:
            raise InstallationError(
                f"manifest authority requires {key}=true"
            )

    result = dict(payload)
    result["direct_repo_paths"] = direct
    result["helper_modified_paths"] = helper_modified
    result["expected_public_paths"] = expected_public
    result["helper_path"] = helper_path
    return result


def collect_public_scope(repo_root: Path) -> List[str]:
    changed = git_read(repo_root, "diff", "--name-only")
    untracked = git_read(
        repo_root,
        "ls-files",
        "--others",
        "--exclude-standard",
    )

    return sorted(
        {
            line.strip()
            for line in (changed + "\n" + untracked).splitlines()
            if line.strip()
        }
    )


def collect_staged_scope(repo_root: Path) -> List[str]:
    staged = git_read(repo_root, "diff", "--cached", "--name-only")
    return sorted(line for line in staged.splitlines() if line)


def file_hashes(repo_root: Path, paths: Iterable[str]) -> Dict[str, str]:
    hashes: Dict[str, str] = {}

    for relative in paths:
        path = (repo_root / relative).resolve()
        if not is_relative_to(path, repo_root):
            raise InstallationError(
                f"public path escapes repository root: {relative}"
            )
        if not path.is_file():
            raise InstallationError(
                f"direct package file missing: {relative}"
            )
        hashes[relative] = sha256_file(path)

    return hashes


def determine_state(
    actual_scope: Sequence[str],
    direct_scope: Sequence[str],
    final_scope: Sequence[str],
) -> str:
    actual = list(actual_scope)
    if actual == list(direct_scope):
        return "READY_FOR_HELPER_APPLY"
    if actual == list(final_scope):
        return "INSTALLED"
    return "BLOCKED_SCOPE_MISMATCH"


def run_helper(
    repo_root: Path,
    helper_path: Path,
    helper_token: str,
    log_path: Path,
) -> Dict[str, Any]:
    command = [
        sys.executable,
        "-S",
        str(helper_path),
        "--repo-root",
        ".",
        "--apply",
        "--approval-token",
        helper_token,
    ]

    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            text=True,
            capture_output=True,
            shell=False,
            check=False,
            timeout=180,
        )
    except subprocess.TimeoutExpired as exc:
        raise InstallationError("bounded helper timed out") from exc

    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "COMMAND\n"
        + json.dumps(command)
        + "\n\nSTDOUT\n"
        + completed.stdout
        + "\n\nSTDERR\n"
        + completed.stderr
        + f"\n\nRETURN_CODE\n{completed.returncode}\n",
        encoding="utf-8",
        newline="\n",
    )

    if completed.returncode != 0:
        raise InstallationError(
            f"bounded helper failed with RC={completed.returncode}; "
            f"see {log_path}"
        )

    return {
        "command": command,
        "returncode": completed.returncode,
        "log_path": str(log_path),
    }


def inspect_or_install(
    repo_root: Path,
    manifest: Mapping[str, Any],
    *,
    apply: bool,
    approval_token: str,
) -> Dict[str, Any]:
    branch = git_read(repo_root, "branch", "--show-current")
    head = git_read(repo_root, "rev-parse", "HEAD")
    tracking_head = git_read(
        repo_root,
        "rev-parse",
        "--verify",
        manifest["tracking_ref"],
    )

    if branch != manifest["expected_branch"]:
        raise InstallationError(
            f"expected branch {manifest['expected_branch']}, found {branch}"
        )

    if head != manifest["expected_base_commit"]:
        raise InstallationError(
            f"expected HEAD {manifest['expected_base_commit']}, found {head}"
        )

    if tracking_head != manifest["expected_base_commit"]:
        raise InstallationError(
            "tracking reference does not match expected base commit"
        )

    behind_ahead = git_read(
        repo_root,
        "rev-list",
        "--left-right",
        "--count",
        f"{manifest['tracking_ref']}...HEAD",
    ).replace("\t", " ").split()

    if behind_ahead != ["0", "0"]:
        raise InstallationError(
            "base branch must be synchronized before package installation"
        )

    staged = collect_staged_scope(repo_root)
    if staged:
        raise InstallationError(
            "staged changes block package installation: "
            + ", ".join(staged)
        )

    actual_before = collect_public_scope(repo_root)
    private_actual = [
        path for path in actual_before if is_private_path(path)
    ]
    if private_actual:
        raise InstallationError(
            "actual scope contains blocked paths: "
            + ", ".join(private_actual)
        )

    state_before = determine_state(
        actual_before,
        manifest["direct_repo_paths"],
        manifest["expected_public_paths"],
    )

    if state_before == "BLOCKED_SCOPE_MISMATCH":
        expected_direct = set(manifest["direct_repo_paths"])
        expected_final = set(manifest["expected_public_paths"])
        actual_set = set(actual_before)
        raise InstallationError(
            "package scope mismatch; "
            f"unexpected={sorted(actual_set - expected_final)}, "
            f"missing_direct={sorted(expected_direct - actual_set)}"
        )

    direct_hashes_before = file_hashes(
        repo_root,
        manifest["direct_repo_paths"],
    )

    helper_result: Optional[Dict[str, Any]] = None

    if apply and state_before == "READY_FOR_HELPER_APPLY":
        if approval_token != INSTALL_TOKEN:
            raise InstallationError(
                f"--apply requires --approval-token {INSTALL_TOKEN}"
            )

        helper_path = (repo_root / manifest["helper_path"]).resolve()
        sandbox_root = (repo_root / "sandbox").resolve()
        if not is_relative_to(helper_path, sandbox_root):
            raise InstallationError("helper path escapes sandbox")
        if not helper_path.is_file():
            raise InstallationError(
                f"bounded helper not found: {manifest['helper_path']}"
            )

        helper_log = (
            repo_root
            / "sandbox"
            / "reports"
            / f"{manifest['installation_id']}-helper.log"
        )
        helper_result = run_helper(
            repo_root,
            helper_path,
            manifest["helper_approval_token"],
            helper_log,
        )

    actual_after = collect_public_scope(repo_root)
    state_after = determine_state(
        actual_after,
        manifest["direct_repo_paths"],
        manifest["expected_public_paths"],
    )

    if apply and state_after != "INSTALLED":
        raise InstallationError(
            "helper completed but final public scope is not exact"
        )

    direct_hashes_after = file_hashes(
        repo_root,
        manifest["direct_repo_paths"],
    )
    changed_direct = sorted(
        path
        for path, before_hash in direct_hashes_before.items()
        if direct_hashes_after.get(path) != before_hash
    )
    if changed_direct:
        raise InstallationError(
            "helper modified direct package paths: "
            + ", ".join(changed_direct)
        )

    staged_after = collect_staged_scope(repo_root)
    if staged_after:
        raise InstallationError(
            "helper created staged changes: " + ", ".join(staged_after)
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "generated_at": utc_now(),
        "installation_id": manifest["installation_id"],
        "status": "passed",
        "status_code": state_after,
        "installed": state_after == "INSTALLED",
        "apply_requested": apply,
        "head": head,
        "branch": branch,
        "tracking_ref": manifest["tracking_ref"],
        "scope": {
            "state_before": state_before,
            "state_after": state_after,
            "direct_repo_paths": manifest["direct_repo_paths"],
            "helper_modified_paths": manifest["helper_modified_paths"],
            "expected_public_paths": manifest["expected_public_paths"],
            "actual_before": actual_before,
            "actual_after": actual_after,
            "direct_hashes_preserved": True,
            "staged_paths": staged_after,
        },
        "helper": helper_result,
        "next_action": (
            "Run again with --apply and the explicit installation token."
            if state_after == "READY_FOR_HELPER_APPLY"
            else "Package installation scope is complete."
        ),
        "boundaries": BOUNDARIES,
        "authority": {
            "installation_report_is_evidence_only": True,
            "install_token_authorizes_only_bounded_helper": True,
            "git_delivery_requires_separate_workflow": True,
            "release_closure_requires_separate_workflow": True,
        },
    }


def print_minimal(report: Mapping[str, Any], output: Path) -> None:
    scope = report.get("scope") or {}
    print("KONOHA SUPERVISED PACKAGE INSTALLATION")
    print(f"installation_id: {report.get('installation_id')}")
    print(f"status_code: {report.get('status_code')}")
    print(f"installed: {report.get('installed')}")
    print(f"direct_paths: {len(scope.get('direct_repo_paths') or [])}")
    print(f"helper_paths: {len(scope.get('helper_modified_paths') or [])}")
    print(f"public_scope: {len(scope.get('actual_after') or [])}")
    print(f"direct_hashes_preserved: {scope.get('direct_hashes_preserved')}")
    print(f"report: {output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate or apply a bounded Konoha package helper."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--approval-token", default="")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        repo_root = Path(args.repo_root).resolve()

        manifest_path = Path(args.manifest)
        if not manifest_path.is_absolute():
            manifest_path = repo_root / manifest_path
        manifest_path = manifest_path.resolve()

        if not is_relative_to(manifest_path, repo_root):
            raise InstallationError(
                "manifest path must stay under repository root"
            )

        relative_manifest = manifest_path.relative_to(repo_root).as_posix()
        if is_private_path(relative_manifest):
            raise InstallationError(
                "manifest path points to blocked private context"
            )

        output = resolve_output(repo_root, args.output)
        manifest = validate_manifest(
            read_json_object(manifest_path, "installation manifest")
        )

        report = inspect_or_install(
            repo_root,
            manifest,
            apply=args.apply,
            approval_token=args.approval_token,
        )

        write_json(output, report, args.force)

        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_minimal(report, output)

        return 0

    except InstallationError as exc:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "report_type": REPORT_TYPE,
            "generated_at": utc_now(),
            "status": "blocked",
            "status_code": "BLOCKED_INSTALLATION",
            "installed": False,
            "blocker": str(exc),
            "boundaries": BOUNDARIES,
            "authority": {
                "blocked_report_is_evidence_only": True,
                "failure_does_not_authorize_fallback": True,
            },
        }

        try:
            repo_root = Path(args.repo_root).resolve()
            output = resolve_output(repo_root, args.output)
            write_json(output, payload, args.force)
        except InstallationError:
            output = None

        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("KONOHA PACKAGE INSTALLATION BLOCKED", file=sys.stderr)
            print(f"blocker: {exc}", file=sys.stderr)
            if output is not None:
                print(f"report: {output}", file=sys.stderr)

        return 1

    except (OSError, ValueError) as exc:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "report_type": REPORT_TYPE,
            "generated_at": utc_now(),
            "status": "failed",
            "status_code": "BLOCKED_CONFIGURATION",
            "installed": False,
            "blocker": str(exc),
            "boundaries": BOUNDARIES,
        }

        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("KONOHA PACKAGE CONFIGURATION BLOCKED", file=sys.stderr)
            print(f"blocker: {exc}", file=sys.stderr)

        return 2


if __name__ == "__main__":
    raise SystemExit(main())
