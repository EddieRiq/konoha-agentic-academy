#!/usr/bin/env python3
"""
Git Commit Gate for Konoha Agentic Academy.

Safety boundary:
- may inspect staged files;
- may create a commit only with explicit confirmation and exact approval token;
- may not stage files;
- may not push;
- may not clean, reset, rebase, amend, or rewrite history;
- may not access private Village context;
- may not execute mission actions.

This tool uses Git through subprocess.run with shell=False and fixed allowlisted
commands only.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


APPROVAL_TOKEN = "COMMIT_STAGED_ALLOWLISTED_FILES"

ALLOWED_PREFIXES = (
    "README.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "AGENTS.md",
    "docs/",
    "scrolls/",
    "runtime/",
    "schemas/",
    "tools/",
    "tests/",
    "examples/",
    "adapters/",
    "evals/",
    "alliance/templates/",
    "protocols/",
    "missions/",
    "memory/",
    "telemetry/",
    "clans/",
    "core/",
    "council/",
    "hokage/",
    "jounin/",
    "kagebunshin/",
    "marketplace/",
    "sandbox/tmp/.gitkeep",
    "shikamaru/",
    "shinobi/",
    "ui/",
)

BLOCKED_PATTERNS = (
    "alliance/kirigakure/",
    "/private-library/",
    "private-library/",
    "/vault/",
    "vault/",
    "/memory/local/",
    "memory/local/",
    "/assets/private/",
    "assets/private/",
    ".env",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    "secrets/",
    "credentials/",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
)

COMMIT_MESSAGE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,_:/()#+'!-]{2,119}$")


def normalize_repo_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def validate_repo_path(path: str) -> Optional[str]:
    normalized = normalize_repo_path(path)
    if not normalized:
        return "empty path"
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
        return "absolute paths are blocked"
    parts = normalized.split("/")
    if ".." in parts:
        return "path traversal is blocked"
    lowered = normalized.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in lowered:
            return "private, credential, cache, or local-only path is blocked"
    if not any(normalized == prefix or normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return "path is not in the commit allowlist"
    return None


def validate_commit_message(message: str) -> Optional[str]:
    if message is None:
        return "commit message is required"
    stripped = message.strip()
    if not stripped:
        return "commit message is empty"
    if stripped != message:
        return "commit message must not have leading or trailing whitespace"
    if "\n" in stripped or "\r" in stripped:
        return "multi-line commit messages are blocked by this gate"
    if len(stripped) > 120:
        return "commit message is too long"
    if not COMMIT_MESSAGE_PATTERN.match(stripped):
        return "commit message contains unsupported characters or is too short"
    return None


def run_git(repo_root: Path, args: List[str]) -> Tuple[int, str, str]:
    # shell=False is intentional. Args are fixed by this tool, not user-provided
    # arbitrary shell commands.
    completed = subprocess.run(
        ["git"] + args,
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def ensure_git_repo(repo_root: Path) -> Tuple[bool, str]:
    code, stdout, stderr = run_git(repo_root, ["rev-parse", "--show-toplevel"])
    if code != 0:
        return False, stderr or "not a Git repository"
    try:
        actual = Path(stdout).resolve()
        expected = repo_root.resolve()
    except OSError as exc:
        return False, str(exc)
    if actual != expected:
        return False, f"repo root mismatch: expected {expected}, got {actual}"
    return True, ""


def get_staged_paths(repo_root: Path) -> Tuple[bool, List[str], str]:
    code, stdout, stderr = run_git(repo_root, ["diff", "--cached", "--name-only", "--diff-filter=ACMRT"])
    if code != 0:
        return False, [], stderr or "failed to inspect staged files"
    paths = [line.strip() for line in stdout.splitlines() if line.strip()]
    return True, paths, ""


def get_status_short(repo_root: Path) -> Tuple[bool, List[str], str]:
    code, stdout, stderr = run_git(repo_root, ["status", "--short"])
    if code != 0:
        return False, [], stderr or "failed to inspect Git status"
    return True, [line for line in stdout.splitlines() if line.strip()], ""


def inspect_staged_paths(paths: List[str]) -> Tuple[List[str], List[Dict[str, str]]]:
    blockers: List[Dict[str, str]] = []
    normalized: List[str] = []
    for path in paths:
        repo_path = normalize_repo_path(path)
        reason = validate_repo_path(repo_path)
        if reason:
            blockers.append({"path": repo_path, "reason": reason})
        else:
            normalized.append(repo_path)
    return normalized, blockers


def build_report(
    outcome: str,
    mode: str,
    repo_root: str,
    message: str,
    staged_paths: List[str],
    blockers: List[Dict[str, str]],
    commit_hash: Optional[str],
    status_lines: List[str],
) -> Dict[str, object]:
    return {
        "schema_version": "0.25.0",
        "tool": "git_commit_gate",
        "outcome": outcome,
        "mode": mode,
        "repo_root": repo_root,
        "commit_message": message,
        "staged_paths": staged_paths,
        "blockers": blockers,
        "commit_hash": commit_hash,
        "status_lines": status_lines,
        "safety": {
            "execution": "blocked",
            "git_stage": "blocked",
            "git_commit": "preview_only" if mode == "preview" else "human_approved",
            "git_push": "blocked",
            "git_clean": "blocked",
            "git_reset": "blocked",
            "private_context_access": "blocked",
            "adapter_execution": "blocked",
            "network_access": "blocked",
        },
    }


def print_text_report(report: Dict[str, object]) -> None:
    if report["outcome"] == "passed" and report["mode"] == "preview":
        print("GIT COMMIT PREVIEW")
    elif report["outcome"] == "passed":
        print("GIT COMMIT CREATED")
    else:
        print("GIT COMMIT GATE FAILED")

    print("Git staging: blocked")
    print("Git commit: preview_only" if report["mode"] == "preview" else "Git commit: human_approved")
    print("Git push: blocked")
    print("Git clean/reset: blocked")
    print("Execution: blocked")
    print("Private context access: blocked")
    print("Adapter execution: blocked")
    print(f"Staged files: {len(report['staged_paths'])}")

    if report.get("commit_hash"):
        print(f"Commit: {report['commit_hash']}")

    blockers = report.get("blockers", [])
    if blockers:
        print("Blockers:")
        for blocker in blockers:
            print(f"- {blocker['path']}: {blocker['reason']}")


def create_commit(repo_root: Path, message: str) -> Tuple[bool, Optional[str], str]:
    code, stdout, stderr = run_git(repo_root, ["commit", "-m", message])
    if code != 0:
        return False, None, stderr or stdout or "git commit failed"
    code, commit_hash, stderr = run_git(repo_root, ["rev-parse", "--short", "HEAD"])
    if code != 0:
        return False, None, stderr or "commit created but hash inspection failed"
    return True, commit_hash, ""


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview or create a human-approved commit from already staged allowlisted files.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument("--message", required=True, help="Single-line commit message.")
    parser.add_argument("--confirm-commit", action="store_true", help="Create the commit. Without this flag the tool only previews.")
    parser.add_argument("--approval-token", default="", help="Required exact token for confirmed commit.")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow unstaged/untracked changes in the working tree. Staged files are still validated.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    blockers: List[Dict[str, str]] = []

    message_error = validate_commit_message(args.message)
    if message_error:
        blockers.append({"path": "<commit_message>", "reason": message_error})

    ok_repo, repo_error = ensure_git_repo(repo_root)
    if not ok_repo:
        blockers.append({"path": str(repo_root), "reason": repo_error})
        report = build_report("failed", "confirmed" if args.confirm_commit else "preview", str(repo_root), args.message, [], blockers, None, [])
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_text_report(report)
        return 1

    ok_status, status_lines, status_error = get_status_short(repo_root)
    if not ok_status:
        blockers.append({"path": "<git_status>", "reason": status_error})
        status_lines = []

    ok_staged, staged_paths_raw, staged_error = get_staged_paths(repo_root)
    if not ok_staged:
        blockers.append({"path": "<staged_files>", "reason": staged_error})
        staged_paths_raw = []

    staged_paths, path_blockers = inspect_staged_paths(staged_paths_raw)
    blockers.extend(path_blockers)

    if not staged_paths_raw:
        blockers.append({"path": "<staged_files>", "reason": "no staged files found; this gate does not stage files"})

    if args.confirm_commit and args.approval_token != APPROVAL_TOKEN:
        blockers.append({"path": "<approval_token>", "reason": "exact approval token is required for confirmed commit"})

    if not args.allow_dirty:
        unstaged_or_untracked = [
            line for line in status_lines
            if len(line) >= 2 and (line[1] != " " or line.startswith("??"))
        ]
        if unstaged_or_untracked:
            blockers.append({"path": "<working_tree>", "reason": "unstaged or untracked changes present; use --allow-dirty only after review"})

    mode = "confirmed" if args.confirm_commit else "preview"
    if blockers:
        report = build_report("failed", mode, str(repo_root), args.message, staged_paths, blockers, None, status_lines)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_text_report(report)
        return 1

    commit_hash = None
    if args.confirm_commit:
        ok_commit, commit_hash, commit_error = create_commit(repo_root, args.message)
        if not ok_commit:
            blockers.append({"path": "<git_commit>", "reason": commit_error})
            report = build_report("failed", mode, str(repo_root), args.message, staged_paths, blockers, None, status_lines)
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print_text_report(report)
            return 1

    report = build_report("passed", mode, str(repo_root), args.message, staged_paths, blockers, commit_hash, status_lines)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
