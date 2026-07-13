#!/usr/bin/env python3
"""Validate a Konoha supervised action proposal.

This validator composes a v3.2.0 supervised task contract and a v3.2.1
supervised task evidence bundle into a proposal-review artifact. It does not
execute commands, consume approvals, apply patches, mutate Git, access network
or private context, or close missions.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

SCHEMA_VERSION = "1.0.0"
PROPOSAL_REPORT_TYPE = "supervised_action_proposal"
VALIDATION_REPORT_TYPE = "supervised_action_proposal_validation_report"
CONTRACT_REPORT_TYPE = "supervised_task_contract"
EVIDENCE_REPORT_TYPE = "supervised_task_evidence_bundle"

SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
APPROVAL_TOKEN_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

OPERATIONS = {
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

STATE_CHANGING_OPERATIONS = {
    "execute_command",
    "apply_patch",
    "git_stage",
    "git_commit",
    "git_push",
    "write_private_memory",
    "close_mission",
}

COMMAND_OPERATIONS = {
    "run_deterministic_checks",
    "invoke_local_model",
    "execute_command",
    "apply_patch",
    "git_stage",
    "git_commit",
    "git_push",
}

RISK_ORDER = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}

REVIEW_ORDER = {
    "standard": 0,
    "strict": 1,
    "critical": 2,
}

PRIVATE_PREFIXES = (
    ".env",
    "alliance/kirigakure",
    "alliance/private-library",
    "memory/local",
    "vault",
)

SHELL_META_TOKENS = {
    "|",
    "||",
    "&&",
    ";",
    ">",
    ">>",
    "<",
    "<<",
    "`",
}

BOUNDARIES = {
    "command_execution": "blocked",
    "approval_consumption": "blocked",
    "filesystem_mutation": "blocked_except_explicit_report_output_under_sandbox",
    "git_operations": "blocked",
    "model_invocation": "blocked",
    "network_access": "blocked",
    "private_context_access": "blocked",
    "repository_apply": "blocked",
    "rollback_execution": "blocked",
    "mission_closure": "blocked",
}


class ProposalValidationError(RuntimeError):
    """Invalid invocation, unsafe path, or unreadable JSON."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json_object(path: Path, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProposalValidationError(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProposalValidationError(
            f"{label} JSON invalid at line {exc.lineno}, column {exc.colno}"
        ) from exc

    if not isinstance(payload, dict):
        raise ProposalValidationError(f"{label} JSON must be an object")
    return payload


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def normalize_relative_path(raw: Any) -> Optional[str]:
    if not isinstance(raw, str):
        return None

    value = raw.strip().replace("\\", "/")
    if not value or value.startswith("/") or re.match(r"^[A-Za-z]:/", value):
        return None

    while value.startswith("./"):
        value = value[2:]

    if value == ".":
        return "."

    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None

    return value


def path_is_private(relative_path: str) -> bool:
    lowered = relative_path.lower()
    parts = lowered.split("/")

    if lowered == ".env" or lowered.startswith(".env."):
        return True

    for prefix in PRIVATE_PREFIXES:
        normalized = prefix.lower()
        if lowered == normalized or lowered.startswith(normalized + "/"):
            return True

    if len(parts) >= 3 and parts[0] == "alliance":
        if parts[2] in {"private-library", "memory"}:
            return True

    return False


def resolve_repo_file(
    repo_root: Path,
    raw_path: Any,
    *,
    label: str,
) -> Tuple[Optional[str], Optional[Path], Optional[str]]:
    relative = normalize_relative_path(raw_path)
    if relative is None or relative == ".":
        return None, None, f"{label} must be a repository-relative file path"

    if path_is_private(relative):
        return (
            relative,
            None,
            f"{label} points to blocked private context: {relative}",
        )

    resolved = (repo_root / relative).resolve()
    if not is_relative_to(resolved, repo_root):
        return relative, None, f"{label} escapes the repository root"

    if not resolved.is_file():
        return relative, resolved, f"{label} file not found: {relative}"

    return relative, resolved, None


def resolve_output(repo_root: Path, raw_output: Optional[str]) -> Optional[Path]:
    if not raw_output:
        return None

    sandbox_root = (repo_root / "sandbox").resolve()
    output = Path(raw_output)
    if not output.is_absolute():
        output = repo_root / output
    output = output.resolve()

    if not is_relative_to(output, sandbox_root):
        raise ProposalValidationError(
            "validation output must stay under <repo-root>/sandbox"
        )
    return output


def write_json(path: Path, payload: Mapping[str, Any], *, force: bool) -> None:
    if path.exists() and not force:
        raise ProposalValidationError(
            f"output exists; use --force to overwrite: {path}"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


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


def list_value(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def validate_safe_id(
    value: Any,
    field: str,
    blockers: List[Dict[str, str]],
) -> Optional[str]:
    if not isinstance(value, str) or not SAFE_ID_RE.fullmatch(value):
        blockers.append(
            issue(
                "safe_id_invalid",
                field,
                f"{field} must match ^[a-z0-9][a-z0-9._-]{{0,79}}$",
            )
        )
        return None
    return value


def validate_reference(
    repo_root: Path,
    reference: Any,
    *,
    field: str,
    expected_report_type: str,
    blockers: List[Dict[str, str]],
) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    if not isinstance(reference, dict):
        blockers.append(
            issue(
                "reference_invalid",
                field,
                f"{field} must be an object",
            )
        )
        return None, None, None

    relative, resolved, path_error = resolve_repo_file(
        repo_root,
        reference.get("path"),
        label=f"{field}.path",
    )
    if path_error:
        blockers.append(
            issue(
                "reference_path_invalid",
                f"{field}.path",
                path_error,
            )
        )
        return None, relative, None

    expected_hash = reference.get("sha256")
    if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(
        expected_hash
    ):
        blockers.append(
            issue(
                "reference_sha256_invalid",
                f"{field}.sha256",
                f"{field}.sha256 must be 64 lowercase hex characters",
            )
        )
        return None, relative, None

    assert resolved is not None
    actual_hash = sha256_file(resolved)
    if actual_hash != expected_hash:
        blockers.append(
            issue(
                "reference_sha256_mismatch",
                f"{field}.sha256",
                f"hash mismatch for {relative}",
            )
        )

    try:
        payload = read_json_object(resolved, field)
    except ProposalValidationError as exc:
        blockers.append(
            issue(
                "reference_unreadable",
                f"{field}.path",
                str(exc),
            )
        )
        return None, relative, actual_hash

    if payload.get("report_type") != expected_report_type:
        blockers.append(
            issue(
                "reference_report_type_invalid",
                f"{field}.path",
                f"referenced file must be {expected_report_type}",
            )
        )

    if payload.get("schema_version") != SCHEMA_VERSION:
        blockers.append(
            issue(
                "reference_schema_version_invalid",
                f"{field}.path",
                f"referenced schema_version must be {SCHEMA_VERSION}",
            )
        )

    return payload, relative, actual_hash


def approval_map(contract: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for item in list_value(contract.get("approval_requirements")):
        if not isinstance(item, dict):
            continue
        operation = item.get("operation")
        token = item.get("approval_token")
        if (
            operation in OPERATIONS
            and isinstance(token, str)
            and APPROVAL_TOKEN_RE.fullmatch(token)
        ):
            result[operation] = item
    return result


def path_matches(pattern: str, path: str) -> bool:
    normalized_pattern = pattern.replace("\\", "/")
    normalized_path = path.replace("\\", "/")
    if normalized_pattern == normalized_path:
        return True
    return fnmatch.fnmatchcase(normalized_path, normalized_pattern)


def path_allowed_by_contract(
    contract: Mapping[str, Any],
    path: str,
) -> Tuple[bool, Optional[str]]:
    if path_is_private(path):
        return False, "private"

    scope = contract.get("scope")
    if not isinstance(scope, dict):
        return False, "scope"

    blocked = [
        item
        for item in list_value(scope.get("blocked_paths"))
        if isinstance(item, str)
    ]
    allowed = [
        item
        for item in list_value(scope.get("allowed_paths"))
        if isinstance(item, str)
    ]

    for pattern in blocked:
        if path_matches(pattern, path):
            return False, "blocked"

    if any(path_matches(pattern, path) for pattern in allowed):
        return True, None

    return False, "outside"


def validate_evidence_bundle(
    repo_root: Path,
    contract: Mapping[str, Any],
    evidence: Mapping[str, Any],
    proposal_contract_ref: Mapping[str, Any],
    blockers: List[Dict[str, str]],
) -> Dict[str, Dict[str, Any]]:
    contract_authority = contract.get("authority")
    required_contract_authority = {
        "contract_is_not_permission": True,
        "validator_output_is_evidence_only": True,
        "mission_state_does_not_authorize_execution": True,
        "approvals_are_operation_specific": True,
    }
    if not isinstance(contract_authority, dict):
        blockers.append(
            issue(
                "contract_authority_invalid",
                "contract_reference",
                "referenced contract authority must be an object",
            )
        )
    else:
        for key, expected in required_contract_authority.items():
            if contract_authority.get(key) is not expected:
                blockers.append(
                    issue(
                        "contract_authority_flag_missing",
                        f"contract_reference.authority.{key}",
                        f"referenced contract requires {key}=true",
                    )
                )

    if contract.get("teachback_required") is not True:
        blockers.append(
            issue(
                "contract_teachback_not_required",
                "contract_reference",
                "referenced contract must require Teachback",
            )
        )

    contract_review = contract.get("review")
    if not isinstance(contract_review, dict) or contract_review.get(
        "required"
    ) is not True:
        blockers.append(
            issue(
                "contract_review_not_required",
                "contract_reference",
                "referenced contract must require review",
            )
        )

    evidence_authority = evidence.get("authority")
    required_evidence_authority = {
        "bundle_is_evidence_only": True,
        "evidence_does_not_authorize_execution": True,
        "hashes_do_not_prove_truth": True,
        "human_review_required": True,
    }
    if not isinstance(evidence_authority, dict):
        blockers.append(
            issue(
                "evidence_authority_invalid",
                "evidence_bundle_reference",
                "referenced evidence authority must be an object",
            )
        )
    else:
        for key, expected in required_evidence_authority.items():
            if evidence_authority.get(key) is not expected:
                blockers.append(
                    issue(
                        "evidence_authority_flag_missing",
                        f"evidence_bundle_reference.authority.{key}",
                        f"referenced evidence requires {key}=true",
                    )
                )

    if evidence.get("contract_id") != contract.get("contract_id"):
        blockers.append(
            issue(
                "evidence_contract_id_mismatch",
                "evidence_bundle_reference",
                "evidence bundle contract_id does not match contract",
            )
        )

    if evidence.get("mission_id") != contract.get("mission_id"):
        blockers.append(
            issue(
                "evidence_mission_id_mismatch",
                "evidence_bundle_reference",
                "evidence bundle mission_id does not match contract",
            )
        )

    evidence_contract_ref = evidence.get("contract_reference")
    if not isinstance(evidence_contract_ref, dict):
        blockers.append(
            issue(
                "evidence_contract_reference_invalid",
                "evidence_bundle_reference",
                "evidence bundle contract_reference must be an object",
            )
        )
    else:
        if evidence_contract_ref.get("path") != proposal_contract_ref.get(
            "path"
        ):
            blockers.append(
                issue(
                    "evidence_contract_path_mismatch",
                    "evidence_bundle_reference",
                    "evidence bundle references a different contract path",
                )
            )
        if evidence_contract_ref.get("sha256") != proposal_contract_ref.get(
            "sha256"
        ):
            blockers.append(
                issue(
                    "evidence_contract_hash_mismatch",
                    "evidence_bundle_reference",
                    "evidence bundle references a different contract hash",
                )
            )

    requirements = [
        item
        for item in list_value(contract.get("evidence_requirements"))
        if isinstance(item, str)
    ]

    by_id: Dict[str, Dict[str, Any]] = {}
    covered_indices: set[int] = set()
    source_ids: set[str] = set()

    items = evidence.get("evidence_items")
    if not isinstance(items, list) or not items:
        blockers.append(
            issue(
                "evidence_items_invalid",
                "evidence_bundle_reference",
                "evidence bundle must contain evidence_items",
            )
        )
        items = []

    for index, item in enumerate(items):
        field = f"evidence_bundle.evidence_items[{index}]"
        if not isinstance(item, dict):
            blockers.append(
                issue(
                    "evidence_item_invalid",
                    field,
                    "evidence item must be an object",
                )
            )
            continue

        evidence_id = item.get("evidence_id")
        if not isinstance(evidence_id, str) or not SAFE_ID_RE.fullmatch(
            evidence_id
        ):
            blockers.append(
                issue(
                    "evidence_id_invalid",
                    f"{field}.evidence_id",
                    "evidence_id is invalid",
                )
            )
        elif evidence_id in by_id:
            blockers.append(
                issue(
                    "evidence_id_duplicate",
                    f"{field}.evidence_id",
                    f"duplicate evidence_id: {evidence_id}",
                )
            )
        else:
            by_id[evidence_id] = item

        requirement_index = item.get("requirement_index")
        if (
            not isinstance(requirement_index, int)
            or isinstance(requirement_index, bool)
            or requirement_index < 0
            or requirement_index >= len(requirements)
        ):
            blockers.append(
                issue(
                    "evidence_requirement_index_invalid",
                    f"{field}.requirement_index",
                    "evidence requirement index is invalid",
                )
            )
        else:
            if requirement_index in covered_indices:
                blockers.append(
                    issue(
                        "evidence_requirement_duplicate",
                        f"{field}.requirement_index",
                        f"duplicate requirement mapping: {requirement_index}",
                    )
                )
            covered_indices.add(requirement_index)
            if item.get("requirement_text") != requirements[
                requirement_index
            ]:
                blockers.append(
                    issue(
                        "evidence_requirement_text_mismatch",
                        f"{field}.requirement_text",
                        "evidence requirement text does not match contract",
                    )
                )

        if item.get("status") != "satisfied":
            blockers.append(
                issue(
                    "evidence_not_satisfied",
                    f"{field}.status",
                    "all evidence requirements must be satisfied before proposal review",
                )
            )

        sources = item.get("source_refs")
        if not isinstance(sources, list) or not sources:
            blockers.append(
                issue(
                    "evidence_sources_missing",
                    f"{field}.source_refs",
                    "satisfied evidence requires source references",
                )
            )
            sources = []

        for source_index, source in enumerate(sources):
            source_field = f"{field}.source_refs[{source_index}]"
            if not isinstance(source, dict):
                blockers.append(
                    issue(
                        "evidence_source_invalid",
                        source_field,
                        "evidence source must be an object",
                    )
                )
                continue

            source_id = source.get("source_id")
            if not isinstance(source_id, str) or not SAFE_ID_RE.fullmatch(
                source_id
            ):
                blockers.append(
                    issue(
                        "evidence_source_id_invalid",
                        f"{source_field}.source_id",
                        "source_id is invalid",
                    )
                )
            elif source_id in source_ids:
                blockers.append(
                    issue(
                        "evidence_source_id_duplicate",
                        f"{source_field}.source_id",
                        f"duplicate source_id: {source_id}",
                    )
                )
            else:
                source_ids.add(source_id)

            relative, resolved, path_error = resolve_repo_file(
                repo_root,
                source.get("path"),
                label=f"{source_field}.path",
            )
            if path_error:
                blockers.append(
                    issue(
                        "evidence_source_path_invalid",
                        f"{source_field}.path",
                        path_error,
                    )
                )
                continue

            expected_hash = source.get("sha256")
            if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(
                expected_hash
            ):
                blockers.append(
                    issue(
                        "evidence_source_sha256_invalid",
                        f"{source_field}.sha256",
                        "source sha256 is invalid",
                    )
                )
                continue

            assert resolved is not None
            actual_hash = sha256_file(resolved)
            if actual_hash != expected_hash:
                blockers.append(
                    issue(
                        "evidence_source_sha256_mismatch",
                        f"{source_field}.sha256",
                        f"source hash mismatch for {relative}",
                    )
                )

    missing = sorted(set(range(len(requirements))) - covered_indices)
    for requirement_index in missing:
        blockers.append(
            issue(
                "evidence_requirement_missing",
                "evidence_bundle_reference",
                f"evidence requirement {requirement_index} is not mapped",
            )
        )

    unresolved = evidence.get("unresolved")
    if not isinstance(unresolved, list):
        blockers.append(
            issue(
                "evidence_unresolved_invalid",
                "evidence_bundle_reference",
                "evidence unresolved must be a list",
            )
        )
    elif unresolved:
        blockers.append(
            issue(
                "evidence_has_unresolved_items",
                "evidence_bundle_reference",
                "proposal review requires no unresolved evidence items",
            )
        )

    claims = evidence.get("claims")
    if not isinstance(claims, list):
        blockers.append(
            issue(
                "evidence_claims_invalid",
                "evidence_bundle_reference",
                "evidence claims must be a list",
            )
        )
    else:
        for index, claim in enumerate(claims):
            if not isinstance(claim, dict) or claim.get("status") != "supported":
                blockers.append(
                    issue(
                        "evidence_claim_not_supported",
                        f"evidence_bundle.claims[{index}]",
                        "all evidence claims must be supported",
                    )
                )

    findings = evidence.get("findings")
    if not isinstance(findings, list):
        blockers.append(
            issue(
                "evidence_findings_invalid",
                "evidence_bundle_reference",
                "evidence findings must be a list",
            )
        )
    else:
        for index, finding in enumerate(findings):
            if isinstance(finding, dict) and finding.get("level") == "error":
                blockers.append(
                    issue(
                        "evidence_error_finding",
                        f"evidence_bundle.findings[{index}]",
                        "error-level evidence finding blocks proposal review",
                    )
                )

    return by_id


def validate_approval_requirements(
    proposal: Mapping[str, Any],
    contract: Mapping[str, Any],
    action_operations: set[str],
    blockers: List[Dict[str, str]],
) -> Dict[str, Dict[str, Any]]:
    contract_approvals = approval_map(contract)
    proposal_items = proposal.get("approval_requirements")

    if not isinstance(proposal_items, list):
        blockers.append(
            issue(
                "proposal_approvals_invalid",
                "approval_requirements",
                "approval_requirements must be a list",
            )
        )
        proposal_items = []

    proposal_approvals: Dict[str, Dict[str, Any]] = {}
    for index, item in enumerate(proposal_items):
        field = f"approval_requirements[{index}]"
        if not isinstance(item, dict):
            blockers.append(
                issue(
                    "proposal_approval_invalid",
                    field,
                    "approval requirement must be an object",
                )
            )
            continue

        operation = item.get("operation")
        token = item.get("approval_token")

        if operation not in action_operations:
            blockers.append(
                issue(
                    "approval_operation_not_proposed",
                    f"{field}.operation",
                    f"approval operation is not proposed: {operation}",
                )
            )
            continue

        if operation in proposal_approvals:
            blockers.append(
                issue(
                    "proposal_approval_duplicate",
                    f"{field}.operation",
                    f"duplicate proposal approval: {operation}",
                )
            )
            continue

        proposal_approvals[operation] = item

        if not isinstance(token, str) or not APPROVAL_TOKEN_RE.fullmatch(
            token
        ):
            blockers.append(
                issue(
                    "proposal_approval_token_invalid",
                    f"{field}.approval_token",
                    "approval token format is invalid",
                )
            )

        if not non_empty_text(item.get("reason")):
            blockers.append(
                issue(
                    "proposal_approval_reason_missing",
                    f"{field}.reason",
                    "approval reason must be non-empty text",
                )
            )

        contract_item = contract_approvals.get(str(operation))
        if contract_item is None:
            blockers.append(
                issue(
                    "approval_not_declared_by_contract",
                    field,
                    f"contract does not declare approval for {operation}",
                )
            )
            continue

        if token != contract_item.get("approval_token"):
            blockers.append(
                issue(
                    "approval_token_mismatch",
                    f"{field}.approval_token",
                    f"approval token mismatch for {operation}",
                )
            )

    for operation in sorted(action_operations & SENSITIVE_OPERATIONS):
        if operation not in contract_approvals:
            blockers.append(
                issue(
                    "sensitive_operation_not_approved_by_contract",
                    "approval_requirements",
                    f"contract lacks approval declaration for: {operation}",
                )
            )

    required_operations = (
        action_operations & SENSITIVE_OPERATIONS
    ) | (action_operations & set(contract_approvals))

    for operation in sorted(required_operations):
        if operation not in proposal_approvals:
            blockers.append(
                issue(
                    "operation_without_declared_approval",
                    "approval_requirements",
                    f"operation requires declared approval: {operation}",
                )
            )

    return proposal_approvals


def validate_command_argv(
    argv: Any,
    *,
    field: str,
    required: bool,
    blockers: List[Dict[str, str]],
) -> None:
    if argv is None:
        if required:
            blockers.append(
                issue(
                    "command_argv_required",
                    field,
                    "command_argv is required for this operation",
                )
            )
        return

    if not isinstance(argv, list) or not argv:
        blockers.append(
            issue(
                "command_argv_invalid",
                field,
                "command_argv must be a non-empty list",
            )
        )
        return

    for index, token in enumerate(argv):
        token_field = f"{field}[{index}]"
        if not isinstance(token, str) or not token:
            blockers.append(
                issue(
                    "command_token_invalid",
                    token_field,
                    "command token must be non-empty text",
                )
            )
            continue

        if token in SHELL_META_TOKENS or "$(" in token or "`" in token:
            blockers.append(
                issue(
                    "shell_composition_blocked",
                    token_field,
                    f"shell composition token is blocked: {token}",
                )
            )

        if "\n" in token or "\r" in token or "\x00" in token:
            blockers.append(
                issue(
                    "command_control_character_blocked",
                    token_field,
                    "command token contains a blocked control character",
                )
            )


def validate_actions(
    proposal: Mapping[str, Any],
    contract: Mapping[str, Any],
    evidence_by_id: Mapping[str, Mapping[str, Any]],
    blockers: List[Dict[str, str]],
    warnings: List[Dict[str, str]],
) -> Tuple[set[str], bool, set[str]]:
    operations = contract.get("operations")
    allowed_operations = set()
    blocked_operations = set()

    if isinstance(operations, dict):
        allowed_operations = {
            item
            for item in list_value(operations.get("allowed"))
            if isinstance(item, str)
        }
        blocked_operations = {
            item
            for item in list_value(operations.get("blocked"))
            if isinstance(item, str)
        }

    overlap = allowed_operations & blocked_operations
    if overlap:
        blockers.append(
            issue(
                "contract_operation_overlap",
                "contract_reference.operations",
                "contract allowed and blocked operations overlap: "
                + ", ".join(sorted(overlap)),
            )
        )

    missing_contract_operations = OPERATIONS - (
        allowed_operations | blocked_operations
    )
    if missing_contract_operations:
        blockers.append(
            issue(
                "contract_operation_coverage_incomplete",
                "contract_reference.operations",
                "contract operation coverage is incomplete: "
                + ", ".join(sorted(missing_contract_operations)),
            )
        )

    proposal_risk = proposal.get("risk_level")
    if proposal_risk not in RISK_ORDER:
        blockers.append(
            issue(
                "proposal_risk_invalid",
                "risk_level",
                f"risk_level must be one of {sorted(RISK_ORDER)}",
            )
        )
        proposal_risk = "low"

    actions = proposal.get("proposed_actions")
    if not isinstance(actions, list) or not actions:
        blockers.append(
            issue(
                "proposed_actions_invalid",
                "proposed_actions",
                "proposed_actions must be a non-empty list",
            )
        )
        actions = []

    acceptance = [
        item
        for item in list_value(contract.get("acceptance_criteria"))
        if isinstance(item, str)
    ]
    action_ids: set[str] = set()
    action_operations: set[str] = set()
    all_action_paths: set[str] = set()
    state_changing = False
    contract_approvals = approval_map(contract)

    for index, action in enumerate(actions):
        field = f"proposed_actions[{index}]"
        if not isinstance(action, dict):
            blockers.append(
                issue(
                    "proposed_action_invalid",
                    field,
                    "proposed action must be an object",
                )
            )
            continue

        action_id = validate_safe_id(
            action.get("action_id"),
            f"{field}.action_id",
            blockers,
        )
        if action_id is not None:
            if action_id in action_ids:
                blockers.append(
                    issue(
                        "action_id_duplicate",
                        f"{field}.action_id",
                        f"duplicate action_id: {action_id}",
                    )
                )
            action_ids.add(action_id)

        operation = action.get("operation")
        if operation not in OPERATIONS:
            blockers.append(
                issue(
                    "action_operation_invalid",
                    f"{field}.operation",
                    f"operation must be one of {sorted(OPERATIONS)}",
                )
            )
        else:
            action_operations.add(operation)
            if operation not in allowed_operations:
                blockers.append(
                    issue(
                        "action_operation_not_allowed",
                        f"{field}.operation",
                        f"operation is not allowed by contract: {operation}",
                    )
                )
            if operation in blocked_operations:
                blockers.append(
                    issue(
                        "action_operation_blocked",
                        f"{field}.operation",
                        f"operation is blocked by contract: {operation}",
                    )
                )
            if operation in STATE_CHANGING_OPERATIONS:
                state_changing = True

            if operation == "git_push" and contract.get(
                "network_policy"
            ) != "explicit_approval_required":
                blockers.append(
                    issue(
                        "git_push_network_policy_invalid",
                        f"{field}.operation",
                        "git_push requires explicit_approval_required network policy",
                    )
                )

            if operation == "write_private_memory" and contract.get(
                "private_context_policy"
            ) != "explicit_approval_required":
                blockers.append(
                    issue(
                        "private_memory_policy_invalid",
                        f"{field}.operation",
                        "write_private_memory requires explicit private-context approval policy",
                    )
                )

        for text_field in ("purpose", "expected_effect"):
            if not non_empty_text(action.get(text_field)):
                blockers.append(
                    issue(
                        "action_text_missing",
                        f"{field}.{text_field}",
                        f"{text_field} must be non-empty text",
                    )
                )

        if action.get("execution_status") != "proposed_only":
            blockers.append(
                issue(
                    "action_execution_status_invalid",
                    f"{field}.execution_status",
                    "execution_status must be proposed_only",
                )
            )

        action_risk = action.get("risk_level")
        if action_risk not in RISK_ORDER:
            blockers.append(
                issue(
                    "action_risk_invalid",
                    f"{field}.risk_level",
                    f"risk_level must be one of {sorted(RISK_ORDER)}",
                )
            )
        elif RISK_ORDER[action_risk] > RISK_ORDER[proposal_risk]:
            blockers.append(
                issue(
                    "action_risk_exceeds_proposal",
                    f"{field}.risk_level",
                    "action risk cannot exceed proposal risk",
                )
            )

        if action.get("irreversible") is True:
            blockers.append(
                issue(
                    "irreversible_action_blocked",
                    f"{field}.irreversible",
                    "irreversible actions remain blocked in v3.2.2",
                )
            )

        if not isinstance(action.get("destructive"), bool):
            blockers.append(
                issue(
                    "action_destructive_invalid",
                    f"{field}.destructive",
                    "destructive must be boolean",
                )
            )

        paths = action.get("affected_paths")
        if not isinstance(paths, list) or not paths:
            blockers.append(
                issue(
                    "action_paths_invalid",
                    f"{field}.affected_paths",
                    "affected_paths must be a non-empty list",
                )
            )
            paths = []

        seen_paths: set[str] = set()
        for path_index, raw_path in enumerate(paths):
            path_field = f"{field}.affected_paths[{path_index}]"
            normalized = normalize_relative_path(raw_path)
            if normalized is None or normalized == ".":
                blockers.append(
                    issue(
                        "action_path_invalid",
                        path_field,
                        "affected path must be repository-relative",
                    )
                )
                continue
            if normalized in seen_paths:
                blockers.append(
                    issue(
                        "action_path_duplicate",
                        path_field,
                        f"duplicate affected path: {normalized}",
                    )
                )
            seen_paths.add(normalized)
            all_action_paths.add(normalized)

            allowed, reason = path_allowed_by_contract(contract, normalized)
            if not allowed:
                code = (
                    "action_private_path_blocked"
                    if reason == "private"
                    else "action_path_outside_contract"
                )
                blockers.append(
                    issue(
                        code,
                        path_field,
                        f"affected path is not allowed by contract: {normalized}",
                    )
                )

        evidence_ids = action.get("evidence_ids")
        if not isinstance(evidence_ids, list) or not evidence_ids:
            blockers.append(
                issue(
                    "action_evidence_ids_invalid",
                    f"{field}.evidence_ids",
                    "evidence_ids must be a non-empty list",
                )
            )
            evidence_ids = []

        for evidence_index, evidence_id in enumerate(evidence_ids):
            evidence_field = f"{field}.evidence_ids[{evidence_index}]"
            evidence_item = evidence_by_id.get(str(evidence_id))
            if evidence_item is None:
                blockers.append(
                    issue(
                        "action_evidence_unknown",
                        evidence_field,
                        f"unknown evidence_id: {evidence_id}",
                    )
                )
            elif evidence_item.get("status") != "satisfied":
                blockers.append(
                    issue(
                        "action_evidence_not_satisfied",
                        evidence_field,
                        f"evidence is not satisfied: {evidence_id}",
                    )
                )

        criteria = action.get("acceptance_criteria")
        if not isinstance(criteria, list) or not criteria:
            blockers.append(
                issue(
                    "action_acceptance_links_invalid",
                    f"{field}.acceptance_criteria",
                    "acceptance_criteria must be a non-empty list",
                )
            )
            criteria = []

        for criterion_index, value in enumerate(criteria):
            criterion_field = (
                f"{field}.acceptance_criteria[{criterion_index}]"
            )
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
                or value >= len(acceptance)
            ):
                blockers.append(
                    issue(
                        "action_acceptance_index_invalid",
                        criterion_field,
                        "acceptance criterion index is out of range",
                    )
                )

        required_command = operation in COMMAND_OPERATIONS
        command_argv = action.get("command_argv")
        if command_argv is not None and operation not in COMMAND_OPERATIONS:
            blockers.append(
                issue(
                    "command_argv_not_allowed_for_operation",
                    f"{field}.command_argv",
                    f"command_argv is not allowed for operation: {operation}",
                )
            )

        validate_command_argv(
            command_argv,
            field=f"{field}.command_argv",
            required=required_command,
            blockers=blockers,
        )

        working_directory = normalize_relative_path(
            action.get("working_directory")
        )
        if working_directory is None:
            blockers.append(
                issue(
                    "working_directory_invalid",
                    f"{field}.working_directory",
                    "working_directory must be repository-relative",
                )
            )
        elif working_directory != ".":
            if path_is_private(working_directory):
                blockers.append(
                    issue(
                        "working_directory_private",
                        f"{field}.working_directory",
                        "working_directory points to blocked private context",
                    )
                )
            else:
                allowed_workdir, _ = path_allowed_by_contract(
                    contract,
                    working_directory,
                )
                if not allowed_workdir:
                    blockers.append(
                        issue(
                            "working_directory_outside_contract",
                            f"{field}.working_directory",
                            "working_directory is outside contract scope",
                        )
                    )

        requires_approval = action.get("requires_approval")
        if not isinstance(requires_approval, bool):
            blockers.append(
                issue(
                    "requires_approval_invalid",
                    f"{field}.requires_approval",
                    "requires_approval must be boolean",
                )
            )
        elif (
            operation in SENSITIVE_OPERATIONS
            or operation in contract_approvals
        ) and requires_approval is not True:
            blockers.append(
                issue(
                    "action_approval_flag_missing",
                    f"{field}.requires_approval",
                    f"operation must require approval: {operation}",
                )
            )

        if action.get("destructive") is True:
            state_changing = True

        if (
            operation not in SENSITIVE_OPERATIONS
            and operation not in contract_approvals
            and requires_approval is True
        ):
            warnings.append(
                issue(
                    "non_sensitive_action_requires_approval",
                    f"{field}.requires_approval",
                    f"extra approval declared for non-sensitive operation: {operation}",
                    severity="warning",
                )
            )

    return action_operations, state_changing, all_action_paths


def validate_global_paths(
    proposal: Mapping[str, Any],
    contract: Mapping[str, Any],
    blockers: List[Dict[str, str]],
) -> None:
    paths = proposal.get("affected_paths")
    if not isinstance(paths, list) or not paths:
        blockers.append(
            issue(
                "proposal_paths_invalid",
                "affected_paths",
                "affected_paths must be a non-empty list",
            )
        )
        return

    seen: set[str] = set()
    for index, raw_path in enumerate(paths):
        field = f"affected_paths[{index}]"
        normalized = normalize_relative_path(raw_path)
        if normalized is None or normalized == ".":
            blockers.append(
                issue(
                    "proposal_path_invalid",
                    field,
                    "affected path must be repository-relative",
                )
            )
            continue
        if normalized in seen:
            blockers.append(
                issue(
                    "proposal_path_duplicate",
                    field,
                    f"duplicate affected path: {normalized}",
                )
            )
        seen.add(normalized)

        allowed, reason = path_allowed_by_contract(contract, normalized)
        if not allowed:
            code = (
                "proposal_private_path_blocked"
                if reason == "private"
                else "proposal_path_outside_contract"
            )
            blockers.append(
                issue(
                    code,
                    field,
                    f"affected path is not allowed by contract: {normalized}",
                )
            )


def validate_index_links(
    proposal: Mapping[str, Any],
    contract: Mapping[str, Any],
    blockers: List[Dict[str, str]],
) -> None:
    for field_name, contract_field in (
        ("acceptance_criteria_links", "acceptance_criteria"),
        ("stop_trigger_links", "stop_triggers"),
    ):
        links = proposal.get(field_name)
        values = [
            item
            for item in list_value(contract.get(contract_field))
            if isinstance(item, str)
        ]
        if not isinstance(links, list) or not links:
            blockers.append(
                issue(
                    "proposal_links_invalid",
                    field_name,
                    f"{field_name} must be a non-empty list",
                )
            )
            continue

        seen: set[int] = set()
        for index, value in enumerate(links):
            field = f"{field_name}[{index}]"
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
                or value >= len(values)
            ):
                blockers.append(
                    issue(
                        "proposal_link_index_invalid",
                        field,
                        f"{field_name} index is out of range",
                    )
                )
                continue
            if value in seen:
                blockers.append(
                    issue(
                        "proposal_link_duplicate",
                        field,
                        f"duplicate index: {value}",
                    )
                )
            seen.add(value)


def validate_review(
    proposal: Mapping[str, Any],
    contract: Mapping[str, Any],
    blockers: List[Dict[str, str]],
) -> None:
    review = proposal.get("review")
    contract_review = contract.get("review")
    if not isinstance(review, dict):
        blockers.append(
            issue(
                "proposal_review_invalid",
                "review",
                "review must be an object",
            )
        )
        return

    if review.get("required") is not True:
        blockers.append(
            issue(
                "proposal_review_not_required",
                "review.required",
                "review.required must be true",
            )
        )

    level = review.get("level")
    if level not in REVIEW_ORDER:
        blockers.append(
            issue(
                "proposal_review_level_invalid",
                "review.level",
                f"review level must be one of {sorted(REVIEW_ORDER)}",
            )
        )
    elif isinstance(contract_review, dict):
        contract_level = contract_review.get("level")
        if (
            contract_level in REVIEW_ORDER
            and REVIEW_ORDER[level] < REVIEW_ORDER[contract_level]
        ):
            blockers.append(
                issue(
                    "proposal_review_below_contract",
                    "review.level",
                    "proposal review level is below contract review level",
                )
            )

        proposal_risk = proposal.get("risk_level")
        if (
            proposal_risk == "high"
            and REVIEW_ORDER[level] < REVIEW_ORDER["strict"]
        ):
            blockers.append(
                issue(
                    "high_risk_review_too_low",
                    "review.level",
                    "high risk requires strict or critical review",
                )
            )
        if (
            proposal_risk == "critical"
            and level != "critical"
        ):
            blockers.append(
                issue(
                    "critical_risk_review_too_low",
                    "review.level",
                    "critical risk requires critical review",
                )
            )

    reviewers = review.get("reviewers")
    if not isinstance(reviewers, list) or not reviewers:
        blockers.append(
            issue(
                "proposal_reviewers_invalid",
                "review.reviewers",
                "reviewers must be a non-empty list",
            )
        )


def validate_rollback(
    proposal: Mapping[str, Any],
    state_changing: bool,
    blockers: List[Dict[str, str]],
) -> None:
    rollback = proposal.get("rollback_plan")
    if not isinstance(rollback, dict):
        blockers.append(
            issue(
                "rollback_plan_invalid",
                "rollback_plan",
                "rollback_plan must be an object",
            )
        )
        return

    mode = rollback.get("mode")
    if mode not in {
        "not_required",
        "manual",
        "command_proposal",
        "irreversible",
    }:
        blockers.append(
            issue(
                "rollback_mode_invalid",
                "rollback_plan.mode",
                "rollback mode is invalid",
            )
        )
        return

    if state_changing and mode == "not_required":
        blockers.append(
            issue(
                "rollback_required_for_state_change",
                "rollback_plan.mode",
                "state-changing proposals require rollback planning",
            )
        )

    if mode == "irreversible":
        blockers.append(
            issue(
                "irreversible_rollback_mode_blocked",
                "rollback_plan.mode",
                "irreversible proposals remain blocked in v3.2.2",
            )
        )

    for field_name in (
        "affected_state",
        "pre_action_evidence",
        "success_checks",
        "failure_signals",
        "recovery_steps",
        "irreversible_actions",
    ):
        value = rollback.get(field_name)
        if not isinstance(value, list):
            blockers.append(
                issue(
                    "rollback_list_invalid",
                    f"rollback_plan.{field_name}",
                    f"{field_name} must be a list",
                )
            )
        elif field_name != "irreversible_actions" and not value:
            blockers.append(
                issue(
                    "rollback_list_empty",
                    f"rollback_plan.{field_name}",
                    f"{field_name} must not be empty",
                )
            )

    if not non_empty_text(rollback.get("residual_risk")):
        blockers.append(
            issue(
                "rollback_residual_risk_missing",
                "rollback_plan.residual_risk",
                "residual_risk must be non-empty text",
            )
        )

    if not non_empty_text(rollback.get("approval_owner")):
        blockers.append(
            issue(
                "rollback_approval_owner_missing",
                "rollback_plan.approval_owner",
                "approval_owner must be non-empty text",
            )
        )

    commands = rollback.get("rollback_commands")
    if not isinstance(commands, list):
        blockers.append(
            issue(
                "rollback_commands_invalid",
                "rollback_plan.rollback_commands",
                "rollback_commands must be a list",
            )
        )
        commands = []

    for index, argv in enumerate(commands):
        validate_command_argv(
            argv,
            field=f"rollback_plan.rollback_commands[{index}]",
            required=True,
            blockers=blockers,
        )

    if mode == "not_required" and commands:
        blockers.append(
            issue(
                "rollback_commands_unexpected",
                "rollback_plan.rollback_commands",
                "not_required rollback mode must not include commands",
            )
        )

    if mode == "command_proposal" and not commands:
        blockers.append(
            issue(
                "rollback_commands_required",
                "rollback_plan.rollback_commands",
                "command_proposal rollback mode requires commands",
            )
        )

    authority = rollback.get("authority")
    required_authority = {
        "rollback_is_not_authorized": True,
        "rollback_commands_are_data_only": True,
    }
    if not isinstance(authority, dict):
        blockers.append(
            issue(
                "rollback_authority_invalid",
                "rollback_plan.authority",
                "rollback authority must be an object",
            )
        )
    else:
        for key, expected in required_authority.items():
            if authority.get(key) is not expected:
                blockers.append(
                    issue(
                        "rollback_authority_flag_missing",
                        f"rollback_plan.authority.{key}",
                        f"{key} must be true",
                    )
                )


def validate_authority(
    proposal: Mapping[str, Any],
    blockers: List[Dict[str, str]],
) -> None:
    authority = proposal.get("authority")
    required = {
        "proposal_is_not_permission": True,
        "commands_are_data_only": True,
        "approvals_are_not_consumed": True,
        "evidence_does_not_authorize_action": True,
        "human_review_required": True,
        "mission_state_does_not_authorize_execution": True,
    }

    if not isinstance(authority, dict):
        blockers.append(
            issue(
                "proposal_authority_invalid",
                "authority",
                "authority must be an object",
            )
        )
        return

    for key, expected in required.items():
        if authority.get(key) is not expected:
            blockers.append(
                issue(
                    "proposal_authority_flag_missing",
                    f"authority.{key}",
                    f"{key} must be true",
                )
            )


def validate_proposal(
    repo_root: Path,
    proposal_path: Path,
    proposal: Dict[str, Any],
) -> Dict[str, Any]:
    blockers: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    required_fields = {
        "schema_version",
        "report_type",
        "proposal_id",
        "contract_reference",
        "evidence_bundle_reference",
        "contract_id",
        "bundle_id",
        "mission_id",
        "title",
        "rationale",
        "risk_level",
        "affected_paths",
        "proposed_actions",
        "approval_requirements",
        "rollback_plan",
        "acceptance_criteria_links",
        "stop_trigger_links",
        "review",
        "authority",
    }

    for field in sorted(required_fields - set(proposal)):
        blockers.append(
            issue(
                "required_field_missing",
                field,
                f"required field is missing: {field}",
            )
        )

    if proposal.get("schema_version") != SCHEMA_VERSION:
        blockers.append(
            issue(
                "schema_version_invalid",
                "schema_version",
                f"schema_version must be {SCHEMA_VERSION}",
            )
        )

    if proposal.get("report_type") != PROPOSAL_REPORT_TYPE:
        blockers.append(
            issue(
                "report_type_invalid",
                "report_type",
                f"report_type must be {PROPOSAL_REPORT_TYPE}",
            )
        )

    validate_safe_id(proposal.get("proposal_id"), "proposal_id", blockers)
    validate_safe_id(proposal.get("contract_id"), "contract_id", blockers)
    validate_safe_id(proposal.get("bundle_id"), "bundle_id", blockers)
    validate_safe_id(proposal.get("mission_id"), "mission_id", blockers)

    for text_field in ("title", "rationale"):
        if not non_empty_text(proposal.get(text_field)):
            blockers.append(
                issue(
                    "proposal_text_missing",
                    text_field,
                    f"{text_field} must be non-empty text",
                )
            )

    contract, contract_path, contract_hash = validate_reference(
        repo_root,
        proposal.get("contract_reference"),
        field="contract_reference",
        expected_report_type=CONTRACT_REPORT_TYPE,
        blockers=blockers,
    )

    evidence, evidence_path, evidence_hash = validate_reference(
        repo_root,
        proposal.get("evidence_bundle_reference"),
        field="evidence_bundle_reference",
        expected_report_type=EVIDENCE_REPORT_TYPE,
        blockers=blockers,
    )

    evidence_by_id: Dict[str, Dict[str, Any]] = {}
    action_operations: set[str] = set()
    action_paths: set[str] = set()
    state_changing = False

    if contract is not None:
        if proposal.get("contract_id") != contract.get("contract_id"):
            blockers.append(
                issue(
                    "proposal_contract_id_mismatch",
                    "contract_id",
                    "proposal contract_id does not match referenced contract",
                )
            )
        if proposal.get("mission_id") != contract.get("mission_id"):
            blockers.append(
                issue(
                    "proposal_mission_id_mismatch",
                    "mission_id",
                    "proposal mission_id does not match referenced contract",
                )
            )

    if evidence is not None:
        if proposal.get("bundle_id") != evidence.get("bundle_id"):
            blockers.append(
                issue(
                    "proposal_bundle_id_mismatch",
                    "bundle_id",
                    "proposal bundle_id does not match referenced evidence bundle",
                )
            )

    if contract is not None and evidence is not None:
        evidence_by_id = validate_evidence_bundle(
            repo_root,
            contract,
            evidence,
            proposal.get("contract_reference") or {},
            blockers,
        )

        validate_global_paths(proposal, contract, blockers)
        validate_index_links(proposal, contract, blockers)
        validate_review(proposal, contract, blockers)

        (
            action_operations,
            state_changing,
            action_paths,
        ) = validate_actions(
            proposal,
            contract,
            evidence_by_id,
            blockers,
            warnings,
        )

        proposal_paths = {
            normalized
            for raw_path in list_value(proposal.get("affected_paths"))
            if (normalized := normalize_relative_path(raw_path))
            not in {None, "."}
        }
        if proposal_paths != action_paths:
            blockers.append(
                issue(
                    "affected_path_union_mismatch",
                    "affected_paths",
                    "proposal affected_paths must equal the union of action affected_paths",
                )
            )

        validate_approval_requirements(
            proposal,
            contract,
            action_operations,
            blockers,
        )

    validate_rollback(proposal, state_changing, blockers)
    validate_authority(proposal, blockers)

    proposal_state = "proposed" if not blockers else "blocked"

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": VALIDATION_REPORT_TYPE,
        "generated_at": utc_now(),
        "status": "passed",
        "proposal_state": proposal_state,
        "readiness": (
            "ready_for_approval_review"
            if proposal_state == "proposed"
            else "blocked"
        ),
        "proposal_path": str(proposal_path),
        "proposal_id": proposal.get("proposal_id"),
        "contract_id": proposal.get("contract_id"),
        "bundle_id": proposal.get("bundle_id"),
        "mission_id": proposal.get("mission_id"),
        "references": {
            "contract": {
                "path": contract_path,
                "actual_sha256": contract_hash,
            },
            "evidence_bundle": {
                "path": evidence_path,
                "actual_sha256": evidence_hash,
            },
        },
        "summary": {
            "proposed_action_count": len(
                list_value(proposal.get("proposed_actions"))
            ),
            "affected_path_count": len(
                list_value(proposal.get("affected_paths"))
            ),
            "approval_requirement_count": len(
                list_value(proposal.get("approval_requirements"))
            ),
            "blocker_count": len(blockers),
            "warning_count": len(warnings),
            "state_changing_operation_present": state_changing,
        },
        "blockers": blockers,
        "warnings": warnings,
        "authority": {
            "proposal_is_not_permission": True,
            "ready_for_approval_review_is_not_approval": True,
            "commands_are_data_only": True,
            "approvals_are_not_consumed": True,
            "evidence_does_not_authorize_action": True,
            "human_review_required": True,
        },
        "boundaries": BOUNDARIES,
        "next_recommended_action": (
            "Human reviewer may inspect scope, commands, approvals, risk and rollback."
            if proposal_state == "proposed"
            else "Resolve blockers and revalidate before approval review."
        ),
    }


def print_text(report: Mapping[str, Any]) -> None:
    summary = report.get("summary") or {}
    print("KONOHA SUPERVISED ACTION PROPOSAL VALIDATOR")
    print(f"proposal state: {report.get('proposal_state')}")
    print(f"readiness: {report.get('readiness')}")
    print(f"proposal: {report.get('proposal_id')}")
    print(f"contract: {report.get('contract_id')}")
    print(f"evidence bundle: {report.get('bundle_id')}")
    print(f"actions: {summary.get('proposed_action_count')}")
    print(f"affected paths: {summary.get('affected_path_count')}")
    print(f"blockers: {summary.get('blocker_count')}")
    print(f"warnings: {summary.get('warning_count')}")

    for blocker in report.get("blockers", []):
        print(
            f"BLOCKER [{blocker['code']}] "
            f"{blocker['field']}: {blocker['message']}"
        )

    for warning in report.get("warnings", []):
        print(
            f"WARNING [{warning['code']}] "
            f"{warning['field']}: {warning['message']}"
        )

    print(f"next action: {report.get('next_recommended_action')}")
    print("Command execution: blocked")
    print("Approval consumption: blocked")
    print("Git operations: blocked")
    print("Model invocation: blocked")
    print("Network access: blocked")
    print("Private context access: blocked")
    print("Rollback execution: blocked")
    print("Result is evidence only.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a Konoha supervised action proposal."
    )
    parser.add_argument("--proposal", required=True, help="Proposal JSON.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument(
        "--output",
        default=None,
        help="Optional validation report under <repo-root>/sandbox.",
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
    args = build_parser().parse_args(argv)

    try:
        repo_root = Path(args.repo_root).resolve()
        proposal_path = Path(args.proposal)
        if not proposal_path.is_absolute():
            proposal_path = repo_root / proposal_path
        proposal_path = proposal_path.resolve()

        if not is_relative_to(proposal_path, repo_root):
            raise ProposalValidationError(
                "proposal path must stay under the repository root"
            )

        relative_proposal = proposal_path.relative_to(repo_root).as_posix()
        if path_is_private(relative_proposal):
            raise ProposalValidationError(
                "proposal path must not read blocked private context"
            )

        proposal = read_json_object(proposal_path, "action proposal")
        report = validate_proposal(repo_root, proposal_path, proposal)

        output = resolve_output(repo_root, args.output)
        if output is not None:
            write_json(output, report, force=args.force)

        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_text(report)

        return 0 if report["proposal_state"] == "proposed" else 1

    except ProposalValidationError as exc:
        error_report = {
            "schema_version": SCHEMA_VERSION,
            "report_type": VALIDATION_REPORT_TYPE,
            "generated_at": utc_now(),
            "status": "failed",
            "proposal_state": "blocked",
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
            print(f"SUPERVISED ACTION PROPOSAL VALIDATION FAILED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
