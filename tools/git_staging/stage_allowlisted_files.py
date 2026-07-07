#!/usr/bin/env python3
"""
Git Staging Gate for Konoha Agentic Academy.

This CLI performs a tightly scoped Git write operation: staging allowlisted files.

Safety boundary:
- no commit;
- no push;
- no clean/reset;
- no shell=True;
- no adapters;
- no network;
- no private context access;
- no filesystem file edits.

The only confirmed write operation is `git add -- <allowlisted paths>`, and only
when `--confirm-stage` and the exact approval token are provided.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path, PurePosixPath
from typing import Iterable, List, Sequence

APPROVAL_TOKEN = "STAGE_ALLOWLISTED_FILES"

ALLOWED_PREFIXES = (
    "docs/",
    "scrolls/",
    "examples/",
    "runtime/templates/",
    "schemas/runtime/",
    "tools/",
    "tests/",
)

ALLOWED_ROOT_FILES = {
    "README.md",
    "CHANGELOG.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
}

BLOCKED_PREFIXES = (
    "alliance/kirigakure/",
    "alliance/",
    "vault/",
    "memory/local/",
    "assets/private/",
    "sandbox/runs/",
    "sandbox/tmp/",
    "secrets/",
    "credentials/",
    ".git/",
)

BLOCKED_FRAGMENTS = (
    "private-library",
    "private_context",
    "local_context",
    ".env",
)


class GateError(Exception):
    """Raised when the staging gate must block."""


@dataclass
class StagingReport:
    status: str
    mode: str
    repo_root: str
    requested_paths: List[str]
    staged_paths: List[str]
    blockers: List[str]
    approval_required: bool
    approval_received: bool
    execution: str = "blocked"
    filesystem_mutation: str = "blocked"
    git_operations: str = "staged_only"
    git_commit: str = "blocked"
    git_push: str = "blocked"
    private_context_access: str = "blocked"
    adapter_execution: str = "blocked"
    network_access: str = "blocked"


def run_git(repo_root: Path, args: Sequence[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run an allowlisted Git command without shell expansion."""
    allowed = {
        "rev-parse",
        "status",
        "diff",
        "ls-files",
        "check-ignore",
        "add",
    }
    if not args or args[0] not in allowed:
        raise GateError(f"Blocked non-allowlisted git command: {' '.join(args)}")

    if args[0] == "add":
        # The only allowed write command. Callers must gate it explicitly.
        disallowed_flags = {"-A", "--all", "-u", "--update", "."}
        if any(part in disallowed_flags for part in args[1:]):
            raise GateError("Blocked broad git add usage. Only explicit paths after -- are allowed.")
        if "--" not in args:
            raise GateError("Blocked git add without explicit -- path separator.")

    return subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def normalize_repo_path(raw_path: str) -> str:
    """Normalize user-provided paths to safe repo-relative POSIX paths."""
    cleaned = raw_path.strip().replace("\\", "/")
    if not cleaned:
        raise GateError("Empty path is not allowed.")

    pure = PurePosixPath(cleaned)
    if pure.is_absolute():
        raise GateError(f"Absolute path is not allowed: {raw_path}")

    parts = pure.parts
    if any(part in ("..", "") for part in parts):
        raise GateError(f"Path traversal is not allowed: {raw_path}")

    normalized = str(pure)
    if normalized == "." or normalized.startswith("./"):
        raise GateError(f"Ambiguous repo path is not allowed: {raw_path}")

    return normalized


def is_allowlisted(path: str) -> bool:
    if path in ALLOWED_ROOT_FILES:
        return True
    return any(path.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def is_blocked_private_or_local(path: str) -> bool:
    lower = path.lower()
    if any(lower.startswith(prefix.lower()) for prefix in BLOCKED_PREFIXES):
        return True
    return any(fragment.lower() in lower for fragment in BLOCKED_FRAGMENTS)


def validate_repo(repo_root: Path) -> Path:
    resolved = repo_root.resolve()
    if not resolved.exists():
        raise GateError(f"Repository root does not exist: {repo_root}")

    result = run_git(resolved, ["rev-parse", "--show-toplevel"], check=True)
    git_root = Path(result.stdout.strip()).resolve()
    if git_root != resolved:
        raise GateError(f"Repo root must be the Git top-level. Got {resolved}, expected {git_root}.")

    return resolved


def path_exists_in_repo(repo_root: Path, rel_path: str) -> bool:
    return (repo_root / rel_path).exists()


def path_is_ignored(repo_root: Path, rel_path: str) -> bool:
    result = run_git(repo_root, ["check-ignore", "-q", "--", rel_path], check=False)
    return result.returncode == 0


def validate_paths(repo_root: Path, raw_paths: Iterable[str]) -> List[str]:
    normalized_paths: List[str] = []
    seen = set()

    for raw in raw_paths:
        path = normalize_repo_path(raw)
        if path in seen:
            continue
        seen.add(path)

        if is_blocked_private_or_local(path):
            raise GateError(f"Path is private, local-only, or blocked: {path}")

        if not is_allowlisted(path):
            raise GateError(f"Path is not in the staging allowlist: {path}")

        if not path_exists_in_repo(repo_root, path):
            raise GateError(f"Path does not exist and will not be staged: {path}")

        if path_is_ignored(repo_root, path):
            raise GateError(f"Path is ignored and will not be staged: {path}")

        normalized_paths.append(path)

    if not normalized_paths:
        raise GateError("At least one path is required.")

    return normalized_paths


def load_paths_from_plan(plan_path: Path) -> List[str]:
    if not plan_path.exists():
        raise GateError(f"Stage plan does not exist: {plan_path}")

    data = json.loads(plan_path.read_text(encoding="utf-8"))

    if isinstance(data, dict):
        if "paths" in data and isinstance(data["paths"], list):
            return [str(item) for item in data["paths"]]
        if "staging_paths" in data and isinstance(data["staging_paths"], list):
            return [str(item) for item in data["staging_paths"]]

    raise GateError("Stage plan must contain a `paths` or `staging_paths` array.")


def build_report(
    repo_root: Path,
    requested_paths: List[str],
    staged_paths: List[str],
    mode: str,
    approval_received: bool,
    blockers: List[str] | None = None,
) -> StagingReport:
    blockers = blockers or []
    status = "passed" if not blockers else "failed"
    return StagingReport(
        status=status,
        mode=mode,
        repo_root=str(repo_root),
        requested_paths=requested_paths,
        staged_paths=staged_paths,
        blockers=blockers,
        approval_required=True,
        approval_received=approval_received,
        git_operations="staged_only" if mode == "stage" else "preview_only",
    )


def print_report(report: StagingReport, as_json: bool) -> None:
    payload = asdict(report)
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    if report.status == "passed" and report.mode == "preview":
        print("GIT STAGING PREVIEW")
    elif report.status == "passed":
        print("GIT STAGING PASSED")
    else:
        print("GIT STAGING FAILED")

    print(f"Mode: {report.mode}")
    print(f"Requested paths: {len(report.requested_paths)}")
    print(f"Staged paths: {len(report.staged_paths)}")
    print(f"Git operations: {report.git_operations}")
    print(f"Git commit: {report.git_commit}")
    print(f"Git push: {report.git_push}")
    print(f"Filesystem mutation: {report.filesystem_mutation}")
    print(f"Private context access: {report.private_context_access}")
    print(f"Adapter execution: {report.adapter_execution}")
    print(f"Network access: {report.network_access}")

    if report.blockers:
        print("Blockers:")
        for blocker in report.blockers:
            print(f"- {blocker}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or stage allowlisted files using the Konoha Git Staging Gate."
    )
    parser.add_argument("--repo-root", default=".", help="Git repository root.")
    parser.add_argument(
        "--path",
        dest="paths",
        action="append",
        default=[],
        help="Repo-relative path to stage. Repeat for multiple paths.",
    )
    parser.add_argument(
        "--plan",
        help="Optional JSON plan containing `paths` or `staging_paths`.",
    )
    parser.add_argument(
        "--confirm-stage",
        action="store_true",
        help="Actually run git add for allowlisted paths.",
    )
    parser.add_argument(
        "--approval-token",
        default="",
        help="Exact approval token required with --confirm-stage.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    try:
        repo_root = validate_repo(Path(args.repo_root))

        requested_paths = list(args.paths)
        if args.plan:
            requested_paths.extend(load_paths_from_plan(Path(args.plan)))

        safe_paths = validate_paths(repo_root, requested_paths)
        approval_received = args.confirm_stage and args.approval_token == APPROVAL_TOKEN

        if args.confirm_stage and not approval_received:
            raise GateError("Explicit approval token is required: STAGE_ALLOWLISTED_FILES")

        if args.confirm_stage:
            run_git(repo_root, ["add", "--", *safe_paths], check=True)
            report = build_report(repo_root, safe_paths, safe_paths, "stage", True)
        else:
            report = build_report(repo_root, safe_paths, [], "preview", False)

        print_report(report, args.json)
        return 0

    except (GateError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        report = StagingReport(
            status="failed",
            mode="blocked",
            repo_root=str(Path(args.repo_root).resolve()),
            requested_paths=list(args.paths),
            staged_paths=[],
            blockers=[str(exc)],
            approval_required=True,
            approval_received=False,
            git_operations="blocked",
        )
        print_report(report, args.json)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
