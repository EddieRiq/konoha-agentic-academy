"""Deterministic supervised mission decision support for the Hokage."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


SCHEMA_VERSION = "1.0.0"
MINIMUM_SAVINGS_PERCENT = 30


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _contains(text: str, values: Iterable[str]) -> bool:
    tokens = set(
        re.findall(
            r"[a-z0-9_+.-]+",
            text.lower(),
        )
    )
    normalized = {
        value.lower()
        for value in values
    }
    return bool(tokens & normalized)


def classify_mission(intent: Dict[str, Any]) -> Dict[str, Any]:
    material = " ".join(
        [
            str(intent.get("objective", "")),
            *[str(item) for item in intent.get("targets", [])],
            *[str(item) for item in intent.get("requested_outputs", [])],
        ]
    )
    if _contains(material, ("code", "implement", "fix", "test", "repo", "git", ".py")):
        category = "software_engineering"
        complexity = "high" if _contains(material, ("architecture", "migration", "release")) else "medium"
    elif _contains(material, ("research", "paper", "thesis", "sources", "investigate")):
        category = "research"
        complexity = "medium"
    elif _contains(material, ("summarize", "summary", "rewrite", "format", "extract")):
        category = "knowledge_processing"
        complexity = "low"
    elif _contains(material, ("audit", "review", "security", "privacy", "risk")):
        category = "audit_and_review"
        complexity = "high"
    else:
        category = "general_supervised_task"
        complexity = "medium"

    return {
        "category": category,
        "complexity": complexity,
        "risk_level": intent.get("risk_level", "medium"),
        "evidence": {
            "intent_type": intent.get("intent_type"),
            "targets": list(intent.get("targets", [])),
            "requested_outputs": list(intent.get("requested_outputs", [])),
        },
    }


def _provider_map(snapshot: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(row.get("provider")): row
        for row in snapshot.get("providers", [])
        if isinstance(row, dict) and row.get("provider")
    }


def select_provider_and_model(
    classification: Dict[str, Any],
    snapshot: Dict[str, Any],
    local_model: str,
) -> Dict[str, Any]:
    providers = _provider_map(snapshot)
    ready = {
        name for name, row in providers.items()
        if row.get("status") == "ready"
    }
    category = classification["category"]
    complexity = classification["complexity"]

    if category == "knowledge_processing" and "ollama" in ready:
        provider = "ollama"
        strategy = "local"
        model = local_model
        rationale = "Low-risk knowledge processing fits the ready local provider."
    elif category in {"software_engineering", "audit_and_review"} and "codex" in ready:
        provider = "codex"
        strategy = "remote"
        model = "provider_default"
        rationale = "Repository and review work prioritizes the ready coding provider."
    elif category in {"research", "general_supervised_task"} and "claude" in ready:
        provider = "claude"
        strategy = "remote"
        model = "provider_default"
        rationale = "Long-form reasoning prioritizes the ready general remote provider."
    elif "codex" in ready:
        provider = "codex"
        strategy = "remote"
        model = "provider_default"
        rationale = "Codex is the highest-priority ready fallback."
    elif "claude" in ready:
        provider = "claude"
        strategy = "remote"
        model = "provider_default"
        rationale = "Claude is the available ready fallback."
    elif "ollama" in ready:
        provider = "ollama"
        strategy = "local"
        model = local_model
        rationale = "Only the local provider is ready."
    else:
        provider = "none"
        strategy = "blocked"
        model = "none"
        rationale = "No provider is ready; execution must stop and escalate."

    if complexity == "high" and provider == "ollama":
        strategy = "hybrid_review_required"
        rationale += " High complexity requires superior independent review."

    return {
        "provider": provider,
        "model": model,
        "strategy": strategy,
        "rationale": rationale,
        "provider_readiness": sorted(ready),
        "selection_is_proposal_only": True,
    }


def estimate_economy(
    intent: Dict[str, Any],
    classification: Dict[str, Any],
    selection: Dict[str, Any],
) -> Dict[str, Any]:
    objective_words = len(str(intent.get("objective", "")).split())
    target_count = len(intent.get("targets", []))
    complexity_factor = {"low": 1, "medium": 2, "high": 4}[classification["complexity"]]
    estimated_input_tokens = max(500, objective_words * 8 + target_count * 350)
    estimated_output_tokens = 500 * complexity_factor
    premium_baseline_tokens = (estimated_input_tokens + estimated_output_tokens) * 2
    planned_tokens = estimated_input_tokens + estimated_output_tokens
    estimated_savings = round(
        (1 - planned_tokens / premium_baseline_tokens) * 100,
        2,
    )
    return {
        "estimate_source": "deterministic_heuristic",
        "estimated_input_tokens": estimated_input_tokens,
        "estimated_output_tokens": estimated_output_tokens,
        "premium_baseline_tokens": premium_baseline_tokens,
        "planned_tokens": planned_tokens,
        "estimated_savings_percent": estimated_savings,
        "minimum_savings_percent": MINIMUM_SAVINGS_PERCENT,
        "minimum_savings_met": estimated_savings >= MINIMUM_SAVINGS_PERCENT,
        "monetary_cost": {
            "status": "manual_required",
            "reason": "Provider price and subscription limits are not inferred.",
        },
        "estimate_is_not_billing_truth": True,
    }


def build_supervision_policy(classification: Dict[str, Any]) -> Dict[str, Any]:
    high_risk = (
        classification["risk_level"] == "high"
        or classification["complexity"] == "high"
    )
    return {
        "maximum_worker_attempts": 1 if high_risk else 2,
        "retry_requires_new_root_cause_evidence": True,
        "stop_on_repeated_error_signature": True,
        "root_cause_escalation": "hokage_and_human_council",
        "independent_jounin_review": True,
        "review_before_permanent_change": True,
        "teachback_required": True,
        "instruction_delta": {
            "owner": "shikamaru",
            "status": "proposal_only",
            "requires_independent_review": True,
            "requires_human_approval": True,
            "may_modify_own_policy": False,
        },
    }


class MissionDecisionEngine:
    """Produces evidence-backed proposals; never invokes a provider."""

    def __init__(
        self,
        *,
        state_root: Path,
        bootstrap_snapshot: Dict[str, Any],
        local_model: str,
    ) -> None:
        self.state_root = state_root.resolve()
        self.bootstrap_snapshot = bootstrap_snapshot
        self.local_model = local_model

    def decide(
        self,
        *,
        mission_id: str,
        intent: Dict[str, Any],
    ) -> Dict[str, Any]:
        snapshot = self.bootstrap_snapshot.get("snapshot", self.bootstrap_snapshot)
        classification = classify_mission(intent)
        selection = select_provider_and_model(
            classification,
            snapshot,
            self.local_model,
        )
        economy = estimate_economy(intent, classification, selection)
        policy = build_supervision_policy(classification)
        decision_id = "decision-" + hashlib.sha256(
            f"{mission_id}|{intent.get('objective', '')}".encode("utf-8")
        ).hexdigest()[:12]
        payload = {
            "schema_version": SCHEMA_VERSION,
            "report_type": "hokage_mission_decision",
            "decision_id": decision_id,
            "mission_id": mission_id,
            "created_at": utc_now(),
            "classification": classification,
            "selection": selection,
            "economy": economy,
            "supervision": policy,
            "review_checkpoints": [
                "mission_charter_approval",
                "per_action_approval",
                "independent_jounin_review",
                "teachback",
                "human_closure",
            ],
            "telemetry_contract": {
                "record_provider": True,
                "record_model": True,
                "record_input_output_tokens_when_available": True,
                "record_duration": True,
                "record_outcome": True,
                "record_error_signature": True,
                "private_state_only": True,
            },
            "authority": {
                "hokage_decision_is_proposal_only": True,
                "decision_does_not_authorize_execution": True,
                "provider_output_is_evidence_only": True,
                "no_self_approval": True,
            },
        }
        write_json(
            self.state_root / "decisions" / f"{mission_id}.json",
            payload,
        )
        return payload
