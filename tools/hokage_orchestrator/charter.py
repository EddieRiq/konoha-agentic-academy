"""Mission Charter construction and exact approval phrases."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

SCHEMA_VERSION = "1.0.0"


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
