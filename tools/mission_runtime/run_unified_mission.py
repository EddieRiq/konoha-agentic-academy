#!/usr/bin/env python3
"""Unified Mission Runtime for Konoha Agentic Academy.

This tool coordinates mission intake, Mission Workspace creation,
runtime planning, command proposal generation, notification state, report
writing, optional memory note capture, and status inspection.

It does not execute arbitrary commands.
It does not invoke models.
It does not invoke adapters.
It does not perform Git operations.
It does not access private context by default.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


START_TOKEN = "START_UNIFIED_MISSION"
MEMORY_TOKEN = "RECORD_YAMANAKA_MEMORY"
SCHEMA_VERSION = "1.0.0"

BOUNDARIES = {
    "execution": "blocked",
    "command_execution": "proposed_only",
    "repository_apply": "blocked",
    "git_operations": "blocked",
    "private_context_access": "blocked",
    "real_model_invocation": "blocked",
    "adapter_invocation": "blocked",
    "network_access": "blocked",
    "background_agents": "blocked",
    "mission_closure": "blocked_until_teachback",
}

AUTHORITY = {
    "runtime_report_is_evidence_only": True,
    "command_proposals_are_not_permission": True,
    "mission_state_does_not_authorize_execution": True,
    "memory_notes_do_not_authorize_action": True,
}


class MissionRuntimeError(Exception):
    """Controlled runtime failure."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    original = value.strip()
    if not original:
        raise MissionRuntimeError("value cannot be converted to a safe identifier")
    if original in {".", ".."} or ".." in original or "/" in original or "\\" in original:
        raise MissionRuntimeError(f"unsafe identifier: {original}")
    value = original.lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = value.strip("-._")
    if not value:
        raise MissionRuntimeError("value cannot be converted to a safe identifier")
    if value in {".", ".."} or ".." in value:
        raise MissionRuntimeError(f"unsafe identifier: {value}")
    return value[:120]


def resolve_root(path_value: str) -> Path:
    return Path(path_value).expanduser().resolve()


def ensure_inside(root: Path, candidate: Path) -> Path:
    root = root.resolve()
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise MissionRuntimeError(f"path escapes allowed root: {candidate}") from exc
    return candidate


def mission_dir(workspace_root: Path, mission_id: str) -> Path:
    safe_id = slugify(mission_id)
    path = workspace_root / "missions" / safe_id
    return ensure_inside(workspace_root, path)


def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MissionRuntimeError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MissionRuntimeError(f"invalid JSON file: {path}: {exc}") from exc


def write_json(path: Path, payload: Dict[str, Any], force: bool = False) -> None:
    if path.exists() and not force:
        raise MissionRuntimeError(f"refusing to overwrite existing file without --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build_charter(mission_id: str, title: str, task: str, risk_level: str, actor: str) -> str:
    return f"""# Mission Charter: {title}

mission_id: {mission_id}
risk_level: {risk_level}
human_actor: {actor}
generated_at: {utc_now()}

## Goal

{task}

## Scope

This mission may create mission-local plans, reports, evidence records, command proposals,
notification state, and optional memory notes under explicitly provided roots.

## Allowed actions

- Create Mission Workspace scaffolding under the explicit workspace root.
- Write mission-local plan and report files.
- Write command proposals as evidence.
- Write notification state.
- Write optional memory note only with explicit approval.
- Ask for human approval before any sensitive action.

## Forbidden actions

- Arbitrary command execution.
- Model invocation.
- Adapter invocation.
- Repository apply.
- Git add, commit, or push.
- Private context access by default.
- Network access.
- Background agents.
- Mission closure without Teachback.

## Acceptance criteria

- Mission plan exists.
- Command proposals are explicit and reviewable.
- No command is executed by this runtime.
- Next required human action is recorded.
- Runtime report is written.
"""


def build_manifest(mission_id: str, title: str, task: str, risk_level: str, run_id: str, actor: str) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "manifest_type": "mission_manifest",
        "mission_id": mission_id,
        "title": title,
        "task": task,
        "risk_level": risk_level,
        "created_at": utc_now(),
        "created_by": actor,
        "current_run_id": run_id,
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
    }


def classify_task(task: str) -> Dict[str, bool]:
    lower = task.lower()
    return {
        "docker": any(token in lower for token in ["docker", "container", "compose"]),
        "airflow": "airflow" in lower or "dag" in lower,
        "java_or_jar": any(token in lower for token in ["jar", "java", "jvm"]),
        "server": any(token in lower for token in ["server", "servidor", "ssh", "remote", "linux"]),
        "python": any(token in lower for token in ["python", "pytest", "unittest", "pip"]),
        "git": "git" in lower or "repository" in lower or "repo" in lower,
        "data": any(token in lower for token in ["sql", "parquet", "etl", "pipeline", "data"]),
    }


def proposal(command_id: str, command: str, purpose: str, risk: str, notes: str) -> Dict[str, Any]:
    return {
        "command_id": command_id,
        "command": command,
        "purpose": purpose,
        "risk_level": risk,
        "requires_human_approval": True,
        "execution_status": "proposed_only",
        "allowed_after": "explicit_command_or_batch_approval_in_future_gate",
        "notes": notes,
    }


def build_command_proposals(task: str) -> List[Dict[str, Any]]:
    tags = classify_task(task)
    items: List[Dict[str, Any]] = [
        proposal(
            "inspect-python-version",
            "python --version",
            "Inspect Python availability for local tooling.",
            "low",
            "Read-only environment inspection proposal.",
        ),
        proposal(
            "inspect-git-status",
            "git status --short",
            "Inspect repository working tree before any future changes.",
            "low",
            "Read-only Git inspection proposal; not a stage, commit, or push.",
        ),
    ]

    if tags["docker"]:
        items.extend([
            proposal(
                "inspect-docker-version",
                "docker --version",
                "Check whether Docker is available.",
                "low",
                "Read-only Docker availability check.",
            ),
            proposal(
                "inspect-docker-compose-version",
                "docker compose version",
                "Check whether Docker Compose is available.",
                "low",
                "Read-only Compose availability check.",
            ),
        ])

    if tags["airflow"]:
        items.extend([
            proposal(
                "inspect-airflow-files",
                "dir dags docker-compose.yml requirements.txt",
                "Inspect common Airflow project files if present.",
                "medium",
                "Path and shell syntax should be adapted by the human/operator before approval.",
            ),
            proposal(
                "propose-airflow-dag-validation",
                "python -m py_compile dags/*.py",
                "Validate Airflow DAG Python files if a DAG folder exists.",
                "medium",
                "This is only a future command proposal and may need platform-specific adjustment.",
            ),
        ])

    if tags["java_or_jar"]:
        items.extend([
            proposal(
                "inspect-java-version",
                "java -version",
                "Check Java runtime availability.",
                "low",
                "Read-only runtime availability check.",
            ),
            proposal(
                "find-jar-candidates",
                "dir /s *.jar",
                "Locate candidate JAR files on Windows; adapt for Linux with find.",
                "medium",
                "May be expensive on large trees; human should narrow path before approval.",
            ),
        ])

    if tags["server"]:
        items.extend([
            proposal(
                "server-access-plan-placeholder",
                "ssh <user>@<host>",
                "Represent remote server access as a human-managed step.",
                "high",
                "Konoha must not store credentials. The human owns secure authentication.",
            ),
            proposal(
                "remote-readonly-baseline-placeholder",
                "uname -a && whoami && pwd",
                "Inspect remote baseline after secure human-controlled connection.",
                "medium",
                "Only after explicit server-access approval in a future operation gate.",
            ),
        ])

    if tags["python"]:
        items.append(
            proposal(
                "run-python-tests-proposal",
                "python -m unittest discover",
                "Run Python unit tests if a test suite exists.",
                "medium",
                "Future execution requires explicit approval and evidence capture.",
            )
        )

    if tags["data"]:
        items.append(
            proposal(
                "inspect-data-project-layout",
                "dir data src notebooks",
                "Inspect common data project folders if present.",
                "medium",
                "Must avoid private data unless explicit scope allows it.",
            )
        )

    return items


def build_runtime_plan(mission_id: str, run_id: str, title: str, task: str, risk_level: str) -> Dict[str, Any]:
    tags = classify_task(task)
    return {
        "schema_version": SCHEMA_VERSION,
        "plan_type": "unified_mission_runtime_plan",
        "mission_id": mission_id,
        "run_id": run_id,
        "title": title,
        "task": task,
        "risk_level": risk_level,
        "generated_at": utc_now(),
        "task_tags": tags,
        "phases": [
            {
                "phase_id": "mission_intake",
                "status": "prepared",
                "description": "Capture mission goal, charter, manifest, risk, and safety boundaries.",
            },
            {
                "phase_id": "environment_understanding",
                "status": "requires_human_review",
                "description": "Use command proposals for explicit read-only inspection before acting.",
            },
            {
                "phase_id": "planning",
                "status": "requires_human_review",
                "description": "Review plan and decide whether to use model/router gates in later runtime.",
            },
            {
                "phase_id": "controlled_execution",
                "status": "blocked_in_v2_6",
                "description": "No commands are executed by v2.6. Command proposals are evidence only.",
            },
            {
                "phase_id": "verification",
                "status": "planned",
                "description": "Define checks that a future supervised runtime will execute with approval.",
            },
            {
                "phase_id": "memory_and_teachback",
                "status": "ready_after_review",
                "description": "Record memory and teachback readiness after human review.",
            },
        ],
        "next_required_human_action": "Review mission plan and command proposals.",
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
    }


def notification_state(mission_id: str, run_id: str) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "state_type": "mission_notification_state",
        "mission_id": mission_id,
        "run_id": run_id,
        "state": "ready_for_review",
        "severity": "attention",
        "reason": "Unified Mission Runtime prepared plan and command proposals.",
        "required_human_action": "Review the runtime plan and command proposals before any execution.",
        "updated_at": utc_now(),
        "authority": {
            "notification_state_is_evidence_only": True,
            "state_change_does_not_authorize_execution": True,
        },
    }


def evidence_markdown(mission_id: str, run_id: str, title: str) -> str:
    return f"""# Unified Mission Runtime Evidence

mission_id: {mission_id}
run_id: {run_id}
title: {title}
generated_at: {utc_now()}

## Evidence

- Mission charter generated.
- Mission manifest generated.
- Runtime plan generated.
- Command proposals generated.
- Notification state set to ready_for_review.
- No command execution performed.

## Non-authority

This evidence does not authorize execution, model invocation, adapter invocation,
repository apply, Git operations, private context access, or mission closure.
"""


def memory_note(mission_id: str, run_id: str, title: str, task: str, actor: str) -> str:
    return f"""---
type: yamanaka_mission_memory
schema_version: {SCHEMA_VERSION}
mission_id: {mission_id}
run_id: {run_id}
created_at: {utc_now()}
created_by: {actor}
status: prepared_for_review
authority: evidence_only
---

# Mission Memory: {title}

## Task

{task}

## Runtime summary

The Unified Mission Runtime prepared a mission workspace, charter, manifest,
runtime plan, command proposals, notification state, report, and evidence note.

## Boundaries

Memory supports action but does not authorize action.
Command proposals are not permission.
Summaries are not truth.
"""


def build_report(
    mission_id: str,
    run_id: str,
    title: str,
    task: str,
    status: str,
    invocation: str,
    workspace_root: Path,
    mission_path: Path,
    runtime_plan_path: Optional[Path],
    proposals_path: Optional[Path],
    actor: str,
    memory_note_path: Optional[Path],
    blockers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "unified_mission_runtime_report",
        "status": status,
        "invocation": invocation,
        "generated_at": utc_now(),
        "mission_id": mission_id,
        "run_id": run_id,
        "title": title,
        "task": task,
        "human_actor": actor,
        "platform": {
            "python": sys.version.split()[0],
            "system": platform.system(),
            "machine": platform.machine(),
        },
        "workspace_root": str(workspace_root),
        "mission_path": str(mission_path),
        "runtime_plan_path": str(runtime_plan_path) if runtime_plan_path else None,
        "command_proposals_path": str(proposals_path) if proposals_path else None,
        "memory_note_path": str(memory_note_path) if memory_note_path else None,
        "blockers": blockers or [],
        "next_required_human_action": "Review mission plan and command proposals.",
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
    }


def run_preview(args: argparse.Namespace) -> int:
    mission_id = slugify(args.mission_id)
    run_id = slugify(args.run_id)
    workspace_root = resolve_root(args.workspace_root)
    path = mission_dir(workspace_root, mission_id)
    report = build_report(
        mission_id=mission_id,
        run_id=run_id,
        title=args.title,
        task=args.task,
        status="preview",
        invocation="preview_only",
        workspace_root=workspace_root,
        mission_path=path,
        runtime_plan_path=None,
        proposals_path=None,
        actor=args.human_actor,
        memory_note_path=None,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("UNIFIED MISSION RUNTIME PREVIEW")
        print(f"Mission: {mission_id}")
        print(f"Run: {run_id}")
        print("Mission workspace creation: blocked")
        print("Command execution: proposed_only")
        print("Repository apply: blocked")
        print("Git operations: blocked")
        print("Private context access: blocked")
        print("Real model invocation: blocked")
        print("Adapter invocation: blocked")
        print("Network access: blocked")
        print("Next required action: approve mission runtime start")
    return 0


def run_confirmed(args: argparse.Namespace) -> int:
    if args.approval_token != START_TOKEN:
        raise MissionRuntimeError("invalid approval token for unified mission runtime start")

    mission_id = slugify(args.mission_id)
    run_id = slugify(args.run_id)
    workspace_root = resolve_root(args.workspace_root)
    sandbox_root = resolve_root(args.sandbox_root)
    workspace_root.mkdir(parents=True, exist_ok=True)
    sandbox_root.mkdir(parents=True, exist_ok=True)

    path = mission_dir(workspace_root, mission_id)
    for rel in [
        "inputs",
        "context",
        "plans",
        "outputs",
        "reports",
        "approvals",
        "evidence",
        "notifications",
    ]:
        ensure_inside(path, path / rel).mkdir(parents=True, exist_ok=True)

    charter_path = path / "charter.md"
    manifest_path = path / "mission_manifest.json"
    plan_path = path / "plans" / f"{run_id}_unified_mission_runtime_plan.json"
    proposals_path = path / "plans" / f"{run_id}_command_proposals.json"
    state_path = path / "mission_notification_state.json"
    evidence_path = path / "evidence" / f"{run_id}_unified_mission_runtime_evidence.md"
    report_path = path / "reports" / f"{run_id}_unified_mission_runtime_report.json"

    if charter_path.exists() and not args.force:
        raise MissionRuntimeError(f"mission already exists; use --force to update: {charter_path}")

    charter_path.write_text(
        build_charter(mission_id, args.title, args.task, args.risk_level, args.human_actor),
        encoding="utf-8",
    )
    write_json(
        manifest_path,
        build_manifest(mission_id, args.title, args.task, args.risk_level, run_id, args.human_actor),
        force=True,
    )
    write_json(
        plan_path,
        build_runtime_plan(mission_id, run_id, args.title, args.task, args.risk_level),
        force=args.force,
    )
    write_json(
        proposals_path,
        {
            "schema_version": SCHEMA_VERSION,
            "proposal_type": "mission_command_proposal_set",
            "mission_id": mission_id,
            "run_id": run_id,
            "generated_at": utc_now(),
            "commands": build_command_proposals(args.task),
            "authority": {
                "command_proposals_are_not_permission": True,
                "future_execution_requires_separate_approval": True,
            },
        },
        force=args.force,
    )
    write_json(state_path, notification_state(mission_id, run_id), force=True)
    evidence_path.write_text(evidence_markdown(mission_id, run_id, args.title), encoding="utf-8")
    append_text(
        path / "notifications" / "notification_log.md",
        f"\n## {utc_now()} - ready_for_review\n\nUnified Mission Runtime prepared plan and command proposals. Human review required.\n",
    )

    memory_note_path: Optional[Path] = None
    if args.write_memory:
        if not args.memory_root:
            raise MissionRuntimeError("--memory-root is required when --write-memory is set")
        if args.memory_approval_token != MEMORY_TOKEN:
            raise MissionRuntimeError("invalid approval token for Yamanaka memory recording")
        memory_root = resolve_root(args.memory_root)
        memory_dir = ensure_inside(memory_root, memory_root / "10-missions")
        memory_dir.mkdir(parents=True, exist_ok=True)
        memory_note_path = memory_dir / f"{mission_id}_{run_id}_runtime_note.md"
        if memory_note_path.exists() and not args.force:
            raise MissionRuntimeError(f"refusing to overwrite existing memory note without --force: {memory_note_path}")
        memory_note_path.write_text(
            memory_note(mission_id, run_id, args.title, args.task, args.human_actor),
            encoding="utf-8",
        )

    report = build_report(
        mission_id=mission_id,
        run_id=run_id,
        title=args.title,
        task=args.task,
        status="prepared",
        invocation="confirmed_start",
        workspace_root=workspace_root,
        mission_path=path,
        runtime_plan_path=plan_path,
        proposals_path=proposals_path,
        actor=args.human_actor,
        memory_note_path=memory_note_path,
    )
    write_json(report_path, report, force=True)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("UNIFIED MISSION RUNTIME STARTED")
        print(f"Mission: {mission_id}")
        print(f"Run: {run_id}")
        print(f"Mission workspace: {path}")
        print(f"Runtime plan: {plan_path}")
        print(f"Command proposals: {proposals_path}")
        print("Command execution: proposed_only")
        print("Repository apply: blocked")
        print("Git operations: blocked")
        print("Private context access: blocked")
        print("Real model invocation: blocked")
        print("Adapter invocation: blocked")
        print("Network access: blocked")
        print("Next required action: review mission plan and command proposals")
    return 0


def command_run(args: argparse.Namespace) -> int:
    if not args.confirm_start:
        return run_preview(args)
    return run_confirmed(args)


def command_status(args: argparse.Namespace) -> int:
    mission_id = slugify(args.mission_id)
    workspace_root = resolve_root(args.workspace_root)
    path = mission_dir(workspace_root, mission_id)
    reports_dir = path / "reports"
    if not reports_dir.exists():
        raise MissionRuntimeError("mission runtime reports do not exist")
    reports = sorted(reports_dir.glob("*_unified_mission_runtime_report.json"))
    if not reports:
        raise MissionRuntimeError("no unified mission runtime report found")
    report = read_json(reports[-1])
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("UNIFIED MISSION RUNTIME STATUS")
        print(f"Mission: {report.get('mission_id')}")
        print(f"Run: {report.get('run_id')}")
        print(f"Status: {report.get('status')}")
        print(f"Next required action: {report.get('next_required_human_action')}")
    return 0


def command_states(_: argparse.Namespace) -> int:
    payload = {
        "runtime_states": [
            "preview",
            "prepared",
            "ready_for_review",
            "waiting_approval",
            "blocked",
            "ready_for_teachback",
            "closed_by_mission_closure_gate",
        ],
        "approval_tokens": {
            "start_unified_mission": START_TOKEN,
            "optional_memory_record": MEMORY_TOKEN,
        },
        "boundaries": BOUNDARIES,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Konoha Unified Mission Runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Preview or prepare a unified mission runtime")
    run.add_argument("--workspace-root", required=True)
    run.add_argument("--sandbox-root", required=True)
    run.add_argument("--mission-id", required=True)
    run.add_argument("--title", required=True)
    run.add_argument("--task", required=True)
    run.add_argument("--run-id", required=True)
    run.add_argument("--risk-level", default="medium", choices=["low", "medium", "high", "critical"])
    run.add_argument("--human-actor", default="eduardo")
    run.add_argument("--confirm-start", action="store_true")
    run.add_argument("--approval-token", default="")
    run.add_argument("--write-memory", action="store_true")
    run.add_argument("--memory-root")
    run.add_argument("--memory-approval-token", default="")
    run.add_argument("--force", action="store_true")
    run.add_argument("--json", action="store_true")
    run.set_defaults(func=command_run)

    status = sub.add_parser("status", help="Inspect latest unified mission runtime report")
    status.add_argument("--workspace-root", required=True)
    status.add_argument("--mission-id", required=True)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_status)

    states = sub.add_parser("states", help="List states and tokens")
    states.set_defaults(func=command_states)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except MissionRuntimeError as exc:
        print("UNIFIED MISSION RUNTIME FAILED")
        print("Blocker:", exc)
        return 1
    except KeyboardInterrupt:
        print("UNIFIED MISSION RUNTIME INTERRUPTED")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
