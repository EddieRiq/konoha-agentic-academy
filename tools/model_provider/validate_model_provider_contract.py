#!/usr/bin/env python3
"""Validate Konoha model provider contracts and model request plans.

This tool is intentionally read-only. It validates whether a model request plan
is safe to record for later review. It does not call model providers, use
network access, execute tools, mutate the repository, or authorize runtime
actions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


REQUIRED_CONTRACT_FIELDS = {
    "contract_version",
    "provider_allowlist",
    "default_provider",
    "network_access",
    "real_model_invocation",
    "private_context_access",
    "max_prompt_tokens",
    "max_completion_tokens",
    "max_estimated_cost_usd",
    "allowed_context_sources",
    "blocked_context_sources",
    "required_approval_token",
    "redaction_required",
    "logging_required",
}

REQUIRED_REQUEST_FIELDS = {
    "request_id",
    "mission_id",
    "provider",
    "model",
    "purpose",
    "prompt",
    "context_sources",
    "estimated_prompt_tokens",
    "requested_completion_tokens",
    "estimated_cost_usd",
    "contains_private_context",
    "requires_network",
}

SAFE_PURPOSES = {
    "planning",
    "review",
    "summarization",
    "classification",
    "coding_assistance",
    "documentation",
    "risk_review",
}

SECRET_PATTERNS = [
    re.compile(r"api[_-]?key\s*[:=]", re.IGNORECASE),
    re.compile(r"password\s*[:=]", re.IGNORECASE),
    re.compile(r"secret\s*[:=]", re.IGNORECASE),
    re.compile(r"bearer\s+[a-z0-9._\-]{12,}", re.IGNORECASE),
    re.compile(r"sk-[a-zA-Z0-9]{12,}"),
]


def load_json(path: Path) -> Tuple[Dict[str, Any], List[str]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return {}, [f"file not found: {path}"]
    except json.JSONDecodeError as exc:
        return {}, [f"invalid JSON in {path}: {exc}"]

    if not isinstance(data, dict):
        return {}, [f"expected JSON object in {path}"]

    return data, []


def missing_fields(data: Dict[str, Any], required: Iterable[str]) -> List[str]:
    return sorted(field for field in required if field not in data)


def validate_contract(contract: Dict[str, Any]) -> List[str]:
    blockers: List[str] = []

    for field in missing_fields(contract, REQUIRED_CONTRACT_FIELDS):
        blockers.append(f"contract missing required field: {field}")

    if blockers:
        return blockers

    if not isinstance(contract["provider_allowlist"], list) or not contract["provider_allowlist"]:
        blockers.append("provider_allowlist must be a non-empty list")

    if contract["default_provider"] not in contract.get("provider_allowlist", []):
        blockers.append("default_provider must be present in provider_allowlist")

    if contract["network_access"] != "blocked":
        blockers.append("network_access must be blocked in v1.4 contract validation")

    if contract["real_model_invocation"] != "blocked":
        blockers.append("real_model_invocation must be blocked in v1.4")

    if contract["private_context_access"] != "blocked":
        blockers.append("private_context_access must be blocked in v1.4")

    if not bool(contract["redaction_required"]):
        blockers.append("redaction_required must be true")

    if not bool(contract["logging_required"]):
        blockers.append("logging_required must be true")

    for numeric_field in ("max_prompt_tokens", "max_completion_tokens", "max_estimated_cost_usd"):
        value = contract[numeric_field]
        if not isinstance(value, (int, float)) or value < 0:
            blockers.append(f"{numeric_field} must be a non-negative number")

    if not isinstance(contract["allowed_context_sources"], list):
        blockers.append("allowed_context_sources must be a list")

    if not isinstance(contract["blocked_context_sources"], list):
        blockers.append("blocked_context_sources must be a list")

    if not isinstance(contract["required_approval_token"], str) or not contract["required_approval_token"]:
        blockers.append("required_approval_token must be a non-empty string")

    return blockers


def prompt_contains_secret(prompt: str) -> bool:
    return any(pattern.search(prompt) for pattern in SECRET_PATTERNS)


def validate_request(contract: Dict[str, Any], request: Dict[str, Any]) -> List[str]:
    blockers: List[str] = []

    for field in missing_fields(request, REQUIRED_REQUEST_FIELDS):
        blockers.append(f"request missing required field: {field}")

    if blockers:
        return blockers

    provider = request["provider"]
    if provider not in contract.get("provider_allowlist", []):
        blockers.append(f"provider is not allowlisted: {provider}")

    if request["purpose"] not in SAFE_PURPOSES:
        blockers.append(f"purpose is not safe for v1.4 contract validation: {request['purpose']}")

    if bool(request["requires_network"]):
        blockers.append("request requires network access, which is blocked in v1.4")

    if bool(request["contains_private_context"]):
        blockers.append("request contains private context, which is blocked by default")

    prompt = request["prompt"]
    if not isinstance(prompt, str) or not prompt.strip():
        blockers.append("prompt must be a non-empty string")
    elif prompt_contains_secret(prompt):
        blockers.append("prompt appears to contain a secret-like pattern")

    allowed_sources = set(contract.get("allowed_context_sources", []))
    blocked_sources = set(contract.get("blocked_context_sources", []))
    context_sources = request["context_sources"]

    if not isinstance(context_sources, list):
        blockers.append("context_sources must be a list")
    else:
        for source in context_sources:
            if source in blocked_sources:
                blockers.append(f"context source is blocked: {source}")
            if source not in allowed_sources:
                blockers.append(f"context source is not allowlisted: {source}")

    if request["estimated_prompt_tokens"] > contract["max_prompt_tokens"]:
        blockers.append("estimated_prompt_tokens exceeds contract limit")

    if request["requested_completion_tokens"] > contract["max_completion_tokens"]:
        blockers.append("requested_completion_tokens exceeds contract limit")

    if request["estimated_cost_usd"] > contract["max_estimated_cost_usd"]:
        blockers.append("estimated_cost_usd exceeds contract limit")

    for numeric_field in ("estimated_prompt_tokens", "requested_completion_tokens", "estimated_cost_usd"):
        value = request[numeric_field]
        if not isinstance(value, (int, float)) or value < 0:
            blockers.append(f"{numeric_field} must be a non-negative number")

    return blockers


def build_report(contract: Dict[str, Any], request: Dict[str, Any], blockers: List[str]) -> Dict[str, Any]:
    passed = not blockers
    return {
        "report_type": "model_provider_contract_validation",
        "contract_version": contract.get("contract_version"),
        "request_id": request.get("request_id"),
        "mission_id": request.get("mission_id"),
        "provider": request.get("provider"),
        "model": request.get("model"),
        "purpose": request.get("purpose"),
        "status": "passed" if passed else "failed",
        "checks": {
            "contract_shape": "passed" if not missing_fields(contract, REQUIRED_CONTRACT_FIELDS) else "failed",
            "request_shape": "passed" if not missing_fields(request, REQUIRED_REQUEST_FIELDS) else "failed",
            "provider_allowlist": "passed" if request.get("provider") in contract.get("provider_allowlist", []) else "failed",
            "budget": "passed" if passed or not any("exceeds contract limit" in b for b in blockers) else "failed",
            "private_context": "blocked",
            "network_access": "blocked",
            "real_model_invocation": "blocked",
            "filesystem_mutation": "blocked",
            "git_operations": "blocked",
            "runtime_authorization": "blocked",
        },
        "limits": {
            "max_prompt_tokens": contract.get("max_prompt_tokens"),
            "max_completion_tokens": contract.get("max_completion_tokens"),
            "max_estimated_cost_usd": contract.get("max_estimated_cost_usd"),
        },
        "request_budget": {
            "estimated_prompt_tokens": request.get("estimated_prompt_tokens"),
            "requested_completion_tokens": request.get("requested_completion_tokens"),
            "estimated_cost_usd": request.get("estimated_cost_usd"),
        },
        "blockers": blockers,
        "human_review_required": True,
        "approval_token_required_for_future_invocation": contract.get("required_approval_token"),
    }


def print_text_report(report: Dict[str, Any]) -> None:
    if report["status"] == "passed":
        print("MODEL PROVIDER CONTRACT VALIDATION PASSED")
    else:
        print("MODEL PROVIDER CONTRACT VALIDATION FAILED")

    print(f"Provider: {report.get('provider')}")
    print(f"Model: {report.get('model')}")
    print(f"Purpose: {report.get('purpose')}")
    print("Invocation: blocked")
    print("Execution: blocked")
    print("Filesystem mutation: blocked")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Real model invocation: blocked")
    print("Network access: blocked")
    print("Human review required: true")

    for blocker in report.get("blockers", []):
        print(f"Blocker: {blocker}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a Konoha model provider contract and request plan without invoking a model."
    )
    parser.add_argument("--contract", required=True, help="Path to model provider contract JSON.")
    parser.add_argument("--request", required=True, help="Path to model request JSON.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    contract_path = Path(args.contract)
    request_path = Path(args.request)

    contract, contract_errors = load_json(contract_path)
    request, request_errors = load_json(request_path)

    blockers = contract_errors + request_errors
    if not blockers:
        blockers.extend(validate_contract(contract))
    if not blockers:
        blockers.extend(validate_request(contract, request))

    report = build_report(contract, request, blockers)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
