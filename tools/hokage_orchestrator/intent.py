"""Deterministic conversational intent interpretation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

SCHEMA_VERSION = "1.0.0"

_PATH_PATTERN = re.compile(
    r"(?<![\w.-])"
    r"(?P<path>(?:\.{1,2}/|/|[A-Za-z]:[\\/])?[A-Za-z0-9_.-]+"
    r"(?:[\\/][A-Za-z0-9_. -]+)+)"
)


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def _dedupe(values: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _intent_type(text: str) -> str:
    if _contains_any(text, ("revis", "audit", "analiz", "inspect", "review")):
        return "inspect_and_review"
    if _contains_any(
        text,
        ("implement", "crea", "agrega", "añad", "modific", "corrig", "patch", "refactor"),
    ):
        return "implement_change"
    if _contains_any(text, ("test", "prueba", "verific", "validate")):
        return "validate_project"
    if _contains_any(text, ("record", "memoria", "obsidian", "handoff")):
        return "record_memory"
    return "general_mission"


def _targets(request: str, repo_root: Path) -> List[str]:
    lowered = request.lower()
    targets: List[str] = []

    if _contains_any(
        lowered,
        (
            "este repo",
            "este repositorio",
            "este proyecto",
            "the repo",
            "the repository",
            "current project",
        ),
    ):
        targets.append(str(repo_root.resolve()))

    for match in _PATH_PATTERN.finditer(request):
        value = match.group("path").strip(".,;:()[]{}")
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = repo_root / candidate
        try:
            targets.append(str(candidate.resolve()))
        except OSError:
            targets.append(str(candidate))

    if not targets:
        targets.append(str(repo_root.resolve()))

    return _dedupe(targets)


def _constraints(text: str) -> List[str]:
    constraints = [
        "explicit approval before execution",
        "model output is evidence only",
        "memory does not authorize action",
    ]

    if _contains_any(
        text,
        (
            "no modifi",
            "sin modifi",
            "no camb",
            "solo lectura",
            "read only",
            "read-only",
        ),
    ):
        constraints.append("no filesystem mutation before explicit approval")

    if _contains_any(text, ("sin red", "no network", "offline")):
        constraints.append("network access blocked")

    if _contains_any(text, ("ollama", "modelo local", "local model")):
        constraints.append("local model only")

    if _contains_any(
        text,
        ("determin", "checks primero", "controles primero", "tests first"),
    ):
        constraints.append("deterministic checks before model invocation")

    if _contains_any(
        text,
        ("privad", "kirigakure", "obsidian", "context pack", "biblioteca"),
    ):
        constraints.append("private context requires a scoped approval")

    if _contains_any(
        text,
        ("token", "tiempo", "timing", "latencia", "medí", "mide"),
    ):
        constraints.append("record token and timing evidence")

    return _dedupe(constraints)


def _requested_outputs(text: str, intent_type: str) -> List[str]:
    outputs: List[str] = []

    if intent_type in {"inspect_and_review", "validate_project"}:
        outputs.append("findings")
    if _contains_any(text, ("patch", "corrig", "implement", "refactor")):
        outputs.append("patch_proposal")
    if _contains_any(text, ("test", "prueba", "verific", "validate")):
        outputs.append("test_evidence")
    if _contains_any(text, ("token", "tiempo", "timing", "latencia")):
        outputs.append("usage_report")
    if _contains_any(text, ("memoria", "obsidian", "record", "guard")):
        outputs.append("memory_summary")
    if not outputs:
        outputs.append("mission_result")

    return _dedupe(outputs)


def _risk_level(intent_type: str, constraints: List[str]) -> str:
    if intent_type == "implement_change":
        return "medium"
    if "private context requires a scoped approval" in constraints:
        return "medium"
    return "low"


def interpret_intent(request: str, repo_root: Path) -> Dict[str, Any]:
    """Create a bounded deterministic intent contract."""

    normalized = " ".join(request.strip().split())
    lowered = normalized.lower()
    intent_type = _intent_type(lowered)
    constraints = _constraints(lowered)
    targets = _targets(normalized, repo_root)

    missing_context: List[str] = []
    if not normalized:
        missing_context.append("mission request")
    if not targets:
        missing_context.append("target")

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "conversational_intent",
        "intent_type": intent_type,
        "objective": normalized,
        "targets": targets,
        "constraints": constraints,
        "requested_outputs": _requested_outputs(lowered, intent_type),
        "missing_context": missing_context,
        "risk_level": _risk_level(intent_type, constraints),
        "requires_charter": True,
        "authority": {
            "intent_is_not_permission": True,
            "model_output_is_evidence_only": True,
            "explicit_approval_required": True,
        },
    }


def validate_intent(payload: Dict[str, Any], repo_root: Path) -> List[str]:
    """Validate an interpreted intent without granting authority."""

    errors: List[str] = []
    required = {
        "schema_version",
        "report_type",
        "intent_type",
        "objective",
        "targets",
        "constraints",
        "requested_outputs",
        "missing_context",
        "risk_level",
        "requires_charter",
        "authority",
    }

    missing = sorted(required - set(payload))
    if missing:
        errors.append("missing fields: " + ", ".join(missing))

    if payload.get("report_type") != "conversational_intent":
        errors.append("invalid report_type")

    objective = payload.get("objective")
    if not isinstance(objective, str) or not objective.strip():
        errors.append("objective must be non-empty text")

    targets = payload.get("targets")
    if not isinstance(targets, list) or not targets:
        errors.append("targets must be a non-empty list")
    else:
        root = repo_root.resolve()
        for target in targets:
            if not isinstance(target, str) or not target.strip():
                errors.append("target entries must be non-empty text")
                continue
            try:
                Path(target).resolve().relative_to(root)
            except ValueError:
                errors.append(f"target escapes repository scope: {target}")

    if payload.get("risk_level") not in {"low", "medium", "high"}:
        errors.append("risk_level must be low, medium or high")

    authority = payload.get("authority")
    if not isinstance(authority, dict):
        errors.append("authority must be an object")
    elif authority.get("intent_is_not_permission") is not True:
        errors.append("intent authority invariant missing")

    return errors
