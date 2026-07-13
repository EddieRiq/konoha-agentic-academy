#!/usr/bin/env python3
"""Konoha Beta Runtime.

v3.0 beta runtime for supervised real technical tasks.

This module intentionally uses Python stdlib only. It can call external
agent CLIs and run approved commands, but only through explicit subcommands,
explicit flags, explicit approval tokens, path checks, and shell=False.

Core doctrine:
- Model output is evidence only.
- Command proposals are not permission.
- Runtime reports are evidence only.
- Git plans are not permission.
- Push requires explicit approval and explicit network allowance.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.mission_closure.close_mission import main as close_mission_main  # noqa: E402


APPROVAL_TOKENS = {
    "START_BETA_MISSION": "Start or update a supervised beta mission workspace.",
    "PLAN_BETA_MISSION": "Record beta plan and command proposals.",
    "INVOKE_EXTERNAL_AGENT": "Invoke an external agent CLI such as Claude Code or Codex.",
    "INVOKE_LOCAL_MODEL": "Invoke a local model runtime such as Ollama.",
    "PLAN_LOCAL_MODEL_DOWNLOAD": "Record a local model download plan only.",
    "DOWNLOAD_LOCAL_MODEL": "Download a local model through an approved local runtime.",
    "EXECUTE_APPROVED_COMMAND": "Execute one exact approved command with shell=False.",
    "RECORD_EXTERNAL_RESULT": "Record a result produced outside Konoha.",
    "RECORD_BETA_REVIEW": "Record beta self-review and optimization summary.",
    "PLAN_BETA_GIT_OPERATION": "Create a Git operation plan.",
    "APPROVE_BETA_GIT_STAGE": "Run gated git add for approved paths.",
    "APPROVE_BETA_GIT_COMMIT": "Run gated git commit for approved message.",
    "APPROVE_BETA_GIT_PUSH": "Run gated git push with --allow-network.",
    "RECORD_TEACHBACK_EVIDENCE": "Record structured human Teachback evidence.",
    "CLOSE_MISSION_WITH_TEACHBACK": "Close a mission after validated execution, review and Teachback evidence.",
    "CLOSE_BETA_MISSION": "Deprecated alias. Use CLOSE_MISSION_WITH_TEACHBACK through the shared closure gate.",
}

TEACHBACK_CONFIRMATION = "I_CAN_EXPLAIN_AND_DEFEND_THIS_MISSION"  # deprecated compatibility marker

BOUNDARIES = {
    "autonomous_background_agents": "blocked",
    "unapproved_command_execution": "blocked",
    "unapproved_git_operations": "blocked",
    "unapproved_model_invocation": "blocked",
    "private_context_access_by_default": "blocked",
    "arbitrary_shell": "blocked",
    "network_access_by_default": "blocked",
    "mission_closure_without_teachback": "blocked",
}

DANGEROUS_COMMAND_PATTERNS = [
    r"\brm\b",
    r"\brmdir\b",
    r"\bdel\b",
    r"\berase\b",
    r"\bformat\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bmkfs\b",
    r"\bdd\b",
    r"\bchmod\s+777\b",
    r"\bchown\b",
    r"\bInvoke-WebRequest\b",
    r"\bcurl\b",
    r"\bwget\b",
    r"\bscp\b",
    r"\brsync\b",
    r"\bftp\b",
    r"\bsftp\b",
    r"\bnet\s+use\b",
    r"\bpowershell\b",
    r"\bcmd\b",
    r"\bbash\s+-c\b",
    r"\bsh\s+-c\b",
    r"\|\s*",
    r";",
    r"&&",
    r"\|\|",
    r">",
    r"<",
    r"`",
    r"\.env",
    r"secret",
    r"credential",
    r"token",
    r"private-library",
    r"alliance[/\\]kirigakure",
]

FORBIDDEN_GIT_PATH_PATTERNS = [
    r"(^|[/\\])\.git($|[/\\])",
    r"(^|[/\\])\.env",
    r"secret",
    r"credential",
    # Block obvious private token locations without blocking public token usage schemas.
    r"(^|[/\\])(token|tokens)($|[/\\])",
    r"(^|[/\\]).*(token|tokens).*(\.txt|\.key|\.pem|\.env)$",
    r"private-library",
    r"alliance[/\\]kirigakure",
    r"(^|[/\\])vault($|[/\\])",
]


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, default: Optional[Any] = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any, force: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file without --force: {path}")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def safe_id(value: str, field: str = "id") -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{1,120}", value or ""):
        raise ValueError(f"Unsafe {field}: {value!r}")
    return value


def safe_root(path: str, name: str = "path") -> Path:
    p = Path(path).expanduser().resolve()
    return p


def mission_dir(workspace_root: Path, mission_id: str) -> Path:
    safe_id(mission_id, "mission_id")
    return workspace_root.resolve() / "missions" / mission_id


def ensure_mission_dirs(base: Path) -> None:
    for sub in [
        "inputs",
        "context",
        "plans",
        "outputs",
        "reports",
        "approvals",
        "evidence",
        "evidence/agent_invocations",
        "evidence/command_results",
        "notifications",
        "git",
        "logs",
    ]:
        (base / sub).mkdir(parents=True, exist_ok=True)


def state_path(base: Path) -> Path:
    return base / "beta_mission_state.json"


def load_state(base: Path) -> Dict[str, Any]:
    return load_json(state_path(base), default={})


def save_state(base: Path, state: Dict[str, Any], force: bool = True) -> None:
    write_json(state_path(base), state, force=force)


def print_json(payload: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = payload.get("status", "unknown")
        command = payload.get("command", "unknown")
        print(f"KONOHA BETA {status.upper()}")
        print(f"Command: {command}")
        for key, value in payload.get("boundaries", BOUNDARIES).items():
            print(f"{key}: {value}")
        if payload.get("blockers"):
            print("Blockers:")
            for blocker in payload["blockers"]:
                print(f"- {blocker}")
        if payload.get("output_paths"):
            print("Output paths:")
            for p in payload["output_paths"]:
                print(f"- {p}")
        if payload.get("summary"):
            print(payload["summary"])


def require_token(given: Optional[str], expected: str) -> None:
    if given != expected:
        raise PermissionError(f"Expected approval token {expected!r}")


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, int((len(text) + 3) / 4))


def append_token_record(base: Path, record: Dict[str, Any]) -> None:
    ledger_path = base / "reports" / "beta_token_usage_ledger.json"
    ledger = load_json(ledger_path, default={
        "schema_version": "1.0.0",
        "report_type": "beta_token_usage_ledger",
        "generated_at": now(),
        "records": [],
        "totals": {},
        "authority": {
            "token_estimates_are_not_truth": True,
            "usage_reports_do_not_authorize_execution": True,
        },
    })
    ledger["records"].append(record)
    totals = {
        "estimated_input_tokens": 0,
        "estimated_output_tokens": 0,
        "actual_input_tokens": 0,
        "actual_output_tokens": 0,
        "estimated_records": 0,
        "actual_records": 0,
    }
    for item in ledger["records"]:
        source = item.get("usage_source", "estimated")
        if source == "provider_reported":
            totals["actual_records"] += 1
            totals["actual_input_tokens"] += int(item.get("input_tokens", 0))
            totals["actual_output_tokens"] += int(item.get("output_tokens", 0))
        else:
            totals["estimated_records"] += 1
            totals["estimated_input_tokens"] += int(item.get("input_tokens", 0))
            totals["estimated_output_tokens"] += int(item.get("output_tokens", 0))
    ledger["generated_at"] = now()
    ledger["totals"] = totals
    write_json(ledger_path, ledger, force=True)


def detect_tool(name: str) -> Dict[str, Any]:
    path = shutil.which(name)
    return {
        "name": name,
        "available": bool(path),
        "path": path,
    }


def detect_runtime_tools() -> Dict[str, Any]:
    tools = {}
    for name in ["git", "python", "claude", "codex", "ollama", "docker", "ssh", "java"]:
        tools[name] = detect_tool(name)
    return tools


def classify_task(task: str, domain: str = "general") -> Dict[str, Any]:
    text = (task or "").lower()
    tags: List[str] = []
    if any(word in text for word in ["docker", "container", "compose"]):
        tags.append("docker")
    if any(word in text for word in ["airflow", "dag", "scheduler"]):
        tags.append("airflow")
    if any(word in text for word in ["server", "ssh", "linux", "remote"]):
        tags.append("server")
    if any(word in text for word in ["jar", "java"]):
        tags.append("java_jar")
    if any(word in text for word in ["python", "script", "etl", "pipeline"]):
        tags.append("python")
    if any(word in text for word in ["sql", "database", "db2", "postgres"]):
        tags.append("data")
    if any(word in text for word in ["readme", "docs", "documentation"]):
        tags.append("documentation")
    if not tags:
        tags.append(domain or "general")
    risk = "medium"
    if any(tag in tags for tag in ["server", "docker", "airflow", "java_jar", "data"]):
        risk = "high"
    return {"domain": domain, "tags": tags, "risk_level": risk}


def recommended_model_strategy(task_info: Dict[str, Any], tools: Dict[str, Any]) -> Dict[str, Any]:
    tags = task_info.get("tags", [])
    risk = task_info.get("risk_level", "medium")
    local_available = bool(tools.get("ollama", {}).get("available"))
    codex_available = bool(tools.get("codex", {}).get("available"))
    claude_available = bool(tools.get("claude", {}).get("available"))
    primary = "mock"
    rationale = []
    if local_available and risk in ["low", "medium"]:
        primary = "ollama"
        rationale.append("Local model runtime detected and risk is not high.")
    elif codex_available:
        primary = "codex"
        rationale.append("Codex CLI detected and suitable for coding/repo tasks under its sandbox.")
    elif claude_available:
        primary = "claude"
        rationale.append("Claude Code detected and suitable for planning/review with explicit approval.")
    else:
        primary = "mock"
        rationale.append("No supported external/local agent CLI detected; use mock/plan-only mode.")
    if risk == "high":
        rationale.append("High-risk task should use stronger review and explicit approvals.")
    if "server" in tags:
        rationale.append("Server-related tasks require command proposals and human-reviewed execution.")
    return {
        "primary_provider": primary,
        "fallback_provider": "mock",
        "local_model_candidate": "qwen2.5-coder:7b-instruct",
        "download_required_for_local_candidate": not local_available,
        "rationale": rationale,
        "model_choice_is_not_permission": True,
    }


def command_proposals_for_task(task: str, task_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    tags = task_info.get("tags", [])
    proposals: List[Dict[str, Any]] = [
        {
            "command_id": "inspect-python",
            "title": "Inspect Python version",
            "command": "python --version",
            "risk": "low",
            "reason": "Confirm local Python availability for Konoha and project scripts.",
        },
        {
            "command_id": "inspect-git-status",
            "title": "Inspect Git status",
            "command": "git status --short",
            "risk": "low",
            "reason": "Confirm repository cleanliness before work.",
        },
    ]
    if "docker" in tags or "airflow" in tags:
        proposals.extend([
            {
                "command_id": "inspect-docker",
                "title": "Inspect Docker version",
                "command": "docker --version",
                "risk": "medium",
                "reason": "Check Docker availability for containerized tasks.",
            },
            {
                "command_id": "inspect-docker-compose",
                "title": "Inspect Docker Compose version",
                "command": "docker compose version",
                "risk": "medium",
                "reason": "Check Docker Compose availability before proposing compose-based work.",
            },
        ])
    if "java_jar" in tags:
        proposals.append({
            "command_id": "inspect-java",
            "title": "Inspect Java version",
            "command": "java -version",
            "risk": "medium",
            "reason": "Check Java runtime before any JAR workflow.",
        })
    if "server" in tags:
        proposals.append({
            "command_id": "inspect-ssh",
            "title": "Inspect SSH client",
            "command": "ssh -V",
            "risk": "medium",
            "reason": "Check SSH client availability. This does not connect to a server.",
        })
    if "python" in tags or "data" in tags:
        proposals.append({
            "command_id": "inspect-pip-freeze",
            "title": "Inspect installed Python packages",
            "command": "python -m pip list",
            "risk": "medium",
            "reason": "Inspect local Python environment under human approval.",
        })
    for item in proposals:
        item.update({
            "proposal_is_not_permission": True,
            "requires_approval_token": "EXECUTE_APPROVED_COMMAND",
        })
    return proposals


def command_is_dangerous(command: str) -> Optional[str]:
    lowered = command.lower()
    for pattern in DANGEROUS_COMMAND_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            return pattern
    return None


def split_command(command: str) -> List[str]:
    # PowerShell-style commands are intentionally not supported here. v3 beta
    # uses direct process invocation with shell=False only.
    if os.name == "nt":
        return shlex.split(command, posix=False)
    return shlex.split(command)


def run_process(args: List[str], cwd: Path, timeout: int = 120, env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    started = time.time()
    completed = subprocess.run(
        args,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
        timeout=timeout,
        env=env,
    )
    elapsed = time.time() - started
    return {
        "args": args,
        "cwd": str(cwd),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "duration_seconds": round(elapsed, 3),
    }


def write_charter(base: Path, args: argparse.Namespace, task_info: Dict[str, Any]) -> Path:
    charter = f"""# Mission Charter: {args.mission_id}

## Title

{args.title}

## Task

{args.task}

## Risk level

{task_info.get('risk_level')}

## Task tags

{', '.join(task_info.get('tags', []))}

## Authority

- Command proposals are not permission.
- Model output is evidence only.
- Runtime reports are evidence only.
- Git plans are not permission.
- Mission closure requires teachback.

## Required approvals

- START_BETA_MISSION
- PLAN_BETA_MISSION
- INVOKE_EXTERNAL_AGENT or INVOKE_LOCAL_MODEL
- EXECUTE_APPROVED_COMMAND
- PLAN_BETA_GIT_OPERATION
- APPROVE_BETA_GIT_STAGE
- APPROVE_BETA_GIT_COMMIT
- APPROVE_BETA_GIT_PUSH
- CLOSE_BETA_MISSION

## Forbidden by default

{json.dumps(BOUNDARIES, indent=2)}
"""
    path = base / "charter.md"
    path.write_text(charter, encoding="utf-8")
    return path


def cmd_doctor(args: argparse.Namespace) -> int:
    payload = {
        "schema_version": "1.0.0",
        "report_type": "konoha_beta_doctor_report",
        "command": "doctor",
        "status": "passed",
        "generated_at": now(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
        },
        "tools": detect_runtime_tools(),
        "boundaries": BOUNDARIES,
        "authority": {
            "doctor_is_evidence_only": True,
            "tool_presence_is_not_permission": True,
        },
    }
    if args.output:
        write_json(Path(args.output).resolve(), payload, force=args.force)
        payload["output_paths"] = [str(Path(args.output).resolve())]
    print_json(payload, args.json)
    return 0


def teachback_level_for_risk(risk_level: str) -> int:
    return {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }.get((risk_level or "medium").lower(), 2)


def cmd_start(args: argparse.Namespace) -> int:
    if not args.confirm_start:
        payload = {
            "schema_version": "1.0.0",
            "report_type": "konoha_beta_start_preview",
            "command": "start",
            "status": "preview",
            "generated_at": now(),
            "mission_id": args.mission_id,
            "boundaries": BOUNDARIES,
            "summary": "Preview only. No mission workspace written.",
        }
        print_json(payload, args.json)
        return 0

    require_token(args.approval_token, "START_BETA_MISSION")
    workspace_root = safe_root(args.workspace_root, "workspace_root")
    base = mission_dir(workspace_root, args.mission_id)
    ensure_mission_dirs(base)

    task_info = classify_task(args.task, args.task_domain)
    tools = detect_runtime_tools()
    model_strategy = recommended_model_strategy(task_info, tools)
    charter_path = write_charter(base, args, task_info)

    manifest = {
        "schema_version": "1.0.0",
        "mission_id": args.mission_id,
        "title": args.title,
        "task": args.task,
        "task_domain": args.task_domain,
        "created_at": now(),
        "status": "started",
        "runtime": "konoha_beta_v3",
        "task_info": task_info,
        "model_strategy": model_strategy,
        "teachback": {
            "required": True,
            "required_level": teachback_level_for_risk(
                task_info.get("risk_level", "medium")
            ),
            "skip_allowed": False,
        },
        "boundaries": BOUNDARIES,
    }
    manifest_path = base / "mission_manifest.json"
    write_json(manifest_path, manifest, force=args.force)

    state = {
        "schema_version": "1.0.0",
        "mission_id": args.mission_id,
        "title": args.title,
        "task": args.task,
        "status": "started",
        "created_at": now(),
        "updated_at": now(),
        "task_info": task_info,
        "model_strategy": model_strategy,
        "events": [
            {"at": now(), "type": "mission_started", "actor": args.actor or "human", "approval_token": "START_BETA_MISSION"}
        ],
        "command_results": [],
        "agent_invocations": [],
        "git_operations": [],
        "boundaries": BOUNDARIES,
    }
    save_state(base, state)

    notification = {
        "schema_version": "1.0.0",
        "state": "ready_for_planning",
        "severity": "attention",
        "required_human_action": "Review and approve beta mission plan.",
        "updated_at": now(),
        "authority": {"notification_state_is_evidence_only": True},
    }
    write_json(base / "mission_notification_state.json", notification, force=True)

    payload = {
        "schema_version": "1.0.0",
        "report_type": "konoha_beta_start_report",
        "command": "start",
        "status": "passed",
        "generated_at": now(),
        "mission_id": args.mission_id,
        "boundaries": BOUNDARIES,
        "output_paths": [str(charter_path), str(manifest_path), str(state_path(base)), str(base / "mission_notification_state.json")],
        "summary": "Beta mission started. Planning is next.",
    }
    write_json(base / "reports" / f"{args.mission_id}_beta_start_report.json", payload, force=True)
    print_json(payload, args.json)
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    base = mission_dir(safe_root(args.workspace_root), args.mission_id)
    if not base.exists():
        raise FileNotFoundError(f"Mission does not exist: {base}")
    if not args.confirm_plan:
        payload = {
            "schema_version": "1.0.0",
            "report_type": "konoha_beta_plan_preview",
            "command": "plan",
            "status": "preview",
            "generated_at": now(),
            "mission_id": args.mission_id,
            "boundaries": BOUNDARIES,
            "summary": "Preview only. No plan written.",
        }
        print_json(payload, args.json)
        return 0

    require_token(args.approval_token, "PLAN_BETA_MISSION")
    state = load_state(base)
    task = args.task or state.get("task", "")
    task_domain = args.task_domain or state.get("task_info", {}).get("domain", "general")
    task_info = classify_task(task, task_domain)
    tools = detect_runtime_tools()
    model_strategy = recommended_model_strategy(task_info, tools)
    proposals = command_proposals_for_task(task, task_info)

    plan = {
        "schema_version": "1.0.0",
        "report_type": "konoha_beta_runtime_plan",
        "plan_id": args.plan_id,
        "mission_id": args.mission_id,
        "created_at": now(),
        "task": task,
        "task_info": task_info,
        "model_strategy": model_strategy,
        "stages": [
            {"stage": "environment_doctor", "status": "ready", "requires_human_approval": True},
            {"stage": "agent_planning", "status": "ready", "requires_human_approval": True},
            {"stage": "command_execution", "status": "proposed_only", "requires_human_approval": True},
            {"stage": "verification", "status": "ready", "requires_human_approval": True},
            {"stage": "self_review", "status": "ready", "requires_human_approval": True},
            {"stage": "git_gate", "status": "ready_when_changes_exist", "requires_human_approval": True},
            {"stage": "teachback_closure", "status": "ready_when_reviewed", "requires_human_approval": True},
        ],
        "authority": {
            "plan_is_not_permission": True,
            "command_proposals_are_not_permission": True,
            "model_choice_is_not_permission": True,
        },
        "boundaries": BOUNDARIES,
    }
    plan_path = base / "plans" / f"{args.plan_id}_beta_runtime_plan.json"
    proposals_path = base / "plans" / f"{args.plan_id}_command_proposals.json"
    write_json(plan_path, plan, force=args.force)
    write_json(proposals_path, {
        "schema_version": "1.0.0",
        "report_type": "beta_command_proposals",
        "mission_id": args.mission_id,
        "plan_id": args.plan_id,
        "created_at": now(),
        "proposals": proposals,
        "authority": {"command_proposals_are_not_permission": True},
    }, force=args.force)

    prompt = build_agent_prompt(args.mission_id, task, task_info, proposals)
    prompt_path = base / "inputs" / f"{args.plan_id}_agent_prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    state["status"] = "planned"
    state["updated_at"] = now()
    state["task_info"] = task_info
    state["model_strategy"] = model_strategy
    state["latest_plan"] = str(plan_path)
    state["latest_command_proposals"] = str(proposals_path)
    state.setdefault("events", []).append({"at": now(), "type": "mission_planned", "approval_token": "PLAN_BETA_MISSION"})
    save_state(base, state)

    notification = {
        "schema_version": "1.0.0",
        "state": "waiting_approval",
        "severity": "attention",
        "reason": "Plan and command proposals are ready.",
        "required_human_action": "Review plan, choose model/agent, approve external agent or command execution step.",
        "updated_at": now(),
    }
    write_json(base / "mission_notification_state.json", notification, force=True)

    payload = {
        "schema_version": "1.0.0",
        "report_type": "konoha_beta_plan_report",
        "command": "plan",
        "status": "passed",
        "generated_at": now(),
        "mission_id": args.mission_id,
        "boundaries": BOUNDARIES,
        "output_paths": [str(plan_path), str(proposals_path), str(prompt_path)],
        "summary": "Beta runtime plan and command proposals created.",
    }
    write_json(base / "reports" / f"{args.plan_id}_beta_plan_report.json", payload, force=True)
    print_json(payload, args.json)
    return 0


def build_agent_prompt(mission_id: str, task: str, task_info: Dict[str, Any], proposals: List[Dict[str, Any]]) -> str:
    return f"""# Konoha Beta Agent Prompt

Mission: {mission_id}

Task:

{task}

Task classification:

```json
{json.dumps(task_info, indent=2)}
```

Command proposals prepared by Konoha:

```json
{json.dumps(proposals, indent=2)}
```

Instructions:

1. Do not execute commands.
2. Do not modify files.
3. Produce a plan, risks, missing context, validation checklist, and next approved actions.
4. Treat all outputs as evidence only.
5. Ask for missing context instead of assuming.
6. Keep private context local.
"""


def cmd_agent(args: argparse.Namespace) -> int:
    base = mission_dir(safe_root(args.workspace_root), args.mission_id)
    if not base.exists():
        raise FileNotFoundError(f"Mission does not exist: {base}")
    if not args.confirm_invoke:
        payload = {
            "schema_version": "1.0.0",
            "report_type": "beta_agent_invocation_preview",
            "command": "agent",
            "status": "preview",
            "generated_at": now(),
            "provider": args.provider,
            "boundaries": BOUNDARIES,
            "summary": "Preview only. External/local agent not invoked.",
        }
        print_json(payload, args.json)
        return 0

    if args.provider in ["claude", "codex"]:
        require_token(args.approval_token, "INVOKE_EXTERNAL_AGENT")
        if not args.allow_external_agent:
            raise PermissionError("External agent invocation requires --allow-external-agent.")
    elif args.provider in ["ollama"]:
        require_token(args.approval_token, "INVOKE_LOCAL_MODEL")
        if not args.allow_local_model:
            raise PermissionError("Local model invocation requires --allow-local-model.")
    elif args.provider == "mock":
        require_token(args.approval_token, "INVOKE_EXTERNAL_AGENT")
    else:
        raise ValueError(f"Unsupported provider: {args.provider}")

    prompt = args.prompt or ""
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    if not prompt.strip():
        raise ValueError("Prompt is required via --prompt or --prompt-file.")

    cwd = safe_root(args.working_dir or ".")
    if args.provider == "mock":
        stdout = (
            "Mock agent plan:\n"
            "- clarify acceptance criteria\n"
            "- inspect environment with approved commands\n"
            "- implement in small patches\n"
            "- validate with tests\n"
            "- summarize token and command usage\n"
        )
        stderr = ""
        exit_code = 0
        duration = 0.0
        raw = {"args": ["mock"], "cwd": str(cwd), "exit_code": 0, "stdout": stdout, "stderr": "", "duration_seconds": 0.0}
        usage_source = "estimated"
        input_tokens = estimate_tokens(prompt)
        output_tokens = estimate_tokens(stdout)
    elif args.provider == "claude":
        exe = shutil.which("claude")
        if not exe:
            raise FileNotFoundError("Claude Code CLI not found on PATH.")
        raw = run_process([exe, "-p", prompt], cwd=cwd, timeout=args.timeout)
        stdout = raw["stdout"]
        stderr = raw["stderr"]
        exit_code = raw["exit_code"]
        duration = raw["duration_seconds"]
        usage_source = "estimated"
        input_tokens = estimate_tokens(prompt)
        output_tokens = estimate_tokens(stdout)
    elif args.provider == "codex":
        exe = shutil.which("codex")
        if not exe:
            raise FileNotFoundError("Codex CLI not found on PATH.")
        cmd = [exe, "exec", "--json", "--sandbox", args.codex_sandbox, prompt]
        if args.codex_ephemeral:
            cmd.insert(2, "--ephemeral")
        raw = run_process(cmd, cwd=cwd, timeout=args.timeout)
        stdout = raw["stdout"]
        stderr = raw["stderr"]
        exit_code = raw["exit_code"]
        duration = raw["duration_seconds"]
        usage = parse_codex_usage(stdout)
        if usage:
            usage_source = "provider_reported"
            input_tokens = int(usage.get("input_tokens", 0))
            output_tokens = int(usage.get("output_tokens", 0))
        else:
            usage_source = "estimated"
            input_tokens = estimate_tokens(prompt)
            output_tokens = estimate_tokens(stdout)
    elif args.provider == "ollama":
        exe = shutil.which("ollama")
        if not exe:
            raise FileNotFoundError("Ollama CLI not found on PATH.")
        raw = run_process([exe, "run", args.model, prompt], cwd=cwd, timeout=args.timeout)
        stdout = raw["stdout"]
        stderr = raw["stderr"]
        exit_code = raw["exit_code"]
        duration = raw["duration_seconds"]
        usage_source = "estimated"
        input_tokens = estimate_tokens(prompt)
        output_tokens = estimate_tokens(stdout)
    else:
        raise AssertionError(args.provider)

    invocation_id = safe_id(args.invocation_id, "invocation_id")
    record = {
        "schema_version": "1.0.0",
        "report_type": "beta_agent_invocation",
        "invocation_id": invocation_id,
        "mission_id": args.mission_id,
        "provider": args.provider,
        "model": args.model,
        "generated_at": now(),
        "working_dir": str(cwd),
        "exit_code": exit_code,
        "duration_seconds": duration,
        "stdout": stdout[-20000:],
        "stderr": stderr[-8000:],
        "usage": {
            "usage_source": usage_source,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "token_estimates_are_not_truth": usage_source != "provider_reported",
        },
        "authority": {
            "model_output_is_evidence_only": True,
            "model_inference_is_never_permission": True,
        },
        "boundaries": BOUNDARIES,
    }
    out = base / "evidence" / "agent_invocations" / f"{invocation_id}_agent_invocation.json"
    write_json(out, record, force=args.force)
    append_token_record(base, {
        "usage_id": invocation_id,
        "mission_id": args.mission_id,
        "stage": "agent_invocation",
        "provider": args.provider,
        "model": args.model,
        "usage_source": usage_source,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "success": exit_code == 0,
        "recorded_at": now(),
    })
    state = load_state(base)
    state.setdefault("agent_invocations", []).append(str(out))
    state["updated_at"] = now()
    save_state(base, state)

    payload = {
        "schema_version": "1.0.0",
        "report_type": "beta_agent_invocation_report",
        "command": "agent",
        "status": "passed" if exit_code == 0 else "failed",
        "generated_at": now(),
        "mission_id": args.mission_id,
        "provider": args.provider,
        "boundaries": BOUNDARIES,
        "output_paths": [str(out), str(base / "reports" / "beta_token_usage_ledger.json")],
        "summary": f"Agent invocation completed with exit code {exit_code}. Output is evidence only.",
    }
    print_json(payload, args.json)
    return 0 if exit_code == 0 else 1


def parse_codex_usage(stdout: str) -> Optional[Dict[str, Any]]:
    usage = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and item.get("type") == "turn.completed" and isinstance(item.get("usage"), dict):
            usage = item["usage"]
    return usage


def cmd_plan_download(args: argparse.Namespace) -> int:
    base = mission_dir(safe_root(args.workspace_root), args.mission_id)
    if not base.exists():
        raise FileNotFoundError(f"Mission does not exist: {base}")
    if not args.confirm_plan:
        print_json({
            "schema_version": "1.0.0",
            "report_type": "local_model_download_plan_preview",
            "command": "plan-download",
            "status": "preview",
            "generated_at": now(),
            "summary": "Preview only. No download plan written. No model downloaded.",
            "boundaries": BOUNDARIES,
        }, args.json)
        return 0
    require_token(args.approval_token, "PLAN_LOCAL_MODEL_DOWNLOAD")
    plan_id = safe_id(args.plan_id, "plan_id")
    plan = {
        "schema_version": "1.0.0",
        "report_type": "local_model_download_plan",
        "plan_id": plan_id,
        "mission_id": args.mission_id,
        "provider": args.provider,
        "model": args.model,
        "reason": args.reason,
        "created_at": now(),
        "proposed_command": f"{args.provider} pull {args.model}",
        "download_plan_does_not_download_models": True,
        "requires_token_for_download": "DOWNLOAD_LOCAL_MODEL",
        "boundaries": BOUNDARIES,
    }
    out = base / "plans" / f"{plan_id}_local_model_download_plan.json"
    write_json(out, plan, force=args.force)
    print_json({
        "schema_version": "1.0.0",
        "report_type": "local_model_download_plan_report",
        "command": "plan-download",
        "status": "passed",
        "generated_at": now(),
        "output_paths": [str(out)],
        "summary": "Local model download plan recorded. No download executed.",
        "boundaries": BOUNDARIES,
    }, args.json)
    return 0


def cmd_download_model(args: argparse.Namespace) -> int:
    base = mission_dir(safe_root(args.workspace_root), args.mission_id)
    if not args.confirm_download:
        print_json({
            "schema_version": "1.0.0",
            "report_type": "local_model_download_preview",
            "command": "download-model",
            "status": "preview",
            "generated_at": now(),
            "summary": "Preview only. No model downloaded.",
            "boundaries": BOUNDARIES,
        }, args.json)
        return 0
    require_token(args.approval_token, "DOWNLOAD_LOCAL_MODEL")
    if not args.allow_network:
        raise PermissionError("Model download requires --allow-network.")
    if args.provider != "ollama":
        raise ValueError("v3.0 beta supports model download only through ollama.")
    exe = shutil.which("ollama")
    if not exe:
        raise FileNotFoundError("Ollama CLI not found on PATH.")
    raw = run_process([exe, "pull", args.model], cwd=safe_root("."), timeout=args.timeout)
    out = base / "evidence" / f"{safe_id(args.download_id, 'download_id')}_local_model_download_report.json"
    report = {
        "schema_version": "1.0.0",
        "report_type": "local_model_download_report",
        "download_id": args.download_id,
        "mission_id": args.mission_id,
        "provider": args.provider,
        "model": args.model,
        "generated_at": now(),
        "exit_code": raw["exit_code"],
        "stdout": raw["stdout"][-20000:],
        "stderr": raw["stderr"][-8000:],
        "duration_seconds": raw["duration_seconds"],
        "authority": {
            "download_report_is_evidence_only": True,
            "download_does_not_authorize_model_invocation": True,
        },
    }
    write_json(out, report, force=args.force)
    print_json({
        "schema_version": "1.0.0",
        "report_type": "local_model_download_gate_report",
        "command": "download-model",
        "status": "passed" if raw["exit_code"] == 0 else "failed",
        "generated_at": now(),
        "output_paths": [str(out)],
        "boundaries": BOUNDARIES,
        "summary": f"Download command completed with exit code {raw['exit_code']}.",
    }, args.json)
    return 0 if raw["exit_code"] == 0 else 1


def load_proposals(base: Path, plan_id: str) -> List[Dict[str, Any]]:
    path = base / "plans" / f"{plan_id}_command_proposals.json"
    payload = load_json(path)
    return payload.get("proposals", [])


def cmd_execute(args: argparse.Namespace) -> int:
    base = mission_dir(safe_root(args.workspace_root), args.mission_id)
    if not args.confirm_execute:
        print_json({
            "schema_version": "1.0.0",
            "report_type": "command_execution_preview",
            "command": "execute-command",
            "status": "preview",
            "generated_at": now(),
            "summary": "Preview only. Command not executed.",
            "boundaries": BOUNDARIES,
        }, args.json)
        return 0
    require_token(args.approval_token, "EXECUTE_APPROVED_COMMAND")
    proposals = load_proposals(base, args.plan_id)
    proposal = next((p for p in proposals if p.get("command_id") == args.command_id), None)
    if not proposal:
        raise ValueError(f"Command proposal not found: {args.command_id}")
    command = proposal["command"]
    risky = command_is_dangerous(command)
    if risky and not args.allow_risky_command:
        raise PermissionError(f"Command blocked by safety pattern {risky!r}.")
    if risky:
        require_token(args.risky_approval_token, "EXECUTE_RISKY_COMMAND")
    workdir = safe_root(args.working_dir or ".")
    result = run_process(split_command(command), cwd=workdir, timeout=args.timeout)
    result_id = safe_id(args.result_id or f"{args.command_id}-{int(time.time())}", "result_id")
    record = {
        "schema_version": "1.0.0",
        "report_type": "beta_command_execution_report",
        "result_id": result_id,
        "mission_id": args.mission_id,
        "plan_id": args.plan_id,
        "command_id": args.command_id,
        "command": command,
        "executed_at": now(),
        "executed_by": "konoha_beta",
        "approval_token": "EXECUTE_APPROVED_COMMAND",
        "exit_code": result["exit_code"],
        "duration_seconds": result["duration_seconds"],
        "stdout": result["stdout"][-20000:],
        "stderr": result["stderr"][-8000:],
        "authority": {
            "recorded_command_result_is_evidence_only": True,
            "command_result_does_not_authorize_next_action": True,
        },
        "boundaries": BOUNDARIES,
    }
    out = base / "evidence" / "command_results" / f"{result_id}.json"
    write_json(out, record, force=args.force)
    state = load_state(base)
    state.setdefault("command_results", []).append(str(out))
    state["updated_at"] = now()
    save_state(base, state)
    print_json({
        "schema_version": "1.0.0",
        "report_type": "beta_command_execution_gate_report",
        "command": "execute-command",
        "status": "passed" if result["exit_code"] == 0 else "failed",
        "generated_at": now(),
        "output_paths": [str(out)],
        "boundaries": BOUNDARIES,
        "summary": f"Command completed with exit code {result['exit_code']}. Result is evidence only.",
    }, args.json)
    return 0 if result["exit_code"] == 0 else 1


def cmd_record_result(args: argparse.Namespace) -> int:
    base = mission_dir(safe_root(args.workspace_root), args.mission_id)
    if not args.confirm_record:
        print_json({
            "schema_version": "1.0.0",
            "report_type": "external_result_record_preview",
            "command": "record-result",
            "status": "preview",
            "generated_at": now(),
            "summary": "Preview only. External result not recorded.",
            "boundaries": BOUNDARIES,
        }, args.json)
        return 0
    require_token(args.approval_token, "RECORD_EXTERNAL_RESULT")
    result_id = safe_id(args.result_id, "result_id")
    record = {
        "schema_version": "1.0.0",
        "report_type": "beta_command_execution_report",
        "result_id": result_id,
        "mission_id": args.mission_id,
        "command_id": args.command_id,
        "command": args.command,
        "executed_at": now(),
        "executed_by": args.executed_by or "human",
        "exit_code": args.exit_code,
        "stdout": args.stdout_summary or "",
        "stderr": args.stderr_summary or "",
        "observation": args.observation or "",
        "authority": {
            "recorded_external_result_is_evidence_only": True,
            "result_does_not_authorize_next_action": True,
        },
    }
    out = base / "evidence" / "command_results" / f"{result_id}.json"
    write_json(out, record, force=args.force)
    print_json({
        "schema_version": "1.0.0",
        "report_type": "external_result_record_report",
        "command": "record-result",
        "status": "passed",
        "generated_at": now(),
        "output_paths": [str(out)],
        "boundaries": BOUNDARIES,
    }, args.json)
    return 0


def summarize_mission(base: Path) -> Dict[str, Any]:
    state = load_state(base)
    reports = list((base / "reports").glob("*.json")) if (base / "reports").exists() else []
    agent_invocations = list((base / "evidence" / "agent_invocations").glob("*.json")) if (base / "evidence" / "agent_invocations").exists() else []
    command_results = list((base / "evidence" / "command_results").glob("*.json")) if (base / "evidence" / "command_results").exists() else []
    token_ledger = load_json(base / "reports" / "beta_token_usage_ledger.json", default={})
    failures = 0
    for p in command_results:
        try:
            if int(load_json(p).get("exit_code", 0)) != 0:
                failures += 1
        except Exception:
            failures += 1
    return {
        "state": state.get("status"),
        "reports_count": len(reports),
        "agent_invocations_count": len(agent_invocations),
        "command_results_count": len(command_results),
        "command_failures_count": failures,
        "token_totals": token_ledger.get("totals", {}),
        "latest_notification": load_json(base / "mission_notification_state.json", default={}),
    }


def cmd_status(args: argparse.Namespace) -> int:
    base = mission_dir(safe_root(args.workspace_root), args.mission_id)
    payload = {
        "schema_version": "1.0.0",
        "report_type": "konoha_beta_status_report",
        "command": "status",
        "status": "passed",
        "generated_at": now(),
        "mission_id": args.mission_id,
        "summary_data": summarize_mission(base),
        "boundaries": BOUNDARIES,
    }
    print_json(payload, args.json)
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    base = mission_dir(
        safe_root(args.workspace_root),
        args.mission_id,
    )
    if not args.confirm_review:
        print_json(
            {
                "schema_version": "1.0.0",
                "report_type": "konoha_beta_review_preview",
                "command": "review",
                "status": "preview",
                "generated_at": now(),
                "summary": (
                    "Preview only. No human review decision written."
                ),
                "boundaries": BOUNDARIES,
            },
            args.json,
        )
        return 0

    require_token(args.approval_token, "RECORD_BETA_REVIEW")
    if args.decision not in {"approved", "changes_requested"}:
        raise ValueError(
            "--decision must be approved or changes_requested"
        )
    if len((args.review_summary or "").strip()) < 20:
        raise ValueError(
            "review summary must be at least 20 characters"
        )
    if not (args.human_actor or "").strip():
        raise ValueError("human actor is required")

    summary = summarize_mission(base)
    suggestions: List[str] = []
    if summary["agent_invocations_count"] == 0:
        suggestions.append(
            "No approved agent invocation is recorded."
        )
    if summary["command_failures_count"] > 0:
        suggestions.append(
            "Analyze failed command evidence before retry."
        )
    if not suggestions:
        suggestions.append(
            "Mission evidence is coherent for the recorded decision."
        )

    report = {
        "schema_version": "1.0.0",
        "report_type": "konoha_human_review_record",
        "review_id": safe_id(args.review_id, "review_id"),
        "mission_id": args.mission_id,
        "status": "passed",
        "review_decision": args.decision,
        "human_approval": args.decision == "approved",
        "reviewed_by": args.human_actor,
        "review_summary": args.review_summary.strip(),
        "generated_at": now(),
        "mission_summary": summary,
        "quality_assessment": {
            "status": args.decision,
            "suggested_optimizations": suggestions,
        },
        "authority": {
            "review_records_human_evidence_only": True,
            "review_does_not_authorize_execution": True,
            "review_does_not_close_mission": True,
        },
        "boundaries": BOUNDARIES,
    }
    out = (
        base
        / "reports"
        / (
            f"{safe_id(args.review_id, 'review_id')}"
            "_konoha_human_review_record.json"
        )
    )
    write_json(out, report, force=args.force)
    print_json(
        {
            "schema_version": "1.0.0",
            "report_type": "konoha_beta_review_gate_report",
            "command": "review",
            "status": "passed",
            "review_decision": args.decision,
            "generated_at": now(),
            "output_paths": [str(out)],
            "boundaries": BOUNDARIES,
            "summary": (
                "Human review decision recorded. "
                "Mission closure remains a separate gate."
            ),
        },
        args.json,
    )
    return 0

def validate_git_paths(paths: Iterable[str]) -> None:
    for path in paths:
        norm = path.replace("\\", "/")
        for pattern in FORBIDDEN_GIT_PATH_PATTERNS:
            if re.search(pattern, norm, flags=re.IGNORECASE):
                raise PermissionError(f"Forbidden Git path: {path}")


def cmd_git_plan(args: argparse.Namespace) -> int:
    repo_root = safe_root(args.repo_root)
    if not (repo_root / ".git").exists():
        raise FileNotFoundError("Git repo root must contain .git")
    paths = [p.strip() for p in args.paths.split(",") if p.strip()]
    validate_git_paths(paths)
    if not args.confirm_plan:
        print_json({
            "schema_version": "1.0.0",
            "report_type": "beta_git_plan_preview",
            "command": "git-plan",
            "status": "preview",
            "generated_at": now(),
            "summary": "Preview only. Git plan not written.",
            "boundaries": BOUNDARIES,
        }, args.json)
        return 0
    require_token(args.approval_token, "PLAN_BETA_GIT_OPERATION")
    status_result = run_process(["git", "status", "--short"], cwd=repo_root, timeout=30)
    diff_result = run_process(["git", "diff", "--stat"], cwd=repo_root, timeout=30)
    plan = {
        "schema_version": "1.0.0",
        "report_type": "beta_git_operation_plan",
        "plan_id": args.plan_id,
        "created_at": now(),
        "repo_root": str(repo_root),
        "paths": paths,
        "commit_message": args.commit_message,
        "branch": args.branch,
        "remote": args.remote,
        "git_status_short": status_result["stdout"],
        "git_diff_stat": diff_result["stdout"],
        "authority": {
            "git_plan_is_not_permission": True,
            "stage_commit_push_require_separate_approvals": True,
        },
        "boundaries": BOUNDARIES,
    }
    out = Path(args.output).resolve() if args.output else repo_root / "sandbox" / f"{args.plan_id}_beta_git_operation_plan.json"
    write_json(out, plan, force=args.force)
    print_json({
        "schema_version": "1.0.0",
        "report_type": "beta_git_plan_report",
        "command": "git-plan",
        "status": "passed",
        "generated_at": now(),
        "output_paths": [str(out)],
        "boundaries": BOUNDARIES,
    }, args.json)
    return 0


def load_git_plan(plan_path: str) -> Dict[str, Any]:
    plan = load_json(Path(plan_path).resolve())
    validate_git_paths(plan.get("paths", []))
    return plan


def cmd_git_stage(args: argparse.Namespace) -> int:
    if not args.confirm_stage:
        print_json({"schema_version": "1.0.0", "command": "git-stage", "status": "preview", "generated_at": now(), "summary": "Preview only.", "boundaries": BOUNDARIES}, args.json)
        return 0
    require_token(args.approval_token, "APPROVE_BETA_GIT_STAGE")
    plan = load_git_plan(args.plan)
    repo_root = Path(plan["repo_root"]).resolve()
    results = []
    for path in plan.get("paths", []):
        results.append(run_process(["git", "add", "--", path], cwd=repo_root, timeout=60))
    out = repo_root / "sandbox" / f"{plan['plan_id']}_beta_git_stage_report.json"
    write_json(out, {
        "schema_version": "1.0.0",
        "report_type": "beta_git_stage_report",
        "plan_id": plan["plan_id"],
        "generated_at": now(),
        "results": results,
        "authority": {"git_stage_requires_explicit_approval": True},
    }, force=True)
    ok = all(r["exit_code"] == 0 for r in results)
    print_json({"schema_version": "1.0.0", "command": "git-stage", "status": "passed" if ok else "failed", "generated_at": now(), "output_paths": [str(out)], "boundaries": BOUNDARIES}, args.json)
    return 0 if ok else 1


def cmd_git_commit(args: argparse.Namespace) -> int:
    if not args.confirm_commit:
        print_json({"schema_version": "1.0.0", "command": "git-commit", "status": "preview", "generated_at": now(), "summary": "Preview only.", "boundaries": BOUNDARIES}, args.json)
        return 0
    require_token(args.approval_token, "APPROVE_BETA_GIT_COMMIT")
    plan = load_git_plan(args.plan)
    repo_root = Path(plan["repo_root"]).resolve()
    result = run_process(["git", "commit", "-m", plan["commit_message"]], cwd=repo_root, timeout=120)
    out = repo_root / "sandbox" / f"{plan['plan_id']}_beta_git_commit_report.json"
    write_json(out, {
        "schema_version": "1.0.0",
        "report_type": "beta_git_commit_report",
        "plan_id": plan["plan_id"],
        "generated_at": now(),
        "result": result,
        "authority": {"git_commit_requires_explicit_approval": True},
    }, force=True)
    print_json({"schema_version": "1.0.0", "command": "git-commit", "status": "passed" if result["exit_code"] == 0 else "failed", "generated_at": now(), "output_paths": [str(out)], "boundaries": BOUNDARIES}, args.json)
    return 0 if result["exit_code"] == 0 else 1


def cmd_git_push(args: argparse.Namespace) -> int:
    if not args.confirm_push:
        print_json({"schema_version": "1.0.0", "command": "git-push", "status": "preview", "generated_at": now(), "summary": "Preview only.", "boundaries": BOUNDARIES}, args.json)
        return 0
    require_token(args.approval_token, "APPROVE_BETA_GIT_PUSH")
    if not args.allow_network:
        raise PermissionError("Git push requires --allow-network.")
    plan = load_git_plan(args.plan)
    repo_root = Path(plan["repo_root"]).resolve()
    result = run_process(["git", "push", plan["remote"], plan["branch"]], cwd=repo_root, timeout=args.timeout)
    out = repo_root / "sandbox" / f"{plan['plan_id']}_beta_git_push_report.json"
    write_json(out, {
        "schema_version": "1.0.0",
        "report_type": "beta_git_push_report",
        "plan_id": plan["plan_id"],
        "generated_at": now(),
        "result": result,
        "authority": {"git_push_requires_explicit_approval_and_network_allowance": True},
    }, force=True)
    print_json({"schema_version": "1.0.0", "command": "git-push", "status": "passed" if result["exit_code"] == 0 else "failed", "generated_at": now(), "output_paths": [str(out)], "boundaries": BOUNDARIES}, args.json)
    return 0 if result["exit_code"] == 0 else 1


def cmd_close(args: argparse.Namespace) -> int:
    delegated = [
        "--workspace-root",
        args.workspace_root,
        "--mission-id",
        args.mission_id,
        "--memory-root",
        args.memory_root,
        "--closure-id",
        args.closure_id,
        "--execution-evidence",
        args.execution_evidence,
        "--review-evidence",
        args.review_evidence,
        "--teachback-record",
        args.teachback_record,
        "--human-actor",
        args.human_actor or "human",
        "--closure-reason",
        args.closure_reason or "",
    ]
    if args.confirm_close:
        delegated.extend(
            [
                "--confirm-close",
                "--approval-token",
                args.approval_token or "",
            ]
        )
    if args.force:
        delegated.append("--force")
    if args.json:
        delegated.append("--json")
    return int(close_mission_main(delegated))

def cmd_states(args: argparse.Namespace) -> int:
    payload = {
        "schema_version": "1.0.0",
        "report_type": "konoha_beta_states",
        "command": "states",
        "status": "passed",
        "approval_tokens": APPROVAL_TOKENS,
        "teachback_confirmation": TEACHBACK_CONFIRMATION,
        "supported_agents": ["mock", "claude", "codex", "ollama"],
        "supported_git_gates": ["git-plan", "git-stage", "git-commit", "git-push"],
        "boundaries": BOUNDARIES,
    }
    print_json(payload, args.json)
    return 0


def cmd_interactive(args: argparse.Namespace) -> int:
    print("Konoha Beta Terminal")
    print("This interactive helper writes no files by itself. It prints recommended commands.")
    mission_id = input("Mission id: ").strip()
    title = input("Title: ").strip()
    task = input("Task: ").strip()
    workspace = input("Workspace root [./sandbox/konoha-beta-workspace]: ").strip() or "./sandbox/konoha-beta-workspace"
    print("\nSuggested start command:")
    print(f'python .\\tools\\beta_runtime\\run_konoha_beta.py start --workspace-root "{workspace}" --mission-id "{mission_id}" --title "{title}" --task "{task}" --confirm-start --approval-token "START_BETA_MISSION" --force')
    print("\nSuggested plan command:")
    print(f'python .\\tools\\beta_runtime\\run_konoha_beta.py plan --workspace-root "{workspace}" --mission-id "{mission_id}" --plan-id "{mission_id}-plan" --confirm-plan --approval-token "PLAN_BETA_MISSION" --force')
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Konoha v3.0 beta supervised task runtime.")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--json", action="store_true")
        p.add_argument("--force", action="store_true")

    p = sub.add_parser("doctor")
    add_common(p)
    p.add_argument("--output")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("start")
    add_common(p)
    p.add_argument("--workspace-root", required=True)
    p.add_argument("--mission-id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--task", required=True)
    p.add_argument("--task-domain", default="general")
    p.add_argument("--actor", default="human")
    p.add_argument("--confirm-start", action="store_true")
    p.add_argument("--approval-token")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("plan")
    add_common(p)
    p.add_argument("--workspace-root", required=True)
    p.add_argument("--mission-id", required=True)
    p.add_argument("--plan-id", required=True)
    p.add_argument("--task")
    p.add_argument("--task-domain")
    p.add_argument("--confirm-plan", action="store_true")
    p.add_argument("--approval-token")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("agent")
    add_common(p)
    p.add_argument("--workspace-root", required=True)
    p.add_argument("--mission-id", required=True)
    p.add_argument("--invocation-id", required=True)
    p.add_argument("--provider", choices=["mock", "claude", "codex", "ollama"], required=True)
    p.add_argument("--model", default="")
    p.add_argument("--prompt")
    p.add_argument("--prompt-file")
    p.add_argument("--working-dir", default=".")
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--confirm-invoke", action="store_true")
    p.add_argument("--approval-token")
    p.add_argument("--allow-external-agent", action="store_true")
    p.add_argument("--allow-local-model", action="store_true")
    p.add_argument("--codex-sandbox", default="read-only")
    p.add_argument("--codex-ephemeral", action="store_true")
    p.set_defaults(func=cmd_agent)

    p = sub.add_parser("plan-download")
    add_common(p)
    p.add_argument("--workspace-root", required=True)
    p.add_argument("--mission-id", required=True)
    p.add_argument("--plan-id", required=True)
    p.add_argument("--provider", default="ollama")
    p.add_argument("--model", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--confirm-plan", action="store_true")
    p.add_argument("--approval-token")
    p.set_defaults(func=cmd_plan_download)

    p = sub.add_parser("download-model")
    add_common(p)
    p.add_argument("--workspace-root", required=True)
    p.add_argument("--mission-id", required=True)
    p.add_argument("--download-id", required=True)
    p.add_argument("--provider", default="ollama")
    p.add_argument("--model", required=True)
    p.add_argument("--confirm-download", action="store_true")
    p.add_argument("--approval-token")
    p.add_argument("--allow-network", action="store_true")
    p.add_argument("--timeout", type=int, default=1800)
    p.set_defaults(func=cmd_download_model)

    p = sub.add_parser("execute-command")
    add_common(p)
    p.add_argument("--workspace-root", required=True)
    p.add_argument("--mission-id", required=True)
    p.add_argument("--plan-id", required=True)
    p.add_argument("--command-id", required=True)
    p.add_argument("--result-id")
    p.add_argument("--working-dir", default=".")
    p.add_argument("--timeout", type=int, default=120)
    p.add_argument("--confirm-execute", action="store_true")
    p.add_argument("--approval-token")
    p.add_argument("--allow-risky-command", action="store_true")
    p.add_argument("--risky-approval-token")
    p.set_defaults(func=cmd_execute)

    p = sub.add_parser("record-result")
    add_common(p)
    p.add_argument("--workspace-root", required=True)
    p.add_argument("--mission-id", required=True)
    p.add_argument("--result-id", required=True)
    p.add_argument("--command-id", required=True)
    p.add_argument("--command", required=True)
    p.add_argument("--exit-code", type=int, required=True)
    p.add_argument("--stdout-summary", default="")
    p.add_argument("--stderr-summary", default="")
    p.add_argument("--observation", default="")
    p.add_argument("--executed-by", default="human")
    p.add_argument("--confirm-record", action="store_true")
    p.add_argument("--approval-token")
    p.set_defaults(func=cmd_record_result)

    p = sub.add_parser("status")
    add_common(p)
    p.add_argument("--workspace-root", required=True)
    p.add_argument("--mission-id", required=True)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("review")
    add_common(p)
    p.add_argument("--workspace-root", required=True)
    p.add_argument("--mission-id", required=True)
    p.add_argument("--review-id", required=True)
    p.add_argument(
        "--decision",
        choices=["approved", "changes_requested"],
    )
    p.add_argument("--review-summary", default="")
    p.add_argument("--human-actor", default="human")
    p.add_argument("--confirm-review", action="store_true")
    p.add_argument("--approval-token")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("git-plan")
    add_common(p)
    p.add_argument("--repo-root", required=True)
    p.add_argument("--plan-id", required=True)
    p.add_argument("--paths", required=True)
    p.add_argument("--commit-message", required=True)
    p.add_argument("--branch", default="main")
    p.add_argument("--remote", default="origin")
    p.add_argument("--output")
    p.add_argument("--confirm-plan", action="store_true")
    p.add_argument("--approval-token")
    p.set_defaults(func=cmd_git_plan)

    p = sub.add_parser("git-stage")
    add_common(p)
    p.add_argument("--plan", required=True)
    p.add_argument("--confirm-stage", action="store_true")
    p.add_argument("--approval-token")
    p.set_defaults(func=cmd_git_stage)

    p = sub.add_parser("git-commit")
    add_common(p)
    p.add_argument("--plan", required=True)
    p.add_argument("--confirm-commit", action="store_true")
    p.add_argument("--approval-token")
    p.set_defaults(func=cmd_git_commit)

    p = sub.add_parser("git-push")
    add_common(p)
    p.add_argument("--plan", required=True)
    p.add_argument("--confirm-push", action="store_true")
    p.add_argument("--approval-token")
    p.add_argument("--allow-network", action="store_true")
    p.add_argument("--timeout", type=int, default=120)
    p.set_defaults(func=cmd_git_push)

    p = sub.add_parser("close")
    add_common(p)
    p.add_argument("--workspace-root", required=True)
    p.add_argument("--mission-id", required=True)
    p.add_argument("--closure-id", required=True)
    p.add_argument("--memory-root", required=True)
    p.add_argument("--execution-evidence", required=True)
    p.add_argument("--review-evidence", required=True)
    p.add_argument("--teachback-record", required=True)
    p.add_argument("--closure-reason", default="")
    p.add_argument("--confirm-close", action="store_true")
    p.add_argument("--approval-token")
    p.add_argument("--human-actor", default="human")
    p.set_defaults(func=cmd_close)

    p = sub.add_parser("states")
    add_common(p)
    p.set_defaults(func=cmd_states)

    p = sub.add_parser("interactive")
    p.set_defaults(func=cmd_interactive)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        payload = {
            "schema_version": "1.0.0",
            "report_type": "konoha_beta_error_report",
            "command": getattr(args, "command", "unknown"),
            "status": "failed",
            "generated_at": now(),
            "blockers": [str(exc)],
            "boundaries": BOUNDARIES,
            "authority": {
                "failure_does_not_authorize_retry_without_review": True,
            },
        }
        print_json(payload, getattr(args, "json", False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
