#!/usr/bin/env python3
"""Finished local-first terminal product experience for Konoha.

This module provides the user-facing welcome, quickstart, and next-action
experience. It composes existing runtime components without weakening their
approval, network, model, Git, or private-context boundaries.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.product_runtime.konoha_product import init_workspace  # noqa: E402
from tools.version import VERSION  # noqa: E402

SCHEMA_VERSION = "1.0.0"
REPORT_TYPE = "konoha_product_experience_report"
QUICKSTART_TOKEN = "START_KONOHA_QUICKSTART"
DEFAULT_WORKSPACE_ROOT = "sandbox/workspace"
DEFAULT_PERSONA = "calm_mentor"
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")

BOUNDARIES = {
    "arbitrary_shell": "blocked",
    "autonomous_background_agents": "blocked",
    "git_operations": "blocked",
    "model_invocation": "blocked",
    "network_access": "blocked",
    "private_context_access": "blocked",
    "repository_apply": "blocked",
    "quickstart_write": "explicit_token_workspace_only",
}

PERSONAS = {
    "calm_mentor": "Clear guidance with minimal jargon.",
    "strict_auditor": "Direct status, blockers, and evidence.",
    "silent_operator": "Minimal output and explicit next action.",
    "sarcastic_lab_ai": "Dry technical tone without changing safety.",
    "naruto_hokage": "Playful mission-control tone without imitation.",
}


class ProductExperienceError(RuntimeError):
    """Invalid path, state, or explicit user approval."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_under(root: Path, candidate: Path) -> Path:
    root = root.resolve()
    candidate = candidate.resolve()
    if candidate != root and root not in candidate.parents:
        raise ProductExperienceError(f"path escapes allowed root: {candidate}")
    return candidate


def resolve_workspace(repo_root: Path, raw: str) -> Path:
    repo_root = repo_root.resolve()
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    workspace = resolve_under(repo_root, candidate)
    sandbox = (repo_root / "sandbox").resolve()
    resolve_under(sandbox, workspace)
    return workspace


def read_json_object(path: Path, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProductExperienceError(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProductExperienceError(
            f"{label} contains invalid JSON at line {exc.lineno}"
        ) from exc
    if not isinstance(payload, dict):
        raise ProductExperienceError(f"{label} must be a JSON object")
    return payload


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temp.replace(path)


def safe_actor(value: str) -> str:
    value = value.strip()
    if not value:
        raise ProductExperienceError("human actor is required")
    if len(value) > 120:
        raise ProductExperienceError("human actor is too long")
    return value


def choose_latest_mission(missions_root: Path) -> Optional[Path]:
    if not missions_root.is_dir():
        return None
    candidates = [
        child
        for child in missions_root.iterdir()
        if child.is_dir() and SAFE_ID_RE.fullmatch(child.name)
    ]
    if not candidates:
        return None

    def score(path: Path) -> tuple[float, str]:
        timestamps = [path.stat().st_mtime]
        for candidate in (
            path / "mission_manifest.json",
            path / "beta_mission_state.json",
            path / "hokage_shell_session.json",
        ):
            if candidate.is_file():
                timestamps.append(candidate.stat().st_mtime)
        return max(timestamps), path.name

    return max(candidates, key=score)


def json_candidates(root: Path, patterns: Iterable[str]) -> list[Path]:
    found: set[Path] = set()
    for pattern in patterns:
        found.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(found, key=lambda path: path.stat().st_mtime, reverse=True)


def json_status(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {}
    try:
        payload = read_json_object(path, path.name)
    except ProductExperienceError:
        return {"path": str(path), "valid": False}
    payload = dict(payload)
    payload["path"] = str(path)
    payload["valid"] = True
    return payload


def mission_stage(mission_root: Path) -> Dict[str, Any]:
    closure_path = next(
        iter(
            json_candidates(
                mission_root,
                ["reports/*_mission_closure_report.json"],
            )
        ),
        None,
    )
    teachback_path = next(
        iter(
            json_candidates(
                mission_root,
                ["reports/*_teachback_record.json"],
            )
        ),
        None,
    )
    review_path = next(
        iter(
            json_candidates(
                mission_root,
                [
                    "reports/*_konoha_human_review_record.json",
                    "reports/*review*.json",
                ],
            )
        ),
        None,
    )
    execution_path = next(
        iter(
            json_candidates(
                mission_root,
                [
                    "evidence/command_results/*.json",
                    "evidence/agent_invocations/*.json",
                    "reports/*execution*.json",
                ],
            )
        ),
        None,
    )

    closure = json_status(closure_path)
    teachback = json_status(teachback_path)
    review = json_status(review_path)
    execution = json_status(execution_path)

    if closure and (
        closure.get("status") in {"passed", "closed"}
        or closure.get("mission_status") == "closed"
    ):
        return {
            "stage": "MISSION_CLOSED",
            "summary": "The latest mission is closed with recorded evidence.",
            "next_command": "konoha mission start --help",
            "mission_id": mission_root.name,
            "evidence": {
                "closure": closure,
                "teachback": teachback,
                "review": review,
                "execution": execution,
            },
        }

    if teachback:
        result = teachback.get("result")
        if result in {"passed", "skipped"}:
            return {
                "stage": "READY_FOR_MISSION_CLOSE",
                "summary": "Teachback is complete; human closure remains separate.",
                "next_command": "konoha mission close --help",
                "mission_id": mission_root.name,
                "evidence": {
                    "teachback": teachback,
                    "review": review,
                    "execution": execution,
                },
            }
        return {
            "stage": "TEACHBACK_NEEDS_WORK",
            "summary": "Teachback evidence exists but does not permit closure.",
            "next_command": "konoha mission teachback-status --help",
            "mission_id": mission_root.name,
            "evidence": {
                "teachback": teachback,
                "review": review,
                "execution": execution,
            },
        }

    if review:
        decision = (
            review.get("review_decision")
            or (review.get("review") or {}).get("decision")
        )
        if decision == "approved" or review.get("human_approval") is True:
            return {
                "stage": "READY_FOR_TEACHBACK",
                "summary": "Execution has an approved human review.",
                "next_command": "konoha mission teachback-prepare --help",
                "mission_id": mission_root.name,
                "evidence": {
                    "review": review,
                    "execution": execution,
                },
            }
        return {
            "stage": "REVIEW_CHANGES_REQUESTED",
            "summary": "The latest human review requests changes.",
            "next_command": "konoha mission status --help",
            "mission_id": mission_root.name,
            "evidence": {
                "review": review,
                "execution": execution,
            },
        }

    if execution:
        return {
            "stage": "READY_FOR_REVIEW",
            "summary": "Execution evidence exists and needs human review.",
            "next_command": "konoha mission review --help",
            "mission_id": mission_root.name,
            "evidence": {"execution": execution},
        }

    return {
        "stage": "READY_FOR_EXECUTION_OR_PLAN",
        "summary": "The mission exists but has no completed execution evidence.",
        "next_command": "konoha mission plan --help",
        "mission_id": mission_root.name,
        "evidence": {},
    }


def inspect_product(
    repo_root: Path,
    workspace_root: str,
) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    workspace = resolve_workspace(repo_root, workspace_root)
    manifest_path = workspace / "workspace_manifest.json"
    experience_path = workspace / "product_experience.json"

    workspace_initialized = manifest_path.is_file()
    experience_configured = experience_path.is_file()
    latest = choose_latest_mission(workspace / "missions")

    if not workspace_initialized:
        stage = {
            "stage": "QUICKSTART_REQUIRED",
            "summary": "Initialize a supervised local workspace first.",
            "next_command": (
                "konoha quickstart --confirm-quickstart "
                f"--approval-token {QUICKSTART_TOKEN}"
            ),
            "mission_id": None,
            "evidence": {},
        }
    elif latest is None:
        stage = {
            "stage": "READY_FOR_FIRST_MISSION",
            "summary": "Workspace is ready for its first supervised mission.",
            "next_command": "konoha mission start --help",
            "mission_id": None,
            "evidence": {},
        }
    else:
        stage = mission_stage(latest)

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "generated_at": utc_now(),
        "version": VERSION,
        "status": "passed",
        "status_code": stage["stage"],
        "repo_root": str(repo_root),
        "workspace_root": str(workspace),
        "workspace": {
            "initialized": workspace_initialized,
            "manifest_path": str(manifest_path),
            "experience_configured": experience_configured,
            "experience_path": str(experience_path),
        },
        "latest_mission": {
            "mission_id": stage.get("mission_id"),
            "summary": stage["summary"],
            "next_command": stage["next_command"],
            "evidence": stage.get("evidence") or {},
        },
        "boundaries": BOUNDARIES,
        "authority": {
            "status_is_evidence_only": True,
            "next_command_is_not_permission": True,
            "no_approval_token_is_injected": True,
        },
    }


def run_quickstart(
    repo_root: Path,
    workspace_root: str,
    *,
    human_actor: str,
    persona: str,
    confirm_quickstart: bool,
    approval_token: str,
) -> Dict[str, Any]:
    if not confirm_quickstart:
        raise ProductExperienceError(
            "quickstart requires --confirm-quickstart"
        )
    if approval_token != QUICKSTART_TOKEN:
        raise ProductExperienceError(
            f"quickstart requires --approval-token {QUICKSTART_TOKEN}"
        )
    actor = safe_actor(human_actor)
    if persona not in PERSONAS:
        raise ProductExperienceError(
            "persona must be one of: " + ", ".join(sorted(PERSONAS))
        )

    repo_root = repo_root.resolve()
    workspace = resolve_workspace(repo_root, workspace_root)
    relative_workspace = workspace.relative_to(repo_root).as_posix()
    experience_path = workspace / "product_experience.json"

    desired = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "konoha_product_experience_state",
        "version": VERSION,
        "created_by": actor,
        "persona": persona,
        "workspace_root": str(workspace),
        "status": "ready",
        "status_code": "READY_FOR_FIRST_MISSION",
        "commands": {
            "next": "konoha next",
            "start_mission": "konoha mission start --help",
            "open_shell": "konoha shell",
            "doctor": "konoha doctor",
        },
        "boundaries": BOUNDARIES,
        "authority": {
            "quickstart_does_not_start_a_mission": True,
            "quickstart_does_not_authorize_execution": True,
            "quickstart_does_not_enable_network": True,
        },
    }

    if experience_path.is_file():
        current = read_json_object(
            experience_path,
            "product experience state",
        )
        comparable = {
            key: current.get(key)
            for key in (
                "schema_version",
                "report_type",
                "version",
                "created_by",
                "persona",
                "workspace_root",
                "status",
                "status_code",
                "commands",
                "boundaries",
                "authority",
            )
        }
        if comparable != desired:
            raise ProductExperienceError(
                "existing quickstart state conflicts with requested actor "
                "or persona"
            )
        report = inspect_product(repo_root, relative_workspace)
        report["status_code"] = "QUICKSTART_READY"
        report["idempotent"] = True
        report["quickstart_state"] = str(experience_path)
        return report

    manifest_path = workspace / "workspace_manifest.json"
    if not manifest_path.exists():
        init_workspace(repo_root, relative_workspace, force=False)
    else:
        manifest = read_json_object(manifest_path, "workspace manifest")
        if manifest.get("workspace_type") != (
            "konoha_product_runtime_workspace"
        ):
            raise ProductExperienceError(
                "existing workspace manifest has an incompatible type"
            )

    desired["created_at"] = utc_now()
    atomic_write_json(experience_path, desired)

    report = inspect_product(repo_root, relative_workspace)
    report["status_code"] = "QUICKSTART_READY"
    report["idempotent"] = False
    report["quickstart_state"] = str(experience_path)
    return report


def print_human(report: Mapping[str, Any]) -> None:
    latest = report.get("latest_mission") or {}
    workspace = report.get("workspace") or {}
    print("KONOHA LOCAL-FIRST TERMINAL PRODUCT")
    print(f"version: {report.get('version')}")
    print(f"status_code: {report.get('status_code')}")
    print(f"workspace_initialized: {workspace.get('initialized')}")
    print(f"mission: {latest.get('mission_id') or 'none'}")
    print(f"summary: {latest.get('summary')}")
    print(f"next: {latest.get('next_command')}")
    print("status is evidence only; the next command is not permission")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Guide the finished Konoha terminal product experience."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for command in ("welcome", "next"):
        item = sub.add_parser(command)
        item.add_argument("--repo-root", default=".")
        item.add_argument(
            "--workspace-root",
            default=DEFAULT_WORKSPACE_ROOT,
        )
        item.add_argument("--json", action="store_true")

    quickstart = sub.add_parser("quickstart")
    quickstart.add_argument("--repo-root", default=".")
    quickstart.add_argument(
        "--workspace-root",
        default=DEFAULT_WORKSPACE_ROOT,
    )
    quickstart.add_argument("--human-actor", default="human")
    quickstart.add_argument(
        "--persona",
        default=DEFAULT_PERSONA,
        choices=sorted(PERSONAS),
    )
    quickstart.add_argument(
        "--confirm-quickstart",
        action="store_true",
    )
    quickstart.add_argument(
        "--approval-token",
        default="",
        help=f"Exact token required: {QUICKSTART_TOKEN}",
    )
    quickstart.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repo_root = Path(args.repo_root).resolve()
        if not repo_root.is_dir():
            raise ProductExperienceError(
                f"repository root does not exist: {repo_root}"
            )

        if args.command == "quickstart":
            report = run_quickstart(
                repo_root,
                args.workspace_root,
                human_actor=args.human_actor,
                persona=args.persona,
                confirm_quickstart=args.confirm_quickstart,
                approval_token=args.approval_token,
            )
        else:
            report = inspect_product(
                repo_root,
                args.workspace_root,
            )

        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_human(report)
        return 0

    except (ProductExperienceError, OSError, ValueError) as exc:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "report_type": REPORT_TYPE,
            "generated_at": utc_now(),
            "version": VERSION,
            "status": "blocked",
            "status_code": "BLOCKED_PRODUCT_EXPERIENCE",
            "blocker": str(exc),
            "boundaries": BOUNDARIES,
            "authority": {
                "failure_does_not_authorize_fallback": True,
            },
        }
        if getattr(args, "json", False):
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("KONOHA PRODUCT EXPERIENCE BLOCKED", file=sys.stderr)
            print(f"blocker: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
