#!/usr/bin/env python3
"""Controlled Tool Execution Gate for Konoha Agentic Academy.

This gate executes only explicitly allowlisted internal Konoha tools.
It does not accept arbitrary commands, shell strings, network access,
private context access, repository apply, or Git write operations.

A controlled tool result is evidence only. It is never permission to
apply, stage, commit, push, close a mission, or run further tools.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


APPROVAL_TOKEN = "EXECUTE_CONTROLLED_TOOL"
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")

BLOCKED_SAFETY_FLAGS = {
    "private_context_access",
    "network_access",
    "git_operations",
    "repository_apply",
    "real_model_invocation",
    "arbitrary_shell",
    "background_agent",
}

ACTION_TABLE = {
    "mission_workspace_validate": {
        "script": "tools/mission_workspace/manage_mission_workspace.py",
        "description": "Validate a Mission Workspace.",
    },
    "mission_workspace_inspect": {
        "script": "tools/mission_workspace/manage_mission_workspace.py",
        "description": "Inspect a Mission Workspace.",
    },
    "approval_status": {
        "script": "tools/approval_console/manage_mission_approval.py",
        "description": "Read mission approval status.",
    },
    "approval_reports_list": {
        "script": "tools/approval_console/manage_mission_approval.py",
        "description": "List mission-local reports.",
    },
    "runtime_package_validate": {
        "script": "tools/runtime_validator/validate_runtime_package.py",
        "description": "Validate a runtime package JSON file.",
    },
}


def _print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _safe_identifier(value: str, field_name: str) -> None:
    if not value or not SAFE_ID_RE.match(value) or "/" in value or "\\" in value or ".." in value.split("."):
        raise ValueError(f"{field_name} must be alphanumeric plus '.', '_' or '-' and may not contain path separators")


def _resolve_under(root: Path, candidate: Path, label: str) -> Path:
    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve()
    try:
        candidate_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"{label} must resolve under {root_resolved}") from exc
    return candidate_resolved


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("plan must be a JSON object")
    return data


def _write_json(path: Path, payload: Dict[str, Any], force: bool) -> None:
    if path.exists() and not force:
        raise ValueError(f"report already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _validate_safety(plan: Dict[str, Any]) -> List[str]:
    blockers: List[str] = []
    safety = plan.get("safety", {})
    if not isinstance(safety, dict):
        return ["safety must be an object"]

    for flag in sorted(BLOCKED_SAFETY_FLAGS):
        if safety.get(flag) is True:
            blockers.append(f"{flag} must be false for controlled tool execution")

    if safety.get("execution_scope") not in (None, "allowlisted_tool_only"):
        blockers.append("execution_scope must be allowlisted_tool_only")

    return blockers


def _build_command(
    action: str,
    plan: Dict[str, Any],
    repo_root: Path,
    workspace_root: Path,
    sandbox_root: Path,
) -> Tuple[List[str], Dict[str, Any]]:
    params = plan.get("parameters", {})
    if not isinstance(params, dict):
        raise ValueError("parameters must be an object")

    if action not in ACTION_TABLE:
        raise ValueError(f"unknown or non-allowlisted action: {action}")

    script = repo_root / ACTION_TABLE[action]["script"]
    _resolve_under(repo_root, script, "tool script")
    if not script.exists():
        raise ValueError(f"required tool script is missing: {script}")

    command: List[str] = [sys.executable, str(script)]

    if action == "mission_workspace_validate":
        mission_id = str(params.get("mission_id", plan.get("mission_id", "")))
        _safe_identifier(mission_id, "mission_id")
        command.extend([
            "validate",
            "--workspace-root",
            str(workspace_root),
            "--mission-id",
            mission_id,
        ])

    elif action == "mission_workspace_inspect":
        mission_id = str(params.get("mission_id", plan.get("mission_id", "")))
        _safe_identifier(mission_id, "mission_id")
        command.extend([
            "inspect",
            "--workspace-root",
            str(workspace_root),
            "--mission-id",
            mission_id,
            "--json",
        ])

    elif action == "approval_status":
        mission_id = str(params.get("mission_id", plan.get("mission_id", "")))
        _safe_identifier(mission_id, "mission_id")
        command.extend([
            "status",
            "--workspace-root",
            str(workspace_root),
            "--mission-id",
            mission_id,
        ])

    elif action == "approval_reports_list":
        mission_id = str(params.get("mission_id", plan.get("mission_id", "")))
        _safe_identifier(mission_id, "mission_id")
        command.extend([
            "reports",
            "list",
            "--workspace-root",
            str(workspace_root),
            "--mission-id",
            mission_id,
        ])

    elif action == "runtime_package_validate":
        raw_path = params.get("runtime_package_path")
        if not raw_path:
            raise ValueError("runtime_package_path is required")
        candidate = Path(str(raw_path))
        if not candidate.is_absolute():
            candidate = repo_root / candidate
        allowed_roots = [repo_root.resolve(), sandbox_root.resolve()]
        resolved = candidate.resolve()
        if not any(_is_relative_to(resolved, allowed) for allowed in allowed_roots):
            raise ValueError("runtime_package_path must resolve under repo root or sandbox root")
        if not resolved.exists():
            raise ValueError(f"runtime_package_path does not exist: {resolved}")
        command.append(str(resolved))

    metadata = {
        "action": action,
        "description": ACTION_TABLE[action]["description"],
        "tool_script": str(script),
    }
    return command, metadata


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _tail(text: str, max_chars: int = 4000) -> str:
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def validate_plan(plan: Dict[str, Any]) -> List[str]:
    blockers: List[str] = []
    execution_id = str(plan.get("execution_id", ""))
    action = str(plan.get("action", ""))

    try:
        _safe_identifier(execution_id, "execution_id")
    except Exception as exc:
        blockers.append(str(exc))

    if action not in ACTION_TABLE:
        blockers.append(f"unknown or non-allowlisted action: {action}")

    blockers.extend(_validate_safety(plan))

    if plan.get("requires_human_approval") is not True:
        blockers.append("requires_human_approval must be true")

    return blockers


def build_report(
    plan: Dict[str, Any],
    status: str,
    invocation: str,
    command_metadata: Dict[str, Any],
    command: List[str],
    exit_code: int | None,
    stdout: str,
    stderr: str,
    blockers: List[str],
    report_path: Path | None,
) -> Dict[str, Any]:
    return {
        "report_type": "controlled_tool_execution_report",
        "schema_version": "1.0",
        "status": status,
        "execution_id": plan.get("execution_id"),
        "mission_id": plan.get("mission_id"),
        "action": plan.get("action"),
        "invocation": invocation,
        "approval_required": True,
        "approval_token_name": "EXECUTE_CONTROLLED_TOOL",
        "execution": "allowlisted_tool_only" if invocation == "confirmed" else "preview_only",
        "filesystem_mutation": "sandbox reports and delegated tool outputs only" if invocation == "confirmed" else "blocked",
        "repository_apply": "blocked",
        "git_operations": "blocked",
        "private_context_access": "blocked",
        "real_model_invocation": "blocked",
        "network_access": "blocked",
        "arbitrary_shell": "blocked",
        "model_output_authority": "evidence_only",
        "command_metadata": command_metadata,
        "command": command,
        "exit_code": exit_code,
        "stdout_tail": _tail(stdout),
        "stderr_tail": _tail(stderr),
        "blockers": blockers,
        "report_path": str(report_path) if report_path else None,
    }


def run_confirmed(command: List[str], repo_root: Path, timeout_seconds: int) -> Tuple[int, str, str]:
    completed = subprocess.run(
        command,
        cwd=str(repo_root),
        shell=False,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
    )
    return int(completed.returncode), completed.stdout, completed.stderr


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Konoha Controlled Tool Execution Gate")
    parser.add_argument("--plan", required=True, help="Path to controlled tool execution plan JSON.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--workspace-root", required=True, help="Mission workspace root.")
    parser.add_argument("--sandbox-root", default="sandbox", help="Sandbox root.")
    parser.add_argument("--confirm-execution", action="store_true", help="Execute allowlisted tool.")
    parser.add_argument("--approval-token", default="", help="Exact approval token for confirmed execution.")
    parser.add_argument("--timeout-seconds", type=int, default=120, help="Delegated tool timeout.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing controlled tool report.")
    parser.add_argument("--json", action="store_true", help="Print JSON report or preview.")

    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    workspace_root = Path(args.workspace_root)
    sandbox_root = Path(args.sandbox_root)
    if not workspace_root.is_absolute():
        workspace_root = repo_root / workspace_root
    if not sandbox_root.is_absolute():
        sandbox_root = repo_root / sandbox_root

    try:
        plan_path = Path(args.plan)
        if not plan_path.is_absolute():
            plan_path = repo_root / plan_path
        plan_path = _resolve_under(repo_root, plan_path, "plan path")
        plan = _read_json(plan_path)
        blockers = validate_plan(plan)

        action = str(plan.get("action", ""))
        command: List[str] = []
        command_metadata: Dict[str, Any] = {}
        if not blockers:
            command, command_metadata = _build_command(action, plan, repo_root, workspace_root, sandbox_root)

        if args.confirm_execution and args.approval_token != APPROVAL_TOKEN:
            blockers.append(f"approval token must be exactly {APPROVAL_TOKEN}")

        if blockers:
            report = build_report(
                plan=plan,
                status="failed",
                invocation="blocked",
                command_metadata=command_metadata,
                command=command,
                exit_code=None,
                stdout="",
                stderr="",
                blockers=blockers,
                report_path=None,
            )
            if args.json:
                _print_json(report)
            else:
                print("CONTROLLED TOOL EXECUTION FAILED")
                print(f"Action: {action}")
                print("Execution: blocked")
                print("Repository apply: blocked")
                print("Git operations: blocked")
                print("Private context access: blocked")
                print("Real model invocation: blocked")
                print("Network access: blocked")
                for blocker in blockers:
                    print("Blocker:", blocker)
            return 1

        if not args.confirm_execution:
            report = build_report(
                plan=plan,
                status="preview",
                invocation="preview_only",
                command_metadata=command_metadata,
                command=command,
                exit_code=None,
                stdout="",
                stderr="",
                blockers=[],
                report_path=None,
            )
            if args.json:
                _print_json(report)
            else:
                print("CONTROLLED TOOL EXECUTION PREVIEW")
                print(f"Action: {action}")
                print("Invocation: preview_only")
                print("Execution: blocked")
                print("Filesystem mutation: blocked")
                print("Repository apply: blocked")
                print("Git operations: blocked")
                print("Private context access: blocked")
                print("Real model invocation: blocked")
                print("Network access: blocked")
            return 0

        exit_code, stdout, stderr = run_confirmed(command, repo_root, args.timeout_seconds)
        status = "passed" if exit_code == 0 else "failed"
        report_path = sandbox_root / "reports" / f"{plan['execution_id']}_controlled_tool_execution_report.json"
        report = build_report(
            plan=plan,
            status=status,
            invocation="confirmed",
            command_metadata=command_metadata,
            command=command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            blockers=[] if exit_code == 0 else ["delegated tool returned non-zero exit code"],
            report_path=report_path,
        )
        _write_json(report_path, report, args.force)

        if args.json:
            _print_json(report)
        else:
            print("CONTROLLED TOOL EXECUTION PASSED" if exit_code == 0 else "CONTROLLED TOOL EXECUTION FAILED")
            print(f"Action: {action}")
            print("Execution: allowlisted_tool_only")
            print("Filesystem mutation: sandbox reports and delegated tool outputs only")
            print("Repository apply: blocked")
            print("Git operations: blocked")
            print("Private context access: blocked")
            print("Real model invocation: blocked")
            print("Network access: blocked")
            print(f"Report: {report_path}")
            if exit_code != 0:
                print("Blocker: delegated tool returned non-zero exit code")
        return exit_code

    except Exception as exc:
        payload = {
            "report_type": "controlled_tool_execution_report",
            "status": "failed",
            "invocation": "blocked",
            "blockers": [str(exc)],
            "repository_apply": "blocked",
            "git_operations": "blocked",
            "private_context_access": "blocked",
            "real_model_invocation": "blocked",
            "network_access": "blocked",
        }
        if args.json:
            _print_json(payload)
        else:
            print("CONTROLLED TOOL EXECUTION FAILED")
            print("Execution: blocked")
            print("Repository apply: blocked")
            print("Git operations: blocked")
            print("Private context access: blocked")
            print("Real model invocation: blocked")
            print("Network access: blocked")
            print("Blocker:", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
