#!/usr/bin/env python3
"""Validate a Konoha supervised task evidence bundle.

The validator reads a v3.2.0 supervised task contract and local evidence
references. It verifies deterministic structure, coverage, paths, and SHA-256
digests. It does not collect evidence, execute commands, invoke models, mutate
Git, access private context, or authorize mission progress.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

SCHEMA_VERSION = "1.0.0"
BUNDLE_REPORT_TYPE = "supervised_task_evidence_bundle"
VALIDATION_REPORT_TYPE = "supervised_task_evidence_validation_report"
CONTRACT_REPORT_TYPE = "supervised_task_contract"

SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

EVIDENCE_STATUSES = {"satisfied", "missing", "contradicted", "unresolved"}
SOURCE_TYPES = {"file", "report", "command_result", "observation"}
CLAIM_STATUSES = {"supported", "unsupported", "contradicted"}
FINDING_LEVELS = {"info", "warning", "error"}

PRIVATE_PREFIXES = (
    ".env",
    "alliance/kirigakure",
    "alliance/private-library",
    "memory/local",
    "vault",
)

BOUNDARIES = {
    "automatic_evidence_collection": "blocked",
    "command_execution": "blocked",
    "filesystem_mutation": "blocked_except_explicit_report_output_under_sandbox",
    "git_operations": "blocked",
    "model_invocation": "blocked",
    "network_access": "blocked",
    "private_context_access": "blocked",
    "repository_apply": "blocked",
    "mission_closure": "blocked",
}


class EvidenceValidationError(RuntimeError):
    """Invalid invocation, unsafe path, or unreadable JSON."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json_object(path: Path, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvidenceValidationError(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EvidenceValidationError(
            f"{label} JSON invalid at line {exc.lineno}, column {exc.colno}"
        ) from exc

    if not isinstance(payload, dict):
        raise EvidenceValidationError(f"{label} JSON must be an object")
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

    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None

    return value


def path_is_private(relative_path: str) -> bool:
    lowered = relative_path.lower()
    for prefix in PRIVATE_PREFIXES:
        normalized = prefix.lower()
        if lowered == normalized or lowered.startswith(normalized + "/"):
            return True
    return False


def resolve_repo_path(
    repo_root: Path,
    raw_path: Any,
    *,
    label: str,
    allow_missing: bool = False,
) -> Tuple[Optional[str], Optional[Path], Optional[str]]:
    relative = normalize_relative_path(raw_path)
    if relative is None:
        return None, None, f"{label} must be a repository-relative path"

    if path_is_private(relative):
        return (
            relative,
            None,
            f"{label} points to blocked private context: {relative}",
        )

    resolved = (repo_root / relative).resolve()
    if not is_relative_to(resolved, repo_root):
        return relative, None, f"{label} escapes the repository root"

    if not allow_missing and not resolved.is_file():
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
        raise EvidenceValidationError(
            "validation output must stay under <repo-root>/sandbox"
        )
    return output


def write_json(path: Path, payload: Mapping[str, Any], *, force: bool) -> None:
    if path.exists() and not force:
        raise EvidenceValidationError(
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


def validate_authority(
    authority: Any,
    blockers: List[Dict[str, str]],
) -> None:
    required = {
        "bundle_is_evidence_only": True,
        "evidence_does_not_authorize_execution": True,
        "hashes_do_not_prove_truth": True,
        "human_review_required": True,
    }

    if not isinstance(authority, dict):
        blockers.append(
            issue(
                "authority_invalid",
                "authority",
                "authority must be an object",
            )
        )
        return

    for key, expected in required.items():
        if authority.get(key) is not expected:
            blockers.append(
                issue(
                    "authority_flag_missing",
                    f"authority.{key}",
                    f"authority.{key} must be true",
                )
            )


def contract_operations(contract: Mapping[str, Any]) -> set[str]:
    operations = contract.get("operations")
    if not isinstance(operations, dict):
        return set()

    allowed = operations.get("allowed")
    blocked = operations.get("blocked")
    return {
        item
        for item in list_value(allowed) + list_value(blocked)
        if isinstance(item, str)
    }


def contract_lists(
    contract: Mapping[str, Any],
) -> Tuple[List[str], List[str]]:
    requirements = [
        item
        for item in list_value(contract.get("evidence_requirements"))
        if isinstance(item, str)
    ]
    criteria = [
        item
        for item in list_value(contract.get("acceptance_criteria"))
        if isinstance(item, str)
    ]
    return requirements, criteria


def validate_contract_reference(
    repo_root: Path,
    bundle: Mapping[str, Any],
    blockers: List[Dict[str, str]],
) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    reference = bundle.get("contract_reference")
    if not isinstance(reference, dict):
        blockers.append(
            issue(
                "contract_reference_invalid",
                "contract_reference",
                "contract_reference must be an object",
            )
        )
        return None, None, None

    relative, resolved, path_error = resolve_repo_path(
        repo_root,
        reference.get("path"),
        label="contract_reference.path",
    )
    if path_error:
        blockers.append(
            issue(
                "contract_path_invalid",
                "contract_reference.path",
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
                "contract_sha256_invalid",
                "contract_reference.sha256",
                "contract_reference.sha256 must be 64 lowercase hex characters",
            )
        )
        return None, relative, None

    assert resolved is not None
    actual_hash = sha256_file(resolved)
    if actual_hash != expected_hash:
        blockers.append(
            issue(
                "contract_sha256_mismatch",
                "contract_reference.sha256",
                f"contract hash mismatch for {relative}",
            )
        )

    try:
        contract = read_json_object(resolved, "contract")
    except EvidenceValidationError as exc:
        blockers.append(
            issue(
                "contract_unreadable",
                "contract_reference.path",
                str(exc),
            )
        )
        return None, relative, actual_hash

    if contract.get("report_type") != CONTRACT_REPORT_TYPE:
        blockers.append(
            issue(
                "contract_report_type_invalid",
                "contract_reference.path",
                f"referenced file must be {CONTRACT_REPORT_TYPE}",
            )
        )

    if contract.get("schema_version") != SCHEMA_VERSION:
        blockers.append(
            issue(
                "contract_schema_version_invalid",
                "contract_reference.path",
                f"referenced contract schema_version must be {SCHEMA_VERSION}",
            )
        )

    return contract, relative, actual_hash


def validate_evidence_items(
    repo_root: Path,
    bundle: Mapping[str, Any],
    contract: Mapping[str, Any],
    blockers: List[Dict[str, str]],
    warnings: List[Dict[str, str]],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[int, Dict[str, Any]]]:
    requirements, criteria = contract_lists(contract)
    declared_operations = contract_operations(contract)

    raw_items = bundle.get("evidence_items")
    if not isinstance(raw_items, list) or not raw_items:
        blockers.append(
            issue(
                "evidence_items_invalid",
                "evidence_items",
                "evidence_items must be a non-empty list",
            )
        )
        raw_items = []

    by_id: Dict[str, Dict[str, Any]] = {}
    by_requirement: Dict[int, Dict[str, Any]] = {}
    source_ids: set[str] = set()

    for index, raw_item in enumerate(raw_items):
        field = f"evidence_items[{index}]"
        if not isinstance(raw_item, dict):
            blockers.append(
                issue(
                    "evidence_item_not_object",
                    field,
                    "evidence item must be an object",
                )
            )
            continue

        evidence_id = validate_safe_id(
            raw_item.get("evidence_id"),
            f"{field}.evidence_id",
            blockers,
        )
        if evidence_id is not None:
            if evidence_id in by_id:
                blockers.append(
                    issue(
                        "evidence_id_duplicate",
                        f"{field}.evidence_id",
                        f"duplicate evidence_id: {evidence_id}",
                    )
                )
            else:
                by_id[evidence_id] = raw_item

        requirement_index = raw_item.get("requirement_index")
        if not isinstance(requirement_index, int) or isinstance(
            requirement_index, bool
        ):
            blockers.append(
                issue(
                    "requirement_index_invalid",
                    f"{field}.requirement_index",
                    "requirement_index must be an integer",
                )
            )
            requirement_index = None
        elif requirement_index < 0 or requirement_index >= len(requirements):
            blockers.append(
                issue(
                    "requirement_index_out_of_range",
                    f"{field}.requirement_index",
                    f"requirement_index must be within 0..{max(len(requirements)-1, 0)}",
                )
            )
        else:
            if requirement_index in by_requirement:
                blockers.append(
                    issue(
                        "requirement_index_duplicate",
                        f"{field}.requirement_index",
                        f"duplicate evidence mapping for requirement {requirement_index}",
                    )
                )
            else:
                by_requirement[requirement_index] = raw_item

            if raw_item.get("requirement_text") != requirements[
                requirement_index
            ]:
                blockers.append(
                    issue(
                        "requirement_text_mismatch",
                        f"{field}.requirement_text",
                        "requirement_text does not match the referenced contract",
                    )
                )

        status = raw_item.get("status")
        if status not in EVIDENCE_STATUSES:
            blockers.append(
                issue(
                    "evidence_status_invalid",
                    f"{field}.status",
                    f"status must be one of {sorted(EVIDENCE_STATUSES)}",
                )
            )

        if not non_empty_text(raw_item.get("summary")):
            blockers.append(
                issue(
                    "evidence_summary_missing",
                    f"{field}.summary",
                    "summary must be non-empty text",
                )
            )

        related_criteria = raw_item.get("related_acceptance_criteria")
        if not isinstance(related_criteria, list):
            blockers.append(
                issue(
                    "related_acceptance_criteria_invalid",
                    f"{field}.related_acceptance_criteria",
                    "related_acceptance_criteria must be a list",
                )
            )
            related_criteria = []

        seen_criteria: set[int] = set()
        for criterion_position, criterion_index in enumerate(related_criteria):
            criterion_field = (
                f"{field}.related_acceptance_criteria[{criterion_position}]"
            )
            if not isinstance(criterion_index, int) or isinstance(
                criterion_index, bool
            ):
                blockers.append(
                    issue(
                        "acceptance_index_invalid",
                        criterion_field,
                        "acceptance criterion index must be an integer",
                    )
                )
                continue
            if criterion_index < 0 or criterion_index >= len(criteria):
                blockers.append(
                    issue(
                        "acceptance_index_out_of_range",
                        criterion_field,
                        f"acceptance criterion index must be within 0..{max(len(criteria)-1, 0)}",
                    )
                )
                continue
            if criterion_index in seen_criteria:
                blockers.append(
                    issue(
                        "acceptance_index_duplicate",
                        criterion_field,
                        f"duplicate acceptance criterion index: {criterion_index}",
                    )
                )
            seen_criteria.add(criterion_index)

        related_operations = raw_item.get("related_operations")
        if not isinstance(related_operations, list):
            blockers.append(
                issue(
                    "related_operations_invalid",
                    f"{field}.related_operations",
                    "related_operations must be a list",
                )
            )
            related_operations = []

        seen_operations: set[str] = set()
        for operation_position, operation in enumerate(related_operations):
            operation_field = (
                f"{field}.related_operations[{operation_position}]"
            )
            if not isinstance(operation, str) or not operation:
                blockers.append(
                    issue(
                        "related_operation_invalid",
                        operation_field,
                        "related operation must be non-empty text",
                    )
                )
                continue
            if operation not in declared_operations:
                blockers.append(
                    issue(
                        "related_operation_not_in_contract",
                        operation_field,
                        f"operation is not declared by the contract: {operation}",
                    )
                )
            if operation in seen_operations:
                blockers.append(
                    issue(
                        "related_operation_duplicate",
                        operation_field,
                        f"duplicate related operation: {operation}",
                    )
                )
            seen_operations.add(operation)

        raw_sources = raw_item.get("source_refs")
        if not isinstance(raw_sources, list):
            blockers.append(
                issue(
                    "source_refs_invalid",
                    f"{field}.source_refs",
                    "source_refs must be a list",
                )
            )
            raw_sources = []

        if status in {"satisfied", "contradicted"} and not raw_sources:
            blockers.append(
                issue(
                    "evidence_source_required",
                    f"{field}.source_refs",
                    f"{status} evidence requires at least one source",
                )
            )

        if status == "missing" and raw_sources:
            blockers.append(
                issue(
                    "missing_evidence_has_sources",
                    f"{field}.source_refs",
                    "missing evidence must not declare source_refs",
                )
            )

        for source_position, raw_source in enumerate(raw_sources):
            source_field = f"{field}.source_refs[{source_position}]"
            if not isinstance(raw_source, dict):
                blockers.append(
                    issue(
                        "source_ref_not_object",
                        source_field,
                        "source reference must be an object",
                    )
                )
                continue

            source_id = validate_safe_id(
                raw_source.get("source_id"),
                f"{source_field}.source_id",
                blockers,
            )
            if source_id is not None:
                if source_id in source_ids:
                    blockers.append(
                        issue(
                            "source_id_duplicate",
                            f"{source_field}.source_id",
                            f"duplicate source_id: {source_id}",
                        )
                    )
                source_ids.add(source_id)

            source_type = raw_source.get("source_type")
            if source_type not in SOURCE_TYPES:
                blockers.append(
                    issue(
                        "source_type_invalid",
                        f"{source_field}.source_type",
                        f"source_type must be one of {sorted(SOURCE_TYPES)}",
                    )
                )

            relative, resolved, source_error = resolve_repo_path(
                repo_root,
                raw_source.get("path"),
                label=f"{source_field}.path",
            )
            if source_error:
                blockers.append(
                    issue(
                        "source_path_invalid",
                        f"{source_field}.path",
                        source_error,
                    )
                )
                continue

            expected_hash = raw_source.get("sha256")
            if not isinstance(expected_hash, str) or not SHA256_RE.fullmatch(
                expected_hash
            ):
                blockers.append(
                    issue(
                        "source_sha256_invalid",
                        f"{source_field}.sha256",
                        "source sha256 must be 64 lowercase hex characters",
                    )
                )
                continue

            assert resolved is not None
            actual_hash = sha256_file(resolved)
            if actual_hash != expected_hash:
                blockers.append(
                    issue(
                        "source_sha256_mismatch",
                        f"{source_field}.sha256",
                        f"source hash mismatch for {relative}",
                    )
                )

        if (
            status == "satisfied"
            and not related_criteria
            and not related_operations
        ):
            warnings.append(
                issue(
                    "satisfied_evidence_without_links",
                    field,
                    "satisfied evidence has no acceptance-criterion or operation links",
                    severity="warning",
                )
            )

    expected_indices = set(range(len(requirements)))
    actual_indices = set(by_requirement)

    for missing_index in sorted(expected_indices - actual_indices):
        blockers.append(
            issue(
                "requirement_evidence_missing",
                "evidence_items",
                f"no evidence item maps requirement {missing_index}",
            )
        )

    for extra_index in sorted(actual_indices - expected_indices):
        blockers.append(
            issue(
                "requirement_evidence_extra",
                "evidence_items",
                f"unexpected requirement mapping: {extra_index}",
            )
        )

    return by_id, by_requirement


def validate_claims(
    claims: Any,
    evidence_by_id: Mapping[str, Mapping[str, Any]],
    blockers: List[Dict[str, str]],
) -> None:
    if not isinstance(claims, list):
        blockers.append(
            issue(
                "claims_invalid",
                "claims",
                "claims must be a list",
            )
        )
        return

    seen_ids: set[str] = set()
    for index, raw_claim in enumerate(claims):
        field = f"claims[{index}]"
        if not isinstance(raw_claim, dict):
            blockers.append(
                issue(
                    "claim_not_object",
                    field,
                    "claim must be an object",
                )
            )
            continue

        claim_id = validate_safe_id(
            raw_claim.get("claim_id"),
            f"{field}.claim_id",
            blockers,
        )
        if claim_id is not None:
            if claim_id in seen_ids:
                blockers.append(
                    issue(
                        "claim_id_duplicate",
                        f"{field}.claim_id",
                        f"duplicate claim_id: {claim_id}",
                    )
                )
            seen_ids.add(claim_id)

        if not non_empty_text(raw_claim.get("statement")):
            blockers.append(
                issue(
                    "claim_statement_missing",
                    f"{field}.statement",
                    "claim statement must be non-empty text",
                )
            )

        status = raw_claim.get("status")
        if status not in CLAIM_STATUSES:
            blockers.append(
                issue(
                    "claim_status_invalid",
                    f"{field}.status",
                    f"claim status must be one of {sorted(CLAIM_STATUSES)}",
                )
            )

        evidence_ids = raw_claim.get("evidence_ids")
        if not isinstance(evidence_ids, list):
            blockers.append(
                issue(
                    "claim_evidence_ids_invalid",
                    f"{field}.evidence_ids",
                    "claim evidence_ids must be a list",
                )
            )
            evidence_ids = []

        referenced_statuses: List[str] = []
        for evidence_position, evidence_id in enumerate(evidence_ids):
            evidence_field = f"{field}.evidence_ids[{evidence_position}]"
            if evidence_id not in evidence_by_id:
                blockers.append(
                    issue(
                        "claim_evidence_unknown",
                        evidence_field,
                        f"unknown evidence_id: {evidence_id}",
                    )
                )
                continue
            referenced_statuses.append(
                str(evidence_by_id[evidence_id].get("status"))
            )

        if status == "supported":
            if not evidence_ids:
                blockers.append(
                    issue(
                        "supported_claim_without_evidence",
                        f"{field}.evidence_ids",
                        "supported claim requires evidence",
                    )
                )
            elif any(item != "satisfied" for item in referenced_statuses):
                blockers.append(
                    issue(
                        "supported_claim_uses_non_satisfied_evidence",
                        f"{field}.evidence_ids",
                        "supported claim may reference only satisfied evidence",
                    )
                )

        if status == "contradicted":
            if "contradicted" not in referenced_statuses:
                blockers.append(
                    issue(
                        "contradicted_claim_without_contradiction",
                        f"{field}.evidence_ids",
                        "contradicted claim requires contradicted evidence",
                    )
                )


def validate_findings(
    findings: Any,
    evidence_by_id: Mapping[str, Mapping[str, Any]],
    blockers: List[Dict[str, str]],
) -> None:
    if not isinstance(findings, list):
        blockers.append(
            issue(
                "findings_invalid",
                "findings",
                "findings must be a list",
            )
        )
        return

    seen_ids: set[str] = set()
    for index, raw_finding in enumerate(findings):
        field = f"findings[{index}]"
        if not isinstance(raw_finding, dict):
            blockers.append(
                issue(
                    "finding_not_object",
                    field,
                    "finding must be an object",
                )
            )
            continue

        finding_id = validate_safe_id(
            raw_finding.get("finding_id"),
            f"{field}.finding_id",
            blockers,
        )
        if finding_id is not None:
            if finding_id in seen_ids:
                blockers.append(
                    issue(
                        "finding_id_duplicate",
                        f"{field}.finding_id",
                        f"duplicate finding_id: {finding_id}",
                    )
                )
            seen_ids.add(finding_id)

        if raw_finding.get("level") not in FINDING_LEVELS:
            blockers.append(
                issue(
                    "finding_level_invalid",
                    f"{field}.level",
                    f"finding level must be one of {sorted(FINDING_LEVELS)}",
                )
            )

        if not non_empty_text(raw_finding.get("statement")):
            blockers.append(
                issue(
                    "finding_statement_missing",
                    f"{field}.statement",
                    "finding statement must be non-empty text",
                )
            )

        evidence_ids = raw_finding.get("evidence_ids")
        if not isinstance(evidence_ids, list) or not evidence_ids:
            blockers.append(
                issue(
                    "finding_evidence_ids_invalid",
                    f"{field}.evidence_ids",
                    "finding evidence_ids must be a non-empty list",
                )
            )
            evidence_ids = []

        for evidence_position, evidence_id in enumerate(evidence_ids):
            if evidence_id not in evidence_by_id:
                blockers.append(
                    issue(
                        "finding_evidence_unknown",
                        f"{field}.evidence_ids[{evidence_position}]",
                        f"unknown evidence_id: {evidence_id}",
                    )
                )


def validate_unresolved(
    unresolved: Any,
    requirement_count: int,
    evidence_state: str,
    blockers: List[Dict[str, str]],
) -> None:
    if not isinstance(unresolved, list):
        blockers.append(
            issue(
                "unresolved_invalid",
                "unresolved",
                "unresolved must be a list",
            )
        )
        return

    if evidence_state == "complete" and unresolved:
        blockers.append(
            issue(
                "complete_bundle_has_unresolved_items",
                "unresolved",
                "complete evidence bundle must not contain unresolved items",
            )
        )

    if evidence_state == "incomplete" and not unresolved:
        blockers.append(
            issue(
                "incomplete_bundle_missing_unresolved_items",
                "unresolved",
                "incomplete evidence bundle must explain unresolved or missing evidence",
            )
        )

    seen_ids: set[str] = set()
    for index, raw_item in enumerate(unresolved):
        field = f"unresolved[{index}]"
        if not isinstance(raw_item, dict):
            blockers.append(
                issue(
                    "unresolved_item_not_object",
                    field,
                    "unresolved item must be an object",
                )
            )
            continue

        unresolved_id = validate_safe_id(
            raw_item.get("unresolved_id"),
            f"{field}.unresolved_id",
            blockers,
        )
        if unresolved_id is not None:
            if unresolved_id in seen_ids:
                blockers.append(
                    issue(
                        "unresolved_id_duplicate",
                        f"{field}.unresolved_id",
                        f"duplicate unresolved_id: {unresolved_id}",
                    )
                )
            seen_ids.add(unresolved_id)

        for text_field in ("statement", "reason"):
            if not non_empty_text(raw_item.get(text_field)):
                blockers.append(
                    issue(
                        "unresolved_text_missing",
                        f"{field}.{text_field}",
                        f"{text_field} must be non-empty text",
                    )
                )

        indices = raw_item.get("requirement_indices")
        if not isinstance(indices, list) or not indices:
            blockers.append(
                issue(
                    "unresolved_requirement_indices_invalid",
                    f"{field}.requirement_indices",
                    "requirement_indices must be a non-empty list",
                )
            )
            indices = []

        for position, requirement_index in enumerate(indices):
            item_field = f"{field}.requirement_indices[{position}]"
            if not isinstance(requirement_index, int) or isinstance(
                requirement_index, bool
            ):
                blockers.append(
                    issue(
                        "unresolved_requirement_index_invalid",
                        item_field,
                        "requirement index must be an integer",
                    )
                )
                continue
            if requirement_index < 0 or requirement_index >= requirement_count:
                blockers.append(
                    issue(
                        "unresolved_requirement_index_out_of_range",
                        item_field,
                        f"requirement index must be within 0..{max(requirement_count-1, 0)}",
                    )
                )


def determine_evidence_state(
    by_requirement: Mapping[int, Mapping[str, Any]],
    requirement_count: int,
) -> str:
    statuses = [
        by_requirement[index].get("status")
        for index in range(requirement_count)
        if index in by_requirement
    ]

    if "contradicted" in statuses:
        return "contradicted"

    if len(statuses) != requirement_count:
        return "incomplete"

    if any(status in {"missing", "unresolved"} for status in statuses):
        return "incomplete"

    if statuses and all(status == "satisfied" for status in statuses):
        return "complete"

    return "incomplete"


def validate_bundle(
    repo_root: Path,
    bundle_path: Path,
    bundle: Dict[str, Any],
) -> Dict[str, Any]:
    blockers: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    required_fields = {
        "schema_version",
        "report_type",
        "bundle_id",
        "contract_reference",
        "contract_id",
        "mission_id",
        "evidence_items",
        "claims",
        "findings",
        "unresolved",
        "authority",
    }
    for field in sorted(required_fields - set(bundle)):
        blockers.append(
            issue(
                "required_field_missing",
                field,
                f"required field is missing: {field}",
            )
        )

    if bundle.get("schema_version") != SCHEMA_VERSION:
        blockers.append(
            issue(
                "schema_version_invalid",
                "schema_version",
                f"schema_version must be {SCHEMA_VERSION}",
            )
        )

    if bundle.get("report_type") != BUNDLE_REPORT_TYPE:
        blockers.append(
            issue(
                "report_type_invalid",
                "report_type",
                f"report_type must be {BUNDLE_REPORT_TYPE}",
            )
        )

    validate_safe_id(bundle.get("bundle_id"), "bundle_id", blockers)
    validate_safe_id(bundle.get("contract_id"), "contract_id", blockers)
    validate_safe_id(bundle.get("mission_id"), "mission_id", blockers)
    validate_authority(bundle.get("authority"), blockers)

    contract, contract_path, contract_actual_sha256 = (
        validate_contract_reference(repo_root, bundle, blockers)
    )

    requirement_count = 0
    acceptance_count = 0
    evidence_by_id: Dict[str, Dict[str, Any]] = {}
    by_requirement: Dict[int, Dict[str, Any]] = {}

    if contract is not None:
        if bundle.get("contract_id") != contract.get("contract_id"):
            blockers.append(
                issue(
                    "contract_id_mismatch",
                    "contract_id",
                    "bundle contract_id does not match referenced contract",
                )
            )

        if bundle.get("mission_id") != contract.get("mission_id"):
            blockers.append(
                issue(
                    "mission_id_mismatch",
                    "mission_id",
                    "bundle mission_id does not match referenced contract",
                )
            )

        requirements, criteria = contract_lists(contract)
        requirement_count = len(requirements)
        acceptance_count = len(criteria)

        evidence_by_id, by_requirement = validate_evidence_items(
            repo_root,
            bundle,
            contract,
            blockers,
            warnings,
        )
    else:
        if bundle.get("evidence_items") not in (None, []):
            warnings.append(
                issue(
                    "evidence_items_not_fully_validated",
                    "evidence_items",
                    "evidence items could not be cross-checked without a valid contract",
                    severity="warning",
                )
            )

    evidence_state = determine_evidence_state(
        by_requirement,
        requirement_count,
    )

    validate_claims(bundle.get("claims"), evidence_by_id, blockers)
    validate_findings(bundle.get("findings"), evidence_by_id, blockers)
    validate_unresolved(
        bundle.get("unresolved"),
        requirement_count,
        evidence_state,
        blockers,
    )

    readiness = (
        "ready_for_human_review"
        if not blockers and evidence_state == "complete"
        else "blocked"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": VALIDATION_REPORT_TYPE,
        "generated_at": utc_now(),
        "status": "passed",
        "readiness": readiness,
        "evidence_state": evidence_state,
        "bundle_path": str(bundle_path),
        "bundle_id": bundle.get("bundle_id"),
        "contract_id": bundle.get("contract_id"),
        "mission_id": bundle.get("mission_id"),
        "contract_reference": {
            "path": contract_path,
            "actual_sha256": contract_actual_sha256,
        },
        "summary": {
            "requirement_count": requirement_count,
            "mapped_requirement_count": len(by_requirement),
            "acceptance_criteria_count": acceptance_count,
            "evidence_item_count": len(evidence_by_id),
            "claim_count": len(list_value(bundle.get("claims"))),
            "finding_count": len(list_value(bundle.get("findings"))),
            "unresolved_count": len(list_value(bundle.get("unresolved"))),
            "blocker_count": len(blockers),
            "warning_count": len(warnings),
        },
        "blockers": blockers,
        "warnings": warnings,
        "authority": {
            "bundle_is_evidence_only": True,
            "ready_for_human_review_is_not_permission": True,
            "evidence_state_does_not_authorize_execution": True,
            "hashes_verify_bytes_not_truth": True,
            "human_review_required": True,
        },
        "boundaries": BOUNDARIES,
        "next_recommended_action": (
            "Human reviewer must inspect source meaning and contract satisfaction."
            if readiness == "ready_for_human_review"
            else "Resolve blockers and revalidate before human evidence review."
        ),
    }


def print_text(report: Mapping[str, Any]) -> None:
    summary = report.get("summary") or {}
    print("KONOHA SUPERVISED TASK EVIDENCE VALIDATOR")
    print(f"readiness: {report.get('readiness')}")
    print(f"evidence state: {report.get('evidence_state')}")
    print(f"bundle: {report.get('bundle_id')}")
    print(f"contract: {report.get('contract_id')}")
    print(
        "requirements: "
        f"{summary.get('mapped_requirement_count')}/"
        f"{summary.get('requirement_count')}"
    )
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
    print("Automatic evidence collection: blocked")
    print("Command execution: blocked")
    print("Git operations: blocked")
    print("Model invocation: blocked")
    print("Network access: blocked")
    print("Private context access: blocked")
    print("Result is evidence only.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a Konoha supervised task evidence bundle."
    )
    parser.add_argument("--bundle", required=True, help="Evidence bundle JSON.")
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
        bundle_path = Path(args.bundle)
        if not bundle_path.is_absolute():
            bundle_path = repo_root / bundle_path
        bundle_path = bundle_path.resolve()

        if not is_relative_to(bundle_path, repo_root):
            raise EvidenceValidationError(
                "bundle path must stay under the repository root"
            )

        relative_bundle = bundle_path.relative_to(repo_root).as_posix()
        if path_is_private(relative_bundle):
            raise EvidenceValidationError(
                "bundle path must not read blocked private context"
            )

        bundle = read_json_object(bundle_path, "evidence bundle")
        report = validate_bundle(repo_root, bundle_path, bundle)

        output = resolve_output(repo_root, args.output)
        if output is not None:
            write_json(output, report, force=args.force)

        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_text(report)

        return 0 if report["readiness"] == "ready_for_human_review" else 1

    except EvidenceValidationError as exc:
        error_report = {
            "schema_version": SCHEMA_VERSION,
            "report_type": VALIDATION_REPORT_TYPE,
            "generated_at": utc_now(),
            "status": "failed",
            "readiness": "blocked",
            "evidence_state": "unavailable",
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
            print(f"SUPERVISED TASK EVIDENCE VALIDATION FAILED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
