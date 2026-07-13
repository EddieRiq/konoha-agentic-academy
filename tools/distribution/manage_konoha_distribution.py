#!/usr/bin/env python3
"""Manage a verified local Konoha terminal installation.

The installer creates a managed state record outside the repository. This tool
uses that state to inspect, upgrade, or uninstall only the exact installation
that Konoha created. It never guesses an install root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

REPO_SLUG = "EddieRiq/konoha-agentic-academy"
REPO_HTTPS = "https://github.com/EddieRiq/konoha-agentic-academy.git"
STATE_REPORT_TYPE = "managed_konoha_install_state"
STATUS_REPORT_TYPE = "managed_konoha_install_status"
SCHEMA_VERSION = "1.0.0"

UPGRADE_TOKEN = "UPGRADE_KONOHA_INSTALL"
UNINSTALL_TOKEN = "UNINSTALL_KONOHA_CLI"

VERSION_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
MARKER_NAME = ".konoha-managed-install.json"

BOUNDARIES = {
    "arbitrary_shell": "blocked",
    "force_checkout": "blocked",
    "force_reset": "blocked",
    "branch_mutation": "blocked",
    "network_access": "explicit_upgrade_only",
    "uninstall": "recoverable_move_only",
    "private_context_access": "blocked",
    "state_is_authority": False,
}


class DistributionError(RuntimeError):
    """Unsafe, unmanaged, or inconsistent installation."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_state_file() -> Path:
    base = Path(
        os.environ.get(
            "XDG_STATE_HOME",
            str(Path.home() / ".local" / "state"),
        )
    )
    return base / "konoha" / "install.json"


def parse_version(value: str) -> Tuple[int, int, int]:
    match = VERSION_RE.fullmatch(value)
    if match is None:
        raise DistributionError(
            "version must use exact vMAJOR.MINOR.PATCH format"
        )
    return tuple(int(part) for part in match.groups())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json_object(path: Path, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DistributionError(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DistributionError(
            f"{label} JSON invalid at line {exc.lineno}, column {exc.colno}"
        ) from exc

    if not isinstance(payload, dict):
        raise DistributionError(f"{label} JSON must be an object")
    return payload


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp-{uuid.uuid4().hex}")
    temp.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temp, path)


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def ensure_user_managed_path(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    home = Path.home().resolve()

    if resolved == home or not is_relative_to(resolved, home):
        raise DistributionError(
            f"{label} must be a child of the current user home"
        )
    if len(resolved.parts) <= len(home.parts) + 1:
        raise DistributionError(f"{label} is too broad to manage safely")
    return resolved


def normalize_origin(value: str) -> str:
    normalized = value.strip().rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    if normalized.startswith("git@github.com:"):
        normalized = (
            "https://github.com/"
            + normalized[len("git@github.com:") :]
        )
    return normalized


def run(
    command: Sequence[str],
    cwd: Path,
    *,
    timeout: int = 180,
    expected: Sequence[int] = (0,),
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            text=True,
            capture_output=True,
            shell=False,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise DistributionError(
            f"command timed out: {list(command)!r}"
        ) from exc

    if completed.returncode not in expected:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise DistributionError(
            f"command failed RC={completed.returncode}: "
            f"{list(command)!r}: {detail or 'no output'}"
        )
    return completed


def git_stdout(root: Path, *args: str) -> str:
    return run(["git", *args], root).stdout.strip()


def validate_state(payload: Mapping[str, Any]) -> Dict[str, Any]:
    required = {
        "schema_version",
        "report_type",
        "managed",
        "repository",
        "version",
        "commit",
        "install_root",
        "venv_root",
        "bin_path",
        "state_file",
        "marker_id",
        "wrapper_sha256",
        "installed_at",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise DistributionError(
            "managed install state missing: " + ", ".join(missing)
        )

    if payload.get("schema_version") != SCHEMA_VERSION:
        raise DistributionError("unsupported managed state schema")
    if payload.get("report_type") != STATE_REPORT_TYPE:
        raise DistributionError("managed state report_type mismatch")
    if payload.get("managed") is not True:
        raise DistributionError("installation is not marked managed")
    if payload.get("repository") != REPO_SLUG:
        raise DistributionError("managed repository mismatch")

    parse_version(str(payload.get("version")))

    commit = payload.get("commit")
    if (
        not isinstance(commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", commit) is None
    ):
        raise DistributionError("managed commit must be 40 lowercase hex")

    marker_id = payload.get("marker_id")
    if (
        not isinstance(marker_id, str)
        or re.fullmatch(r"[0-9a-f]{32}", marker_id) is None
    ):
        raise DistributionError("managed marker_id is invalid")

    wrapper_sha256 = payload.get("wrapper_sha256")
    if (
        not isinstance(wrapper_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", wrapper_sha256) is None
    ):
        raise DistributionError("managed wrapper_sha256 is invalid")

    result = dict(payload)
    result["install_root"] = str(
        ensure_user_managed_path(
            Path(str(payload["install_root"])),
            "install_root",
        )
    )
    result["venv_root"] = str(
        ensure_user_managed_path(
            Path(str(payload["venv_root"])),
            "venv_root",
        )
    )
    result["bin_path"] = str(
        ensure_user_managed_path(
            Path(str(payload["bin_path"])),
            "bin_path",
        )
    )
    result["state_file"] = str(
        ensure_user_managed_path(
            Path(str(payload["state_file"])),
            "state_file",
        )
    )
    return result


def load_managed_state(state_file: Path) -> Dict[str, Any]:
    resolved_state = ensure_user_managed_path(
        state_file,
        "state_file",
    )
    state = validate_state(
        read_json_object(resolved_state, "managed install state")
    )

    if Path(state["state_file"]).resolve() != resolved_state:
        raise DistributionError(
            "managed state_file does not match requested state"
        )

    root = Path(state["install_root"]).resolve()
    marker_path = root / MARKER_NAME
    marker = read_json_object(marker_path, "managed install marker")

    if marker.get("marker_id") != state["marker_id"]:
        raise DistributionError("managed marker identity mismatch")
    if marker.get("repository") != REPO_SLUG:
        raise DistributionError("managed marker repository mismatch")
    if marker.get("wrapper_sha256") != state["wrapper_sha256"]:
        raise DistributionError("managed marker wrapper hash mismatch")
    if Path(str(marker.get("install_root"))).resolve() != root:
        raise DistributionError("managed marker root mismatch")

    return state


def inspect_state(state: Mapping[str, Any]) -> Dict[str, Any]:
    root = Path(state["install_root"]).resolve()
    venv = Path(state["venv_root"]).resolve()
    binary = Path(state["bin_path"]).resolve(strict=False)

    checks: Dict[str, bool] = {
        "install_root_exists": root.is_dir(),
        "git_repo_exists": (root / ".git").is_dir(),
        "cli_exists": (root / "tools" / "konoha_cli.py").is_file(),
        "version_module_exists": (
            root / "tools" / "version.py"
        ).is_file(),
        "venv_python_exists": (
            venv / "bin" / "python"
        ).is_file(),
        "binary_exists": Path(state["bin_path"]).is_file(),
        "wrapper_hash_matches": False,
    }

    actual: Dict[str, Any] = {
        "head": None,
        "tag": None,
        "origin": None,
        "working_tree_clean": False,
        "binary_target": None,
    }

    if checks["git_repo_exists"]:
        try:
            actual["head"] = git_stdout(root, "rev-parse", "HEAD")
            actual["tag"] = git_stdout(
                root,
                "describe",
                "--tags",
                "--exact-match",
                "HEAD",
            )
            actual["origin"] = git_stdout(
                root,
                "remote",
                "get-url",
                "origin",
            )
            actual["working_tree_clean"] = (
                git_stdout(root, "status", "--porcelain=v1") == ""
            )
        except DistributionError:
            pass

    bin_path = Path(state["bin_path"])
    configured_bin = Path(state["bin_path"])
    if configured_bin.is_symlink():
        try:
            actual["binary_target"] = str(
                configured_bin.resolve()
            )
        except OSError:
            actual["binary_target"] = None
    elif configured_bin.is_file():
        actual["binary_target"] = str(
            configured_bin.resolve()
        )

    if configured_bin.is_file():
        checks["wrapper_hash_matches"] = (
            sha256_file(configured_bin)
            == state["wrapper_sha256"]
        )

    checks["head_matches_state"] = (
        actual["head"] == state["commit"]
    )
    checks["tag_matches_state"] = (
        actual["tag"] == state["version"]
    )
    checks["origin_matches"] = (
        normalize_origin(str(actual["origin"] or ""))
        == normalize_origin(REPO_HTTPS)
    )
    checks["working_tree_clean"] = (
        actual["working_tree_clean"] is True
    )

    healthy = bool(checks) and all(checks.values())
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": STATUS_REPORT_TYPE,
        "generated_at": utc_now(),
        "status": "healthy" if healthy else "degraded",
        "status_code": (
            "MANAGED_INSTALL_HEALTHY"
            if healthy
            else "MANAGED_INSTALL_DEGRADED"
        ),
        "healthy": healthy,
        "state": dict(state),
        "checks": checks,
        "actual": actual,
        "boundaries": BOUNDARIES,
        "authority": {
            "status_is_evidence_only": True,
            "status_does_not_authorize_upgrade": True,
            "status_does_not_authorize_uninstall": True,
        },
    }


def require_healthy_for_mutation(state: Mapping[str, Any]) -> Dict[str, Any]:
    report = inspect_state(state)
    if report["healthy"] is not True:
        failed = sorted(
            key
            for key, passed in report["checks"].items()
            if passed is not True
        )
        raise DistributionError(
            "managed installation is not healthy: "
            + ", ".join(failed)
        )
    return report


def perform_upgrade(
    state_file: Path,
    state: Mapping[str, Any],
    *,
    target_version: str,
    allow_network: bool,
    confirm_upgrade: bool,
    approval_token: str,
) -> Dict[str, Any]:
    current = parse_version(str(state["version"]))
    target = parse_version(target_version)

    if target <= current:
        raise DistributionError(
            "target version must be newer than installed version"
        )
    if not allow_network:
        raise DistributionError("upgrade requires --allow-network")
    if not confirm_upgrade:
        raise DistributionError("upgrade requires --confirm-upgrade")
    if approval_token != UPGRADE_TOKEN:
        raise DistributionError(
            f"upgrade requires --approval-token {UPGRADE_TOKEN}"
        )

    before = require_healthy_for_mutation(state)
    root = Path(state["install_root"]).resolve()
    previous_commit = str(state["commit"])
    previous_version = str(state["version"])

    run(
        [
            "git",
            "fetch",
            "--quiet",
            "--tags",
            "origin",
            f"refs/tags/{target_version}:refs/tags/{target_version}",
        ],
        root,
        timeout=300,
    )
    target_commit = git_stdout(
        root,
        "rev-parse",
        f"refs/tags/{target_version}^{{}}",
    )

    checkout_completed = False
    try:
        run(
            ["git", "checkout", "--detach", target_version],
            root,
            timeout=180,
        )
        checkout_completed = True

        observed = git_stdout(root, "rev-parse", "HEAD")
        observed_tag = git_stdout(
            root,
            "describe",
            "--tags",
            "--exact-match",
            "HEAD",
        )
        if observed != target_commit or observed_tag != target_version:
            raise DistributionError(
                "upgraded checkout does not match target tag"
            )

        new_state = dict(state)
        new_state.update(
            {
                "version": target_version,
                "commit": target_commit,
                "updated_at": utc_now(),
                "previous_version": previous_version,
                "previous_commit": previous_commit,
            }
        )
        write_json(state_file, new_state)

        marker_path = root / MARKER_NAME
        marker = read_json_object(
            marker_path,
            "managed install marker",
        )
        marker.update(
            {
                "version": target_version,
                "commit": target_commit,
                "updated_at": utc_now(),
            }
        )
        write_json(marker_path, marker)

        after = inspect_state(new_state)
        if after["healthy"] is not True:
            raise DistributionError(
                "post-upgrade installation is not healthy"
            )

        return {
            "schema_version": SCHEMA_VERSION,
            "report_type": "managed_konoha_upgrade_report",
            "generated_at": utc_now(),
            "status": "passed",
            "status_code": "MANAGED_INSTALL_UPGRADED",
            "from_version": previous_version,
            "to_version": target_version,
            "from_commit": previous_commit,
            "to_commit": target_commit,
            "before": before,
            "after": after,
            "boundaries": BOUNDARIES,
            "authority": {
                "explicit_upgrade_token_was_required": True,
                "network_was_explicitly_enabled": True,
                "force_operations_were_blocked": True,
            },
        }

    except Exception:
        if checkout_completed:
            try:
                run(
                    ["git", "checkout", "--detach", previous_commit],
                    root,
                    timeout=180,
                )
                write_json(state_file, dict(state))
                marker_path = root / MARKER_NAME
                marker = read_json_object(
                    marker_path,
                    "managed install marker",
                )
                marker.update(
                    {
                        "version": previous_version,
                        "commit": previous_commit,
                        "updated_at": utc_now(),
                    }
                )
                write_json(marker_path, marker)
            except Exception as rollback_exc:
                raise DistributionError(
                    "upgrade failed and rollback also failed: "
                    f"{rollback_exc}"
                ) from rollback_exc
        raise


def perform_uninstall(
    state_file: Path,
    state: Mapping[str, Any],
    *,
    confirm_uninstall: bool,
    approval_token: str,
) -> Dict[str, Any]:
    if not confirm_uninstall:
        raise DistributionError(
            "uninstall requires --confirm-uninstall"
        )
    if approval_token != UNINSTALL_TOKEN:
        raise DistributionError(
            f"uninstall requires --approval-token {UNINSTALL_TOKEN}"
        )

    before = require_healthy_for_mutation(state)
    root = Path(state["install_root"]).resolve()
    bin_path = Path(state["bin_path"]).resolve(strict=False)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    trash = root.with_name(
        root.name + f".uninstalled-{timestamp}"
    )
    if trash.exists():
        raise DistributionError(
            f"recoverable uninstall target exists: {trash}"
        )

    configured_bin = Path(state["bin_path"])
    if configured_bin.is_symlink() or configured_bin.is_file():
        configured_bin.unlink()

    root.rename(trash)

    archived_state = state_file.with_name(
        f"install.uninstalled-{timestamp}.json"
    )
    archived_payload = dict(state)
    archived_payload.update(
        {
            "managed": False,
            "uninstalled_at": utc_now(),
            "recoverable_root": str(trash),
            "previous_bin_path": str(bin_path),
        }
    )
    write_json(archived_state, archived_payload)
    state_file.unlink()

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "managed_konoha_uninstall_report",
        "generated_at": utc_now(),
        "status": "passed",
        "status_code": "MANAGED_INSTALL_MOVED_TO_TRASH",
        "recoverable_root": str(trash),
        "archived_state": str(archived_state),
        "before": before,
        "boundaries": BOUNDARIES,
        "authority": {
            "explicit_uninstall_token_was_required": True,
            "source_was_moved_not_deleted": True,
            "network_access_was_blocked": True,
        },
    }


def print_minimal(report: Mapping[str, Any]) -> None:
    print("KONOHA MANAGED DISTRIBUTION")
    print(f"status_code: {report.get('status_code')}")
    if "healthy" in report:
        print(f"healthy: {report.get('healthy')}")
        state = report.get("state") or {}
        print(f"version: {state.get('version')}")
        print(f"install_root: {state.get('install_root')}")
    if "to_version" in report:
        print(f"upgraded_to: {report.get('to_version')}")
    if "recoverable_root" in report:
        print(
            f"recoverable_root: {report.get('recoverable_root')}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage a verified Konoha terminal installation."
    )
    parser.add_argument(
        "--state-file",
        default=str(default_state_file()),
    )
    parser.add_argument("--json", action="store_true")

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser("status")

    upgrade = subparsers.add_parser("upgrade")
    upgrade.add_argument("--target-version", required=True)
    upgrade.add_argument("--allow-network", action="store_true")
    upgrade.add_argument("--confirm-upgrade", action="store_true")
    upgrade.add_argument("--approval-token", default="")

    uninstall = subparsers.add_parser("uninstall")
    uninstall.add_argument(
        "--confirm-uninstall",
        action="store_true",
    )
    uninstall.add_argument("--approval-token", default="")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    state_file = Path(args.state_file).expanduser().resolve()

    try:
        state = load_managed_state(state_file)

        if args.command == "status":
            report = inspect_state(state)
            rc = 0 if report["healthy"] else 1
        elif args.command == "upgrade":
            report = perform_upgrade(
                state_file,
                state,
                target_version=args.target_version,
                allow_network=args.allow_network,
                confirm_upgrade=args.confirm_upgrade,
                approval_token=args.approval_token,
            )
            rc = 0
        elif args.command == "uninstall":
            report = perform_uninstall(
                state_file,
                state,
                confirm_uninstall=args.confirm_uninstall,
                approval_token=args.approval_token,
            )
            rc = 0
        else:
            raise DistributionError(
                f"unsupported command: {args.command}"
            )

        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_minimal(report)
        return rc

    except DistributionError as exc:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "report_type": STATUS_REPORT_TYPE,
            "generated_at": utc_now(),
            "status": "blocked",
            "status_code": "BLOCKED_MANAGED_DISTRIBUTION",
            "blocker": str(exc),
            "boundaries": BOUNDARIES,
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("KONOHA MANAGED DISTRIBUTION BLOCKED", file=sys.stderr)
            print(f"blocker: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
