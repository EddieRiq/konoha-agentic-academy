"""Mission Charter construction and exact approval phrases."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from . import authority

SCHEMA_VERSION = "1.0.0"
CHARTER_SCHEMA_VERSION_1_1 = "1.1.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _dedupe(values: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        value = value.strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def charter_id(intent: Dict[str, Any]) -> str:
    material = "|".join(
        [
            str(intent.get("objective", "")),
            *[str(item) for item in intent.get("targets", [])],
            *[str(item) for item in intent.get("constraints", [])],
        ]
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:10]
    return f"charter-{digest}"


def approval_phrase(charter: Dict[str, Any]) -> str:
    suffix = str(charter["charter_id"]).split("-", 1)[-1].upper()
    return f"APROBAR CHARTER-{suffix}"


def rejection_phrase(charter: Dict[str, Any]) -> str:
    suffix = str(charter["charter_id"]).split("-", 1)[-1].upper()
    return f"RECHAZAR CHARTER-{suffix}"


def proposed_skills(intent: Dict[str, Any]) -> List[str]:
    intent_type = intent.get("intent_type")
    constraints = set(intent.get("constraints", []))
    outputs = set(intent.get("requested_outputs", []))
    skills: List[str] = []

    if intent_type in {"inspect_and_review", "validate_project", "implement_change"}:
        skills.append("inspect_public_repo")
    if (
        intent_type in {"validate_project", "implement_change"}
        or "test_evidence" in outputs
    ):
        skills.append("run_deterministic_tests")
    if "local model only" in constraints:
        skills.append("invoke_local_model")
    if "patch_proposal" in outputs:
        skills.extend(["prepare_patch", "run_self_review"])
    if "memory_summary" in outputs:
        skills.append("write_private_memory")

    skills.append("close_mission")
    return _dedupe(skills)


def build_charter(intent: Dict[str, Any], actor: str) -> Dict[str, Any]:
    charter = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "conversational_mission_charter",
        "charter_id": charter_id(intent),
        "created_at": utc_now(),
        "actor": actor,
        "objective": intent["objective"],
        "scope": {
            "targets": list(intent["targets"]),
            "requested_outputs": list(intent["requested_outputs"]),
        },
        "out_of_scope": [
            "autonomous background execution",
            "arbitrary shell execution",
            "unapproved filesystem mutation",
            "unapproved Git writes",
            "unapproved network access",
        ],
        "constraints": list(intent["constraints"]),
        "risk_level": intent["risk_level"],
        "proposed_skills": proposed_skills(intent),
        "approval_gates": [
            "charter approval",
            "per-action approval before execution",
            "separate patch approval before mutation",
            "separate Git approvals for stage, commit and push",
        ],
        "success_criteria": [
            "requested outputs are produced",
            "evidence is retained",
            "model output is deterministically reviewed",
            "no action exceeds its approved scope",
            "Teachback and human closure remain required",
        ],
        "state": "proposed",
        "authority": {
            "charter_is_not_permission": True,
            "skill_proposals_are_not_permission": True,
            "memory_does_not_authorize_action": True,
        },
    }
    charter["approval_phrase"] = approval_phrase(charter)
    charter["rejection_phrase"] = rejection_phrase(charter)
    return charter


def real_proposed_skills(intent: Dict[str, Any]) -> List[str]:
    """1.1 proposed_skills: exclusively real tools.hokage_orchestrator.
    skill_runtime.SKILLS ids, never a cosmetic legacy name. Every initial
    skill a mission may execute must be explicitly proposed here.

    Driven strictly by requested output / intent_type, never by a provider
    constraint:

    - inspection/audit scope (inspect_and_review, validate_project,
      implement_change) -> inspect_python_runtime, inspect_git_status.
    - "findings" or "patch_proposal" requested, or an audit/review intent
      -> run_deterministic_audit_checks + invoke_local_model_audit
      (ollama-only, per skill_runtime's own provider table - never
      triggered by a "local model only" constraint, which governs provider
      choice, not which skill to run).

    run_technical_plan is deliberately never proposed from intent here:
    intent.py's requested_outputs vocabulary (findings, patch_proposal,
    test_evidence, usage_report, memory_summary, mission_result) has no
    token that actually means "a technical plan is requested", and
    intent.py is out of this block's authorized file scope to extend. It
    stays a real, registered, callable skill; wiring it into automatic
    Charter proposal is deferred until intent.py grows a proper token."""

    intent_type = intent.get("intent_type")
    outputs = set(intent.get("requested_outputs", []))
    skills: List[str] = []

    if intent_type in {"inspect_and_review", "validate_project", "implement_change"}:
        skills.append("inspect_python_runtime")
        skills.append("inspect_git_status")

    audit_requested = (
        "findings" in outputs
        or "patch_proposal" in outputs
        or intent_type in {"inspect_and_review", "validate_project"}
    )
    if audit_requested:
        skills.append("run_deterministic_audit_checks")
        skills.append("invoke_local_model_audit")

    return _dedupe(skills)


def real_allowed_followup_skills(intent: Dict[str, Any]) -> List[str]:
    """1.1 allowed_followup_skills: real skill ids only, reachable solely
    after their prerequisite initial skills complete and a separate,
    explicit patch approval is granted - never proposed as initial."""

    intent_type = intent.get("intent_type")
    outputs = set(intent.get("requested_outputs", []))
    skills: List[str] = []

    if "patch_proposal" in outputs or intent_type == "implement_change":
        skills.append("apply_validated_patch")
        skills.append("run_post_patch_tests")

    return _dedupe(skills)


def build_charter_1_1(
    intent: Dict[str, Any],
    decision: Dict[str, Any],
    *,
    actor: str,
    human_constraints: Dict[str, bool],
    forbidden_skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build (but do not persist) a schema_version 1.1.0
    conversational_mission_charter bound to an already-built Decision.
    Validated in-memory via authority.validate_charter_construction()
    before it is ever returned - no charter this function returns can
    violate human_constraints, skill registration, or the decision
    binding. Additive: build_charter() (1.0.0) is untouched."""

    proposed = real_proposed_skills(intent)
    followups = real_allowed_followup_skills(intent)
    forbidden = list(forbidden_skills or [])

    charter: Dict[str, Any] = {
        "schema_version": CHARTER_SCHEMA_VERSION_1_1,
        "report_type": "conversational_mission_charter",
        "charter_id": charter_id(intent),
        "mission_id": decision["mission_id"],
        "state": "proposed",
        "human_constraints": dict(human_constraints),
        "proposed_skills": proposed,
        "forbidden_skills": forbidden,
        "allowed_followup_skills": followups,
        "memory_write_allowed": not human_constraints["private_context_restricted"],
        "decision_id": decision["decision_id"],
        "decision_digest": authority.canonical_digest(decision),
        "created_at": utc_now(),
        "actor": actor,
        "objective": intent["objective"],
        "scope": {
            "targets": list(intent["targets"]),
            "requested_outputs": list(intent["requested_outputs"]),
        },
        "out_of_scope": [
            "autonomous background execution",
            "arbitrary shell execution",
            "unapproved filesystem mutation",
            "unapproved Git writes",
            "unapproved network access",
        ],
        "constraints": list(intent["constraints"]),
        "risk_level": intent["risk_level"],
        "approval_gates": [
            "charter approval",
            "per-action approval before execution",
            "separate patch approval before mutation",
            "separate Git approvals for stage, commit and push",
        ],
        "success_criteria": [
            "requested outputs are produced",
            "evidence is retained",
            "model output is deterministically reviewed",
            "no action exceeds its approved scope",
            "Teachback and human closure remain required",
        ],
        "authority": {
            "charter_is_not_permission": True,
            "skill_proposals_are_not_permission": True,
            "memory_does_not_authorize_action": True,
        },
    }
    charter["approval_phrase"] = approval_phrase(charter)
    charter["rejection_phrase"] = rejection_phrase(charter)

    authority.validate_charter_construction(charter, decision)
    return charter


def approve_charter_1_1(
    mission_dir: Path,
    charter: Dict[str, Any],
    decision: Dict[str, Any],
    *,
    approval_phrase: str,
    approved_by: str,
) -> Dict[str, Any]:
    """Transition a proposed 1.1 Charter to approved. approval_phrase is
    the human's typed response, checked against charter["approval_phrase"]
    (the stored challenge) before anything is persisted - the stored
    phrase is never itself treated as proof of approval, and the same
    normalized human-typed value (not the charter's stored copy) is what
    gets forwarded to authority.write_authority_receipt() as evidence of
    the actual approval. Revalidates schema_version, charter.state==
    "proposed", and the full Charter<->Decision binding via authority.
    validate_charter_construction() before any mutation. Then, still
    strictly before any file is written, checks whether a mission
    authority receipt already exists for this mission_dir - if so, fails
    closed immediately, before mission_decision.json or mission_charter.
    json are ever touched, so a second approval attempt (or any conflict
    with an already-approved mission) can never overwrite already-frozen
    authoritative files ahead of a doomed write_authority_receipt() call.
    Only after every one of those checks passes does it persist both
    authoritative files and call authority.write_authority_receipt(),
    which independently re-validates the now-approved shape one more time
    before the write-once receipt is ever published."""

    normalized_phrase = approval_phrase.strip() if isinstance(approval_phrase, str) else None
    if normalized_phrase != charter.get("approval_phrase"):
        raise authority.AuthorityBindingError(
            "approval_binding_mismatch",
            "approval_phrase does not match charter.approval_phrase",
        )
    normalized_approved_by = approved_by.strip() if isinstance(approved_by, str) else ""
    if not normalized_approved_by:
        raise authority.AuthorityBindingError(
            "approval_binding_mismatch", "approved_by must be a non-empty string"
        )
    if charter.get("schema_version") != CHARTER_SCHEMA_VERSION_1_1:
        raise authority.AuthorityBindingError(
            "charter_schema_migration_required",
            f"charter schema_version={charter.get('schema_version')!r}",
        )
    if charter.get("state") != "proposed":
        raise authority.AuthorityBindingError(
            "charter_binding_mismatch",
            f"only a proposed charter can be approved, found state={charter.get('state')!r}",
        )

    authority.validate_charter_construction(charter, decision)

    if authority.mission_authority_receipt_path(mission_dir).is_file():
        raise authority.AuthorityBindingError(
            "authority_receipt_invalid",
            "a mission authority receipt already exists for this mission; "
            "approve_charter_1_1() cannot run again - re-approval is not "
            "reentrant and never overwrites already-frozen authoritative "
            "files",
        )

    approved = dict(charter)
    approved["state"] = "approved"
    approved["approved_at"] = utc_now()
    approved["approved_by"] = normalized_approved_by

    authority.atomic_write_json(authority.mission_decision_path(mission_dir), decision)
    authority.atomic_write_json(authority.mission_charter_path(mission_dir), approved)
    authority.write_authority_receipt(
        mission_dir,
        mission_id=approved["mission_id"],
        charter=approved,
        decision=decision,
        approved_at=approved["approved_at"],
        approval_phrase=normalized_phrase,
    )
    return approved


def charter_markdown(charter: Dict[str, Any]) -> str:
    lines = [
        f"# Mission Charter: {charter['charter_id']}",
        "",
        f"- state: `{charter['state']}`",
        f"- actor: `{charter['actor']}`",
        f"- risk_level: `{charter['risk_level']}`",
        "",
        "## Objective",
        "",
        charter["objective"],
        "",
        "## Scope",
        "",
    ]
    lines.extend(f"- `{target}`" for target in charter["scope"]["targets"])
    lines += ["", "## Requested outputs", ""]
    lines.extend(f"- {item}" for item in charter["scope"]["requested_outputs"])
    lines += ["", "## Constraints", ""]
    lines.extend(f"- {item}" for item in charter["constraints"])
    lines += ["", "## Proposed skills", ""]
    lines.extend(f"- `{item}`" for item in charter["proposed_skills"])
    lines += ["", "## Approval gates", ""]
    lines.extend(f"- {item}" for item in charter["approval_gates"])
    lines += [
        "",
        "## Authority",
        "",
        "- Charter is not permission.",
        "- Skill proposals are not permission.",
        "- Memory does not authorize action.",
        "",
        "## Human response",
        "",
        f"- Approve: `{charter['approval_phrase']}`",
        f"- Reject: `{charter['rejection_phrase']}`",
        "",
    ]
    return "\n".join(lines)
