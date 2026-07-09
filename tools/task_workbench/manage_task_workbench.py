#!/usr/bin/env python3
"""General Task Execution Workbench for Konoha.

v2.8 intentionally does not execute arbitrary commands. It prepares a
mission-level workbench for general technical tasks, proposes command batches,
records externally/supervised command results, and summarizes evidence.

Command proposals are not permission.
Recorded command results are evidence only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{1,120}$")

TOKENS = {
    "start": "START_TASK_WORKBENCH",
    "plan": "PLAN_GENERAL_TASK_WORKBENCH",
    "record_result": "RECORD_TASK_COMMAND_RESULT",
    "review": "REVIEW_TASK_WORKBENCH",
}

TASK_DOMAINS = [
    "general",
    "software_development",
    "data_engineering",
    "devops",
    "server_operations",
    "docker_workflow",
    "documentation",
]

TARGET_ENVIRONMENTS = [
    "local",
    "docker",
    "server",
    "ssh_ready",
    "mixed",
]

RISK_LEVELS = ["low", "medium", "high"]
PRIVACY_LEVELS = ["public", "internal", "local_private", "sensitive"]
APPROVAL_MODES = ["individual", "batch"]

BOUNDARIES = {
    "command_execution": "blocked_in_v2_8",
    "arbitrary_shell": "blocked",
    "repository_apply": "blocked",
    "git_operations": "blocked",
    "model_invocation": "blocked",
    "adapter_invocation": "blocked",
    "private_context_access": "blocked_by_default",
    "network_access": "blocked",
    "background_agents": "blocked",
    "mission_closure": "blocked",
}

AUTHORITY = {
    "command_proposals_are_permission": False,
    "recorded_results_are_permission": False,
    "workbench_reports_authorize_execution": False,
    "human_approval_required_for_execution": True,
    "v2_8_executes_commands": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fail(message: str, json_output: bool = False) -> int:
    payload = {
        "status": "failed",
        "generated_at": utc_now(),
        "blockers": [message],
        "boundaries": BOUNDARIES,
        "authority": AUTHORITY,
    }
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("GENERAL TASK EXECUTION WORKBENCH FAILED")
        print("Blocker:", message)
    return 1


def ensure_safe_id(value: str, field_name: str) -> str:
    if not value or not SAFE_ID_RE.match(value):
        raise ValueError(f"unsafe {field_name}: {value!r}")
    if ".." in value or "/" in value or "\\" in value:
        raise ValueError(f"unsafe {field_name}: {value!r}")
    return value


def resolve_root(path: str) -> Path:
    return Path(path).expanduser().resolve()


def mission_dir(workspace_root: Path, mission_id: str) -> Path:
    ensure_safe_id(mission_id, "mission_id")
    root = workspace_root.resolve()
    target = (root / "missions" / mission_id).resolve()
    if root != target and root not in target.parents:
        raise ValueError("mission path escapes workspace root")
    return target


def ensure_dirs(mission: Path) -> None:
    for child in [
        "plans",
        "reports",
        "evidence",
        "evidence/command_results",
        "notifications",
        "task_workbench",
        "approvals",
    ]:
        (mission / child).mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, Any], force: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str, force: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def command_id(prefix: str, index: int) -> str:
    return f"{prefix}-{index:02d}"


def build_charter(args: argparse.Namespace) -> str:
    return f"""# Mission Charter: {args.title}

mission_id: {args.mission_id}
task_domain: {args.task_domain}
target_environment: {args.target_environment}
risk_level: {args.risk_level}
privacy_level: {args.privacy_level}

## Task

{args.task}

## Runtime boundary

- Command proposals are not permission.
- v2.8 does not execute arbitrary commands.
- Human approval is required before any external command execution.
- Private context stays local and is blocked by default.
- Repository apply, Git operations, model invocation, adapter invocation, network access, background agents, and mission closure remain blocked.

## Acceptance criteria

- Workbench plan is created.
- Command batches are proposed.
- Verification checklist exists.
- Rollback notes exist.
- Evidence capture path exists.
- Human review can decide whether to execute commands outside this v2.8 workbench.
"""


def build_manifest(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "mission_id": args.mission_id,
        "title": args.title,
        "task": args.task,
        "task_domain": args.task_domain,
        "target_environment": args.target_environment,
        "risk_level": args.risk_level,
        "privacy_level": args.privacy_level,
        "created_at": utc_now(),
        "runtime": "general_task_execution_workbench",
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
    }


def infer_playbook(task: str, task_domain: str, target_environment: str) -> Dict[str, Any]:
    text = task.lower()
    tags = []
    if any(word in text for word in ["docker", "compose", "container"]):
        tags.append("docker")
    if any(word in text for word in ["airflow", "dag", "scheduler"]):
        tags.append("workflow_orchestration")
    if any(word in text for word in ["jar", "java"]):
        tags.append("java_jar")
    if any(word in text for word in ["server", "ssh", "linux"]):
        tags.append("server")
    if any(word in text for word in ["sql", "pipeline", "etl", "data"]):
        tags.append("data_pipeline")
    if not tags:
        tags.append(task_domain)

    return {
        "playbook_type": "general_supervised_task",
        "detected_tags": sorted(set(tags)),
        "target_environment": target_environment,
        "principle": "inspect, plan, ask, execute externally with approval, verify, record evidence",
    }


def build_command_batches(plan_id: str, task_domain: str, target_environment: str) -> Dict[str, Any]:
    batches: List[Dict[str, Any]] = []

    batches.append({
        "batch_id": f"{plan_id}-inspect",
        "title": "Environment inspection proposals",
        "approval_mode": "batch_or_individual",
        "execution_mode": "human_supervised_external",
        "commands": [
            {
                "command_id": command_id("inspect", 1),
                "purpose": "Identify current working directory.",
                "proposed_command": "pwd",
                "risk": "low",
                "requires_human_approval": True,
            },
            {
                "command_id": command_id("inspect", 2),
                "purpose": "Check Python availability.",
                "proposed_command": "python --version",
                "risk": "low",
                "requires_human_approval": True,
            },
            {
                "command_id": command_id("inspect", 3),
                "purpose": "Check Docker availability if the task needs containers.",
                "proposed_command": "docker --version",
                "risk": "low",
                "requires_human_approval": True,
            },
            {
                "command_id": command_id("inspect", 4),
                "purpose": "Check Docker Compose availability if the task needs multi-service orchestration.",
                "proposed_command": "docker compose version",
                "risk": "low",
                "requires_human_approval": True,
            },
        ],
    })

    if target_environment in {"server", "ssh_ready", "mixed"}:
        batches.append({
            "batch_id": f"{plan_id}-server-readiness",
            "title": "Server readiness proposals",
            "approval_mode": "individual_required",
            "execution_mode": "human_supervised_external",
            "commands": [
                {
                    "command_id": command_id("server", 1),
                    "purpose": "Confirm remote host identity after the human opens a safe session.",
                    "proposed_command": "hostname",
                    "risk": "medium",
                    "requires_human_approval": True,
                    "notes": "Konoha does not collect or store credentials.",
                },
                {
                    "command_id": command_id("server", 2),
                    "purpose": "Check disk availability on the target environment.",
                    "proposed_command": "df -h",
                    "risk": "medium",
                    "requires_human_approval": True,
                },
            ],
        })

    if task_domain in {"docker_workflow", "devops", "server_operations"} or target_environment in {"docker", "mixed"}:
        batches.append({
            "batch_id": f"{plan_id}-docker-design",
            "title": "Docker workflow proposals",
            "approval_mode": "individual_required",
            "execution_mode": "proposal_only",
            "commands": [
                {
                    "command_id": command_id("docker", 1),
                    "purpose": "List candidate project files before proposing container changes.",
                    "proposed_command": "dir",
                    "risk": "low",
                    "requires_human_approval": True,
                },
                {
                    "command_id": command_id("docker", 2),
                    "purpose": "Validate a compose file after the human-approved file exists.",
                    "proposed_command": "docker compose config",
                    "risk": "medium",
                    "requires_human_approval": True,
                },
            ],
        })

    batches.append({
        "batch_id": f"{plan_id}-verification",
        "title": "Verification proposals",
        "approval_mode": "batch_or_individual",
        "execution_mode": "human_supervised_external",
        "commands": [
            {
                "command_id": command_id("verify", 1),
                "purpose": "Run the project-specific validation command after the human approves it.",
                "proposed_command": "<project-specific test or validation command>",
                "risk": "medium",
                "requires_human_approval": True,
            },
            {
                "command_id": command_id("verify", 2),
                "purpose": "Collect relevant logs after a supervised run.",
                "proposed_command": "<project-specific log inspection command>",
                "risk": "medium",
                "requires_human_approval": True,
            },
        ],
    })

    return {
        "schema_version": "1.0.0",
        "plan_id": plan_id,
        "report_type": "task_command_batches",
        "generated_at": utc_now(),
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
        "batches": batches,
    }


def build_verification_checklist(args: argparse.Namespace, plan_id: str) -> str:
    return f"""# Verification Checklist: {plan_id}

Mission: {args.mission_id}

## Before execution

- [ ] Task goal is understood.
- [ ] Target environment is explicit.
- [ ] Allowed paths are explicit.
- [ ] Secrets and credentials are not requested or stored.
- [ ] Human reviewed command proposals.
- [ ] Human approved each command or batch outside this v2.8 workbench.

## During supervised execution

- [ ] Capture command executed.
- [ ] Capture timestamp.
- [ ] Capture exit code.
- [ ] Capture stdout/stderr summary.
- [ ] Capture relevant logs.
- [ ] Stop on unexpected output, credential request, destructive operation, or unclear state.

## After execution

- [ ] Validate result against task acceptance criteria.
- [ ] Record evidence.
- [ ] Record unresolved blockers.
- [ ] Record rollback notes.
- [ ] Prepare self-review for v2.9/v3.0 integration.
"""


def build_rollback_notes(args: argparse.Namespace, plan_id: str) -> str:
    return f"""# Rollback Notes: {plan_id}

Mission: {args.mission_id}

v2.8 does not perform rollback automatically.

## Required rollback thinking

- What files or services could be affected?
- What commands changed state?
- What backups or snapshots exist?
- What command would revert each change?
- Who approves rollback?

## Default stance

Stop and ask before destructive rollback.
Record evidence before and after rollback.
"""


def make_report(
    command: str,
    status: str,
    mission_id: str,
    run_id: str,
    blockers: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "report_type": "general_task_execution_workbench_report",
        "command": command,
        "status": status,
        "mission_id": mission_id,
        "run_id": run_id,
        "generated_at": utc_now(),
        "blockers": blockers or [],
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
    }
    if extra:
        payload.update(extra)
    return payload


def output(payload: Dict[str, Any], json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = payload.get("status", "unknown")
        command = payload.get("command", "workbench")
        if status == "preview":
            print("GENERAL TASK EXECUTION WORKBENCH PREVIEW")
        elif status == "passed":
            print("GENERAL TASK EXECUTION WORKBENCH UPDATED")
        else:
            print("GENERAL TASK EXECUTION WORKBENCH REPORT")
        print("Command:", command)
        print("Command execution:", BOUNDARIES["command_execution"])
        print("Repository apply:", BOUNDARIES["repository_apply"])
        print("Git operations:", BOUNDARIES["git_operations"])
        print("Private context access:", BOUNDARIES["private_context_access"])
        print("Model invocation:", BOUNDARIES["model_invocation"])
        print("Network access:", BOUNDARIES["network_access"])
        if payload.get("output_paths"):
            print("Output paths:")
            for item in payload["output_paths"]:
                print("-", item)


def cmd_init(args: argparse.Namespace) -> int:
    try:
        workspace = resolve_root(args.workspace_root)
        ensure_safe_id(args.mission_id, "mission_id")
        ensure_safe_id(args.run_id, "run_id")
        mission = mission_dir(workspace, args.mission_id)

        if not args.confirm_start:
            payload = make_report("init", "preview", args.mission_id, args.run_id, extra={
                "invocation": "preview_only",
                "mission_workspace_creation": "blocked",
                "task": args.task,
            })
            output(payload, args.json)
            return 0

        if args.approval_token != TOKENS["start"]:
            return fail("invalid approval token for task workbench start", args.json)

        ensure_dirs(mission)
        charter_path = mission / "charter.md"
        manifest_path = mission / "mission_manifest.json"
        report_path = mission / "reports" / f"{args.run_id}_task_workbench_init_report.json"
        notification_path = mission / "mission_notification_state.json"

        write_text(charter_path, build_charter(args), force=args.force)
        write_json(manifest_path, build_manifest(args), force=args.force)

        notification = {
            "schema_version": "1.0.0",
            "mission_id": args.mission_id,
            "state": "ready_for_review",
            "severity": "attention",
            "reason": "Task workbench initialized. Human review is required before any command execution outside v2.8.",
            "required_human_action": "Review the generated plan and command proposals before execution.",
            "updated_at": utc_now(),
            "authority": AUTHORITY,
        }
        write_json(notification_path, notification, force=True)

        report = make_report("init", "passed", args.mission_id, args.run_id, extra={
            "output_paths": [
                str(charter_path),
                str(manifest_path),
                str(notification_path),
                str(report_path),
            ],
            "task": args.task,
        })
        write_json(report_path, report, force=args.force)
        output(report, args.json)
        return 0
    except Exception as exc:
        return fail(str(exc), args.json)


def cmd_plan(args: argparse.Namespace) -> int:
    try:
        workspace = resolve_root(args.workspace_root)
        ensure_safe_id(args.mission_id, "mission_id")
        ensure_safe_id(args.plan_id, "plan_id")
        mission = mission_dir(workspace, args.mission_id)

        playbook = infer_playbook(args.task, args.task_domain, args.target_environment)
        command_batches = build_command_batches(args.plan_id, args.task_domain, args.target_environment)

        plan = {
            "schema_version": "1.0.0",
            "plan_id": args.plan_id,
            "mission_id": args.mission_id,
            "task": args.task,
            "task_domain": args.task_domain,
            "target_environment": args.target_environment,
            "risk_level": args.risk_level,
            "privacy_level": args.privacy_level,
            "approval_mode": args.command_approval_mode,
            "generated_at": utc_now(),
            "playbook": playbook,
            "phases": [
                "clarify_task",
                "inspect_environment_with_permission",
                "prepare_command_batches",
                "human_review",
                "external_supervised_execution",
                "record_results",
                "verify",
                "self_review",
            ],
            "authority": AUTHORITY,
            "boundaries": BOUNDARIES,
        }

        if not args.confirm_plan:
            payload = make_report("plan", "preview", args.mission_id, args.plan_id, extra={
                "invocation": "preview_only",
                "plan": plan,
                "command_batches": command_batches,
            })
            output(payload, args.json)
            return 0

        if args.approval_token != TOKENS["plan"]:
            return fail("invalid approval token for task workbench planning", args.json)

        ensure_dirs(mission)
        plan_path = mission / "plans" / f"{args.plan_id}_task_workbench_plan.json"
        batch_path = mission / "plans" / f"{args.plan_id}_command_batches.json"
        checklist_path = mission / "plans" / f"{args.plan_id}_verification_checklist.md"
        rollback_path = mission / "plans" / f"{args.plan_id}_rollback_notes.md"
        report_path = mission / "reports" / f"{args.plan_id}_task_workbench_plan_report.json"

        write_json(plan_path, plan, force=args.force)
        write_json(batch_path, command_batches, force=args.force)
        write_text(checklist_path, build_verification_checklist(args, args.plan_id), force=args.force)
        write_text(rollback_path, build_rollback_notes(args, args.plan_id), force=args.force)

        report = make_report("plan", "passed", args.mission_id, args.plan_id, extra={
            "output_paths": [
                str(plan_path),
                str(batch_path),
                str(checklist_path),
                str(rollback_path),
                str(report_path),
            ],
            "command_batches_count": len(command_batches["batches"]),
            "detected_tags": playbook["detected_tags"],
        })
        write_json(report_path, report, force=args.force)
        output(report, args.json)
        return 0
    except Exception as exc:
        return fail(str(exc), args.json)


def cmd_record_result(args: argparse.Namespace) -> int:
    try:
        workspace = resolve_root(args.workspace_root)
        ensure_safe_id(args.mission_id, "mission_id")
        ensure_safe_id(args.result_id, "result_id")
        ensure_safe_id(args.command_id, "command_id")
        mission = mission_dir(workspace, args.mission_id)

        if not args.confirm_record:
            payload = make_report("record-result", "preview", args.mission_id, args.result_id, extra={
                "invocation": "preview_only",
                "result_recording": "blocked",
                "command_id": args.command_id,
            })
            output(payload, args.json)
            return 0

        if args.approval_token != TOKENS["record_result"]:
            return fail("invalid approval token for command result recording", args.json)

        ensure_dirs(mission)
        result_path = mission / "evidence" / "command_results" / f"{args.result_id}.json"
        report_path = mission / "reports" / f"{args.result_id}_task_command_result_report.json"

        result = {
            "schema_version": "1.0.0",
            "result_id": args.result_id,
            "mission_id": args.mission_id,
            "command_id": args.command_id,
            "command": args.command,
            "execution_context": args.execution_context,
            "executed_by": args.executed_by,
            "exit_code": args.exit_code,
            "stdout_summary": args.stdout_summary,
            "stderr_summary": args.stderr_summary,
            "observation": args.observation,
            "recorded_at": utc_now(),
            "authority": AUTHORITY,
            "boundaries": BOUNDARIES,
        }
        write_json(result_path, result, force=args.force)

        report = make_report("record-result", "passed", args.mission_id, args.result_id, extra={
            "output_paths": [str(result_path), str(report_path)],
            "command_id": args.command_id,
            "exit_code": args.exit_code,
            "result_is_evidence_only": True,
        })
        write_json(report_path, report, force=args.force)
        output(report, args.json)
        return 0
    except Exception as exc:
        return fail(str(exc), args.json)


def collect_files(path: Path, pattern: str) -> List[str]:
    if not path.exists():
        return []
    return [str(p) for p in sorted(path.glob(pattern)) if p.is_file()]


def cmd_review(args: argparse.Namespace) -> int:
    try:
        workspace = resolve_root(args.workspace_root)
        ensure_safe_id(args.mission_id, "mission_id")
        ensure_safe_id(args.review_id, "review_id")
        mission = mission_dir(workspace, args.mission_id)

        if not mission.exists():
            return fail("mission workspace does not exist", args.json)

        plans = collect_files(mission / "plans", "*_task_workbench_plan.json")
        command_batches = collect_files(mission / "plans", "*_command_batches.json")
        results = collect_files(mission / "evidence" / "command_results", "*.json")
        reports = collect_files(mission / "reports", "*.json")

        review = make_report("review", "passed", args.mission_id, args.review_id, extra={
            "plans": plans,
            "command_batches": command_batches,
            "recorded_command_results": results,
            "reports": reports,
            "readiness": {
                "has_plan": bool(plans),
                "has_command_batches": bool(command_batches),
                "has_recorded_results": bool(results),
                "ready_for_v3_supervised_execution": bool(plans and command_batches),
            },
            "recommendations": [
                "Review command batches with a human before execution.",
                "Record actual command results after supervised execution.",
                "Use v2.7 token ledger for model calls and planning sessions.",
                "Use v2.9 self-review before any Git operation.",
            ],
        })

        if args.confirm_review:
            if args.approval_token != TOKENS["review"]:
                return fail("invalid approval token for task workbench review", args.json)
            ensure_dirs(mission)
            report_path = mission / "reports" / f"{args.review_id}_task_workbench_review_report.json"
            write_json(report_path, review, force=args.force)
            review["output_paths"] = [str(report_path)]

        output(review, args.json)
        return 0
    except Exception as exc:
        return fail(str(exc), args.json)


def cmd_states(args: argparse.Namespace) -> int:
    payload = {
        "schema_version": "1.0.0",
        "report_type": "general_task_execution_workbench_states",
        "generated_at": utc_now(),
        "tokens": TOKENS,
        "task_domains": TASK_DOMAINS,
        "target_environments": TARGET_ENVIRONMENTS,
        "risk_levels": RISK_LEVELS,
        "privacy_levels": PRIVACY_LEVELS,
        "approval_modes": APPROVAL_MODES,
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def add_common_mission_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--mission-id", required=True)
    parser.add_argument("--json", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Konoha General Task Execution Workbench")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize a general task workbench mission")
    add_common_mission_args(init)
    init.add_argument("--run-id", required=True)
    init.add_argument("--title", required=True)
    init.add_argument("--task", required=True)
    init.add_argument("--task-domain", choices=TASK_DOMAINS, default="general")
    init.add_argument("--target-environment", choices=TARGET_ENVIRONMENTS, default="local")
    init.add_argument("--risk-level", choices=RISK_LEVELS, default="medium")
    init.add_argument("--privacy-level", choices=PRIVACY_LEVELS, default="local_private")
    init.add_argument("--confirm-start", action="store_true")
    init.add_argument("--approval-token", default="")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    plan = sub.add_parser("plan", help="Create a general task plan and command proposals")
    add_common_mission_args(plan)
    plan.add_argument("--plan-id", required=True)
    plan.add_argument("--task", required=True)
    plan.add_argument("--task-domain", choices=TASK_DOMAINS, default="general")
    plan.add_argument("--target-environment", choices=TARGET_ENVIRONMENTS, default="local")
    plan.add_argument("--risk-level", choices=RISK_LEVELS, default="medium")
    plan.add_argument("--privacy-level", choices=PRIVACY_LEVELS, default="local_private")
    plan.add_argument("--command-approval-mode", choices=APPROVAL_MODES, default="individual")
    plan.add_argument("--confirm-plan", action="store_true")
    plan.add_argument("--approval-token", default="")
    plan.add_argument("--force", action="store_true")
    plan.set_defaults(func=cmd_plan)

    record = sub.add_parser("record-result", help="Record a supervised/external command result")
    add_common_mission_args(record)
    record.add_argument("--result-id", required=True)
    record.add_argument("--command-id", required=True)
    record.add_argument("--command", required=True)
    record.add_argument("--execution-context", default="human_supervised_external")
    record.add_argument("--executed-by", default="human")
    record.add_argument("--exit-code", type=int, required=True)
    record.add_argument("--stdout-summary", default="")
    record.add_argument("--stderr-summary", default="")
    record.add_argument("--observation", default="")
    record.add_argument("--confirm-record", action="store_true")
    record.add_argument("--approval-token", default="")
    record.add_argument("--force", action="store_true")
    record.set_defaults(func=cmd_record_result)

    review = sub.add_parser("review", help="Review task workbench readiness and evidence")
    add_common_mission_args(review)
    review.add_argument("--review-id", required=True)
    review.add_argument("--confirm-review", action="store_true")
    review.add_argument("--approval-token", default="")
    review.add_argument("--force", action="store_true")
    review.set_defaults(func=cmd_review)

    states = sub.add_parser("states", help="List states, tokens, and boundaries")
    states.set_defaults(func=cmd_states)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
