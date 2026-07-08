#!/usr/bin/env python3
"""
Human-in-the-loop Agent Runtime for Konoha.

This runtime coordinates already-gated Konoha tools. It does not execute arbitrary
commands, apply repository changes, perform Git operations, access private context,
or treat model/tool output as permission.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union


PLANNING_APPROVAL_TOKEN = "INVOKE_REAL_MODEL"
TOOL_APPROVAL_TOKEN = "EXECUTE_CONTROLLED_TOOL"
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass
class StepResult:
    name: str
    command: List[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def require_safe_id(value: str, label: str) -> None:
    if not value or not SAFE_ID_RE.match(value) or "/" in value or "\\" in value or ".." in value:
        raise ValueError(f"{label} must be alphanumeric plus '.', '_' or '-' and may not contain path separators")


def resolve_under(root: Path, child: Union[str, Path]) -> Path:
    root_resolved = root.resolve()
    target = (root_resolved / child).resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"path escapes root: {target}") from exc
    return target


def load_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return value


def run_command(name: str, command: List[str]) -> StepResult:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        shell=False,
    )
    return StepResult(
        name=name,
        command=command,
        returncode=int(completed.returncode),
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def build_workspace_validate_command(args: argparse.Namespace, repo_root: Path) -> List[str]:
    return [
        sys.executable,
        str(repo_root / "tools" / "mission_workspace" / "manage_mission_workspace.py"),
        "validate",
        "--workspace-root",
        str(args.workspace_root),
        "--mission-id",
        args.mission_id,
    ]


def build_planner_command(args: argparse.Namespace, repo_root: Path) -> List[str]:
    command = [
        sys.executable,
        str(repo_root / "tools" / "planner_loop" / "run_hokage_planner_loop.py"),
        "--repo-root",
        str(args.repo_root),
        "--workspace-root",
        str(args.workspace_root),
        "--mission-id",
        args.mission_id,
        "--sandbox-root",
        str(args.sandbox_root),
        "--run-id",
        args.run_id + "-planner",
        "--contract",
        str(args.contract),
        "--request",
        str(args.request),
    ]
    if args.confirm_planning:
        command.extend(["--confirm-invocation", "--approval-token", args.planning_approval_token])
    if args.allow_network:
        command.append("--allow-network")
    if args.force:
        command.append("--force")
    return command


def build_tool_command(args: argparse.Namespace, repo_root: Path) -> Optional[List[str]]:
    if args.tool_plan is None:
        return None
    command = [
        sys.executable,
        str(repo_root / "tools" / "tool_execution" / "run_controlled_tool.py"),
        "--plan",
        str(args.tool_plan),
        "--repo-root",
        str(args.repo_root),
        "--workspace-root",
        str(args.workspace_root),
        "--sandbox-root",
        str(args.sandbox_root),
    ]
    if args.confirm_tool_execution:
        command.extend(["--confirm-execution", "--approval-token", args.tool_approval_token])
    if args.force:
        command.append("--force")
    return command


def report_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    mission_dir = resolve_under(Path(args.workspace_root), Path("missions") / args.mission_id)
    mission_report = resolve_under(mission_dir, Path("reports") / f"{args.run_id}_human_in_loop_agent_runtime_report.json")
    sandbox_report = resolve_under(Path(args.sandbox_root), Path("reports") / f"{args.run_id}_human_in_loop_agent_runtime_report.json")
    return mission_report, sandbox_report


def write_report(path: Path, report: Dict[str, Any], force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(f"report already exists: {path}. Use --force to overwrite.")
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def make_report(
    args: argparse.Namespace,
    status: str,
    steps: List[StepResult],
    blockers: List[str],
) -> Dict[str, Any]:
    confirmed_planning = bool(args.confirm_planning)
    confirmed_tool = bool(args.confirm_tool_execution and args.tool_plan is not None)
    return {
        "schema_version": "1.0",
        "report_type": "human_in_loop_agent_runtime_report",
        "created_at": utc_now(),
        "run_id": args.run_id,
        "mission_id": args.mission_id,
        "status": status,
        "mode": "confirmed" if confirmed_planning or confirmed_tool else "preview",
        "human_approval_required": True,
        "planning": {
            "requested": True,
            "confirmed": confirmed_planning,
            "approval_token_name": PLANNING_APPROVAL_TOKEN if confirmed_planning else None,
            "model_output_authority": "evidence_only",
        },
        "controlled_tool_execution": {
            "requested": args.tool_plan is not None,
            "confirmed": confirmed_tool,
            "approval_token_name": TOOL_APPROVAL_TOKEN if confirmed_tool else None,
            "tool_result_authority": "evidence_only",
        },
        "paths": {
            "repo_root": str(args.repo_root),
            "workspace_root": str(args.workspace_root),
            "sandbox_root": str(args.sandbox_root),
            "contract": str(args.contract),
            "request": str(args.request),
            "tool_plan": str(args.tool_plan) if args.tool_plan else None,
        },
        "steps": [
            {
                "name": step.name,
                "returncode": step.returncode,
                "passed": step.passed,
                "command": step.command,
                "stdout_excerpt": step.stdout[:2000],
                "stderr_excerpt": step.stderr[:2000],
            }
            for step in steps
        ],
        "blockers": blockers,
        "safety": {
            "execution": "human_in_loop_only",
            "filesystem_mutation": "mission_workspace_and_sandbox_reports_only",
            "repository_apply": "blocked",
            "git_operations": "blocked",
            "private_context_access": "blocked",
            "real_model_invocation": "gated",
            "adapter_invocation": "blocked",
            "network_access": "model_gate_only_when_explicitly_allowed",
            "arbitrary_shell": "blocked",
            "background_agents": "blocked",
            "autonomous_closure": "blocked",
        },
        "non_authority_rules": [
            "Model output is evidence only.",
            "Model inference is never permission.",
            "Controlled tool output is evidence only.",
            "A plan proposal is not permission to execute.",
            "Agent runtime output is not permission to apply, stage, commit, push, access private context, or close a mission.",
        ],
    }


def print_summary(report: Dict[str, Any]) -> None:
    status = report["status"]
    mode = report["mode"]
    if status == "passed" and mode == "preview":
        print("HUMAN-IN-THE-LOOP AGENT RUNTIME PREVIEW PASSED")
    elif status == "passed":
        print("HUMAN-IN-THE-LOOP AGENT RUNTIME PASSED")
    else:
        print("HUMAN-IN-THE-LOOP AGENT RUNTIME FAILED")

    print(f"Mission: {report['mission_id']}")
    print(f"Run: {report['run_id']}")
    print(f"Mode: {mode}")
    print("Execution: human-in-the-loop only")
    print("Repository apply: blocked")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Model output authority: evidence_only")
    print("Tool output authority: evidence_only")
    print("Real model invocation: gated")
    print("Network access: model gate only when explicitly allowed")
    for blocker in report["blockers"]:
        print("Blocker:", blocker)


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Konoha Human-in-the-loop Agent Runtime."
    )
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--mission-id", required=True)
    parser.add_argument("--sandbox-root", default="./sandbox", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--tool-plan", type=Path)
    parser.add_argument("--confirm-planning", action="store_true")
    parser.add_argument("--planning-approval-token", default="")
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--confirm-tool-execution", action="store_true")
    parser.add_argument("--tool-approval-token", default="")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    blockers: List[str] = []
    steps: List[StepResult] = []

    try:
        require_safe_id(args.mission_id, "mission_id")
        require_safe_id(args.run_id, "run_id")
        args.repo_root = Path(args.repo_root).resolve()
        args.workspace_root = Path(args.workspace_root).resolve()
        args.sandbox_root = Path(args.sandbox_root).resolve()
        args.contract = Path(args.contract).resolve()
        args.request = Path(args.request).resolve()
        args.tool_plan = Path(args.tool_plan).resolve() if args.tool_plan else None

        if args.confirm_planning and args.planning_approval_token != PLANNING_APPROVAL_TOKEN:
            raise PermissionError("confirmed planning requires exact approval token INVOKE_REAL_MODEL")
        if args.confirm_tool_execution and args.tool_approval_token != TOOL_APPROVAL_TOKEN:
            raise PermissionError("confirmed tool execution requires exact approval token EXECUTE_CONTROLLED_TOOL")
        if args.confirm_tool_execution and args.tool_plan is None:
            raise ValueError("--confirm-tool-execution requires --tool-plan")

        load_json(args.contract)
        load_json(args.request)
        if args.tool_plan is not None:
            load_json(args.tool_plan)

        mission_dir = resolve_under(args.workspace_root, Path("missions") / args.mission_id)
        if not mission_dir.exists():
            raise FileNotFoundError(f"mission workspace not found: {mission_dir}")

        commands: List[tuple[str, List[str]]] = [
            ("mission_workspace_validate", build_workspace_validate_command(args, args.repo_root)),
            ("hokage_planner_loop", build_planner_command(args, args.repo_root)),
        ]
        tool_command = build_tool_command(args, args.repo_root)
        if tool_command is not None:
            commands.append(("controlled_tool_execution", tool_command))

        for name, command in commands:
            step = run_command(name, command)
            steps.append(step)
            if not step.passed:
                blockers.append(f"{name} failed with return code {step.returncode}")
                break

        status = "passed" if not blockers else "failed"
        report = make_report(args, status, steps, blockers)
        mission_report, sandbox_report = report_paths(args)
        write_report(mission_report, report, args.force)
        write_report(sandbox_report, report, args.force)

    except Exception as exc:
        blockers.append(str(exc))
        report = make_report(args, "failed", steps, blockers)
        try:
            mission_report, sandbox_report = report_paths(args)
            write_report(mission_report, report, True)
            write_report(sandbox_report, report, True)
        except Exception:
            pass

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_summary(report)

    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
