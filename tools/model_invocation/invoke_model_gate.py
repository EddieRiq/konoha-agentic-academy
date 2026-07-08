#!/usr/bin/env python3
"""Konoha Real Model Invocation Gate.

This gate allows model-shaped invocations only under explicit approval.

Safety rules:
- Preview is the default.
- Real providers require --confirm-invocation, exact token, --allow-network, allowed provider, and safe request plan.
- Model output is only evidence/proposal. It is never permission to execute, apply, stage, commit, push, or close a mission.
- Private context is blocked.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple


APPROVAL_TOKEN = "INVOKE_REAL_MODEL"
SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")

REAL_PROVIDERS = {"openai", "anthropic", "ollama"}
MOCK_PROVIDER = "mock"
SUPPORTED_PROVIDERS = REAL_PROVIDERS | {MOCK_PROVIDER}

SECRET_PATTERNS = [
    "api_key",
    "apikey",
    "secret",
    "password",
    "passwd",
    "token=",
    "authorization:",
    "bearer ",
    "private key",
    "BEGIN RSA PRIVATE KEY",
]


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Invoke a model provider only through the Konoha approval gate."
    )
    parser.add_argument("--contract", required=True, help="Path to model provider contract JSON.")
    parser.add_argument("--request", required=True, help="Path to model request plan JSON.")
    parser.add_argument("--sandbox-root", required=True, help="Sandbox root containing runs/<run_id>.")
    parser.add_argument("--run-id", required=True, help="Existing sandbox run id.")
    parser.add_argument("--confirm-invocation", action="store_true", help="Confirm model invocation.")
    parser.add_argument("--approval-token", default="", help="Exact approval token.")
    parser.add_argument("--allow-network", action="store_true", help="Allow network for real providers.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing model output files.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--timeout-seconds", type=int, default=30, help="Provider call timeout.")
    return parser.parse_args(argv)


def fail_report(args: argparse.Namespace, blockers: List[str], provider: str = "unknown") -> Dict[str, Any]:
    return {
        "status": "failed",
        "target_release": "v1.5.0",
        "gate": "real_model_invocation",
        "provider": provider,
        "invocation": "blocked",
        "execution": "blocked",
        "filesystem_mutation": "blocked",
        "repository_apply": "blocked",
        "git_operations": "blocked",
        "private_context_access": "blocked",
        "real_model_invocation": "blocked",
        "network_access": "blocked",
        "human_review_required": True,
        "model_output_is_permission": False,
        "blockers": blockers,
    }


def print_report(report: Dict[str, Any], json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    status = report.get("status", "unknown")
    if status == "passed":
        if report.get("invocation") == "preview_only":
            print("REAL MODEL INVOCATION GATE PREVIEW")
        else:
            print("REAL MODEL INVOCATION GATE PASSED")
    else:
        print("REAL MODEL INVOCATION GATE FAILED")

    print(f"Provider: {report.get('provider', 'unknown')}")
    print(f"Invocation: {report.get('invocation', 'blocked')}")
    print(f"Execution: {report.get('execution', 'blocked')}")
    print(f"Filesystem mutation: {report.get('filesystem_mutation', 'blocked')}")
    print(f"Repository apply: {report.get('repository_apply', 'blocked')}")
    print(f"Git operations: {report.get('git_operations', 'blocked')}")
    print(f"Private context access: {report.get('private_context_access', 'blocked')}")
    print(f"Real model invocation: {report.get('real_model_invocation', 'blocked')}")
    print(f"Network access: {report.get('network_access', 'blocked')}")
    print(f"Human review required: {str(report.get('human_review_required', True)).lower()}")
    for blocker in report.get("blockers", []):
        print(f"Blocker: {blocker}")
    if report.get("report_path"):
        print(f"Report: {report['report_path']}")


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate_run_id(run_id: str) -> None:
    if not SAFE_ID_PATTERN.match(run_id) or "/" in run_id or "\\" in run_id or ".." in run_id:
        raise ValueError("run_id must be alphanumeric plus '.', '_' or '-' and may not contain path separators")


def resolve_under(root: Path, *parts: str) -> Path:
    base = root.resolve()
    candidate = base.joinpath(*parts).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"path escapes root: {candidate}") from exc
    return candidate


def normalize_allowed_providers(contract: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    providers = contract.get("providers")
    if isinstance(providers, dict):
        return {str(k): v if isinstance(v, dict) else {} for k, v in providers.items()}

    allowed = contract.get("allowed_providers")
    if isinstance(allowed, list):
        return {str(name): {} for name in allowed}

    return {MOCK_PROVIDER: {"enabled": True}}


def has_secret_like_text(text: str) -> bool:
    lower = text.lower()
    return any(pattern.lower() in lower for pattern in SECRET_PATTERNS)


def validate_request(contract: Dict[str, Any], request: Dict[str, Any]) -> Tuple[str, List[str]]:
    blockers: List[str] = []
    provider = str(request.get("provider", "")).strip().lower()
    prompt = str(request.get("prompt", ""))

    if not provider:
        blockers.append("request provider is required")
    elif provider not in SUPPORTED_PROVIDERS:
        blockers.append(f"provider is not supported by this gate: {provider}")

    allowed_providers = normalize_allowed_providers(contract)
    if provider and provider not in allowed_providers:
        blockers.append(f"provider is not allowed by contract: {provider}")

    provider_policy = allowed_providers.get(provider, {})
    if provider_policy.get("enabled") is False:
        blockers.append(f"provider is disabled by contract: {provider}")

    if not str(request.get("request_id", "")).strip():
        blockers.append("request_id is required")
    if not str(request.get("mission_id", "")).strip():
        blockers.append("mission_id is required")
    if not str(request.get("model", "")).strip():
        blockers.append("model is required")
    if not str(request.get("purpose", "")).strip():
        blockers.append("purpose is required")
    if not prompt.strip():
        blockers.append("prompt is required")

    if bool(request.get("contains_private_context", False)):
        blockers.append("request contains private context")
    if has_secret_like_text(prompt):
        blockers.append("prompt appears to contain secret-like text")

    context_sources = request.get("context_sources", [])
    if not isinstance(context_sources, list):
        blockers.append("context_sources must be a list")
    else:
        blocked_sources = set(contract.get("blocked_context_sources", []))
        for source in context_sources:
            if str(source) in blocked_sources:
                blockers.append(f"context source is blocked: {source}")

    estimated_tokens = int(request.get("estimated_prompt_tokens", 0) or 0)
    completion_tokens = int(request.get("requested_completion_tokens", 0) or 0)
    max_prompt_tokens = int(contract.get("max_prompt_tokens", 8000) or 8000)
    max_completion_tokens = int(contract.get("max_completion_tokens", 2000) or 2000)

    if estimated_tokens <= 0:
        blockers.append("estimated_prompt_tokens must be positive")
    if completion_tokens <= 0:
        blockers.append("requested_completion_tokens must be positive")
    if estimated_tokens > max_prompt_tokens:
        blockers.append("estimated_prompt_tokens exceeds contract max")
    if completion_tokens > max_completion_tokens:
        blockers.append("requested_completion_tokens exceeds contract max")

    estimated_cost = float(request.get("estimated_cost_usd", 0) or 0)
    max_cost = float(contract.get("max_estimated_cost_usd", 1.0) or 1.0)
    if estimated_cost < 0:
        blockers.append("estimated_cost_usd cannot be negative")
    if estimated_cost > max_cost:
        blockers.append("estimated_cost_usd exceeds contract max")

    if provider in REAL_PROVIDERS and not bool(request.get("requires_network", False)):
        blockers.append("real provider requests must explicitly set requires_network=true")

    return provider or "unknown", blockers


def build_mock_output(request: Dict[str, Any]) -> str:
    task = str(request.get("prompt", "")).strip()
    purpose = str(request.get("purpose", "planning")).strip()
    model = str(request.get("model", "mock-model")).strip()
    return (
        "# Konoha mock model output\n\n"
        f"- Provider: mock\n"
        f"- Model: {model}\n"
        f"- Purpose: {purpose}\n"
        "- Status: review_required\n"
        "- Permission: none\n\n"
        "## Deterministic response\n\n"
        f"This is a deterministic mock response for: {task}\n\n"
        "## Safety note\n\n"
        "This output is evidence only. It does not authorize execution, repository apply, "
        "Git staging, Git commit, Git push, adapter invocation, or mission closure.\n"
    )


def provider_endpoint(contract: Dict[str, Any], provider: str) -> str:
    providers = normalize_allowed_providers(contract)
    endpoint = providers.get(provider, {}).get("endpoint")
    if endpoint:
        return str(endpoint)

    defaults = {
        "openai": "https://api.openai.com/v1/chat/completions",
        "anthropic": "https://api.anthropic.com/v1/messages",
        "ollama": "http://localhost:11434/api/generate",
    }
    return defaults[provider]


def post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    parsed = json.loads(body)
    if not isinstance(parsed, dict):
        raise ValueError("provider response must be a JSON object")
    return parsed


def invoke_openai(contract: Dict[str, Any], request: Dict[str, Any], timeout: int) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required for openai provider")

    payload = {
        "model": request["model"],
        "messages": [{"role": "user", "content": request["prompt"]}],
        "max_tokens": int(request.get("requested_completion_tokens", 500)),
    }
    response = post_json(
        provider_endpoint(contract, "openai"),
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        payload,
        timeout,
    )
    choices = response.get("choices", [])
    if choices and isinstance(choices, list):
        message = choices[0].get("message", {})
        if isinstance(message, dict):
            return str(message.get("content", "")).strip()
    return json.dumps(response, indent=2, sort_keys=True)


def invoke_anthropic(contract: Dict[str, Any], request: Dict[str, Any], timeout: int) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is required for anthropic provider")

    payload = {
        "model": request["model"],
        "max_tokens": int(request.get("requested_completion_tokens", 500)),
        "messages": [{"role": "user", "content": request["prompt"]}],
    }
    response = post_json(
        provider_endpoint(contract, "anthropic"),
        {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        payload,
        timeout,
    )
    content = response.get("content", [])
    if content and isinstance(content, list):
        first = content[0]
        if isinstance(first, dict):
            return str(first.get("text", "")).strip()
    return json.dumps(response, indent=2, sort_keys=True)


def invoke_ollama(contract: Dict[str, Any], request: Dict[str, Any], timeout: int) -> str:
    payload = {
        "model": request["model"],
        "prompt": request["prompt"],
        "stream": False,
    }
    response = post_json(
        provider_endpoint(contract, "ollama"),
        {"Content-Type": "application/json"},
        payload,
        timeout,
    )
    return str(response.get("response", json.dumps(response, indent=2, sort_keys=True))).strip()


def invoke_provider(provider: str, contract: Dict[str, Any], request: Dict[str, Any], timeout: int) -> str:
    if provider == MOCK_PROVIDER:
        return build_mock_output(request)
    if provider == "openai":
        return invoke_openai(contract, request, timeout)
    if provider == "anthropic":
        return invoke_anthropic(contract, request, timeout)
    if provider == "ollama":
        return invoke_ollama(contract, request, timeout)
    raise ValueError(f"unsupported provider: {provider}")


def write_outputs(
    sandbox_root: Path,
    run_id: str,
    provider: str,
    model_text: str,
    report: Dict[str, Any],
    force: bool,
) -> Dict[str, str]:
    run_dir = resolve_under(sandbox_root, "runs", run_id)
    output_dir = resolve_under(run_dir, "model_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = resolve_under(output_dir, "model_invocation_output.md")
    report_path = resolve_under(run_dir, "model_invocation_gate_report.json")

    if not force and (output_path.exists() or report_path.exists()):
        raise FileExistsError("model invocation outputs already exist; use --force to overwrite")

    output_path.write_text(model_text, encoding="utf-8")
    report["report_path"] = str(report_path)
    report["output_path"] = str(output_path)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    return {"report_path": str(report_path), "output_path": str(output_path)}


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    provider = "unknown"
    try:
        validate_run_id(args.run_id)

        sandbox_root = Path(args.sandbox_root)
        run_dir = resolve_under(sandbox_root, "runs", args.run_id)
        if not run_dir.exists():
            raise ValueError(f"sandbox run does not exist: {run_dir}")

        contract = read_json(Path(args.contract))
        request = read_json(Path(args.request))
        provider, blockers = validate_request(contract, request)

        if blockers:
            report = fail_report(args, blockers, provider)
            print_report(report, args.json)
            return 1

        if not args.confirm_invocation:
            report = {
                "status": "passed",
                "target_release": "v1.5.0",
                "gate": "real_model_invocation",
                "provider": provider,
                "invocation": "preview_only",
                "execution": "blocked",
                "filesystem_mutation": "blocked",
                "repository_apply": "blocked",
                "git_operations": "blocked",
                "private_context_access": "blocked",
                "real_model_invocation": "blocked",
                "network_access": "blocked",
                "human_review_required": True,
                "model_output_is_permission": False,
                "blockers": [],
            }
            print_report(report, args.json)
            return 0

        blockers = []
        if args.approval_token != APPROVAL_TOKEN:
            blockers.append("approval token is invalid")
        if provider in REAL_PROVIDERS and not args.allow_network:
            blockers.append("real provider invocation requires --allow-network")
        if provider in REAL_PROVIDERS and not bool(contract.get("real_model_invocation_enabled", False)):
            blockers.append("real_model_invocation_enabled must be true in contract")

        if blockers:
            report = fail_report(args, blockers, provider)
            print_report(report, args.json)
            return 1

        started = time.time()
        model_text = invoke_provider(provider, contract, request, args.timeout_seconds)
        elapsed_ms = int((time.time() - started) * 1000)

        report = {
            "status": "passed",
            "target_release": "v1.5.0",
            "gate": "real_model_invocation",
            "provider": provider,
            "model": request.get("model"),
            "request_id": request.get("request_id"),
            "mission_id": request.get("mission_id"),
            "purpose": request.get("purpose"),
            "invocation": "confirmed",
            "execution": "blocked",
            "filesystem_mutation": "sandbox model outputs only",
            "repository_apply": "blocked",
            "git_operations": "blocked",
            "private_context_access": "blocked",
            "real_model_invocation": "mock only" if provider == MOCK_PROVIDER else "approved_provider_call",
            "network_access": "blocked" if provider == MOCK_PROVIDER else "allowlisted_provider_only",
            "human_review_required": True,
            "model_output_is_permission": False,
            "elapsed_ms": elapsed_ms,
            "blockers": [],
        }

        paths = write_outputs(sandbox_root, args.run_id, provider, model_text, report, args.force)
        report.update(paths)
        print_report(report, args.json)
        return 0

    except (ValueError, OSError, json.JSONDecodeError, urllib.error.URLError) as exc:
        report = fail_report(args, [str(exc)], provider)
        print_report(report, args.json)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
