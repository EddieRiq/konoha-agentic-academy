#!/usr/bin/env python3
"""Deterministic validator for Konoha supervised task contracts.

The contract is declarative. Validation output is evidence only.
No command, model, Git, network, patch, memory, or mission operation is executed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

SCHEMA_VERSION = "1.0.0"
CONTRACT_REPORT_TYPE = "supervised_task_contract"
VALIDATION_REPORT_TYPE = "supervised_task_contract_validation_report"

SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
TOKEN_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
PATH_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._*?\-\[\]]+$")

RISK_LEVELS = {"low", "medium", "high", "critical"}
REVIEW_LEVELS = {"standard", "strict", "critical"}
NETWORK_POLICIES = {"blocked", "explicit_approval_required"}
PRIVATE_CONTEXT_POLICIES = {"blocked", "explicit_approval_required"}

KNOWN_OPERATIONS = {
    "inspect_repository",
    "read_public_files",
    "run_deterministic_checks",
    "propose_command",
    "record_external_result",
    "invoke_local_model",
    "execute_command",
    "apply_patch",
    "git_stage",
    "git_commit",
    "git_push",
    "write_private_memory",
    "close_mission",
}

SENSITIVE_OPERATIONS = {
    "invoke_local_model",
    "execute_command",
    "apply_patch",
    "git_stage",
    "git_commit",
    "git_push",
    "write_private_memory",
    "close_mission",
}

NETWORK_SENSITIVE_OPERATIONS = {"git_push"}

PROTECTED_PATH_PREFIXES = (
    ".env",
    "alliance/kirigakure",
    "alliance/private-library",
    "memory/local",
    "vault",
    "sandbox",
)

BOUNDARIES = {
    "arbitrary_shell": "blocked",
    "autonomous_background_agents": "blocked",
    "command_execution": "blocked",
    "git_operations": "blocked",
    "model_invocation": "blocked",
    "network_access": "blocked",
    "private_context_access": "blocked",
    "repository_mutation": "blocked",
    "workspace_mutation": "blocked_except_explicit_report_output_under_sandbox",
    "mission_closure": "blocked",
}


class ContractValidationError(RuntimeError):
    """Invalid invocation, path, or unreadable contract."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fail(message: str) -> None:
    raise ContractValidationError(message)


def read_json_object(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractValidationError(f"contract file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractValidationError(
            f"contract JSON invalid at line {exc.lineno}, column {exc.colno}"
        ) from exc

    if not isinstance(payload, dict):
        raise ContractValidationError("contract JSON must be an object")
    return payload


def write_json(path: Path, payload: Mapping[str, Any], *, force: bool) -> None:
    if path.exists() and not force:
        raise ContractValidationError(
            f"output exists; use --force to overwrite: {path}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_report_output(repo_root: Path, raw_output: Optional[str]) -> Optional[Path]:
    if not raw_output:
        return None

    repo_root = repo_root.resolve()
    sandbox_root = (repo_root / "sandbox").resolve()
    output = Path(raw_output)
    if not output.is_absolute():
        output = repo_root / output
    output = output.resolve()

    if not is_relative_to(output, sandbox_root):
        raise ContractValidationError(
            "report output must stay under <repo-root>/sandbox"
        )
    return output


def issue(
    code: str,
    field: str,
    message: str,
    severity: str = "blocker",
) -> Dict[str, str]:
    return {
        "code": code,
        "field": field,
        "message": message,
        "severity": severity,
    }


def non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def list_of_non_empty_text(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(non_empty_text(item) for item in value)
    )


def normalize_repo_path(raw: str) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    value = raw.strip().replace("\\", "/")
    if not value or value.startswith("/") or re.match(r"^[A-Za-z]:/", value):
        return None

    while value.startswith("./"):
        value = value[2:]

    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None
    if not all(PATH_SEGMENT_RE.fullmatch(part) for part in parts):
        return None
    return value


def path_is_protected(path: str) -> bool:
    lowered = path.lower()
    for prefix in PROTECTED_PATH_PREFIXES:
        p = prefix.lower()
        if lowered == p or lowered.startswith(p + "/"):
            return True
    return False


def approval_map(
    approval_requirements: Any,
    blockers: List[Dict[str, str]],
) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    if not isinstance(approval_requirements, list):
        blockers.append(
            issue(
                "approval_requirements_not_list",
                "approval_requirements",
                "approval_requirements must be a list",
            )
        )
        return result

    for index, item in enumerate(approval_requirements):
        field = f"approval_requirements[{index}]"
        if not isinstance(item, dict):
            blockers.append(
                issue(
                    "approval_requirement_not_object",
                    field,
                    "approval requirement must be an object",
                )
            )
            continue

        operation = item.get("operation")
        token = item.get("approval_token")
        reason = item.get("reason")

        if operation not in KNOWN_OPERATIONS:
            blockers.append(
                issue(
                    "approval_operation_unknown",
                    f"{field}.operation",
                    f"unknown operation: {operation!r}",
                )
            )
            continue

        if operation in result:
            blockers.append(
                issue(
                    "approval_operation_duplicate",
                    f"{field}.operation",
                    f"duplicate approval requirement for {operation}",
                )
            )
            continue

        if not isinstance(token, str) or not TOKEN_RE.fullmatch(token):
            blockers.append(
                issue(
                    "approval_token_invalid",
                    f"{field}.approval_token",
                    "approval token must match ^[A-Z][A-Z0-9_]{2,127}$",
                )
            )

        if not non_empty_text(reason):
            blockers.append(
                issue(
                    "approval_reason_missing",
                    f"{field}.reason",
                    "approval requirement needs a non-empty reason",
                )
            )

        result[operation] = item

    return result


def validate_contract(payload: Dict[str, Any]) -> Tuple[
    List[Dict[str, str]],
    List[Dict[str, str]],
    Dict[str, Any],
]:
    blockers: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    required_top_level = {
        "schema_version",
        "report_type",
        "contract_id",
        "mission_id",
        "title",
        "objective",
        "non_goals",
        "risk_level",
        "scope",
        "operations",
        "network_policy",
        "private_context_policy",
        "acceptance_criteria",
        "evidence_requirements",
        "approval_requirements",
        "completion_conditions",
        "review",
        "teachback_required",
        "stop_triggers",
        "authority",
    }
    missing = sorted(required_top_level - set(payload))
    for field in missing:
        blockers.append(
            issue(
                "required_field_missing",
                field,
                f"required field is missing: {field}",
            )
        )

    if payload.get("schema_version") != SCHEMA_VERSION:
        blockers.append(
            issue(
                "schema_version_invalid",
                "schema_version",
                f"schema_version must be {SCHEMA_VERSION}",
            )
        )

    if payload.get("report_type") != CONTRACT_REPORT_TYPE:
        blockers.append(
            issue(
                "report_type_invalid",
                "report_type",
                f"report_type must be {CONTRACT_REPORT_TYPE}",
            )
        )

    for field in ("contract_id", "mission_id"):
        value = payload.get(field)
        if not isinstance(value, str) or not SAFE_ID_RE.fullmatch(value):
            blockers.append(
                issue(
                    "safe_id_invalid",
                    field,
                    f"{field} must match ^[a-z0-9][a-z0-9._-]{{0,79}}$",
                )
            )

    for field in ("title", "objective"):
        if not non_empty_text(payload.get(field)):
            blockers.append(
                issue(
                    "text_required",
                    field,
                    f"{field} must be non-empty text",
                )
            )

    if not list_of_non_empty_text(payload.get("non_goals")):
        blockers.append(
            issue(
                "non_goals_invalid",
                "non_goals",
                "non_goals must be a non-empty list of text items",
            )
        )

    risk_level = payload.get("risk_level")
    if risk_level not in RISK_LEVELS:
        blockers.append(
            issue(
                "risk_level_invalid",
                "risk_level",
                f"risk_level must be one of {sorted(RISK_LEVELS)}",
            )
        )

    scope = payload.get("scope")
    normalized_allowed_paths: List[str] = []
    normalized_blocked_paths: List[str] = []

    if not isinstance(scope, dict):
        blockers.append(
            issue(
                "scope_invalid",
                "scope",
                "scope must be an object",
            )
        )
        scope = {}

    for key, destination in (
        ("allowed_paths", normalized_allowed_paths),
        ("blocked_paths", normalized_blocked_paths),
    ):
        value = scope.get(key)
        if not list_of_non_empty_text(value):
            blockers.append(
                issue(
                    f"{key}_invalid",
                    f"scope.{key}",
                    f"scope.{key} must be a non-empty list",
                )
            )
            continue

        for index, raw in enumerate(value):
            normalized = normalize_repo_path(raw)
            if normalized is None:
                blockers.append(
                    issue(
                        "repo_path_invalid",
                        f"scope.{key}[{index}]",
                        f"invalid repository-relative path: {raw!r}",
                    )
                )
                continue
            destination.append(normalized)

    for index, path in enumerate(normalized_allowed_paths):
        if path_is_protected(path):
            blockers.append(
                issue(
                    "protected_path_allowed",
                    f"scope.allowed_paths[{index}]",
                    f"protected/private path cannot be allowed: {path}",
                )
            )

    overlap_paths = sorted(
        set(normalized_allowed_paths) & set(normalized_blocked_paths)
    )
    for path in overlap_paths:
        blockers.append(
            issue(
                "scope_path_overlap",
                "scope",
                f"path appears in both allowed_paths and blocked_paths: {path}",
            )
        )

    operations = payload.get("operations")
    if not isinstance(operations, dict):
        blockers.append(
            issue(
                "operations_invalid",
                "operations",
                "operations must be an object",
            )
        )
        operations = {}

    allowed_operations = operations.get("allowed")
    blocked_operations = operations.get("blocked")

    if not list_of_non_empty_text(allowed_operations):
        blockers.append(
            issue(
                "allowed_operations_invalid",
                "operations.allowed",
                "operations.allowed must be a non-empty list",
            )
        )
        allowed_operations = []

    if not list_of_non_empty_text(blocked_operations):
        blockers.append(
            issue(
                "blocked_operations_invalid",
                "operations.blocked",
                "operations.blocked must be a non-empty list",
            )
        )
        blocked_operations = []

    allowed_set = set(allowed_operations)
    blocked_set = set(blocked_operations)

    for index, operation in enumerate(allowed_operations):
        if operation not in KNOWN_OPERATIONS:
            blockers.append(
                issue(
                    "allowed_operation_unknown",
                    f"operations.allowed[{index}]",
                    f"unknown operation: {operation}",
                )
            )

    for index, operation in enumerate(blocked_operations):
        if operation not in KNOWN_OPERATIONS:
            blockers.append(
                issue(
                    "blocked_operation_unknown",
                    f"operations.blocked[{index}]",
                    f"unknown operation: {operation}",
                )
            )

    for operation in sorted(allowed_set & blocked_set):
        blockers.append(
            issue(
                "operation_overlap",
                "operations",
                f"operation appears in allowed and blocked: {operation}",
            )
        )

    uncovered_operations = KNOWN_OPERATIONS - allowed_set - blocked_set
    for operation in sorted(uncovered_operations):
        warnings.append(
            issue(
                "operation_unspecified",
                "operations",
                f"operation is neither allowed nor blocked: {operation}",
                severity="warning",
            )
        )

    network_policy = payload.get("network_policy")
    if network_policy not in NETWORK_POLICIES:
        blockers.append(
            issue(
                "network_policy_invalid",
                "network_policy",
                f"network_policy must be one of {sorted(NETWORK_POLICIES)}",
            )
        )

    private_context_policy = payload.get("private_context_policy")
    if private_context_policy not in PRIVATE_CONTEXT_POLICIES:
        blockers.append(
            issue(
                "private_context_policy_invalid",
                "private_context_policy",
                "private_context_policy must be blocked or explicit_approval_required",
            )
        )

    for field in (
        "acceptance_criteria",
        "evidence_requirements",
        "completion_conditions",
        "stop_triggers",
    ):
        if not list_of_non_empty_text(payload.get(field)):
            blockers.append(
                issue(
                    f"{field}_invalid",
                    field,
                    f"{field} must be a non-empty list of text items",
                )
            )

    approvals = approval_map(payload.get("approval_requirements"), blockers)

    for operation in sorted(allowed_set & SENSITIVE_OPERATIONS):
        if operation not in approvals:
            blockers.append(
                issue(
                    "sensitive_operation_without_approval",
                    "approval_requirements",
                    f"allowed sensitive operation requires approval: {operation}",
                )
            )

    for operation in sorted(set(approvals) - allowed_set):
        warnings.append(
            issue(
                "approval_for_non_allowed_operation",
                "approval_requirements",
                f"approval is declared for an operation not allowed by this contract: {operation}",
                severity="warning",
            )
        )

    if "git_push" in allowed_set and network_policy != "explicit_approval_required":
        blockers.append(
            issue(
                "git_push_network_policy_invalid",
                "network_policy",
                "git_push requires network_policy=explicit_approval_required",
            )
        )

    if (
        "write_private_memory" in allowed_set
        and private_context_policy != "explicit_approval_required"
    ):
        blockers.append(
            issue(
                "private_memory_policy_invalid",
                "private_context_policy",
                "write_private_memory requires explicit_approval_required",
            )
        )

    review = payload.get("review")
    if not isinstance(review, dict):
        blockers.append(
            issue(
                "review_invalid",
                "review",
                "review must be an object",
            )
        )
        review = {}

    if review.get("required") is not True:
        blockers.append(
            issue(
                "review_not_required",
                "review.required",
                "review.required must be true",
            )
        )

    review_level = review.get("level")
    if review_level not in REVIEW_LEVELS:
        blockers.append(
            issue(
                "review_level_invalid",
                "review.level",
                f"review.level must be one of {sorted(REVIEW_LEVELS)}",
            )
        )

    if not list_of_non_empty_text(review.get("reviewers")):
        blockers.append(
            issue(
                "reviewers_invalid",
                "review.reviewers",
                "review.reviewers must be a non-empty list",
            )
        )

    if risk_level == "high" and review_level == "standard":
        blockers.append(
            issue(
                "review_level_too_low",
                "review.level",
                "high-risk contracts require strict or critical review",
            )
        )
    if risk_level == "critical" and review_level != "critical":
        blockers.append(
            issue(
                "review_level_too_low",
                "review.level",
                "critical-risk contracts require critical review",
            )
        )

    if payload.get("teachback_required") is not True:
        blockers.append(
            issue(
                "teachback_not_required",
                "teachback_required",
                "teachback_required must be true",
            )
        )

    authority = payload.get("authority")
    required_authority = {
        "contract_is_not_permission": True,
        "validator_output_is_evidence_only": True,
        "mission_state_does_not_authorize_execution": True,
        "approvals_are_operation_specific": True,
    }
    if not isinstance(authority, dict):
        blockers.append(
            issue(
                "authority_invalid",
                "authority",
                "authority must be an object",
            )
        )
        authority = {}

    for key, expected in required_authority.items():
        if authority.get(key) is not expected:
            blockers.append(
                issue(
                    "authority_flag_missing",
                    f"authority.{key}",
                    f"authority.{key} must be true",
                )
            )

    if "close_mission" in allowed_set:
        if payload.get("teachback_required") is not True:
            blockers.append(
                issue(
                    "closure_without_teachback",
                    "teachback_required",
                    "close_mission cannot be allowed without Teachback",
                )
            )
        if "close_mission" not in approvals:
            blockers.append(
                issue(
                    "closure_without_approval",
                    "approval_requirements",
                    "close_mission requires an operation-specific approval",
                )
            )

    normalized = {
        "contract_id": payload.get("contract_id"),
        "mission_id": payload.get("mission_id"),
        "title": payload.get("title"),
        "objective": payload.get("objective"),
        "risk_level": risk_level,
        "allowed_paths": normalized_allowed_paths,
        "blocked_paths": normalized_blocked_paths,
        "allowed_operations": sorted(
            operation for operation in allowed_set if operation in KNOWN_OPERATIONS
        ),
        "blocked_operations": sorted(
            operation for operation in blocked_set if operation in KNOWN_OPERATIONS
        ),
        "approval_operations": sorted(approvals),
        "network_policy": network_policy,
        "private_context_policy": private_context_policy,
        "acceptance_criteria_count": len(payload.get("acceptance_criteria") or []),
        "evidence_requirements_count": len(payload.get("evidence_requirements") or []),
        "completion_conditions_count": len(payload.get("completion_conditions") or []),
        "stop_triggers_count": len(payload.get("stop_triggers") or []),
        "teachback_required": payload.get("teachback_required") is True,
        "review_required": review.get("required") is True,
        "review_level": review_level,
    }

    return blockers, warnings, normalized


def build_report(
    contract_path: Path,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    blockers, warnings, normalized = validate_contract(payload)
    readiness = "ready" if not blockers else "blocked"

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": VALIDATION_REPORT_TYPE,
        "generated_at": utc_now(),
        "status": "passed",
        "readiness": readiness,
        "contract_path": str(contract_path.resolve()),
        "contract_report_type": payload.get("report_type"),
        "contract_id": payload.get("contract_id"),
        "mission_id": payload.get("mission_id"),
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "blockers": blockers,
        "warnings": warnings,
        "normalized_contract_summary": normalized,
        "authority": {
            "contract_is_not_permission": True,
            "validator_output_is_evidence_only": True,
            "ready_does_not_authorize_execution": True,
            "approval_tokens_are_not_consumed": True,
            "mission_state_does_not_authorize_execution": True,
        },
        "boundaries": BOUNDARIES,
        "next_recommended_action": (
            "Human reviewer must inspect the contract before any separate approval or execution gate."
            if readiness == "ready"
            else "Resolve blockers and revalidate before proposing execution."
        ),
    }


def print_text(report: Dict[str, Any]) -> None:
    print("KONOHA SUPERVISED TASK CONTRACT VALIDATOR")
    print(f"readiness: {report['readiness']}")
    print(f"contract: {report.get('contract_id')}")
    print(f"mission: {report.get('mission_id')}")
    print(f"blockers: {report['blocker_count']}")
    print(f"warnings: {report['warning_count']}")
    for blocker in report["blockers"]:
        print(
            f"BLOCKER [{blocker['code']}] "
            f"{blocker['field']}: {blocker['message']}"
        )
    for warning in report["warnings"]:
        print(
            f"WARNING [{warning['code']}] "
            f"{warning['field']}: {warning['message']}"
        )
    print(f"next action: {report['next_recommended_action']}")
    print("Command execution: blocked")
    print("Git operations: blocked")
    print("Model invocation: blocked")
    print("Network access: blocked")
    print("Private context access: blocked")
    print("Result is evidence only.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a declarative Konoha supervised task contract."
    )
    parser.add_argument("--contract", required=True, help="Contract JSON path.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument(
        "--output",
        default=None,
        help="Optional report path under <repo-root>/sandbox.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing report output.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the validation report as JSON.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        repo_root = Path(args.repo_root).resolve()
        contract_path = Path(args.contract)
        if not contract_path.is_absolute():
            contract_path = repo_root / contract_path
        contract_path = contract_path.resolve()

        payload = read_json_object(contract_path)
        report = build_report(contract_path, payload)

        output = resolve_report_output(repo_root, args.output)
        if output is not None:
            write_json(output, report, force=args.force)

        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_text(report)

        return 0 if report["readiness"] == "ready" else 1
    except ContractValidationError as exc:
        error_report = {
            "schema_version": SCHEMA_VERSION,
            "report_type": VALIDATION_REPORT_TYPE,
            "generated_at": utc_now(),
            "status": "failed",
            "readiness": "blocked",
            "error": str(exc),
            "authority": {
                "validator_output_is_evidence_only": True,
                "error_does_not_authorize_fallback": True,
            },
            "boundaries": BOUNDARIES,
        }
        if args.json:
            print(json.dumps(error_report, indent=2, sort_keys=True))
        else:
            print(f"SUPERVISED TASK CONTRACT VALIDATION FAILED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
