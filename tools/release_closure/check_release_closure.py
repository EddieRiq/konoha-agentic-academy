#!/usr/bin/env python3
"""Read-only release readiness and closure guard for Konoha."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

SCHEMA_VERSION = "1.0.0"
REPORT_TYPE = "release_readiness_closure_guard_report"
TEST_REPORT_TYPE = "canonical_release_test_gate_report"
VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")
REPO_SLUG_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

BOUNDARIES = {
    "arbitrary_shell": "blocked",
    "git_write_operations": "blocked",
    "model_invocation": "blocked",
    "network_access": "blocked_unless_allow_network",
    "private_context_access": "blocked",
    "release_mutation": "blocked",
    "repository_source_mutation": "blocked",
    "report_writes": "optional_sandbox_only",
}


class ClosureGuardError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def truncate(value: str, limit: int = 8000) -> str:
    return value if len(value) <= limit else value[:limit] + "\n...[truncated]..."


def run_command(
    command: Sequence[str],
    cwd: Path,
    timeout: int = 120,
    truncate_output: bool = True,
) -> dict[str, Any]:
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
        return {
            "command": list(command),
            "returncode": completed.returncode,
            "passed": completed.returncode == 0,
            "stdout": (
                truncate(completed.stdout)
                if truncate_output
                else completed.stdout
            ),
            "stderr": (
                truncate(completed.stderr)
                if truncate_output
                else completed.stderr
            ),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": list(command),
            "returncode": None,
            "passed": False,
            "stdout": (
                truncate(exc.stdout if isinstance(exc.stdout, str) else "")
                if truncate_output
                else (exc.stdout if isinstance(exc.stdout, str) else "")
            ),
            "stderr": (
                truncate(exc.stderr if isinstance(exc.stderr, str) else "")
                if truncate_output
                else (exc.stderr if isinstance(exc.stderr, str) else "")
            ),
            "timed_out": True,
        }


def require_success(result: dict[str, Any], label: str) -> str:
    if not result["passed"]:
        detail = result["stderr"].strip() or result["stdout"].strip()
        raise ClosureGuardError(f"{label} failed: {detail or 'unknown error'}")
    return result["stdout"].strip()


def resolve_under(root: Path, candidate: Path) -> Path:
    root = root.resolve()
    candidate = candidate.resolve()
    if candidate != root and root not in candidate.parents:
        raise ClosureGuardError(f"path escapes allowed root: {candidate}")
    return candidate


def validate_version(value: str) -> None:
    if not VERSION_RE.fullmatch(value):
        raise ClosureGuardError("target version must look like vMAJOR.MINOR.PATCH")


def validate_repo_slug(value: str) -> None:
    if not REPO_SLUG_RE.fullmatch(value):
        raise ClosureGuardError("GitHub repository must use OWNER/REPO format")


def git_stdout(repo_root: Path, *args: str) -> str:
    return require_success(
        run_command(["git", *args], repo_root),
        "git " + " ".join(args),
    )


def parse_ahead_behind(value: str) -> tuple[int, int]:
    parts = value.replace("\t", " ").split()
    if len(parts) != 2:
        raise ClosureGuardError(f"unexpected ahead/behind output: {value!r}")
    return int(parts[0]), int(parts[1])


def collect_local_git(
    repo_root: Path,
    expected_branch: str,
    remote: str,
    target_version: str,
) -> dict[str, Any]:
    if git_stdout(repo_root, "rev-parse", "--is-inside-work-tree") != "true":
        raise ClosureGuardError("repo root is not inside a Git worktree")

    head = git_stdout(repo_root, "rev-parse", "HEAD")
    branch = git_stdout(repo_root, "branch", "--show-current")
    status_short = git_stdout(
        repo_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=normal",
    )

    tracking_ref = f"{remote}/{expected_branch}"
    tracking = run_command(["git", "rev-parse", "--verify", tracking_ref], repo_root)
    if tracking["passed"]:
        tracked_remote_head = tracking["stdout"].strip()
        behind, ahead = parse_ahead_behind(
            git_stdout(
                repo_root,
                "rev-list",
                "--left-right",
                "--count",
                f"{tracking_ref}...HEAD",
            )
        )
    else:
        tracked_remote_head = None
        behind = None
        ahead = None

    tag_ref = f"refs/tags/{target_version}"
    tag = run_command(["git", "rev-parse", "--verify", tag_ref], repo_root)
    tag_exists = tag["passed"]
    tag_target = (
        git_stdout(repo_root, "rev-parse", f"{target_version}^{{}}")
        if tag_exists
        else None
    )

    return {
        "head": head,
        "branch": branch,
        "expected_branch": expected_branch,
        "branch_matches": branch == expected_branch,
        "status_short": status_short,
        "working_tree_clean": status_short == "",
        "tracking_ref": tracking_ref,
        "tracking_ref_exists": tracking["passed"],
        "tracked_remote_head": tracked_remote_head,
        "behind": behind,
        "ahead": ahead,
        "tracking_synced": behind == 0 and ahead == 0,
        "local_tag": {
            "name": target_version,
            "exists": tag_exists,
            "object": tag["stdout"].strip() if tag_exists else None,
            "target": tag_target,
            "target_matches_head": tag_target == head if tag_exists else None,
        },
    }


def run_canonical_tests(repo_root: Path, timeout: int) -> dict[str, Any]:
    head_before = git_stdout(repo_root, "rev-parse", "HEAD")
    status_before = git_stdout(
        repo_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=normal",
    )
    command = [
        sys.executable,
        "tools/release_testing/run_release_tests.py",
        "--repo-root",
        ".",
        "--json",
    ]
    result = run_command(
        command,
        repo_root,
        timeout=timeout,
        truncate_output=False,
    )
    head_after = git_stdout(repo_root, "rev-parse", "HEAD")
    status_after = git_stdout(
        repo_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=normal",
    )

    payload = None
    parse_error = None
    try:
        payload = json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        parse_error = str(exc)

    parsed = (
        isinstance(payload, dict)
        and payload.get("report_type") == TEST_REPORT_TYPE
    )
    passed = bool(
        result["passed"]
        and parsed
        and payload.get("passed") is True
        and payload.get("summary", {}).get("failed_suite_count") == 0
        and head_before == head_after
    )

    return {
        "source": "executed_now",
        "command": command,
        "returncode": result["returncode"],
        "timed_out": result["timed_out"],
        "parsed": parsed,
        "parse_error": parse_error,
        "report_sha256": hashlib.sha256(
            result["stdout"].encode("utf-8")
        ).hexdigest(),
        "report_type": payload.get("report_type") if isinstance(payload, dict) else None,
        "report_schema_version": (
            payload.get("schema_version") if isinstance(payload, dict) else None
        ),
        "generated_at": payload.get("generated_at") if isinstance(payload, dict) else None,
        "summary": payload.get("summary") if isinstance(payload, dict) else None,
        "passed": passed,
        "head_before": head_before,
        "head_after": head_after,
        "head_unchanged": head_before == head_after,
        "status_before": status_before,
        "status_after": status_after,
        "stderr": truncate(result["stderr"]),
    }


def load_test_evidence(
    repo_root: Path,
    evidence_path: Path,
    current_head: str,
) -> dict[str, Any]:
    sandbox_root = (repo_root / "sandbox").resolve()
    resolved = (
        evidence_path.resolve()
        if evidence_path.is_absolute()
        else (repo_root / evidence_path).resolve()
    )
    resolve_under(sandbox_root, resolved)
    if not resolved.exists():
        raise ClosureGuardError(f"test evidence does not exist: {resolved}")

    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if payload.get("report_type") != REPORT_TYPE:
        raise ClosureGuardError(
            "test evidence must be a prior release closure guard report"
        )

    test_gate = payload.get("test_gate", {})
    source_head = payload.get("git", {}).get("head")
    passed = bool(
        test_gate.get("passed") is True
        and test_gate.get("head_unchanged") is True
        and source_head == current_head
        and test_gate.get("head_after") == current_head
    )
    return {
        **test_gate,
        "source": "reused_guard_report",
        "source_path": str(resolved),
        "passed": passed,
        "evidence_head_matches": source_head == current_head,
    }


def parse_ls_remote(stdout: str) -> dict[str, str]:
    refs: dict[str, str] = {}
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) == 2:
            refs[parts[1]] = parts[0]
    return refs


def collect_remote_git(
    repo_root: Path,
    remote: str,
    branch: str,
    target_version: str,
) -> dict[str, Any]:
    refs = [
        f"refs/heads/{branch}",
        f"refs/tags/{target_version}",
        f"refs/tags/{target_version}^{{}}",
    ]
    result = run_command(
        ["git", "ls-remote", remote, *refs],
        repo_root,
        timeout=120,
    )
    if not result["passed"]:
        return {
            "checked": True,
            "passed": False,
            "error": result["stderr"].strip() or result["stdout"].strip(),
            "refs": {},
        }

    parsed = parse_ls_remote(result["stdout"])
    return {
        "checked": True,
        "passed": True,
        "error": None,
        "refs": parsed,
        "branch_head": parsed.get(f"refs/heads/{branch}"),
        "tag_object": parsed.get(f"refs/tags/{target_version}"),
        "tag_target": parsed.get(f"refs/tags/{target_version}^{{}}"),
        "tag_exists": f"refs/tags/{target_version}" in parsed,
    }


def collect_github_release(
    repo_root: Path,
    github_repo: str,
    target_version: str,
) -> dict[str, Any]:
    if shutil.which("gh") is None:
        return {
            "checked": True,
            "gh_available": False,
            "authenticated": False,
            "release_exists": False,
        }

    auth = run_command(
        ["gh", "auth", "status", "--active", "--hostname", "github.com"],
        repo_root,
        timeout=60,
    )
    if not auth["passed"]:
        return {
            "checked": True,
            "gh_available": True,
            "authenticated": False,
            "auth_error": auth["stderr"].strip() or auth["stdout"].strip(),
            "release_exists": False,
        }

    listing = run_command(
        [
            "gh",
            "release",
            "list",
            "--repo",
            github_repo,
            "--limit",
            "100",
            "--json",
            "tagName,name,isLatest,isDraft,isPrerelease,publishedAt",
        ],
        repo_root,
        timeout=120,
    )
    if not listing["passed"]:
        return {
            "checked": True,
            "gh_available": True,
            "authenticated": True,
            "query_passed": False,
            "query_error": listing["stderr"].strip() or listing["stdout"].strip(),
            "release_exists": False,
        }

    releases = json.loads(listing["stdout"])
    target = next(
        (item for item in releases if item.get("tagName") == target_version),
        None,
    )
    return {
        "checked": True,
        "gh_available": True,
        "authenticated": True,
        "query_passed": True,
        "release_exists": target is not None,
        "release": target,
        "is_latest": target.get("isLatest") if target else None,
        "is_draft": target.get("isDraft") if target else None,
        "is_prerelease": target.get("isPrerelease") if target else None,
    }


def decide_status(
    git_state: dict[str, Any],
    test_gate: dict[str, Any],
    allow_network: bool,
    remote_git: dict[str, Any] | None,
    github_release: dict[str, Any] | None,
) -> tuple[str, str]:
    if not git_state["working_tree_clean"]:
        return "BLOCKED_DIRTY_WORKTREE", "Commit or remove public working-tree changes."
    if not git_state["branch_matches"]:
        return "BLOCKED_BRANCH_MISMATCH", "Switch to the expected release branch."
    if not test_gate.get("passed"):
        if test_gate.get("source") == "reused_guard_report":
            return (
                "BLOCKED_TEST_EVIDENCE_STALE",
                "Run the canonical test gate again for the current HEAD.",
            )
        return "BLOCKED_TEST_GATE_FAILED", "Fix the canonical test gate failures."
    if not git_state["tracking_ref_exists"] or not git_state["tracking_synced"]:
        return (
            "BLOCKED_BRANCH_NOT_SYNCED",
            "Synchronize the local branch and remote-tracking ref.",
        )

    local_tag = git_state["local_tag"]
    if not local_tag["exists"]:
        return "NEEDS_TAG_CREATION", "Create the annotated local release tag."
    if local_tag["target_matches_head"] is not True:
        return (
            "BLOCKED_LOCAL_TAG_TARGET_MISMATCH",
            "The local tag does not point to the tested HEAD.",
        )

    if not allow_network:
        return (
            "NEEDS_NETWORK_VERIFICATION",
            "Re-run with --allow-network for remote and GitHub checks.",
        )

    if not remote_git or not remote_git.get("passed"):
        return (
            "BLOCKED_REMOTE_BRANCH_MISMATCH",
            "Remote Git state could not be verified.",
        )
    if remote_git.get("branch_head") != git_state["head"]:
        return (
            "BLOCKED_REMOTE_BRANCH_MISMATCH",
            "Remote branch does not point to the tested HEAD.",
        )
    if not remote_git.get("tag_exists"):
        return "NEEDS_TAG_PUBLICATION", "Push the existing local tag."
    if remote_git.get("tag_target") != git_state["head"]:
        return (
            "BLOCKED_REMOTE_TAG_TARGET_MISMATCH",
            "Remote tag does not point to the tested HEAD.",
        )

    if not github_release:
        return "BLOCKED_GH_AUTH", "GitHub Release state was not checked."
    if not github_release.get("gh_available"):
        return "BLOCKED_GH_CLI_MISSING", "Install GitHub CLI."
    if not github_release.get("authenticated"):
        return "BLOCKED_GH_AUTH", "Authenticate GitHub CLI."
    if not github_release.get("query_passed"):
        return "BLOCKED_GH_AUTH", "GitHub Release query failed."
    if not github_release.get("release_exists"):
        return "NEEDS_RELEASE_PUBLICATION", "Create the GitHub Release."
    if github_release.get("is_draft"):
        return "BLOCKED_RELEASE_DRAFT", "Publish the draft release."
    if github_release.get("is_prerelease"):
        return (
            "BLOCKED_RELEASE_PRERELEASE",
            "Publish a stable release or approve prerelease policy.",
        )
    if github_release.get("is_latest") is not True:
        return "NEEDS_LATEST_PROMOTION", "Mark the release as Latest."
    return "RELEASE_CLOSED", "Release code, tag and GitHub Release are aligned."


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    validate_version(args.target_version)
    validate_repo_slug(args.github_repo)

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        raise ClosureGuardError(f"repo root does not exist: {repo_root}")

    git_state = collect_local_git(
        repo_root,
        args.expected_branch,
        args.remote,
        args.target_version,
    )

    if args.run_tests:
        test_gate = run_canonical_tests(repo_root, args.test_timeout)
    else:
        test_gate = load_test_evidence(
            repo_root,
            Path(args.test_evidence),
            git_state["head"],
        )

    remote_git = None
    github_release = None
    if args.allow_network:
        remote_git = collect_remote_git(
            repo_root,
            args.remote,
            args.expected_branch,
            args.target_version,
        )
        github_release = collect_github_release(
            repo_root,
            args.github_repo,
            args.target_version,
        )

    status_code, next_action = decide_status(
        git_state,
        test_gate,
        args.allow_network,
        remote_git,
        github_release,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "generated_at": utc_now(),
        "target_version": args.target_version,
        "github_repo": args.github_repo,
        "status": "passed" if status_code == "RELEASE_CLOSED" else "incomplete",
        "status_code": status_code,
        "release_closed": status_code == "RELEASE_CLOSED",
        "next_action": next_action,
        "git": git_state,
        "test_gate": test_gate,
        "network_approved": args.allow_network,
        "remote_git": remote_git,
        "github_release": github_release,
        "boundaries": BOUNDARIES,
        "authority": {
            "guard_report_is_evidence_only": True,
            "tag_creation_requires_separate_approval": True,
            "tag_push_requires_separate_approval": True,
            "github_release_mutation_requires_separate_approval": True,
        },
    }


def validate_output(repo_root: Path, output: Path) -> Path:
    sandbox_root = (repo_root / "sandbox").resolve()
    resolved = (
        output.resolve()
        if output.is_absolute()
        else (repo_root / output).resolve()
    )
    return resolve_under(sandbox_root, resolved)


def write_report(path: Path, report: dict[str, Any], force: bool) -> None:
    if path.exists() and not force:
        raise ClosureGuardError(f"report already exists: {path}; use --force")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def print_text(report: dict[str, Any]) -> None:
    print("KONOHA RELEASE READINESS AND CLOSURE GUARD")
    print(f"target: {report['target_version']}")
    print(f"status code: {report['status_code']}")
    print(f"release closed: {str(report['release_closed']).lower()}")
    print(f"HEAD: {report['git']['head']}")
    print(f"branch: {report['git']['branch']}")
    print(f"working tree clean: {report['git']['working_tree_clean']}")
    print(f"tracking synced: {report['git']['tracking_synced']}")
    print(f"test gate passed: {report['test_gate']['passed']}")
    print(f"local tag exists: {report['git']['local_tag']['exists']}")
    if report["remote_git"] is not None:
        print(f"remote tag exists: {report['remote_git'].get('tag_exists')}")
    if report["github_release"] is not None:
        print(
            "GitHub Release exists: "
            f"{report['github_release'].get('release_exists')}"
        )
        print(f"Latest: {report['github_release'].get('is_latest')}")
    print(f"next action: {report['next_action']}")
    print("Git writes: blocked")
    print("Release mutation: blocked")
    print("Result is evidence only.")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only release readiness and closure guard."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--target-version", required=True)
    parser.add_argument("--expected-branch", default="main")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--github-repo", required=True)
    test_group = parser.add_mutually_exclusive_group(required=True)
    test_group.add_argument("--run-tests", action="store_true")
    test_group.add_argument(
        "--test-evidence",
        help="Prior closure-guard report below sandbox/ for the same HEAD.",
    )
    parser.add_argument("--test-timeout", type=int, default=900)
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--output", help="JSON report path below sandbox/.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    try:
        if args.test_timeout <= 0:
            raise ClosureGuardError("--test-timeout must be positive")
        report = build_report(args)
        repo_root = Path(args.repo_root).resolve()
        if args.output:
            output = validate_output(repo_root, Path(args.output))
            write_report(output, report, args.force)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_text(report)
            if args.output:
                print(f"Report: {validate_output(repo_root, Path(args.output))}")
        return 0 if report["release_closed"] else 1
    except (ClosureGuardError, json.JSONDecodeError) as exc:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "report_type": REPORT_TYPE,
            "status": "blocked",
            "status_code": "BLOCKED_CONFIGURATION",
            "release_closed": False,
            "blocker": str(exc),
            "boundaries": BOUNDARIES,
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("KONOHA RELEASE CLOSURE GUARD BLOCKED", file=sys.stderr)
            print(f"Blocker: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
