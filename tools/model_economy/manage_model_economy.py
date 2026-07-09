#!/usr/bin/env python3
"""
Konoha Model Router and Token Economy Manager.

This tool builds a safe model-runtime profile, records routing decisions,
prepares local model download plans, records token usage, and summarizes
token economy evidence.

It does not invoke models, download models, run shell commands, use network
access, apply repository changes, or perform Git operations.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


PROFILE_TOKEN = "PROFILE_MODEL_RUNTIME"
DECISION_TOKEN = "RECORD_MODEL_ROUTING_DECISION"
DOWNLOAD_PLAN_TOKEN = "PLAN_LOCAL_MODEL_DOWNLOAD"
USAGE_TOKEN = "RECORD_TOKEN_USAGE"
CALIBRATION_TOKEN = "CALIBRATE_TOKEN_ESTIMATES"

ALLOWED_TASK_TYPES = {
    "general",
    "technical_development",
    "code_review",
    "debugging",
    "data_engineering",
    "documentation",
    "summarization",
    "classification",
    "architecture",
    "operations",
}

ALLOWED_RISK_LEVELS = {"low", "medium", "high", "critical"}
ALLOWED_PRIVACY_LEVELS = {"public", "internal", "local_private", "sensitive"}
LOCAL_PROVIDERS = {"ollama", "lmstudio", "mock_local"}
REMOTE_PROVIDERS = {"openai", "anthropic", "codex_cli", "claude_code"}

DEFAULT_LOCAL_MODELS = [
    {
        "provider": "ollama",
        "model": "qwen2.5-coder:7b-instruct",
        "reason": "balanced local coding model candidate for medium machines",
        "task_fit": ["technical_development", "debugging", "code_review"],
    },
    {
        "provider": "ollama",
        "model": "llama3.1:8b-instruct",
        "reason": "general local assistant candidate",
        "task_fit": ["general", "documentation", "summarization"],
    },
    {
        "provider": "ollama",
        "model": "phi4-mini:latest",
        "reason": "small local candidate for cheap drafting and classification",
        "task_fit": ["classification", "summarization", "documentation"],
    },
]

DEFAULT_BOUNDARIES = {
    "model_invocation": "blocked",
    "local_model_download": "proposed_only",
    "network_access": "blocked",
    "command_execution": "blocked",
    "repository_apply": "blocked",
    "git_operations": "blocked",
    "private_context_access": "blocked_by_default",
    "adapter_invocation": "blocked",
    "background_agents": "blocked",
}

AUTHORITY = {
    "model_routing_is_evidence_only": True,
    "token_estimates_are_not_truth": True,
    "usage_reports_do_not_authorize_execution": True,
    "download_plans_do_not_download_models": True,
    "model_choice_does_not_grant_permission": True,
}


class KonohaModelEconomyError(Exception):
    """Safe CLI error."""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_resolve(path: Path, must_be_within: Optional[Path] = None) -> Path:
    resolved = path.expanduser().resolve()
    if must_be_within is not None:
        root = must_be_within.expanduser().resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise KonohaModelEconomyError(f"path escapes allowed root: {path}") from exc
    return resolved


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: Dict[str, Any], force: bool) -> None:
    if path.exists() and not force:
        raise KonohaModelEconomyError(f"output already exists: {path}")
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise KonohaModelEconomyError(f"file does not exist: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise KonohaModelEconomyError(f"invalid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise KonohaModelEconomyError(f"expected JSON object: {path}")
    return data


def estimate_tokens(text: Optional[str]) -> int:
    if not text:
        return 0
    return max(1, int(math.ceil(len(text) / 4.0)))


def detect_runtime_tools() -> Dict[str, Any]:
    # Read-only detection using PATH. No shell, no process execution.
    known = {
        "ollama": shutil.which("ollama") is not None,
        "lmstudio": shutil.which("lms") is not None or shutil.which("lmstudio") is not None,
        "docker": shutil.which("docker") is not None,
        "git": shutil.which("git") is not None,
        "python": shutil.which("python") is not None or shutil.which("python3") is not None,
        "node": shutil.which("node") is not None,
        "codex_cli": shutil.which("codex") is not None,
        "claude_code": shutil.which("claude") is not None,
    }
    return known


def classify_machine() -> Dict[str, Any]:
    cpu_count = os.cpu_count() or 1
    try:
        usage = shutil.disk_usage(Path.cwd())
        free_gb = round(usage.free / (1024 ** 3), 2)
    except Exception:
        free_gb = None

    if cpu_count >= 12:
        tier = "workstation"
    elif cpu_count >= 6:
        tier = "standard"
    else:
        tier = "small"

    return {
        "machine_tier": tier,
        "os": platform.system(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": cpu_count,
        "disk_free_gb_at_current_workdir": free_gb,
        "gpu_inspection": "not_inspected_by_safe_stdlib_profile",
        "vram_inspection": "not_inspected_by_safe_stdlib_profile",
    }


def recommend_mode(task_type: str, risk_level: str, privacy_level: str, tools: Dict[str, Any]) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    if privacy_level in {"local_private", "sensitive"}:
        reasons.append("privacy level prefers local processing or explicit redaction before remote use")
        if tools.get("ollama") or tools.get("lmstudio"):
            return "local_first", reasons
        reasons.append("no local model runtime detected, remote use requires explicit redaction and model gate")
        return "remote_with_redaction_gate", reasons

    if risk_level in {"high", "critical"}:
        reasons.append("high risk task prefers stronger model review and explicit human approval")
        return "strong_remote_or_dual_review", reasons

    if task_type in {"summarization", "classification", "documentation"}:
        reasons.append("low-risk repetitive task is a good candidate for local or cheap helper models")
        return "local_or_cheap_helper", reasons

    if task_type in {"architecture", "debugging"}:
        reasons.append("reasoning-heavy task may benefit from a stronger remote model with budget cap")
        return "strong_remote_with_budget_cap", reasons

    reasons.append("general task can start local/cheap and escalate if quality is insufficient")
    return "start_local_then_escalate", reasons


def choose_candidate_models(task_type: str, tools: Dict[str, Any]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for model in DEFAULT_LOCAL_MODELS:
        if task_type in model["task_fit"] or task_type == "general":
            item = dict(model)
            item["available_runtime_detected"] = bool(tools.get(item["provider"]))
            item["invocation_status"] = "not_invoked"
            item["download_status"] = "not_requested"
            candidates.append(item)
    candidates.append({
        "provider": "mock_local",
        "model": "konoha-mock-local",
        "reason": "deterministic no-network fallback for tests and dry runs",
        "task_fit": ["general", task_type],
        "available_runtime_detected": True,
        "invocation_status": "not_invoked",
        "download_status": "not_needed",
    })
    return candidates


def command_boundary() -> Dict[str, Any]:
    return {
        "command_proposals_are_not_permission": True,
        "shell_execution": "blocked",
        "subprocess_execution": "blocked",
        "download_execution": "blocked",
        "network_access": "blocked",
    }


def build_profile(args: argparse.Namespace, confirmed: bool) -> Dict[str, Any]:
    if args.task_type not in ALLOWED_TASK_TYPES:
        raise KonohaModelEconomyError(f"invalid task type: {args.task_type}")
    if args.risk_level not in ALLOWED_RISK_LEVELS:
        raise KonohaModelEconomyError(f"invalid risk level: {args.risk_level}")
    if args.privacy_level not in ALLOWED_PRIVACY_LEVELS:
        raise KonohaModelEconomyError(f"invalid privacy level: {args.privacy_level}")

    tools = detect_runtime_tools()
    machine = classify_machine()
    routing_mode, reasons = recommend_mode(args.task_type, args.risk_level, args.privacy_level, tools)
    candidates = choose_candidate_models(args.task_type, tools)

    prompt_tokens = estimate_tokens(args.estimated_input_text)
    output_tokens = int(args.estimated_output_tokens or 0)
    total_estimated = prompt_tokens + output_tokens

    return {
        "schema_version": "1.0.0",
        "report_type": "model_runtime_profile",
        "profile_id": args.profile_id,
        "generated_at": now_iso(),
        "status": "profiled" if confirmed else "preview",
        "invocation": "confirmed_profile" if confirmed else "preview_only",
        "task": {
            "task_type": args.task_type,
            "risk_level": args.risk_level,
            "privacy_level": args.privacy_level,
            "estimated_input_tokens": prompt_tokens,
            "estimated_output_tokens": output_tokens,
            "estimated_total_tokens": total_estimated,
            "token_estimation_method": "chars_div_4_heuristic" if args.estimated_input_text else "not_provided",
        },
        "machine": machine,
        "runtime_tools_detected": tools,
        "routing_recommendation": {
            "mode": routing_mode,
            "reasons": reasons,
            "candidate_models": candidates,
            "escalation_rule": "start with sufficient low-risk model and escalate only when quality, risk, or context requires it",
        },
        "boundaries": DEFAULT_BOUNDARIES,
        "authority": AUTHORITY,
    }


def build_decision(args: argparse.Namespace, profile: Dict[str, Any], confirmed: bool) -> Dict[str, Any]:
    task = profile.get("task", {})
    tools = profile.get("runtime_tools_detected", {})
    task_type = args.task_type or task.get("task_type", "general")
    risk_level = args.risk_level or task.get("risk_level", "medium")
    privacy_level = args.privacy_level or task.get("privacy_level", "internal")
    routing_mode, reasons = recommend_mode(task_type, risk_level, privacy_level, tools)

    selected_provider = args.provider
    selected_model = args.model
    selection_reason = args.selection_reason

    if not selected_provider or not selected_model:
        candidates = choose_candidate_models(task_type, tools)
        local_available = [c for c in candidates if c.get("available_runtime_detected") and c["provider"] in LOCAL_PROVIDERS]
        if routing_mode.startswith("local") and local_available:
            chosen = local_available[0]
        elif candidates:
            chosen = candidates[0]
        else:
            chosen = {"provider": "mock_local", "model": "konoha-mock-local"}
        selected_provider = selected_provider or chosen["provider"]
        selected_model = selected_model or chosen["model"]
        selection_reason = selection_reason or "selected from profile recommendation candidates"

    remote_requires_gate = selected_provider in REMOTE_PROVIDERS
    local_download_required = selected_provider in {"ollama", "lmstudio"} and not tools.get(selected_provider, False)

    return {
        "schema_version": "1.0.0",
        "report_type": "model_routing_decision",
        "decision_id": args.decision_id,
        "profile_id": profile.get("profile_id"),
        "generated_at": now_iso(),
        "status": "recorded" if confirmed else "preview",
        "invocation": "confirmed_decision" if confirmed else "preview_only",
        "mission_id": args.mission_id,
        "task": {
            "task_type": task_type,
            "risk_level": risk_level,
            "privacy_level": privacy_level,
            "summary": args.task or "not provided",
        },
        "routing_mode": routing_mode,
        "routing_reasons": reasons,
        "selected": {
            "provider": selected_provider,
            "model": selected_model,
            "selection_reason": selection_reason,
            "model_invocation_status": "not_invoked",
            "remote_model_gate_required": remote_requires_gate,
            "local_download_required_before_use": local_download_required,
        },
        "budget": {
            "max_prompt_tokens": args.max_prompt_tokens,
            "max_completion_tokens": args.max_completion_tokens,
            "budget_status": "recorded_limit" if args.max_prompt_tokens or args.max_completion_tokens else "not_set",
        },
        "boundaries": DEFAULT_BOUNDARIES,
        "authority": AUTHORITY,
    }


def build_download_plan(args: argparse.Namespace, confirmed: bool) -> Dict[str, Any]:
    if args.provider not in {"ollama", "lmstudio"}:
        raise KonohaModelEconomyError("download plans are only supported for local providers: ollama, lmstudio")

    if args.provider == "ollama":
        proposed_command = ["ollama", "pull", args.model]
    else:
        proposed_command = ["lmstudio", "download", args.model]

    return {
        "schema_version": "1.0.0",
        "report_type": "local_model_download_plan",
        "plan_id": args.plan_id,
        "generated_at": now_iso(),
        "status": "planned" if confirmed else "preview",
        "invocation": "confirmed_plan" if confirmed else "preview_only",
        "provider": args.provider,
        "model": args.model,
        "reason": args.reason,
        "proposed_command": proposed_command,
        "execution_status": "not_executed",
        "download_status": "not_downloaded",
        "command_boundary": command_boundary(),
        "boundaries": DEFAULT_BOUNDARIES,
        "authority": AUTHORITY,
    }


def ledger_path(root: Path) -> Path:
    return root / "token_usage_ledger.json"


def empty_ledger() -> Dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "ledger_type": "token_usage_ledger",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "records": [],
        "totals": {
            "records": 0,
            "actual_records": 0,
            "estimated_records": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": None,
        },
        "calibration": {
            "method": "none",
            "estimated_vs_actual_samples": 0,
            "average_estimation_error_ratio": None,
        },
        "authority": AUTHORITY,
    }


def load_ledger(root: Path) -> Dict[str, Any]:
    path = ledger_path(root)
    if not path.exists():
        return empty_ledger()
    return load_json(path)


def recompute_totals(ledger: Dict[str, Any]) -> Dict[str, Any]:
    records = ledger.get("records", [])
    actual = sum(1 for r in records if r.get("usage_source") == "actual")
    estimated = sum(1 for r in records if r.get("usage_source") == "estimated")
    input_tokens = sum(int(r.get("input_tokens") or 0) for r in records)
    output_tokens = sum(int(r.get("output_tokens") or 0) for r in records)
    costs = [r.get("estimated_cost_usd") for r in records if isinstance(r.get("estimated_cost_usd"), (int, float))]
    ledger["updated_at"] = now_iso()
    ledger["totals"] = {
        "records": len(records),
        "actual_records": actual,
        "estimated_records": estimated,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated_cost_usd": round(sum(costs), 6) if costs else None,
    }
    return ledger


def build_usage_record(args: argparse.Namespace) -> Dict[str, Any]:
    if args.actual_input_tokens is not None or args.actual_output_tokens is not None:
        input_tokens = int(args.actual_input_tokens or 0)
        output_tokens = int(args.actual_output_tokens or 0)
        usage_source = "actual"
        method = args.usage_source or "provider_reported"
    else:
        input_tokens = estimate_tokens(args.prompt_text)
        output_tokens = estimate_tokens(args.completion_text)
        usage_source = "estimated"
        method = "chars_div_4_heuristic"

    total_tokens = input_tokens + output_tokens
    estimated_cost = None
    if args.input_cost_per_million is not None or args.output_cost_per_million is not None:
        in_cost = float(args.input_cost_per_million or 0.0) * input_tokens / 1_000_000
        out_cost = float(args.output_cost_per_million or 0.0) * output_tokens / 1_000_000
        estimated_cost = round(in_cost + out_cost, 6)

    return {
        "usage_id": args.usage_id,
        "recorded_at": now_iso(),
        "mission_id": args.mission_id,
        "stage": args.stage,
        "provider": args.provider,
        "model": args.model,
        "usage_source": usage_source,
        "token_estimation_method": method,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": estimated_cost,
        "latency_ms": args.latency_ms,
        "success": args.success,
        "quality_rating": args.quality_rating,
        "notes": args.notes,
        "boundaries": {
            "record_does_not_invoke_model": True,
            "record_does_not_authorize_execution": True,
        },
    }


def summarize_ledger(ledger: Dict[str, Any]) -> Dict[str, Any]:
    totals = ledger.get("totals", {})
    records = ledger.get("records", [])
    suggestions: List[str] = []
    if totals.get("estimated_records", 0) > 0:
        suggestions.append("collect provider-reported usage where available to calibrate estimates")
    if totals.get("records", 0) == 0:
        suggestions.append("record at least one model usage sample before judging token efficiency")
    if any(r.get("provider") in REMOTE_PROVIDERS for r in records):
        suggestions.append("review whether remote model calls were reserved for high-impact reasoning")
    if any(r.get("provider") in LOCAL_PROVIDERS for r in records):
        suggestions.append("compare local latency and quality against remote escalation thresholds")
    if not suggestions:
        suggestions.append("ledger has enough structure for basic review; continue collecting actual usage samples")

    return {
        "schema_version": "1.0.0",
        "report_type": "token_economy_summary",
        "generated_at": now_iso(),
        "totals": totals,
        "calibration": ledger.get("calibration", {}),
        "efficiency_review": {
            "records_reviewed": len(records),
            "summary": "token economy is evidence for future routing decisions, not a permission source",
            "suggestions": suggestions,
        },
        "authority": AUTHORITY,
    }


def calibrate_ledger(ledger: Dict[str, Any]) -> Dict[str, Any]:
    # This is intentionally conservative. Calibration needs paired actual and estimated
    # records with the same usage_id prefix or explicit later enhancement.
    estimated = [r for r in ledger.get("records", []) if r.get("usage_source") == "estimated"]
    actual = [r for r in ledger.get("records", []) if r.get("usage_source") == "actual"]
    samples = min(len(estimated), len(actual))
    if samples == 0:
        ledger["calibration"] = {
            "method": "no_paired_samples",
            "estimated_vs_actual_samples": 0,
            "average_estimation_error_ratio": None,
        }
        return ledger

    ratios: List[float] = []
    for e, a in zip(estimated[:samples], actual[:samples]):
        e_total = max(1, int(e.get("total_tokens") or 0))
        a_total = max(1, int(a.get("total_tokens") or 0))
        ratios.append(abs(e_total - a_total) / a_total)
    avg = sum(ratios) / len(ratios)
    ledger["calibration"] = {
        "method": "paired_order_estimated_actual",
        "estimated_vs_actual_samples": samples,
        "average_estimation_error_ratio": round(avg, 4),
    }
    return ledger


def print_or_json(data: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        status = data.get("status", "ok")
        report_type = data.get("report_type", data.get("ledger_type", "report"))
        print(f"{report_type.upper()} {status.upper()}")
        for key in ("profile_id", "decision_id", "plan_id", "usage_id"):
            if data.get(key):
                print(f"{key}: {data[key]}")
        if data.get("boundaries"):
            for k, v in data["boundaries"].items():
                print(f"{k.replace('_', ' ').title()}: {v}")


def cmd_profile(args: argparse.Namespace) -> int:
    confirmed = bool(args.confirm_profile)
    if confirmed and args.approval_token != PROFILE_TOKEN:
        raise KonohaModelEconomyError("invalid approval token for model runtime profile")
    report = build_profile(args, confirmed)
    if confirmed or args.output:
        out = Path(args.output) if args.output else Path(args.sandbox_root) / "reports" / f"{args.profile_id}_model_runtime_profile.json"
        write_json(out, report, args.force)
        report["output_path"] = str(out)
    print_or_json(report, args.json)
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    confirmed = bool(args.confirm_decision)
    if confirmed and args.approval_token != DECISION_TOKEN:
        raise KonohaModelEconomyError("invalid approval token for model routing decision")
    profile = load_json(Path(args.profile))
    decision = build_decision(args, profile, confirmed)
    if confirmed or args.output:
        out = Path(args.output) if args.output else Path(args.sandbox_root) / "reports" / f"{args.decision_id}_model_routing_decision.json"
        write_json(out, decision, args.force)
        decision["output_path"] = str(out)
    print_or_json(decision, args.json)
    return 0


def cmd_plan_download(args: argparse.Namespace) -> int:
    confirmed = bool(args.confirm_plan)
    if confirmed and args.approval_token != DOWNLOAD_PLAN_TOKEN:
        raise KonohaModelEconomyError("invalid approval token for local model download plan")
    plan = build_download_plan(args, confirmed)
    if confirmed or args.output:
        out = Path(args.output) if args.output else Path(args.sandbox_root) / "model_download_plans" / f"{args.plan_id}_local_model_download_plan.json"
        write_json(out, plan, args.force)
        plan["output_path"] = str(out)
    print_or_json(plan, args.json)
    return 0


def cmd_record_usage(args: argparse.Namespace) -> int:
    if args.confirm_record and args.approval_token != USAGE_TOKEN:
        raise KonohaModelEconomyError("invalid approval token for token usage record")
    if not args.confirm_record:
        record = build_usage_record(args)
        preview = {
            "schema_version": "1.0.0",
            "report_type": "token_usage_record_preview",
            "status": "preview",
            "invocation": "preview_only",
            "record": record,
            "authority": AUTHORITY,
            "boundaries": DEFAULT_BOUNDARIES,
        }
        print_or_json(preview, args.json)
        return 0

    root = Path(args.ledger_root)
    ensure_dir(root)
    ledger = load_ledger(root)
    record = build_usage_record(args)
    ledger.setdefault("records", []).append(record)
    ledger = recompute_totals(ledger)
    write_json(ledger_path(root), ledger, True)
    response = {
        "schema_version": "1.0.0",
        "report_type": "token_usage_record",
        "status": "recorded",
        "usage_id": args.usage_id,
        "ledger_path": str(ledger_path(root)),
        "record": record,
        "totals": ledger["totals"],
        "authority": AUTHORITY,
    }
    print_or_json(response, args.json)
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    ledger = load_ledger(Path(args.ledger_root))
    ledger = recompute_totals(ledger)
    summary = summarize_ledger(ledger)
    if args.write_summary:
        out = Path(args.output) if args.output else Path(args.ledger_root) / "token_economy_summary.json"
        write_json(out, summary, args.force)
        summary["output_path"] = str(out)
    print_or_json(summary, args.json)
    return 0


def cmd_calibrate(args: argparse.Namespace) -> int:
    if args.confirm_calibration and args.approval_token != CALIBRATION_TOKEN:
        raise KonohaModelEconomyError("invalid approval token for token estimate calibration")
    root = Path(args.ledger_root)
    ledger = load_ledger(root)
    preview_ledger = calibrate_ledger(dict(ledger))
    if not args.confirm_calibration:
        response = {
            "schema_version": "1.0.0",
            "report_type": "token_calibration_preview",
            "status": "preview",
            "calibration": preview_ledger.get("calibration"),
            "authority": AUTHORITY,
        }
        print_or_json(response, args.json)
        return 0
    write_json(ledger_path(root), preview_ledger, True)
    response = {
        "schema_version": "1.0.0",
        "report_type": "token_calibration_report",
        "status": "calibrated",
        "ledger_path": str(ledger_path(root)),
        "calibration": preview_ledger.get("calibration"),
        "authority": AUTHORITY,
    }
    print_or_json(response, args.json)
    return 0


def cmd_states(args: argparse.Namespace) -> int:
    data = {
        "approval_tokens": {
            "profile_model_runtime": PROFILE_TOKEN,
            "record_model_routing_decision": DECISION_TOKEN,
            "plan_local_model_download": DOWNLOAD_PLAN_TOKEN,
            "record_token_usage": USAGE_TOKEN,
            "calibrate_token_estimates": CALIBRATION_TOKEN,
        },
        "allowed_task_types": sorted(ALLOWED_TASK_TYPES),
        "allowed_risk_levels": sorted(ALLOWED_RISK_LEVELS),
        "allowed_privacy_levels": sorted(ALLOWED_PRIVACY_LEVELS),
        "local_providers": sorted(LOCAL_PROVIDERS),
        "remote_providers": sorted(REMOTE_PROVIDERS),
        "boundaries": DEFAULT_BOUNDARIES,
        "authority": AUTHORITY,
    }
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Konoha Model Router and Token Economy Manager")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("profile", help="Build a safe model runtime profile")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--sandbox-root", default="./sandbox")
    p.add_argument("--profile-id", required=True)
    p.add_argument("--task-type", default="general", choices=sorted(ALLOWED_TASK_TYPES))
    p.add_argument("--risk-level", default="medium", choices=sorted(ALLOWED_RISK_LEVELS))
    p.add_argument("--privacy-level", default="internal", choices=sorted(ALLOWED_PRIVACY_LEVELS))
    p.add_argument("--estimated-input-text", default="")
    p.add_argument("--estimated-output-tokens", type=int, default=0)
    p.add_argument("--confirm-profile", action="store_true")
    p.add_argument("--approval-token", default="")
    p.add_argument("--output")
    p.add_argument("--force", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_profile)

    p = sub.add_parser("recommend", help="Record a model routing decision from a profile")
    p.add_argument("--profile", required=True)
    p.add_argument("--sandbox-root", default="./sandbox")
    p.add_argument("--decision-id", required=True)
    p.add_argument("--mission-id", default="")
    p.add_argument("--task", default="")
    p.add_argument("--task-type", choices=sorted(ALLOWED_TASK_TYPES))
    p.add_argument("--risk-level", choices=sorted(ALLOWED_RISK_LEVELS))
    p.add_argument("--privacy-level", choices=sorted(ALLOWED_PRIVACY_LEVELS))
    p.add_argument("--provider")
    p.add_argument("--model")
    p.add_argument("--selection-reason", default="")
    p.add_argument("--max-prompt-tokens", type=int)
    p.add_argument("--max-completion-tokens", type=int)
    p.add_argument("--confirm-decision", action="store_true")
    p.add_argument("--approval-token", default="")
    p.add_argument("--output")
    p.add_argument("--force", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_recommend)

    p = sub.add_parser("plan-download", help="Plan but do not execute a local model download")
    p.add_argument("--sandbox-root", default="./sandbox")
    p.add_argument("--plan-id", required=True)
    p.add_argument("--provider", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--reason", default="Local model candidate for supervised mission runtime.")
    p.add_argument("--confirm-plan", action="store_true")
    p.add_argument("--approval-token", default="")
    p.add_argument("--output")
    p.add_argument("--force", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_plan_download)

    p = sub.add_parser("record-usage", help="Record actual or estimated token usage into a ledger")
    p.add_argument("--ledger-root", required=True)
    p.add_argument("--usage-id", required=True)
    p.add_argument("--mission-id", default="")
    p.add_argument("--stage", default="unknown")
    p.add_argument("--provider", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--prompt-text", default="")
    p.add_argument("--completion-text", default="")
    p.add_argument("--actual-input-tokens", type=int)
    p.add_argument("--actual-output-tokens", type=int)
    p.add_argument("--usage-source", default="")
    p.add_argument("--input-cost-per-million", type=float)
    p.add_argument("--output-cost-per-million", type=float)
    p.add_argument("--latency-ms", type=int)
    p.add_argument("--success", default="unknown", choices=["true", "false", "unknown"])
    p.add_argument("--quality-rating", type=int, choices=[1, 2, 3, 4, 5])
    p.add_argument("--notes", default="")
    p.add_argument("--confirm-record", action="store_true")
    p.add_argument("--approval-token", default="")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_record_usage)

    p = sub.add_parser("summarize", help="Summarize a token usage ledger")
    p.add_argument("--ledger-root", required=True)
    p.add_argument("--write-summary", action="store_true")
    p.add_argument("--output")
    p.add_argument("--force", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_summarize)

    p = sub.add_parser("calibrate", help="Calibrate token estimates when actual samples exist")
    p.add_argument("--ledger-root", required=True)
    p.add_argument("--confirm-calibration", action="store_true")
    p.add_argument("--approval-token", default="")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_calibrate)

    p = sub.add_parser("states", help="List tokens, providers, and boundaries")
    p.set_defaults(func=cmd_states)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KonohaModelEconomyError as exc:
        print("MODEL ROUTER AND TOKEN ECONOMY FAILED")
        print("Blocker:", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
