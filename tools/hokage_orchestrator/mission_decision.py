"""Deterministic supervised mission decision support for the Hokage."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from . import authority

SCHEMA_VERSION = "1.0.0"
DECISION_SCHEMA_VERSION_1_1 = "1.1.0"
MINIMUM_SAVINGS_PERCENT = 30

REQUIRED_HUMAN_CONSTRAINT_KEYS = (
    "mutation_forbidden",
    "network_blocked",
    "local_model_only",
    "private_context_restricted",
)


class ProviderSelectionError(RuntimeError):
    """Raised when no provider satisfies human_constraints together with
    current provider readiness and effective capabilities. Decision
    construction must fail closed here, before any Charter is ever built -
    never fall back to a partially-compatible provider."""


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


def _validate_human_constraints(human_constraints: Dict[str, bool]) -> None:
    if (
        not isinstance(human_constraints, dict)
        or set(human_constraints) != set(REQUIRED_HUMAN_CONSTRAINT_KEYS)
    ):
        raise ProviderSelectionError(
            "human_constraints must be an object with exactly the four "
            f"closed boolean keys: {sorted(REQUIRED_HUMAN_CONSTRAINT_KEYS)}"
        )
    for key in REQUIRED_HUMAN_CONSTRAINT_KEYS:
        if not isinstance(human_constraints[key], bool):
            raise ProviderSelectionError(f"human_constraints.{key} must be an exact bool")


def select_provider_and_model_1_1(
    classification: Dict[str, Any],
    snapshot: Dict[str, Any],
    *,
    human_constraints: Dict[str, bool],
    local_model: str,
    provider_skill_id: str,
) -> Dict[str, Any]:
    """1.1 provider selection for one explicit provider skill.

    provider_skill_id is never inferred from category/complexity - the
    caller must state, from the mission's requested output, which provider
    skill this Decision is selecting a provider for:

    - "run_technical_plan": codex or ollama, chosen by readiness,
      human_constraints and requested-output-driven category priority.
    - "invoke_local_model_audit": ollama only - codex/claude are never
      candidates, regardless of readiness or category. If ollama is not
      ready or violates a constraint, this fails closed with
      ProviderSelectionError before any Charter exists - there is no
      fallback to a remote provider for this skill.

    Under human_constraints["local_model_only"], the provider is always
    ollama and strategy never suggests a remote/hybrid-with-external-
    provider path - "hybrid_review_required" (extra supervision, not a
    second provider bound into this selection) is only ever applied when
    local_model_only is False."""

    _validate_human_constraints(human_constraints)

    if provider_skill_id not in {"run_technical_plan", "invoke_local_model_audit"}:
        raise ProviderSelectionError(
            f"unknown provider skill for decision selection: {provider_skill_id!r}"
        )

    from . import skill_runtime  # local import: skill_runtime imports authority too

    providers = _provider_map(snapshot)
    ready = {name for name, row in providers.items() if row.get("status") == "ready"}
    category = classification["category"]
    complexity = classification["complexity"]

    if human_constraints["local_model_only"]:
        candidate_order = ["ollama"]
        selection_source = "human_constraint_local_model_only"
    elif provider_skill_id == "invoke_local_model_audit":
        candidate_order = ["ollama"]
        selection_source = "provider_skill_ollama_only"
    else:
        if category == "knowledge_processing":
            candidate_order = ["ollama", "codex", "claude"]
        elif category in {"software_engineering", "audit_and_review"}:
            candidate_order = ["codex", "claude", "ollama"]
        elif category in {"research", "general_supervised_task"}:
            candidate_order = ["claude", "codex", "ollama"]
        else:
            candidate_order = ["codex", "claude", "ollama"]
        selection_source = "deterministic_classification_and_readiness"

    for provider in candidate_order:
        if provider not in ready:
            continue
        try:
            caps = skill_runtime.effective_capabilities(provider_skill_id, provider)
        except (KeyError, TypeError, ValueError):
            continue

        if human_constraints["network_blocked"] and caps["external_network"]:
            continue
        if human_constraints["mutation_forbidden"] and caps["mutates_files"]:
            continue
        if human_constraints["private_context_restricted"] and caps["private_context"]:
            continue

        model = local_model if provider == "ollama" else "provider_default"
        strategy = "local" if provider == "ollama" else "remote"
        if (
            complexity == "high"
            and provider == "ollama"
            and not human_constraints["local_model_only"]
        ):
            strategy = "hybrid_review_required"

        return {
            "provider": provider,
            "model": model,
            "strategy": strategy,
            "selection_source": selection_source,
            "rationale": (
                f"Selected the highest-priority provider for {provider_skill_id} "
                "that is ready and compatible with this mission's human "
                "constraints and effective capabilities."
            ),
            "provider_readiness": sorted(ready),
            "selection_is_proposal_only": True,
        }

    raise ProviderSelectionError(
        f"no provider satisfies human_constraints together with current "
        f"provider readiness and effective capabilities for {provider_skill_id!r}"
    )


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


def build_decision_1_1(
    *,
    mission_id: str,
    intent: Dict[str, Any],
    bootstrap_snapshot: Dict[str, Any],
    local_model: str,
    human_constraints: Dict[str, bool],
    provider_skill_id: str,
) -> Dict[str, Any]:
    """Build (but do not persist) a schema_version 1.1.0
    hokage_mission_decision. Additive: MissionDecisionEngine.decide() and
    its 1.0.0 payload shape are untouched. Provider selection is delegated
    to select_provider_and_model_1_1() - see that function for the
    fail-closed, requested-output-driven policy."""

    snapshot = bootstrap_snapshot.get("snapshot", bootstrap_snapshot)
    classification = classify_mission(intent)
    selection = select_provider_and_model_1_1(
        classification,
        snapshot,
        human_constraints=human_constraints,
        local_model=local_model,
        provider_skill_id=provider_skill_id,
    )
    economy = estimate_economy(intent, classification, selection)
    policy = build_supervision_policy(classification)
    decision_id = "decision-" + hashlib.sha256(
        f"{mission_id}|{intent.get('objective', '')}".encode("utf-8")
    ).hexdigest()[:12]

    return {
        "schema_version": DECISION_SCHEMA_VERSION_1_1,
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


def publish_decision_1_1(mission_dir: Path, decision: Dict[str, Any]) -> Dict[str, Any]:
    """Persist the Decision at mission_dir/mission_decision.json via
    authority.atomic_write_json() - the same path convention as the
    Charter and the authority receipt."""

    authority.atomic_write_json(authority.mission_decision_path(mission_dir), decision)
    return decision


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
