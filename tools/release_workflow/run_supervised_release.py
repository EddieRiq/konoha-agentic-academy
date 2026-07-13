#!/usr/bin/env python3
"""Unified supervised release workflow for Konoha.

This orchestrator composes existing deterministic components:

- the canonical release test gate;
- the beta Git plan/stage/commit/push gates;
- the read-only release readiness and closure guard;
- explicit annotated-tag and GitHub Release mutations.

It advances only when an observed return code and status_code match an allowed
transition. It never treats a proposal, test result, guard report, approval
declaration, or model output as authority by itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

SCHEMA_VERSION = "1.0.0"
PLAN_REPORT_TYPE = "supervised_release_workflow_plan"
REPORT_TYPE = "supervised_release_workflow_report"
STATUS_REPORT_TYPE = "supervised_release_status_report"
CLOSURE_REPORT_TYPE = "release_readiness_closure_guard_report"

RUN_TOKEN = "RUN_SUPERVISED_RELEASE_WORKFLOW"
TAG_CREATE_TOKEN = "APPROVE_SUPERVISED_RELEASE_TAG_CREATE"
TAG_PUSH_TOKEN = "APPROVE_SUPERVISED_RELEASE_TAG_PUSH"
RELEASE_PUBLISH_TOKEN = "APPROVE_SUPERVISED_RELEASE_PUBLISH"
LATEST_PROMOTION_TOKEN = "APPROVE_SUPERVISED_RELEASE_LATEST"

VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

PRIVATE_PATTERNS = (
    ".env",
    "alliance/kirigakure",
    "memory/local",
    "vault",
    "sandbox",
)

EXPECTED_STATES = {
    "BLOCKED_BRANCH_NOT_SYNCED",
    "NEEDS_TAG_CREATION",
    "NEEDS_TAG_PUBLICATION",
    "NEEDS_RELEASE_PUBLICATION",
    "NEEDS_LATEST_PROMOTION",
    "RELEASE_CLOSED",
}

BOUNDARIES = {
    "arbitrary_shell": "blocked",
    "force_push": "blocked",
    "force_tag": "blocked",
    "tag_rewrite": "blocked",
    "release_delete": "blocked",
    "release_overwrite": "blocked",
    "model_invocation": "blocked",
    "private_context_access": "blocked",
    "git_mutations": "explicit_tokens_only",
    "network_access": "explicit_allow_network_only",
    "report_output": "sandbox_only",
}


class WorkflowError(RuntimeError):
    """Unsafe configuration, unexpected transition, or failed command."""


@dataclass
class CommandResult:
    command: List[str]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def passed(self) -> bool:
        return self.returncode == 0 and not self.timed_out


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

    for prefix in PRIVATE_PATTERNS:
        normalized = prefix.lower()
        if lowered == normalized or lowered.startswith(normalized + "/"):
            return True

    if len(parts) >= 3 and parts[0] == "alliance":
        if parts[2] in {"private-library", "memory"}:
            return True

    return False


def resolve_under(root: Path, raw: str, label: str) -> Path:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    root = root.resolve()
    if candidate != root and not is_relative_to(candidate, root):
        raise WorkflowError(f"{label} escapes allowed root: {candidate}")
    return candidate


def resolve_repo_file(
    repo_root: Path,
    raw: Any,
    label: str,
    *,
    allow_sandbox: bool = False,
) -> Tuple[str, Path]:
    relative = normalize_relative_path(raw)
    if relative is None or relative == ".":
        raise WorkflowError(f"{label} must be a repository-relative file path")

    if is_private_path(relative) and not (
        allow_sandbox and relative.startswith("sandbox/")
    ):
        raise WorkflowError(f"{label} points to blocked private context: {relative}")

    resolved = (repo_root / relative).resolve()
    if not is_relative_to(resolved, repo_root):
        raise WorkflowError(f"{label} escapes repository root")
    if not resolved.is_file():
        raise WorkflowError(f"{label} file not found: {relative}")
    return relative, resolved


def resolve_output(repo_root: Path, raw: str) -> Path:
    sandbox = (repo_root / "sandbox").resolve()
    output = Path(raw)
    if not output.is_absolute():
        output = repo_root / output
    output = output.resolve()
    if not is_relative_to(output, sandbox):
        raise WorkflowError("workflow output must stay under <repo-root>/sandbox")
    return output


def read_json(path: Path, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkflowError(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise WorkflowError(
            f"{label} JSON invalid at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(payload, dict):
        raise WorkflowError(f"{label} JSON must be an object")
    return payload


def write_json(path: Path, payload: Mapping[str, Any], force: bool) -> None:
    if path.exists() and not force:
        raise WorkflowError(f"output exists; use --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def default_command_runner(
    command: Sequence[str],
    cwd: Path,
    timeout: int,
) -> CommandResult:
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
        return CommandResult(
            command=list(command),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            command=list(command),
            returncode=124,
            stdout=exc.stdout if isinstance(exc.stdout, str) else "",
            stderr=exc.stderr if isinstance(exc.stderr, str) else "",
            timed_out=True,
        )


def require_command(result: CommandResult, label: str) -> str:
    if not result.passed:
        detail = result.stderr.strip() or result.stdout.strip()
        raise WorkflowError(
            f"{label} failed with RC={result.returncode}: "
            f"{detail or 'no output'}"
        )
    return result.stdout.strip()


def git_stdout(
    runner: Callable[[Sequence[str], Path, int], CommandResult],
    repo_root: Path,
    *args: str,
    timeout: int = 120,
) -> str:
    return require_command(
        runner(["git", *args], repo_root, timeout),
        "git " + " ".join(args),
    )


def parse_count_pair(value: str) -> Tuple[int, int]:
    parts = value.replace("\t", " ").split()
    if len(parts) != 2:
        raise WorkflowError(f"unexpected behind/ahead output: {value!r}")
    return int(parts[0]), int(parts[1])


def collect_scope(
    runner: Callable[[Sequence[str], Path, int], CommandResult],
    repo_root: Path,
) -> List[str]:
    changed = git_stdout(runner, repo_root, "diff", "--name-only")
    untracked = git_stdout(
        runner,
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


def collect_commit_paths(
    runner: Callable[[Sequence[str], Path, int], CommandResult],
    repo_root: Path,
    commit: str,
) -> List[str]:
    value = git_stdout(
        runner,
        repo_root,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        commit,
    )
    return sorted(line for line in value.splitlines() if line)


def validate_plan(plan: Mapping[str, Any]) -> Dict[str, Any]:
    required = {
        "schema_version",
        "report_type",
        "workflow_id",
        "expected_base_commit",
        "expected_branch",
        "remote",
        "github_repo",
        "target_version",
        "previous_version",
        "commit_message",
        "release_title",
        "release_notes_path",
        "release_notes_sha256",
        "public_paths",
        "expected_test_gate",
        "authority",
    }
    missing = sorted(required - set(plan))
    if missing:
        raise WorkflowError("plan missing fields: " + ", ".join(missing))

    if plan.get("schema_version") != SCHEMA_VERSION:
        raise WorkflowError(f"plan schema_version must be {SCHEMA_VERSION}")
    if plan.get("report_type") != PLAN_REPORT_TYPE:
        raise WorkflowError(f"plan report_type must be {PLAN_REPORT_TYPE}")

    workflow_id = plan.get("workflow_id")
    if not isinstance(workflow_id, str) or not SAFE_ID_RE.fullmatch(workflow_id):
        raise WorkflowError("workflow_id is invalid")

    base = plan.get("expected_base_commit")
    if not isinstance(base, str) or not COMMIT_RE.fullmatch(base):
        raise WorkflowError("expected_base_commit must be 40 lowercase hex")

    for field in ("target_version", "previous_version"):
        value = plan.get(field)
        if not isinstance(value, str) or not VERSION_RE.fullmatch(value):
            raise WorkflowError(f"{field} must look like vMAJOR.MINOR.PATCH")

    github_repo = plan.get("github_repo")
    if not isinstance(github_repo, str) or not REPO_RE.fullmatch(github_repo):
        raise WorkflowError("github_repo must use OWNER/REPO format")

    for field in (
        "expected_branch",
        "remote",
        "commit_message",
        "release_title",
        "release_notes_path",
    ):
        value = plan.get(field)
        if not isinstance(value, str) or not value.strip():
            raise WorkflowError(f"{field} must be non-empty text")

    notes_hash = plan.get("release_notes_sha256")
    if not isinstance(notes_hash, str) or not SHA256_RE.fullmatch(notes_hash):
        raise WorkflowError("release_notes_sha256 must be 64 lowercase hex")

    raw_paths = plan.get("public_paths")
    if not isinstance(raw_paths, list) or not raw_paths:
        raise WorkflowError("public_paths must be a non-empty list")

    normalized_paths: List[str] = []
    for index, raw in enumerate(raw_paths):
        normalized = normalize_relative_path(raw)
        if normalized is None or normalized == ".":
            raise WorkflowError(f"public_paths[{index}] is invalid")
        if is_private_path(normalized):
            raise WorkflowError(
                f"public_paths[{index}] points to blocked context: {normalized}"
            )
        normalized_paths.append(normalized)

    if len(normalized_paths) != len(set(normalized_paths)):
        raise WorkflowError("public_paths contains duplicates")

    expected = plan.get("expected_test_gate")
    if not isinstance(expected, dict):
        raise WorkflowError("expected_test_gate must be an object")
    for field in ("suite_count", "test_count", "focused_suite", "focused_tests"):
        if field not in expected:
            raise WorkflowError(f"expected_test_gate missing {field}")
    if not isinstance(expected["suite_count"], int) or expected["suite_count"] <= 0:
        raise WorkflowError("expected suite_count must be positive")
    if not isinstance(expected["test_count"], int) or expected["test_count"] <= 0:
        raise WorkflowError("expected test_count must be positive")
    if not isinstance(expected["focused_suite"], str) or not expected["focused_suite"]:
        raise WorkflowError("expected focused_suite must be non-empty")
    if not isinstance(expected["focused_tests"], int) or expected["focused_tests"] <= 0:
        raise WorkflowError("expected focused_tests must be positive")

    authority = plan.get("authority")
    required_authority = {
        "plan_is_not_permission": True,
        "operation_tokens_required": True,
        "test_results_are_evidence_only": True,
        "guard_reports_are_evidence_only": True,
        "release_mutations_are_explicit": True,
    }
    if not isinstance(authority, dict):
        raise WorkflowError("plan authority must be an object")
    for key, expected_value in required_authority.items():
        if authority.get(key) is not expected_value:
            raise WorkflowError(f"plan authority requires {key}=true")

    result = dict(plan)
    result["public_paths"] = sorted(normalized_paths)
    return result


def validate_tokens(args: argparse.Namespace) -> None:
    expected = {
        "workflow_token": RUN_TOKEN,
        "git_plan_token": "PLAN_BETA_GIT_OPERATION",
        "git_stage_token": "APPROVE_BETA_GIT_STAGE",
        "git_commit_token": "APPROVE_BETA_GIT_COMMIT",
        "git_push_token": "APPROVE_BETA_GIT_PUSH",
        "tag_create_token": TAG_CREATE_TOKEN,
        "tag_push_token": TAG_PUSH_TOKEN,
        "release_publish_token": RELEASE_PUBLISH_TOKEN,
        "latest_promotion_token": LATEST_PROMOTION_TOKEN,
    }
    mismatches = [
        field
        for field, required in expected.items()
        if getattr(args, field, None) != required
    ]
    if mismatches:
        raise WorkflowError(
            "missing or invalid explicit approval tokens: "
            + ", ".join(sorted(mismatches))
        )
    if not args.confirm_run:
        raise WorkflowError("--confirm-run is required")
    if not args.allow_network:
        raise WorkflowError("--allow-network is required for unified delivery")


def validate_test_summary(
    closure_report: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> Dict[str, Any]:
    test_gate = closure_report.get("test_gate")
    if not isinstance(test_gate, dict):
        raise WorkflowError("closure report has no test_gate")

    summary = test_gate.get("summary")
    if not isinstance(summary, dict):
        raise WorkflowError("closure report has no canonical test summary")

    required = {
        "discovered_suite_count": expected["suite_count"],
        "selected_suite_count": expected["suite_count"],
        "passed_suite_count": expected["suite_count"],
        "failed_suite_count": 0,
        "test_count": expected["test_count"],
        "failure_count": 0,
        "error_count": 0,
        "timeout_count": 0,
    }

    for key, expected_value in required.items():
        actual = summary.get(key)
        if actual != expected_value:
            raise WorkflowError(
                f"canonical test summary mismatch for {key}: "
                f"expected {expected_value}, found {actual}"
            )

    if test_gate.get("passed") is not True:
        raise WorkflowError("closure report says canonical test gate failed")
    if test_gate.get("head_unchanged") is not True:
        raise WorkflowError("canonical test gate changed HEAD")

    return summary


def load_closure_report(path: Path) -> Dict[str, Any]:
    report = read_json(path, "closure report")
    if report.get("report_type") != CLOSURE_REPORT_TYPE:
        raise WorkflowError("closure report type mismatch")
    status = report.get("status_code")
    if not isinstance(status, str) or not status:
        raise WorkflowError("closure report has no status_code")
    return report


def expected_action(status_code: str) -> str:
    mapping = {
        "BLOCKED_BRANCH_NOT_SYNCED": "push_main",
        "NEEDS_TAG_CREATION": "create_tag",
        "NEEDS_TAG_PUBLICATION": "push_tag",
        "NEEDS_RELEASE_PUBLICATION": "publish_release",
        "NEEDS_LATEST_PROMOTION": "promote_latest",
        "RELEASE_CLOSED": "complete",
    }
    try:
        return mapping[status_code]
    except KeyError as exc:
        raise WorkflowError(f"unexpected closure status: {status_code}") from exc


def validate_closure_rc_status(
    report: Mapping[str, Any],
    returncode: int,
) -> None:
    status = report.get("status_code")
    release_closed = report.get("release_closed")

    if status == "RELEASE_CLOSED":
        if returncode != 0 or release_closed is not True:
            raise WorkflowError(
                "RELEASE_CLOSED requires RC=0 and release_closed=true"
            )
        return

    if status not in EXPECTED_STATES:
        raise WorkflowError(f"unexpected closure status: {status}")

    if returncode != 1 or release_closed is not False:
        raise WorkflowError(
            f"{status} requires RC=1 and release_closed=false"
        )


def inspect_cached_test_evidence(
    repo_root: Path,
    plan: Mapping[str, Any],
    head: str,
) -> Dict[str, Any]:
    path = (
        repo_root
        / "sandbox"
        / "reports"
        / f"{plan['workflow_id']}-closure-tests.json"
    ).resolve()

    result: Dict[str, Any] = {
        "path": str(path),
        "state": "absent",
        "reusable": False,
        "reason": "No cached closure test evidence exists.",
    }

    if not path.is_file():
        return result

    try:
        report = load_closure_report(path)
        summary = validate_test_summary(
            report,
            plan["expected_test_gate"],
        )
    except (WorkflowError, json.JSONDecodeError, OSError) as exc:
        result.update(
            {
                "state": "corrupt",
                "reason": str(exc),
            }
        )
        return result

    report_head = (report.get("git") or {}).get("head")
    test_head = (report.get("test_gate") or {}).get("head_after")
    if report_head != head or test_head != head:
        result.update(
            {
                "state": "stale",
                "reason": (
                    "Cached evidence references a different HEAD."
                ),
                "report_head": report_head,
                "test_head": test_head,
                "summary": summary,
            }
        )
        return result

    result.update(
        {
            "state": "valid",
            "reusable": True,
            "reason": "Cached canonical test evidence matches current HEAD.",
            "report_head": report_head,
            "test_head": test_head,
            "summary": summary,
        }
    )
    return result


def derive_recovery_state(snapshot: Mapping[str, Any]) -> Dict[str, Any]:
    branch = snapshot.get("branch")
    expected_branch = snapshot.get("expected_branch")
    head = snapshot.get("head")
    base = snapshot.get("expected_base_commit")
    clean = snapshot.get("working_tree_clean") is True
    scope_matches = snapshot.get("scope_matches") is True
    aligned_commit = snapshot.get("release_commit_aligned") is True
    tracking = snapshot.get("tracking") or {}
    behind = tracking.get("behind")
    ahead = tracking.get("ahead")
    network = snapshot.get("network_requested") is True
    remote_branch_head = snapshot.get("remote_branch_head")
    local_tag = snapshot.get("local_tag") or {}
    remote_tag = snapshot.get("remote_tag") or {}
    release = snapshot.get("release") or {}

    def state(
        code: str,
        action: str,
        *,
        resumable: bool,
        closed: bool = False,
        blocked: bool = False,
    ) -> Dict[str, Any]:
        return {
            "status_code": code,
            "next_action": action,
            "safe_to_resume": resumable,
            "release_closed": closed,
            "blocked": blocked,
        }

    if branch != expected_branch:
        return state(
            "BLOCKED_BRANCH_MISMATCH",
            f"Checkout {expected_branch} and re-run status.",
            resumable=False,
            blocked=True,
        )

    if head == base:
        if clean:
            return state(
                "NEEDS_PACKAGE_APPLY",
                "Extract and apply the reviewed release package.",
                resumable=False,
            )
        if not scope_matches:
            return state(
                "BLOCKED_SCOPE_MISMATCH",
                "Restore the exact reviewed public scope before delivery.",
                resumable=False,
                blocked=True,
            )
        return state(
            "NEEDS_GIT_DELIVERY",
            "Run the unified supervised release workflow.",
            resumable=True,
        )

    if not aligned_commit:
        return state(
            "BLOCKED_COMMIT_DIVERGENCE",
            "HEAD is not the exact planned release commit.",
            resumable=False,
            blocked=True,
        )

    if not clean:
        return state(
            "BLOCKED_WORKING_TREE",
            "Clean or review unexpected repository changes.",
            resumable=False,
            blocked=True,
        )

    if not isinstance(behind, int) or not isinstance(ahead, int):
        return state(
            "BLOCKED_TRACKING_UNKNOWN",
            "Repair or configure the local tracking reference.",
            resumable=False,
            blocked=True,
        )

    if not network:
        if behind > 0 or ahead > 1:
            return state(
                "BLOCKED_BRANCH_DIVERGENCE",
                "Resolve branch divergence without force operations.",
                resumable=False,
                blocked=True,
            )

        if ahead == 1:
            return state(
                "NEEDS_BRANCH_PUSH",
                "Resume the workflow to publish the exact release commit.",
                resumable=True,
            )

        return state(
            "NEEDS_REMOTE_INSPECTION",
            "Re-run --status with --allow-network for remote release state.",
            resumable=True,
        )

    if remote_branch_head == base:
        return state(
            "NEEDS_BRANCH_PUSH",
            "Resume the workflow to publish the exact release commit.",
            resumable=True,
        )

    if remote_branch_head != head:
        return state(
            "BLOCKED_REMOTE_BRANCH_DIVERGENCE",
            "Remote main differs from both base and release commit.",
            resumable=False,
            blocked=True,
        )

    if local_tag.get("exists") is not True:
        return state(
            "NEEDS_TAG_CREATION",
            "Resume the workflow to create the annotated release tag.",
            resumable=True,
        )

    if (
        local_tag.get("annotated") is not True
        or local_tag.get("target_matches_head") is not True
    ):
        return state(
            "BLOCKED_LOCAL_TAG_DIVERGENCE",
            "Existing local tag is lightweight or targets another commit.",
            resumable=False,
            blocked=True,
        )

    if remote_tag.get("exists") is not True:
        return state(
            "NEEDS_TAG_PUBLICATION",
            "Resume the workflow to publish the aligned annotated tag.",
            resumable=True,
        )

    if (
        remote_tag.get("target_matches_head") is not True
        or remote_tag.get("object_matches_local") is not True
    ):
        return state(
            "BLOCKED_REMOTE_TAG_DIVERGENCE",
            "Remote tag object or target differs from the local tag.",
            resumable=False,
            blocked=True,
        )

    if release.get("exists") is not True:
        return state(
            "NEEDS_RELEASE_PUBLICATION",
            "Resume the workflow to publish the GitHub Release.",
            resumable=True,
        )

    if (
        release.get("tag_matches") is not True
        or release.get("title_matches") is not True
        or release.get("draft") is not False
        or release.get("prerelease") is not False
    ):
        return state(
            "BLOCKED_RELEASE_DIVERGENCE",
            "Existing GitHub Release metadata differs from the plan.",
            resumable=False,
            blocked=True,
        )

    if release.get("latest") is not True:
        return state(
            "NEEDS_LATEST_PROMOTION",
            "Resume the workflow to promote the release to Latest.",
            resumable=True,
        )

    return state(
        "RELEASE_CLOSED",
        "No release action is required.",
        resumable=True,
        closed=True,
    )


def inspect_release_status(
    repo_root: Path,
    plan: Mapping[str, Any],
    *,
    allow_network: bool,
    runner: Callable[[Sequence[str], Path, int], CommandResult] = default_command_runner,
) -> Dict[str, Any]:
    branch = git_stdout(runner, repo_root, "branch", "--show-current")
    head = git_stdout(runner, repo_root, "rev-parse", "HEAD")
    base = plan["expected_base_commit"]
    status_text = git_stdout(
        runner,
        repo_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=normal",
    )
    clean = status_text == ""

    tracking_ref = f"{plan['remote']}/{plan['expected_branch']}"
    try:
        tracking = parse_count_pair(
            git_stdout(
                runner,
                repo_root,
                "rev-list",
                "--left-right",
                "--count",
                f"{tracking_ref}...HEAD",
            )
        )
    except WorkflowError:
        tracking = (None, None)

    actual_scope = collect_scope(runner, repo_root)
    scope_matches = actual_scope == plan["public_paths"]

    release_commit_aligned = False
    if head != base:
        try:
            parent = git_stdout(runner, repo_root, "rev-parse", f"{head}^")
            subject = git_stdout(
                runner,
                repo_root,
                "log",
                "-1",
                "--format=%s",
            )
            paths = collect_commit_paths(runner, repo_root, head)
            release_commit_aligned = (
                parent == base
                and subject == plan["commit_message"]
                and paths == plan["public_paths"]
            )
        except WorkflowError:
            release_commit_aligned = False

    tag = plan["target_version"]
    local_tag: Dict[str, Any] = {
        "exists": False,
        "annotated": False,
        "target_matches_head": False,
    }
    local_tag_object: Optional[str] = None
    tag_probe = runner(
        ["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"],
        repo_root,
        60,
    )
    if tag_probe.returncode == 0:
        local_tag_object = git_stdout(runner, repo_root, "rev-parse", tag)
        local_target = git_stdout(
            runner,
            repo_root,
            "rev-parse",
            f"{tag}^{{}}",
        )
        tag_type = git_stdout(runner, repo_root, "cat-file", "-t", tag)
        local_tag = {
            "exists": True,
            "object": local_tag_object,
            "target": local_target,
            "annotated": tag_type == "tag",
            "target_matches_head": local_target == head,
        }
    elif tag_probe.returncode not in (0, 1):
        raise WorkflowError("unable to inspect local target tag")

    remote_branch_head: Optional[str] = None
    remote_tag: Dict[str, Any] = {
        "exists": False,
        "target_matches_head": False,
        "object_matches_local": False,
    }
    release: Dict[str, Any] = {
        "exists": False,
        "tag_matches": False,
        "title_matches": False,
        "draft": None,
        "prerelease": None,
        "latest": None,
    }
    remote_error: Optional[str] = None

    if allow_network:
        try:
            require_command(
                runner(
                    [
                        "gh",
                        "auth",
                        "status",
                        "--hostname",
                        "github.com",
                    ],
                    repo_root,
                    120,
                ),
                "GitHub authentication status",
            )

            branch_result = require_command(
                runner(
                    [
                        "git",
                        "ls-remote",
                        plan["remote"],
                        f"refs/heads/{plan['expected_branch']}",
                    ],
                    repo_root,
                    120,
                ),
                "remote branch status",
            )
            if branch_result:
                remote_branch_head = branch_result.split()[0]

            tag_result = require_command(
                runner(
                    [
                        "git",
                        "ls-remote",
                        plan["remote"],
                        f"refs/tags/{tag}",
                        f"refs/tags/{tag}^{{}}",
                    ],
                    repo_root,
                    120,
                ),
                "remote tag status",
            )
            refs: Dict[str, str] = {}
            for line in tag_result.splitlines():
                parts = line.split()
                if len(parts) == 2:
                    refs[parts[1]] = parts[0]
            remote_object = refs.get(f"refs/tags/{tag}")
            remote_target = refs.get(f"refs/tags/{tag}^{{}}")
            remote_tag = {
                "exists": remote_object is not None,
                "object": remote_object,
                "target": remote_target,
                "target_matches_head": remote_target == head,
                "object_matches_local": (
                    local_tag_object is not None
                    and remote_object == local_tag_object
                ),
            }

            view_result = runner(
                [
                    "gh",
                    "release",
                    "view",
                    tag,
                    "--repo",
                    plan["github_repo"],
                    "--json",
                    "tagName,name,isDraft,isPrerelease,publishedAt,url",
                ],
                repo_root,
                120,
            )
            if view_result.returncode == 0:
                view = json.loads(view_result.stdout)
                list_result = require_command(
                    runner(
                        [
                            "gh",
                            "release",
                            "list",
                            "--repo",
                            plan["github_repo"],
                            "--limit",
                            "100",
                            "--json",
                            (
                                "tagName,name,isLatest,isDraft,"
                                "isPrerelease,publishedAt"
                            ),
                        ],
                        repo_root,
                        120,
                    ),
                    "GitHub Release list status",
                )
                listing = json.loads(list_result)
                matches = [
                    item
                    for item in listing
                    if item.get("tagName") == tag
                ]
                release = {
                    "exists": True,
                    "tag": view.get("tagName"),
                    "name": view.get("name"),
                    "url": view.get("url"),
                    "published_at": view.get("publishedAt"),
                    "tag_matches": view.get("tagName") == tag,
                    "title_matches": (
                        view.get("name") == plan["release_title"]
                    ),
                    "draft": view.get("isDraft"),
                    "prerelease": view.get("isPrerelease"),
                    "latest": (
                        len(matches) == 1
                        and matches[0].get("isLatest") is True
                    ),
                }
            elif view_result.returncode != 1:
                raise WorkflowError(
                    "GitHub Release inspection failed with "
                    f"RC={view_result.returncode}"
                )
        except (
            WorkflowError,
            json.JSONDecodeError,
            IndexError,
        ) as exc:
            remote_error = str(exc)

    evidence = inspect_cached_test_evidence(repo_root, plan, head)

    snapshot = {
        "branch": branch,
        "expected_branch": plan["expected_branch"],
        "head": head,
        "expected_base_commit": base,
        "working_tree_clean": clean,
        "scope_matches": scope_matches,
        "actual_scope": actual_scope,
        "release_commit_aligned": release_commit_aligned,
        "tracking": {
            "behind": tracking[0],
            "ahead": tracking[1],
        },
        "network_requested": allow_network,
        "remote_branch_head": remote_branch_head,
        "local_tag": local_tag,
        "remote_tag": remote_tag,
        "release": release,
    }

    if allow_network and remote_error:
        derived = {
            "status_code": "BLOCKED_REMOTE_INSPECTION",
            "next_action": "Resolve read-only remote inspection failure.",
            "safe_to_resume": False,
            "release_closed": False,
            "blocked": True,
        }
    else:
        derived = derive_recovery_state(snapshot)

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": STATUS_REPORT_TYPE,
        "generated_at": utc_now(),
        "workflow_id": plan["workflow_id"],
        "target_version": plan["target_version"],
        "status": (
            "blocked"
            if derived["blocked"]
            else "closed"
            if derived["release_closed"]
            else "incomplete"
        ),
        **derived,
        "snapshot": snapshot,
        "test_evidence": evidence,
        "remote_inspection": {
            "requested": allow_network,
            "error": remote_error,
            "read_only": True,
        },
        "boundaries": {
            **BOUNDARIES,
            "git_mutations": "blocked_in_status_mode",
            "network_access": (
                "read_only_queries_only"
                if allow_network
                else "blocked"
            ),
        },
        "authority": {
            "status_is_evidence_only": True,
            "status_does_not_authorize_resume": True,
            "resume_requires_full_explicit_tokens": True,
            "no_mutation_was_performed": True,
        },
    }


class SupervisedReleaseWorkflow:
    def __init__(
        self,
        *,
        repo_root: Path,
        plan: Dict[str, Any],
        args: argparse.Namespace,
        runner: Callable[[Sequence[str], Path, int], CommandResult] = default_command_runner,
    ) -> None:
        self.repo_root = repo_root
        self.plan = plan
        self.args = args
        self.runner = runner
        self.workflow_id = plan["workflow_id"]
        self.report_dir = (repo_root / "sandbox" / "reports").resolve()
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.beta_plan = repo_root / "sandbox" / f"{self.workflow_id}-beta-git-plan.json"
        self.test_evidence = self.report_dir / f"{self.workflow_id}-closure-tests.json"
        self.transitions: List[Dict[str, Any]] = []
        self.command_logs: List[Dict[str, Any]] = []
        self.current_head: Optional[str] = None
        self.test_summary: Optional[Dict[str, Any]] = None

    def run_logged(
        self,
        label: str,
        command: Sequence[str],
        *,
        timeout: int = 900,
        expected_rcs: Iterable[int] = (0,),
    ) -> CommandResult:
        result = self.runner(command, self.repo_root, timeout)
        log_path = self.report_dir / f"{self.workflow_id}-{len(self.command_logs)+1:02d}-{label}.log"
        log_path.write_text(
            "COMMAND\n"
            + json.dumps(result.command)
            + "\n\nSTDOUT\n"
            + result.stdout
            + "\n\nSTDERR\n"
            + result.stderr
            + f"\n\nRETURN_CODE\n{result.returncode}\n",
            encoding="utf-8",
            newline="\n",
        )
        self.command_logs.append(
            {
                "label": label,
                "command": result.command,
                "returncode": result.returncode,
                "timed_out": result.timed_out,
                "log_path": str(log_path),
            }
        )
        if result.timed_out or result.returncode not in set(expected_rcs):
            raise WorkflowError(
                f"{label} returned RC={result.returncode}; "
                f"see {log_path}"
            )
        return result

    def record_transition(
        self,
        *,
        status_code: str,
        action: str,
        evidence_path: Path,
    ) -> None:
        self.transitions.append(
            {
                "observed_at": utc_now(),
                "status_code": status_code,
                "action": action,
                "evidence_path": str(evidence_path),
                "head": self.current_head,
            }
        )

    def preflight(self) -> str:
        if shutil.which("git") is None:
            raise WorkflowError("git is required")

        for relative in (
            "tools/beta_runtime/run_konoha_beta.py",
            "tools/release_closure/check_release_closure.py",
            "tools/release_testing/run_release_tests.py",
        ):
            if not (self.repo_root / relative).is_file():
                raise WorkflowError(f"required component missing: {relative}")

        branch = git_stdout(self.runner, self.repo_root, "branch", "--show-current")
        if branch != self.plan["expected_branch"]:
            raise WorkflowError(
                f"expected branch {self.plan['expected_branch']}, found {branch}"
            )

        head = git_stdout(self.runner, self.repo_root, "rev-parse", "HEAD")
        base = self.plan["expected_base_commit"]
        tracking_ref = (
            f"{self.plan['remote']}/{self.plan['expected_branch']}"
        )
        tracked_head = git_stdout(
            self.runner,
            self.repo_root,
            "rev-parse",
            "--verify",
            tracking_ref,
        )
        behind, ahead = parse_count_pair(
            git_stdout(
                self.runner,
                self.repo_root,
                "rev-list",
                "--left-right",
                "--count",
                f"{tracking_ref}...HEAD",
            )
        )
        previous_target = git_stdout(
            self.runner,
            self.repo_root,
            "rev-parse",
            f"{self.plan['previous_version']}^{{}}",
        )
        if previous_target != base:
            raise WorkflowError("previous version does not target expected base")

        notes_relative, notes_path = resolve_repo_file(
            self.repo_root,
            self.plan["release_notes_path"],
            "release_notes_path",
            allow_sandbox=True,
        )
        if not notes_relative.startswith("sandbox/"):
            raise WorkflowError("release notes must stay under sandbox/")
        if sha256_file(notes_path) != self.plan["release_notes_sha256"]:
            raise WorkflowError("release notes SHA-256 mismatch")

        if head == base:
            if tracked_head != base or behind != 0 or ahead != 0:
                raise WorkflowError(
                    "expected base is not synchronized with remote tracking"
                )
            require_command(
                self.runner(
                    ["git", "diff", "--check"],
                    self.repo_root,
                    120,
                ),
                "git diff --check",
            )
            actual_scope = collect_scope(self.runner, self.repo_root)
            if actual_scope != self.plan["public_paths"]:
                raise WorkflowError(
                    "public scope mismatch: expected "
                    + json.dumps(self.plan["public_paths"])
                    + ", found "
                    + json.dumps(actual_scope)
                )
            return "needs_commit"

        parent = git_stdout(self.runner, self.repo_root, "rev-parse", f"{head}^")
        subject = git_stdout(self.runner, self.repo_root, "log", "-1", "--format=%s")
        commit_paths = collect_commit_paths(self.runner, self.repo_root, head)
        status = git_stdout(
            self.runner,
            self.repo_root,
            "status",
            "--porcelain=v1",
            "--untracked-files=normal",
        )

        if (
            parent == base
            and subject == self.plan["commit_message"]
            and commit_paths == self.plan["public_paths"]
            and status == ""
            and behind == 0
            and ahead in {0, 1}
            and tracked_head in {base, head}
        ):
            self.current_head = head
            return "resume_committed"

        raise WorkflowError("HEAD is neither expected base nor aligned release commit")

    def create_commit(self) -> None:
        paths_csv = ",".join(self.plan["public_paths"])

        self.run_logged(
            "git-plan",
            [
                sys.executable,
                "tools/beta_runtime/run_konoha_beta.py",
                "git-plan",
                "--repo-root",
                ".",
                "--plan-id",
                self.workflow_id,
                "--paths",
                paths_csv,
                "--commit-message",
                self.plan["commit_message"],
                "--branch",
                self.plan["expected_branch"],
                "--remote",
                self.plan["remote"],
                "--output",
                str(self.beta_plan),
                "--confirm-plan",
                "--approval-token",
                self.args.git_plan_token,
                "--force",
            ],
            timeout=180,
        )

        self.run_logged(
            "git-stage",
            [
                sys.executable,
                "tools/beta_runtime/run_konoha_beta.py",
                "git-stage",
                "--plan",
                str(self.beta_plan),
                "--confirm-stage",
                "--approval-token",
                self.args.git_stage_token,
            ],
            timeout=180,
        )

        staged = git_stdout(
            self.runner,
            self.repo_root,
            "diff",
            "--cached",
            "--name-only",
        )
        staged_paths = sorted(line for line in staged.splitlines() if line)
        if staged_paths != self.plan["public_paths"]:
            raise WorkflowError("staged scope differs from plan")

        require_command(
            self.runner(
                ["git", "diff", "--cached", "--check"],
                self.repo_root,
                120,
            ),
            "git diff --cached --check",
        )

        self.run_logged(
            "git-commit",
            [
                sys.executable,
                "tools/beta_runtime/run_konoha_beta.py",
                "git-commit",
                "--plan",
                str(self.beta_plan),
                "--confirm-commit",
                "--approval-token",
                self.args.git_commit_token,
            ],
            timeout=180,
        )

        head = git_stdout(self.runner, self.repo_root, "rev-parse", "HEAD")
        parent = git_stdout(self.runner, self.repo_root, "rev-parse", "HEAD^")
        subject = git_stdout(self.runner, self.repo_root, "log", "-1", "--format=%s")
        commit_paths = collect_commit_paths(self.runner, self.repo_root, head)

        if parent != self.plan["expected_base_commit"]:
            raise WorkflowError("release commit parent mismatch")
        if subject != self.plan["commit_message"]:
            raise WorkflowError("release commit subject mismatch")
        if commit_paths != self.plan["public_paths"]:
            raise WorkflowError("release commit scope mismatch")
        if git_stdout(
            self.runner,
            self.repo_root,
            "status",
            "--porcelain=v1",
            "--untracked-files=normal",
        ):
            raise WorkflowError("working tree not clean after commit")

        self.current_head = head

    def ensure_beta_plan(self) -> None:
        if self.beta_plan.is_file():
            return

        paths_csv = ",".join(self.plan["public_paths"])
        self.run_logged(
            "git-plan-resume",
            [
                sys.executable,
                "tools/beta_runtime/run_konoha_beta.py",
                "git-plan",
                "--repo-root",
                ".",
                "--plan-id",
                self.workflow_id,
                "--paths",
                paths_csv,
                "--commit-message",
                self.plan["commit_message"],
                "--branch",
                self.plan["expected_branch"],
                "--remote",
                self.plan["remote"],
                "--output",
                str(self.beta_plan),
                "--confirm-plan",
                "--approval-token",
                self.args.git_plan_token,
                "--force",
            ],
            timeout=180,
        )

    def run_initial_closure_guard(self) -> Tuple[Dict[str, Any], Path]:
        if self.test_evidence.is_file():
            try:
                existing = load_closure_report(self.test_evidence)
                self.test_summary = validate_test_summary(
                    existing,
                    self.plan["expected_test_gate"],
                )
                if existing.get("git", {}).get("head") != self.current_head:
                    raise WorkflowError(
                        "existing closure test evidence HEAD mismatch"
                    )
                test_gate = existing.get("test_gate") or {}
                if test_gate.get("head_after") != self.current_head:
                    raise WorkflowError(
                        "existing closure test evidence is stale"
                    )

                refreshed, refreshed_path = self.run_reused_closure_guard(
                    self.test_evidence,
                    0,
                )
                return refreshed, refreshed_path
            except (WorkflowError, json.JSONDecodeError):
                self.test_summary = None

        result = self.run_logged(
            "closure-tests",
            [
                sys.executable,
                "tools/release_closure/check_release_closure.py",
                "--repo-root",
                ".",
                "--target-version",
                self.plan["target_version"],
                "--expected-branch",
                self.plan["expected_branch"],
                "--remote",
                self.plan["remote"],
                "--github-repo",
                self.plan["github_repo"],
                "--run-tests",
                "--allow-network",
                "--output",
                str(self.test_evidence),
                "--force",
            ],
            timeout=self.args.test_timeout,
            expected_rcs=(0, 1),
        )
        report = load_closure_report(self.test_evidence)
        validate_closure_rc_status(report, result.returncode)
        self.test_summary = validate_test_summary(
            report,
            self.plan["expected_test_gate"],
        )
        if report.get("git", {}).get("head") != self.current_head:
            raise WorkflowError("closure test evidence HEAD mismatch")
        return report, self.test_evidence

    def run_reused_closure_guard(
        self,
        prior_evidence: Path,
        step: int,
    ) -> Tuple[Dict[str, Any], Path]:
        output = self.report_dir / f"{self.workflow_id}-transition-{step:02d}.json"
        result = self.run_logged(
            f"closure-transition-{step:02d}",
            [
                sys.executable,
                "tools/release_closure/check_release_closure.py",
                "--repo-root",
                ".",
                "--target-version",
                self.plan["target_version"],
                "--expected-branch",
                self.plan["expected_branch"],
                "--remote",
                self.plan["remote"],
                "--github-repo",
                self.plan["github_repo"],
                "--test-evidence",
                str(prior_evidence),
                "--allow-network",
                "--output",
                str(output),
                "--force",
            ],
            timeout=240,
            expected_rcs=(0, 1),
        )
        report = load_closure_report(output)
        validate_closure_rc_status(report, result.returncode)
        validate_test_summary(report, self.plan["expected_test_gate"])
        if report.get("git", {}).get("head") != self.current_head:
            raise WorkflowError("transition guard HEAD mismatch")
        return report, output

    def push_main(self) -> None:
        self.ensure_beta_plan()
        behind, ahead = parse_count_pair(
            git_stdout(
                self.runner,
                self.repo_root,
                "rev-list",
                "--left-right",
                "--count",
                f"{self.plan['remote']}/{self.plan['expected_branch']}...HEAD",
            )
        )
        if behind != 0 or ahead != 1:
            raise WorkflowError(
                f"push_main requires behind=0 ahead=1, found {behind}/{ahead}"
            )

        self.run_logged(
            "git-push",
            [
                sys.executable,
                "tools/beta_runtime/run_konoha_beta.py",
                "git-push",
                "--plan",
                str(self.beta_plan),
                "--confirm-push",
                "--approval-token",
                self.args.git_push_token,
                "--allow-network",
            ],
            timeout=240,
        )

        self.run_logged(
            "git-fetch-main",
            [
                "git",
                "fetch",
                self.plan["remote"],
                self.plan["expected_branch"],
                "--quiet",
            ],
            timeout=240,
        )

    def create_tag(self) -> None:
        tag = self.plan["target_version"]
        existing = self.runner(
            ["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"],
            self.repo_root,
            60,
        )
        if existing.returncode == 0:
            target = git_stdout(
                self.runner,
                self.repo_root,
                "rev-parse",
                f"{tag}^{{}}",
            )
            tag_type = git_stdout(
                self.runner,
                self.repo_root,
                "cat-file",
                "-t",
                tag,
            )
            if target != self.current_head or tag_type != "tag":
                raise WorkflowError("existing local tag is not aligned annotated tag")
            return
        if existing.returncode not in (0, 1):
            raise WorkflowError("unable to inspect local tag")

        self.run_logged(
            "tag-create",
            [
                "git",
                "tag",
                "-a",
                tag,
                str(self.current_head),
                "-m",
                self.plan["release_title"],
            ],
            timeout=120,
        )

    def push_tag(self) -> None:
        tag = self.plan["target_version"]
        self.run_logged(
            "tag-push",
            [
                "git",
                "push",
                self.plan["remote"],
                f"refs/tags/{tag}",
            ],
            timeout=240,
        )

    def publish_release(self) -> None:
        _, notes_path = resolve_repo_file(
            self.repo_root,
            self.plan["release_notes_path"],
            "release_notes_path",
            allow_sandbox=True,
        )
        self.run_logged(
            "release-publish",
            [
                "gh",
                "release",
                "create",
                self.plan["target_version"],
                "--repo",
                self.plan["github_repo"],
                "--verify-tag",
                "--latest",
                "--title",
                self.plan["release_title"],
                "--notes-file",
                str(notes_path),
            ],
            timeout=240,
        )

    def promote_latest(self) -> None:
        self.run_logged(
            "release-latest",
            [
                "gh",
                "release",
                "edit",
                self.plan["target_version"],
                "--repo",
                self.plan["github_repo"],
                "--latest",
            ],
            timeout=240,
        )

    def verify_final(self, final_report: Mapping[str, Any]) -> Dict[str, Any]:
        if final_report.get("status_code") != "RELEASE_CLOSED":
            raise WorkflowError("final guard did not report RELEASE_CLOSED")
        if final_report.get("release_closed") is not True:
            raise WorkflowError("final guard release_closed is not true")

        head = git_stdout(self.runner, self.repo_root, "rev-parse", "HEAD")
        remote_head_output = require_command(
            self.runner(
                [
                    "git",
                    "ls-remote",
                    self.plan["remote"],
                    f"refs/heads/{self.plan['expected_branch']}",
                ],
                self.repo_root,
                120,
            ),
            "remote branch verification",
        )
        remote_head = remote_head_output.split()[0] if remote_head_output else None

        tag = self.plan["target_version"]
        local_tag_object = git_stdout(self.runner, self.repo_root, "rev-parse", tag)
        local_tag_target = git_stdout(
            self.runner,
            self.repo_root,
            "rev-parse",
            f"{tag}^{{}}",
        )
        remote_tags_output = require_command(
            self.runner(
                [
                    "git",
                    "ls-remote",
                    self.plan["remote"],
                    f"refs/tags/{tag}",
                    f"refs/tags/{tag}^{{}}",
                ],
                self.repo_root,
                120,
            ),
            "remote tag verification",
        )
        refs: Dict[str, str] = {}
        for line in remote_tags_output.splitlines():
            parts = line.split()
            if len(parts) == 2:
                refs[parts[1]] = parts[0]

        remote_tag_object = refs.get(f"refs/tags/{tag}")
        remote_tag_target = refs.get(f"refs/tags/{tag}^{{}}")

        release_view = self.run_logged(
            "release-view",
            [
                "gh",
                "release",
                "view",
                tag,
                "--repo",
                self.plan["github_repo"],
                "--json",
                "tagName,name,isDraft,isPrerelease,publishedAt,url",
            ],
            timeout=120,
        )
        release = json.loads(release_view.stdout)

        release_list = self.run_logged(
            "release-list",
            [
                "gh",
                "release",
                "list",
                "--repo",
                self.plan["github_repo"],
                "--limit",
                "100",
                "--json",
                "tagName,name,isLatest,isDraft,isPrerelease,publishedAt",
            ],
            timeout=120,
        )
        listing = json.loads(release_list.stdout)
        matches = [item for item in listing if item.get("tagName") == tag]

        checks = {
            "head_matches": head == self.current_head,
            "remote_head_matches": remote_head == self.current_head,
            "local_tag_target_matches": local_tag_target == self.current_head,
            "remote_tag_target_matches": remote_tag_target == self.current_head,
            "tag_object_matches": local_tag_object == remote_tag_object,
            "release_entry_unique": len(matches) == 1,
            "release_title_matches": release.get("name") == self.plan["release_title"],
            "release_tag_matches": release.get("tagName") == tag,
            "release_not_draft": release.get("isDraft") is False,
            "release_not_prerelease": release.get("isPrerelease") is False,
            "release_latest": bool(matches and matches[0].get("isLatest") is True),
            "working_tree_clean": git_stdout(
                self.runner,
                self.repo_root,
                "status",
                "--porcelain=v1",
                "--untracked-files=normal",
            )
            == "",
        }
        failed = sorted(key for key, value in checks.items() if not value)
        if failed:
            raise WorkflowError("final direct verification failed: " + ", ".join(failed))

        behind, ahead = parse_count_pair(
            git_stdout(
                self.runner,
                self.repo_root,
                "rev-list",
                "--left-right",
                "--count",
                f"{self.plan['remote']}/{self.plan['expected_branch']}...HEAD",
            )
        )
        if behind != 0 or ahead != 0:
            raise WorkflowError("final tracking is not synchronized")

        return {
            "head": head,
            "remote_head": remote_head,
            "local_tag_object": local_tag_object,
            "remote_tag_object": remote_tag_object,
            "local_tag_target": local_tag_target,
            "remote_tag_target": remote_tag_target,
            "tracking": {"behind": behind, "ahead": ahead},
            "release": release,
            "checks": checks,
        }

    def execute(self) -> Dict[str, Any]:
        validate_tokens(self.args)

        if shutil.which("git") is None:
            raise WorkflowError("git is required")
        if shutil.which("gh") is None:
            raise WorkflowError("GitHub CLI is required")

        self.run_logged(
            "git-fetch-preflight",
            [
                "git",
                "fetch",
                self.plan["remote"],
                self.plan["expected_branch"],
                "--quiet",
            ],
            timeout=240,
        )
        self.run_logged(
            "gh-auth",
            [
                "gh",
                "auth",
                "status",
                "--hostname",
                "github.com",
            ],
            timeout=120,
        )

        mode = self.preflight()

        if mode == "needs_commit":
            self.create_commit()
        elif self.current_head is None:
            self.current_head = git_stdout(
                self.runner,
                self.repo_root,
                "rev-parse",
                "HEAD",
            )

        initial, evidence = self.run_initial_closure_guard()
        status = initial["status_code"]

        max_transitions = int(self.plan.get("max_transitions", 8))
        for step in range(max_transitions + 1):
            action = expected_action(status)
            self.record_transition(
                status_code=status,
                action=action,
                evidence_path=evidence,
            )

            if action == "complete":
                final_verification = self.verify_final(initial)
                return self.build_report(
                    status="passed",
                    status_code="RELEASE_CLOSED",
                    release_closed=True,
                    final_verification=final_verification,
                )

            if action == "push_main":
                self.push_main()
            elif action == "create_tag":
                self.create_tag()
            elif action == "push_tag":
                self.push_tag()
            elif action == "publish_release":
                self.publish_release()
            elif action == "promote_latest":
                self.promote_latest()
            else:
                raise WorkflowError(f"unsupported action: {action}")

            initial, evidence = self.run_reused_closure_guard(evidence, step + 1)
            status = initial["status_code"]

        raise WorkflowError("maximum supervised transitions exceeded")

    def build_report(
        self,
        *,
        status: str,
        status_code: str,
        release_closed: bool,
        final_verification: Optional[Mapping[str, Any]] = None,
        blocker: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "report_type": REPORT_TYPE,
            "generated_at": utc_now(),
            "workflow_id": self.workflow_id,
            "target_version": self.plan["target_version"],
            "status": status,
            "status_code": status_code,
            "release_closed": release_closed,
            "head": self.current_head,
            "test_gate": {
                "passed": bool(self.test_summary),
                "summary": self.test_summary,
            },
            "transitions": self.transitions,
            "command_logs": self.command_logs,
            "final_verification": final_verification,
            "blocker": blocker,
            "boundaries": BOUNDARIES,
            "authority": {
                "workflow_report_is_evidence_only": True,
                "explicit_operation_tokens_were_required": True,
                "unexpected_rc_or_state_stops_workflow": True,
                "tests_do_not_authorize_release": True,
                "release_closed_requires_direct_verification": True,
            },
        }


def print_status_minimal(report: Mapping[str, Any], output: Path) -> None:
    snapshot = report.get("snapshot") or {}
    tracking = snapshot.get("tracking") or {}
    evidence = report.get("test_evidence") or {}
    remote = report.get("remote_inspection") or {}

    print("KONOHA SUPERVISED RELEASE STATUS")
    print(f"version: {report.get('target_version')}")
    print(f"status_code: {report.get('status_code')}")
    print(f"head: {snapshot.get('head')}")
    print(
        "tracking: "
        f"{tracking.get('behind')} behind / "
        f"{tracking.get('ahead')} ahead"
    )
    print(f"test_evidence: {evidence.get('state')}")
    print(
        "remote_inspection: "
        + (
            "read-only"
            if remote.get("requested")
            else "not requested"
        )
    )
    print(f"safe_to_resume: {report.get('safe_to_resume')}")
    print(f"next_action: {report.get('next_action')}")
    print(f"report: {output}")


def print_minimal(report: Mapping[str, Any], output: Path) -> None:
    final = report.get("final_verification") or {}
    release = final.get("release") or {}
    tests = report.get("test_gate", {}).get("summary") or {}
    tracking = final.get("tracking") or {}

    if report.get("release_closed") is True:
        print("KONOHA UNIFIED SUPERVISED RELEASE GATE")
        print(f"version: {report.get('target_version')}")
        print(f"status_code: {report.get('status_code')}")
        print(f"head: {report.get('head')}")
        print(f"tag_target: {final.get('local_tag_target')}")
        print(f"release: {release.get('url')}")
        print(
            "tests: "
            f"{tests.get('passed_suite_count')}/"
            f"{tests.get('discovered_suite_count')} suites, "
            f"{tests.get('test_count')} tests"
        )
        print(
            "tracking: "
            f"{tracking.get('behind')} behind / "
            f"{tracking.get('ahead')} ahead"
        )
        print("working_tree: clean")
        print(f"report: {output}")
        print("UNIFIED SUPERVISED RELEASE GATE PASSED")
    else:
        print("KONOHA UNIFIED SUPERVISED RELEASE GATE BLOCKED", file=sys.stderr)
        print(f"status_code: {report.get('status_code')}", file=sys.stderr)
        print(f"blocker: {report.get('blocker')}", file=sys.stderr)
        print(f"report: {output}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one supervised Acceptance→Git→Release workflow."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--status",
        action="store_true",
        help="Inspect recovery state without release mutations.",
    )
    parser.add_argument("--test-timeout", type=int, default=1200)

    parser.add_argument("--confirm-run", action="store_true")
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--workflow-token", default="")
    parser.add_argument("--git-plan-token", default="")
    parser.add_argument("--git-stage-token", default="")
    parser.add_argument("--git-commit-token", default="")
    parser.add_argument("--git-push-token", default="")
    parser.add_argument("--tag-create-token", default="")
    parser.add_argument("--tag-push-token", default="")
    parser.add_argument("--release-publish-token", default="")
    parser.add_argument("--latest-promotion-token", default="")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.test_timeout <= 0:
            raise WorkflowError("--test-timeout must be positive")

        repo_root = Path(args.repo_root).resolve()
        plan_path = Path(args.plan)
        if not plan_path.is_absolute():
            plan_path = repo_root / plan_path
        plan_path = plan_path.resolve()

        if not is_relative_to(plan_path, repo_root):
            raise WorkflowError("plan path must stay under repository root")
        relative_plan = plan_path.relative_to(repo_root).as_posix()
        if is_private_path(relative_plan):
            raise WorkflowError("plan path points to blocked private context")

        output = resolve_output(repo_root, args.output)
        plan = validate_plan(read_json(plan_path, "workflow plan"))

        if args.status:
            if shutil.which("git") is None:
                raise WorkflowError("git is required")
            if args.allow_network and shutil.which("gh") is None:
                raise WorkflowError(
                    "GitHub CLI is required for network status"
                )

            report = inspect_release_status(
                repo_root,
                plan,
                allow_network=args.allow_network,
            )
            write_json(output, report, args.force)

            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print_status_minimal(report, output)

            return 1 if report.get("blocked") is True else 0

        workflow = SupervisedReleaseWorkflow(
            repo_root=repo_root,
            plan=plan,
            args=args,
        )

        try:
            report = workflow.execute()
            rc = 0
        except WorkflowError as exc:
            report = workflow.build_report(
                status="blocked",
                status_code="BLOCKED_WORKFLOW",
                release_closed=False,
                blocker=str(exc),
            )
            rc = 1

        write_json(output, report, args.force)

        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_minimal(report, output)
        return rc

    except (WorkflowError, json.JSONDecodeError) as exc:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "report_type": REPORT_TYPE,
            "generated_at": utc_now(),
            "status": "failed",
            "status_code": "BLOCKED_CONFIGURATION",
            "release_closed": False,
            "blocker": str(exc),
            "boundaries": BOUNDARIES,
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("KONOHA UNIFIED RELEASE CONFIGURATION BLOCKED", file=sys.stderr)
            print(f"blocker: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
