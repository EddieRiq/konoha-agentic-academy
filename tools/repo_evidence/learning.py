"""Evidence-backed proposals over approved studies; no apply capability."""
from __future__ import annotations

from typing import Any

from tools.local_model_audit.manage_local_model_audit import partition_evidence_linked_suggestions
from tools.teachback.manage_teachback import validate_repository_teachback, TeachbackError
from .study import RepositoryStudyRecord, validate_repository_study
from .acquire_repo_evidence import RepositoryEvidencePack

NON_AUTHORITY = "Recommendation is not permission. Human review and a separately approved mission are required for any adoption or patch."


def _understood(study: RepositoryStudyRecord, pack: RepositoryEvidencePack, teachback: dict) -> None:
    validate_repository_study(study.as_dict(), pack)
    session = validate_repository_teachback(teachback, study)
    if session["status"] != "understood":
        raise TeachbackError("repository_teachback_requires_human_entendido_before_learning")


def _provenance(study: RepositoryStudyRecord, fact: dict) -> dict:
    return {"study_id": study.study_id, "evidence_reference": dict(study.evidence_reference),
            "evidence_ref": fact["evidence_ref"], "locator": dict(fact["locator"])}


def self_improvement_recommendations(study: RepositoryStudyRecord, pack: RepositoryEvidencePack,
                                    teachback: dict, model_suggestions: Any = None) -> dict:
    _understood(study, pack, teachback)
    # Work from original structured evidence, never parse prose summaries.
    candidates = {row["evidence_ref"]: row for row in pack.dead_code_candidates}
    entrypoints = {row["evidence_ref"]: row for row in pack.entrypoints if not row.get("resolved_path")}
    validated = []
    for fact in study.facts:
        ref = fact["evidence_ref"]
        if ref in entrypoints:
            observation = "A manifest entrypoint has no statically resolved target in the acquired scope."
            recommendation = "Review the declaration and target together; propose a targeted correction only after confirming the intended command."
            risk = "Static resolution may miss packaging conventions; no runtime failure is proven."
            scope = "The cited entrypoint and its target, subject to a new approved mission."
        elif ref in candidates:
            observation = "The static extractor found a symbol without an observed incoming reference."
            recommendation = "Check entrypoints, dynamic use and public API consumers before proposing any removal or test improvement."
            risk = "Dynamic dispatch and external consumers can make this a false positive; automatic deletion is forbidden."
            scope = "Reachability review of the cited symbol only."
        else:
            continue
        validated.append({"observation": observation, "provenance": _provenance(study, fact),
                          "basis": "deterministic_candidate", "validation": "static_observation_not_proven_defect",
                          "recommendation": recommendation, "risk": risk, "scope": scope,
                          "status": "proposed", "authorizes_action": False})
        if len(validated) == 10:
            break
    known = {fact["evidence_ref"]: fact for fact in study.facts}
    linked, suppressed = partition_evidence_linked_suggestions(
        [] if model_suggestions is None else model_suggestions, known,
    )
    for item in linked:
        item["provenance"] = [_provenance(study, known[ref]) for ref in item["evidence_refs"]]
    return {"schema_version": "1.0.0", "report_type": "self_improvement_recommendations",
            "study_id": study.study_id, "evidence_reference": dict(study.evidence_reference),
            "validated": validated, "model_suggestions": linked, "suppressed": suppressed,
            "status": "proposed", "authorizes_action": False, "non_authority": NON_AUTHORITY,
            "limitations": ["Validated means a deterministic candidate was observed, not that a defect was proven.",
                            "Only included study facts are considered. Empty results do not prove the repository needs no improvement."]}


_LESSONS = {
    "tests": ("Consider the donor's explicit test organization for a comparable target component.",
              "Test discovery proves file presence, not test quality, coverage or execution."),
    "capabilities": ("Consider whether the donor's declared entrypoint structure would clarify a target command.",
                     "Packaging and runtime conventions may differ; a declaration is not proof of working behavior."),
    "relationships": ("Review whether the observed module separation would simplify a comparable target dependency.",
                      "Static imports do not prove good architecture; compare runtime responsibilities first."),
}


def donor_learning(donor: RepositoryStudyRecord, donor_pack: RepositoryEvidencePack, donor_teachback: dict,
                   target: RepositoryStudyRecord, target_pack: RepositoryEvidencePack, target_teachback: dict,
                   *, source_url: str | None = None) -> dict:
    if source_url is not None and (not isinstance(source_url, str) or len(source_url) > 2000):
        raise ValueError("public_source_url_invalid")
    _understood(donor, donor_pack, donor_teachback)
    _understood(target, target_pack, target_teachback)
    if donor.repository_identity["repo_root_id"] == target.repository_identity["repo_root_id"]:
        raise ValueError("donor_and_target_must_be_distinct")
    lessons = []
    # Include each supported category before filling the remaining bound.
    eligible = [f for f in donor.facts if f["category"] in _LESSONS]
    grouped = [[f for f in eligible if f["category"] == category] for category in _LESSONS]
    eligible = [group[index] for index in range(10) for group in grouped if index < len(group)]
    for fact in eligible[:10]:
        peers = [f for f in target.facts if f["category"] == fact["category"]]
        lesson, risk = _LESSONS[fact["category"]]
        comparison = ({"observation": peers[0]["observation"], "provenance": _provenance(target, peers[0])}
                      if peers else {"observation": "No comparable fact is included in the bounded target study; absence is not proven.",
                                     "provenance": {"study_id": target.study_id, "evidence_reference": target.evidence_reference}})
        lessons.append({"observed_donor_fact": fact["observation"], "provenance": _provenance(donor, fact),
                        "comparison_with_target": comparison, "candidate_lesson": lesson,
                        "compatibility_and_risk": risk + " License/provenance and doctrine compatibility require human review before adoption.",
                        "recommendation": "Prepare a separately scoped evaluation proposal; do not copy code or apply changes from this report.",
                        "status": "proposed", "authorizes_action": False, "non_authority": NON_AUTHORITY})
    return {"schema_version": "1.0.0", "report_type": "donor_learning_recommendations",
            "donor_study_id": donor.study_id, "target_study_id": target.study_id,
            "donor_evidence_reference": donor.evidence_reference, "target_evidence_reference": target.evidence_reference,
            "source_url": source_url, "origin_verification": "human_declared_public_origin_not_network_verified",
            "recommendations": lessons, "status": "proposed", "authorizes_action": False,
            "non_authority": NON_AUTHORITY, "code_copying": "not_performed_requires_separate_review"}
