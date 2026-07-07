#!/usr/bin/env python3
"""
Konoha Git Read-only Gate.

This tool inspects Git readiness using read-only Git commands only.
It does not stage files, create commits, move refs, clean files, or send data anywhere.

Allowed behavior:
- read Git status;
- read tracked file list;
- read changed file names;
- optionally verify ignored paths using read-only ignore checks;
- print a text or JSON readiness report.

It never authorizes runtime actions.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


ALLOWED_GIT_SUBCOMMANDS = {
    "rev-parse",
    "status",
    "diff",
    "ls-files",
    "check-ignore",
}

PRIVATE_TRACKED_PATTERNS = (
    "private-library/",
    "/private-library/",
    "memory/local/",
    "/memory/local/",
    ".venv/",
    "/.venv/",
    ".env",
    "secrets/",
    "/secrets/",
    "credentials/",
    "/credentials/",
    "vault/",
    "/vault/",
)


@dataclass(frozen=True)
class GitCommandResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip()


def is_allowed_git_args(args: Sequence[str]) -> bool:
    """Return True only for the read-only Git subcommands used by this gate."""
    if not args:
        return False

    subcommand = args[0]
    if subcommand not in ALLOWED_GIT_SUBCOMMANDS:
        return False

    if subcommand == "rev-parse":
        return tuple(args) == ("rev-parse", "--show-toplevel")

    if subcommand == "status":
        return tuple(args) == ("status", "--porcelain=v1")

    if subcommand == "diff":
        return tuple(args) == ("diff", "--name-only")

    if subcommand == "ls-files":
        return tuple(args) == ("ls-files",)

    if subcommand == "check-ignore":
        return len(args) >= 3 and tuple(args[:2]) == ("check-ignore", "-v")

    return False


def run_git(repo_root: Path, args: Sequence[str]) -> GitCommandResult:
    if not is_allowed_git_args(args):
        raise ValueError(f"Unsupported Git read-only command: {' '.join(args)}")

    completed = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )

    return GitCommandResult(
        args=tuple(args),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def parse_status_porcelain(output: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []

    for raw_line in output.splitlines():
        if not raw_line:
            continue

        if len(raw_line) < 4:
            entries.append(
                {
                    "status": raw_line.strip(),
                    "path": "",
                    "category": "unknown",
                }
            )
            continue

        status = raw_line[:2]
        path = normalize_path(raw_line[3:])

        if status == "??":
            category = "untracked"
        elif status == "!!":
            category = "ignored"
        else:
            category = "modified"

        entries.append(
            {
                "status": status,
                "path": path,
                "category": category,
            }
        )

    return entries


def tracked_private_paths(tracked_paths: Iterable[str]) -> list[str]:
    findings: list[str] = []

    for path in tracked_paths:
        normalized = normalize_path(path)
        padded = f"/{normalized}"
        for pattern in PRIVATE_TRACKED_PATTERNS:
            if pattern in normalized or pattern in padded:
                findings.append(normalized)
                break

    return sorted(set(findings))


def summarize_status(
    status_entries: list[dict[str, str]],
    allow_dirty: bool,
) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []

    modified = [item["path"] for item in status_entries if item["category"] == "modified"]
    untracked = [item["path"] for item in status_entries if item["category"] == "untracked"]

    if modified:
        message = f"Working tree has modified or staged paths: {len(modified)}"
        if allow_dirty:
            warnings.append(message)
        else:
            blockers.append(message)

    if untracked:
        message = f"Working tree has untracked paths: {len(untracked)}"
        if allow_dirty:
            warnings.append(message)
        else:
            blockers.append(message)

    return blockers, warnings


def check_ignore_paths(repo_root: Path, paths: Iterable[str]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    for raw_path in paths:
        path = normalize_path(raw_path)
        if not path:
            continue

        result = run_git(repo_root, ("check-ignore", "-v", path))

        results.append(
            {
                "path": path,
                "ignored": result.returncode == 0,
                "detail": result.stdout.strip(),
            }
        )

    return results


def build_report(
    repo_root: Path,
    allow_dirty: bool = False,
    ignore_check_paths: Iterable[str] | None = None,
) -> dict:
    repo_root = repo_root.resolve()

    blockers: list[str] = []
    warnings: list[str] = []

    root_result = run_git(repo_root, ("rev-parse", "--show-toplevel"))
    if root_result.returncode != 0:
        return {
            "tool": "git_read_only_gate",
            "status": "blocked",
            "repo_root": str(repo_root),
            "blockers": ["Path is not inside a Git repository."],
            "warnings": [],
            "safety": safety_boundary(),
        }

    status_result = run_git(repo_root, ("status", "--porcelain=v1"))
    diff_result = run_git(repo_root, ("diff", "--name-only"))
    tracked_result = run_git(repo_root, ("ls-files",))

    for result in (status_result, diff_result, tracked_result):
        if result.returncode != 0:
            blockers.append(f"Git read-only command failed: {' '.join(result.args)}")

    status_entries = parse_status_porcelain(status_result.stdout)
    status_blockers, status_warnings = summarize_status(status_entries, allow_dirty=allow_dirty)
    blockers.extend(status_blockers)
    warnings.extend(status_warnings)

    tracked_paths = [normalize_path(line) for line in tracked_result.stdout.splitlines() if line.strip()]
    private_tracked = tracked_private_paths(tracked_paths)

    if private_tracked:
        blockers.append(f"Tracked private or local-only paths detected: {len(private_tracked)}")

    changed_paths = [normalize_path(line) for line in diff_result.stdout.splitlines() if line.strip()]
    ignore_results = check_ignore_paths(repo_root, ignore_check_paths or [])

    report_status = "passed" if not blockers else "blocked"

    return {
        "tool": "git_read_only_gate",
        "status": report_status,
        "repo_root": str(repo_root),
        "allow_dirty": allow_dirty,
        "status_entries": status_entries,
        "changed_paths": changed_paths,
        "tracked_file_count": len(tracked_paths),
        "tracked_private_paths": private_tracked,
        "ignore_checks": ignore_results,
        "blockers": blockers,
        "warnings": warnings,
        "safety": safety_boundary(),
    }


def safety_boundary() -> dict[str, str]:
    return {
        "execution": "blocked",
        "filesystem_mutation": "blocked",
        "git_operations": "read_only",
        "git_write_operations": "blocked",
        "private_context_access": "blocked",
        "adapter_execution": "blocked",
        "network_access": "blocked",
    }


def print_text_report(report: dict) -> None:
    if report["status"] == "passed":
        print("GIT READINESS PASSED")
    else:
        print("GIT READINESS BLOCKED")

    print(f"Tracked files: {report.get('tracked_file_count', 0)}")
    print(f"Status entries: {len(report.get('status_entries', []))}")
    print(f"Changed paths: {len(report.get('changed_paths', []))}")

    blockers = report.get("blockers", [])
    warnings = report.get("warnings", [])

    if blockers:
        print("Blockers:")
        for item in blockers:
            print(f"- {item}")

    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"- {item}")

    safety = report.get("safety", {})
    print(f"Execution: {safety.get('execution')}")
    print(f"Filesystem mutation: {safety.get('filesystem_mutation')}")
    print(f"Git operations: {safety.get('git_operations')}")
    print(f"Git write operations: {safety.get('git_write_operations')}")
    print(f"Private context access: {safety.get('private_context_access')}")
    print(f"Adapter execution: {safety.get('adapter_execution')}")
    print(f"Network access: {safety.get('network_access')}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Git readiness using read-only Git commands."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root or any path inside the repository.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Downgrade modified/untracked working-tree findings to warnings.",
    )
    parser.add_argument(
        "--check-ignore-path",
        action="append",
        default=[],
        help="Optional path to verify with a read-only ignore check. May be repeated.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON report to stdout.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    report = build_report(
        Path(args.repo_root),
        allow_dirty=args.allow_dirty,
        ignore_check_paths=args.check_ignore_path,
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
