"""Bounded deterministic repository comprehension, independent of repository name.

A study is a projection with provenance, never a replacement evidence pack.
No provider, filesystem, network, approval or patch side effects live here.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from .acquire_repo_evidence import RepositoryEvidencePack, bounded_evidence_view
from .persistence import evidence_reference

MAX_STUDY_ITEMS = 10
MAX_STUDY_TEXT = 2_000
STUDY_LIMITATIONS = (
    "Static evidence only; no tests or application code were executed.",
    "Python imports show structural links, not runtime behavior.",
    "Documentation statements and dead-code candidates are not verified truth.",
    "Collections are bounded; omitted material is not evidence of absence.",
    "Study and teachback do not authorize execution, patches or doctrine changes.",
)


@dataclass(frozen=True)
class RepositoryStudyRecord:
    schema_version: str
    study_id: str
    evidence_reference: dict[str, str]
    repository_identity: dict[str, Any]
    facts: list[dict[str, Any]]
    coverage: dict[str, Any]
    limitations: list[str]
    authority: str = "evidence_only"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _study_id(payload: dict) -> str:
    body = {k: v for k, v in payload.items() if k != "study_id"}
    return "study-" + hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:32]


def build_repository_study(pack: RepositoryEvidencePack) -> RepositoryStudyRecord:
    view = bounded_evidence_view(pack)
    facts: list[dict[str, Any]] = []
    coverage: dict[str, Any] = {}

    def add(category: str, rows: list[dict], describe, *, total: int | None = None):
        selected = rows[:MAX_STUDY_ITEMS]
        actual_total = len(rows) if total is None else total
        included = 0
        for row in selected:
            ref = row.get("evidence_ref")
            locator = pack.provenance_index.get(ref)
            if not locator:
                continue
            statement = describe(row)
            # Provenance is structured and exact. No model-generated locators.
            facts.append({"fact_id": f"fact-{len(facts):03d}", "category": category,
                          "observation": statement[:MAX_STUDY_TEXT],
                          "text_truncated": len(statement) > MAX_STUDY_TEXT,
                          "evidence_ref": ref, "locator": dict(locator),
                          "basis": "deterministic_extraction"})
            included += 1
        coverage[category] = {"total": actual_total, "included": included, "truncated": included < actual_total}

    add("components", view["modules"]["items"], lambda r: f"Python module {r['path']} has {r['fan_in']} incoming and {r['fan_out']} outgoing local import links.", total=len(pack.modules))
    test_paths = {row["path"] for row in pack.test_files}
    relationships = sorted(pack.imports_graph, key=lambda r: (r["from_path"] in test_paths, r["from_path"], r["to_path"]))
    entrypoints = sorted(pack.entrypoints, key=lambda r: (not r["path"].endswith("pyproject.toml"), r["path"] in test_paths, r["path"]))
    documentation = sorted((row for row in pack.doc_claims if row["statement"].strip() and not row["statement"].strip().startswith("```")),
                           key=lambda r: (r["path"].rsplit("/", 1)[-1].lower() != "readme.md", r["path"], r["line"]))
    add("relationships", relationships, lambda r: f"{r['from_path']} imports {r['to_path']}.")
    add("capabilities", entrypoints, lambda r: f"Declared entrypoint: {r['reason']}; resolved target: {r.get('resolved_path') or 'unresolved'}.")
    add("tests", pack.test_files, lambda r: f"Test source discovered: {r['path']}; execution result unknown.")
    add("documentation", documentation, lambda r: f"Documentation states (unverified claim): {r['statement']}")
    add("candidates", pack.dead_code_candidates, lambda r: f"Static candidate for human investigation: {r.get('name', r.get('symbol', 'symbol'))} in {r['path']}; not proof of dead code.")
    coverage["scan"] = {"paths": len(pack.scan_paths), "missing_tracked": len(pack.missing_tracked_files),
                        "unknowns": len(pack.unknowns)}
    record = RepositoryStudyRecord(
        schema_version="1.0.0", study_id="", evidence_reference=evidence_reference(pack),
        repository_identity={"repo_root_id": pack.workspace_identity["repo_root_id"],
                             "vcs": pack.workspace_identity["vcs"], "head": pack.workspace_identity["head"]},
        facts=facts, coverage=coverage, limitations=list(STUDY_LIMITATIONS),
    )
    return RepositoryStudyRecord(**{**record.as_dict(), "study_id": _study_id(record.as_dict())})


def validate_repository_study(payload: dict, pack: RepositoryEvidencePack) -> RepositoryStudyRecord:
    """Verify against the retained pack, not against generated summaries."""
    expected = build_repository_study(pack)
    if payload != expected.as_dict():
        raise ValueError("repository_study_evidence_mismatch")
    return expected


def explain_repository_study(study: RepositoryStudyRecord, category: str | None = None) -> str:
    categories = {fact["category"] for fact in study.facts}
    if category is not None and category not in categories:
        return "That area has no included evidence. Absence from this bounded study does not prove absence from the repository."
    lines = [f"Repository study {study.study_id}", f"Evidence pack: {study.evidence_reference['pack_id']}",
             "This is a static map of the inspected repository. It is not execution approval."]
    # A simple overview; clarification selects up to ten facts in one area.
    selected = [f for f in study.facts if category is None or f["category"] == category]
    if category is None:
        selected = [next(f for f in selected if f["category"] == key) for key in sorted(categories)]
    for fact in selected:
        loc = fact["locator"]
        lines.append(f"- {fact['observation']} [{loc['path']}:{loc['line_start']}; {fact['evidence_ref']}]")
    lines.extend(study.limitations)
    lines.append("Ask for clarification or repetition. Only your exact :entendido command ends this repository teachback.")
    return "\n".join(lines)
