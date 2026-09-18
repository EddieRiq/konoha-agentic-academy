"""Canonical required_sources / produces_sources contract for Konoha v4.2.0.

One vocabulary, one resolver, called identically at planning time (preview)
and at executor pre-invocation time (enforcing) - see resolve_required_sources.
No free-text or substring interpretation anywhere in this module: every
canonical source resolves through a named, dedicated, testable function.

Deliberately NOT imported into or re-exported from models.py (avoids a
circular import: this module needs AgentAssignment/EvidenceRecord from
models.py, and a future executor.py will need SourceAvailability from here -
models.py stays exactly as it is).

This module is pure: it takes already-acquired data (a ResolutionContext) and
returns a resolution. It does not read files itself except for the two
narrow, explicitly-scoped checks that are inherently filesystem-based
(memory/failures/ content, and a declared task input's existence/
authorization under the authorized repo root) - both reuse
tools.konoha_v4.context_acquisition.PRIVATE_MARKERS, the same enforced
exclusion constant tools/repo_evidence/acquire_repo_evidence.py already
reuses, rather than inventing a second exclusion vocabulary.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping

from tools.konoha_v4.context_acquisition import PRIVATE_MARKERS
from tools.konoha_v4.models import AgentAssignment, EvidenceRecord
from tools.repo_evidence.acquire_repo_evidence import (
    RepositoryEvidencePack,
    bounded_evidence_view,
    is_evidence_current,
)


class SourceAvailability(str, Enum):
    AVAILABLE = "available"
    PENDING_PRODUCER = "pending_producer"
    MISSING = "missing"
    UNAUTHORIZED = "unauthorized"
    NOT_APPLICABLE = "not_applicable"
    # NOT_APPLICABLE is part of the contract's vocabulary but has no current
    # call site among the 10 existing families' required_sources - every
    # declared source today is unconditionally required whenever its family
    # runs. Reserved for a future source that a specific assignment's own
    # flags make structurally irrelevant, not invented here to exercise the
    # enum member.


class SourceKind(str, Enum):
    PLAN_SCOPE = "plan_scope"
    ASSIGNMENT_PRODUCED = "assignment_produced"
    STRUCTURAL_DEPENDENCY = "structural_dependency"


class UnknownSourceError(RuntimeError):
    """canonical_id is not in SOURCE_VOCABULARY - a migration bug, not a
    runtime data condition, so this raises rather than returning a status."""


@dataclass(frozen=True)
class SourceSpec:
    canonical_id: str
    kind: SourceKind
    description: str


@dataclass(frozen=True)
class SourceResolution:
    canonical_id: str
    availability: SourceAvailability
    reason: str | None = None
    producer_task_ids: tuple[str, ...] = ()
    materialization: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class ResolutionContext:
    """Pure input bundle - no file reads happen here, only in the two
    filesystem-based resolvers explicitly documented above."""
    plan_approval_status: str
    plan_acceptance_criteria: tuple[str, ...]
    user_mission_request: str | None
    repo_root: Path | None
    repo_evidence_pack: RepositoryEvidencePack | None
    family_contracts: Mapping[str, Mapping[str, Any]]
    task_family_by_id: Mapping[str, str]
    evidence_by_task_id: Mapping[str, EvidenceRecord]
    failure_log_dir: Path | None = None


# ---------------------------------------------------------------------------
# Canonical vocabulary - exactly the IDs the 10 existing family contracts
# need, migrated from their prior free-text required_sources values.
# ---------------------------------------------------------------------------

SOURCE_VOCABULARY: dict[str, SourceSpec] = {
    "mission_plan": SourceSpec(
        "mission_plan", SourceKind.PLAN_SCOPE,
        "The approved MissionPlan itself (was: 'approved mission plan' / 'mission charter' / 'plan').",
    ),
    "acceptance_criteria": SourceSpec(
        "acceptance_criteria", SourceKind.PLAN_SCOPE,
        "plan.acceptance_criteria, non-empty (was: 'acceptance criteria').",
    ),
    "user_mission_request": SourceSpec(
        "user_mission_request", SourceKind.PLAN_SCOPE,
        "The literal human mission request text, pre-plan (was: 'user mission').",
    ),
    "repository_state": SourceSpec(
        "repository_state", SourceKind.PLAN_SCOPE,
        "A current (non-stale) RepositoryEvidencePack for the authorized repo (was: 'repository state').",
    ),
    "capability_registry": SourceSpec(
        "capability_registry", SourceKind.PLAN_SCOPE,
        "The loaded CapabilityRegistry (was: 'capability registry').",
    ),
    "failure_logs": SourceSpec(
        "failure_logs", SourceKind.PLAN_SCOPE,
        "memory/failures/ containing at least one real (non-dotfile) entry (was: 'failure logs').",
    ),
    "python_coding_rules": SourceSpec(
        "python_coding_rules", SourceKind.PLAN_SCOPE,
        "An explicit task.inputs-attached rules document (was: 'Python coding rules' / 'Python rules').",
    ),
    "python_source_files": SourceSpec(
        "python_source_files", SourceKind.PLAN_SCOPE,
        "task.inputs-attached Python source file(s) (was: 'Python files').",
    ),
    "approved_checklist": SourceSpec(
        "approved_checklist", SourceKind.PLAN_SCOPE,
        "An explicit task.inputs-attached checklist document (was: 'approved checklist').",
    ),
    "authorized_local_source": SourceSpec(
        "authorized_local_source", SourceKind.PLAN_SCOPE,
        "task.inputs-attached authorized local document(s) (was: 'authorized local source' / 'approved sources' / 'source material').",
    ),
    "approved_style_statute": SourceSpec(
        "approved_style_statute", SourceKind.PLAN_SCOPE,
        "An explicit task.inputs-attached style statute document (was: 'approved style statute').",
    ),
    "target_journal_rules": SourceSpec(
        "target_journal_rules", SourceKind.PLAN_SCOPE,
        "An explicit task.inputs-attached journal-rules document (was: 'target journal rules').",
    ),
    "target_assignment_evidence": SourceSpec(
        "target_assignment_evidence", SourceKind.STRUCTURAL_DEPENDENCY,
        "Evidence of the reviewed assignment(s) named in task.dependencies (was: 'target agent output'). "
        "No existing AgentAssignment field distinguishes one dependency as 'the' primary review target - "
        "see _resolve_structural_dependency for why this deliberately requires the same structural test as "
        "dependency_evidence_bundle rather than inventing a positional convention.",
    ),
    "dependency_evidence_bundle": SourceSpec(
        "dependency_evidence_bundle", SourceKind.STRUCTURAL_DEPENDENCY,
        "Evidence for task.dependencies collectively (was: 'source evidence' / 'all evidence').",
    ),
    "implementation_diff": SourceSpec(
        "implementation_diff", SourceKind.ASSIGNMENT_PRODUCED,
        "A python-implementation dependency's produced_source marker (was: 'implementation diff').",
    ),
    "test_evidence": SourceSpec(
        "test_evidence", SourceKind.ASSIGNMENT_PRODUCED,
        "A python-implementation dependency's produced_source marker (was: 'test evidence').",
    ),
    "review_evidence": SourceSpec(
        "review_evidence", SourceKind.ASSIGNMENT_PRODUCED,
        "A jounin-review/python-review dependency's produced_source marker (was: 'review evidence').",
    ),
    "source_fact_cards": SourceSpec(
        "source_fact_cards", SourceKind.ASSIGNMENT_PRODUCED,
        "A source-extraction dependency's produced_source marker AND at least one concrete "
        "fact-card material row carrying a non-empty locator (was: 'source fact cards' / "
        "'original locators' - collapsed into one ID: source-extraction.json's own "
        "instruction_set lists 'Cite locator' as one instruction for producing a fact card, "
        "evidence a locator is an attribute of a fact card, not an independent artifact; "
        "see evaluate_produced_source_material's source_fact_cards validator, which fails "
        "closed on a fact card with no locator).",
    ),
}


# ---------------------------------------------------------------------------
# produced_source marker + material encoding/extraction
# ---------------------------------------------------------------------------
#
# AssignmentResult.evidence stays tuple[dict[str, str], ...] exactly as
# schemas/runtime/konoha_v4_assignment_result.schema.json fixes it
# (additionalProperties: false, items required to be exactly {source,
# observation}) - confirmed by reading that schema and
# executor._validate_assignment_result_payload before writing this module.
# Two distinct row shapes live inside that fixed {source, observation} pair:
#
#   1. the marker - declares intent, proves nothing by itself:
#        {"source": "produced_source", "observation": "source_id=test_evidence"}
#   2. material - one or more concrete, source-specific evidence rows:
#        {"source": "material:test_evidence", "observation": "command=... | result=pass"}
#
# A bare marker is NEVER sufficient. AVAILABLE requires all three of:
#   A. the producer's family declares this source in produces_sources
#      (checked in _resolve_assignment_produced against family_contracts);
#   B. the marker row is present (extract_produced_source_ids);
#   C. at least one material row for that exact source_id passes its
#      dedicated validator (evaluate_produced_source_material) - a summary
#      string, output_schema prose, or the family name are never evidence.

PRODUCED_SOURCE_MARKER = "produced_source"
MATERIAL_ROW_PREFIX = "material:"


def _parse_kv_observation(observation: str) -> dict[str, str]:
    """"k1=v1 | k2=v2" -> {"k1": "v1", "k2": "v2"}. Unparseable/empty parts
    are silently dropped, never raise - callers only ever check for the
    presence of specific non-empty keys."""
    result: dict[str, str] = {}
    for part in observation.split("|"):
        if "=" not in part:
            continue
        key, _, value = part.strip().partition("=")
        key, value = key.strip(), value.strip()
        if key:
            result[key] = value
    return result


def extract_produced_source_ids(record: EvidenceRecord) -> frozenset[str]:
    """canonical source IDs a completed EvidenceRecord marked as produced
    via the marker row. This alone never implies AVAILABLE - see module
    docstring above; _resolve_assignment_produced additionally requires
    evaluate_produced_source_material to pass. Never inferred from
    output_schema text, family-name substrings, or any other heuristic -
    only this exact marker row shape. A non-"completed" record,
    unparseable output, or a source_id outside SOURCE_VOCABULARY all yield
    an empty set - no fallback guessing."""
    if record.status != "completed":
        return frozenset()
    try:
        payload = json.loads(record.output)
    except (json.JSONDecodeError, TypeError):
        return frozenset()
    if not isinstance(payload, dict):
        return frozenset()
    rows = payload.get("evidence")
    if not isinstance(rows, list):
        return frozenset()

    ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("source") != PRODUCED_SOURCE_MARKER:
            continue
        observation = row.get("observation")
        if not isinstance(observation, str):
            continue
        candidate = _parse_kv_observation(observation).get("source_id")
        if candidate in SOURCE_VOCABULARY:
            ids.add(candidate)
    return frozenset(ids)


def _material_rows_for(record: EvidenceRecord, canonical_id: str) -> list[dict[str, str]]:
    """Parsed key=value dicts from every material:<canonical_id> row in a
    completed record. [] on any non-completed/unparseable/absent case."""
    if record.status != "completed":
        return []
    try:
        payload = json.loads(record.output)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(payload, dict):
        return []
    rows = payload.get("evidence")
    if not isinstance(rows, list):
        return []

    tag = f"{MATERIAL_ROW_PREFIX}{canonical_id}"
    parsed: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict) or row.get("source") != tag:
            continue
        observation = row.get("observation")
        if isinstance(observation, str):
            parsed.append(_parse_kv_observation(observation))
    return parsed


def _validate_implementation_diff_material(rows: list[dict[str, str]]) -> bool:
    """At least one row names a concrete file/line locator for the diff -
    never just a bare marker."""
    return any(kv.get("locator", "").strip() for kv in rows)


def _validate_test_evidence_material(rows: list[dict[str, str]]) -> bool:
    """At least one row names both the command actually run and its
    concrete result - "it produced tests" prose alone never counts."""
    return any(kv.get("command", "").strip() and kv.get("result", "").strip() for kv in rows)


def _validate_review_evidence_material(rows: list[dict[str, str]]) -> bool:
    """At least one row names a concrete verdict, not a vague summary."""
    return any(kv.get("verdict", "").strip() for kv in rows)


def _validate_source_fact_cards_material(rows: list[dict[str, str]]) -> bool:
    """At least one fact-card row carries BOTH a fact statement and a
    non-empty locator. A fact with no locator does not satisfy this - see
    SOURCE_VOCABULARY["source_fact_cards"] for why locator presence,
    formerly its own canonical ID (original_locators), is validated here
    as a required property of this source instead."""
    return any(kv.get("fact", "").strip() and kv.get("locator", "").strip() for kv in rows)


_MATERIAL_VALIDATORS: dict[str, Callable[[list[dict[str, str]]], bool]] = {
    "implementation_diff": _validate_implementation_diff_material,
    "test_evidence": _validate_test_evidence_material,
    "review_evidence": _validate_review_evidence_material,
    "source_fact_cards": _validate_source_fact_cards_material,
}


def evaluate_produced_source_material(canonical_id: str, record: EvidenceRecord) -> bool:
    """True only if record carries at least one material:<canonical_id> row
    that passes that source's dedicated validator. False (never an
    exception) for a canonical_id with no registered validator - an
    assignment_produced source with no material contract can never be
    proven, so it fails closed rather than defaulting to trusting the
    marker alone."""
    validator = _MATERIAL_VALIDATORS.get(canonical_id)
    if validator is None:
        return False
    return validator(_material_rows_for(record, canonical_id))


def find_undeclared_produced_sources(
    record: EvidenceRecord, declared_produces_sources: Any,
) -> frozenset[str]:
    """Producer-side integrity check, independent of any consumer:
    canonical IDs this record's marker or material rows claim, that its
    OWN family's produces_sources does not list. A worker attaching
    material for a source its family was never authorized to produce is a
    contract violation this catches regardless of whether anything
    currently depends on that task."""
    if record.status != "completed":
        return frozenset()
    try:
        payload = json.loads(record.output)
    except (json.JSONDecodeError, TypeError):
        return frozenset()
    if not isinstance(payload, dict):
        return frozenset()
    rows = payload.get("evidence")
    if not isinstance(rows, list):
        return frozenset()

    declared = set(declared_produces_sources or [])
    undeclared: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        source = row.get("source")
        if not isinstance(source, str):
            continue
        candidate: str | None = None
        if source == PRODUCED_SOURCE_MARKER:
            observation = row.get("observation")
            if isinstance(observation, str):
                candidate = _parse_kv_observation(observation).get("source_id")
        elif source.startswith(MATERIAL_ROW_PREFIX):
            candidate = source[len(MATERIAL_ROW_PREFIX):]
        if candidate and candidate in SOURCE_VOCABULARY and candidate not in declared:
            undeclared.add(candidate)
    return frozenset(undeclared)


# ---------------------------------------------------------------------------
# plan_scope resolvers
# ---------------------------------------------------------------------------

def _resolve_mission_plan(task: AgentAssignment, ctx: ResolutionContext) -> SourceResolution:
    if ctx.plan_approval_status == "approved":
        return SourceResolution("mission_plan", SourceAvailability.AVAILABLE)
    return SourceResolution("mission_plan", SourceAvailability.MISSING, reason="plan_not_yet_approved")


def _resolve_acceptance_criteria(task: AgentAssignment, ctx: ResolutionContext) -> SourceResolution:
    if ctx.plan_acceptance_criteria:
        return SourceResolution(
            "acceptance_criteria", SourceAvailability.AVAILABLE,
            materialization={"acceptance_criteria": ctx.plan_acceptance_criteria},
        )
    return SourceResolution("acceptance_criteria", SourceAvailability.MISSING, reason="plan_acceptance_criteria_empty")


def _resolve_user_mission_request(task: AgentAssignment, ctx: ResolutionContext) -> SourceResolution:
    if ctx.user_mission_request and ctx.user_mission_request.strip():
        return SourceResolution("user_mission_request", SourceAvailability.AVAILABLE)
    return SourceResolution("user_mission_request", SourceAvailability.MISSING, reason="user_mission_request_empty")


def _resolve_capability_registry(task: AgentAssignment, ctx: ResolutionContext) -> SourceResolution:
    # Structurally always true by the time any resolution call can happen at
    # all: CapabilityRegistry.__init__ reads config/konoha_v4_capabilities.json
    # and raises immediately on failure, before any plan/assignment exists.
    return SourceResolution(
        "capability_registry", SourceAvailability.AVAILABLE,
        materialization={"source": "config/konoha_v4_capabilities.json"},
    )


def _resolve_repository_state(task: AgentAssignment, ctx: ResolutionContext) -> SourceResolution:
    if ctx.repo_evidence_pack is None:
        return SourceResolution("repository_state", SourceAvailability.MISSING, reason="repository_evidence_not_acquired")
    if ctx.repo_root is None:
        return SourceResolution("repository_state", SourceAvailability.MISSING, reason="repo_root_unavailable_for_currentness_check")
    if not is_evidence_current(ctx.repo_evidence_pack, ctx.repo_root):
        return SourceResolution("repository_state", SourceAvailability.MISSING, reason="repository_evidence_stale")
    # bounded_evidence_view is the one materialization path for a
    # RepositoryEvidencePack - the planner's Codex context and this
    # resolver's AVAILABLE materialization both call it, never a
    # second/parallel serializer. See tools/repo_evidence/acquire_repo_evidence.py.
    return SourceResolution(
        "repository_state", SourceAvailability.AVAILABLE,
        materialization=bounded_evidence_view(ctx.repo_evidence_pack),
    )


def _resolve_failure_logs(task: AgentAssignment, ctx: ResolutionContext) -> SourceResolution:
    directory = ctx.failure_log_dir
    if directory is None or not directory.is_dir():
        return SourceResolution("failure_logs", SourceAvailability.MISSING, reason="failure_log_directory_absent")
    # An empty directory (or one containing only dotfiles/placeholders such
    # as .gitkeep) is not failure-log evidence - there is nothing to cite.
    real_entries = [p for p in directory.iterdir() if p.is_file() and not p.name.startswith(".")]
    if not real_entries:
        return SourceResolution("failure_logs", SourceAvailability.MISSING, reason="failure_log_directory_empty")
    return SourceResolution(
        "failure_logs", SourceAvailability.AVAILABLE,
        materialization={"failure_log_paths": tuple(sorted(p.name for p in real_entries))},
    )


def _resolve_task_input_source(canonical_id: str, task: AgentAssignment, ctx: ResolutionContext) -> SourceResolution:
    """Generic resolver for every plan_scope source satisfied by an
    explicit task.inputs-attached document (python_coding_rules,
    python_source_files, approved_checklist, authorized_local_source,
    approved_style_statute, target_journal_rules).

    Known, honestly-stated limitation: AgentAssignment.inputs is an
    untyped list[str] today - nothing tags a given input path as "the
    python_coding_rules one" versus "the approved_checklist one". This
    resolver can only prove "at least one declared, existing, authorized
    input is attached", not that it is semantically the right document. A
    future per-input tag on AgentAssignment could sharpen this; inventing
    that tag is out of scope here (no models.py/schema change in this
    block; see also target_assignment_evidence's docstring for the same
    kind of honest limit).
    """
    if not task.inputs:
        return SourceResolution(canonical_id, SourceAvailability.MISSING, reason="no_task_inputs_declared")
    if ctx.repo_root is None:
        return SourceResolution(canonical_id, SourceAvailability.MISSING, reason="repo_root_unavailable_for_input_check")

    root = ctx.repo_root.resolve()
    resolved_inputs: list[str] = []
    for raw in task.inputs:
        rel = raw.strip().lstrip("/")
        if not rel or ".." in Path(rel).parts:
            continue
        if any(marker in rel for marker in PRIVATE_MARKERS):
            return SourceResolution(canonical_id, SourceAvailability.UNAUTHORIZED, reason=f"input_path_excluded:{rel}")
        candidate = (root / rel).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return SourceResolution(canonical_id, SourceAvailability.UNAUTHORIZED, reason=f"input_path_escapes_root:{rel}")
        if candidate.is_file():
            resolved_inputs.append(rel)

    if not resolved_inputs:
        return SourceResolution(canonical_id, SourceAvailability.MISSING, reason="declared_task_inputs_not_found_on_disk")
    return SourceResolution(
        canonical_id, SourceAvailability.AVAILABLE,
        materialization={"input_locators": tuple(resolved_inputs)},
    )


_PLAN_SCOPE_RESOLVERS: dict[str, Callable[[AgentAssignment, ResolutionContext], SourceResolution]] = {
    "mission_plan": _resolve_mission_plan,
    "acceptance_criteria": _resolve_acceptance_criteria,
    "user_mission_request": _resolve_user_mission_request,
    "capability_registry": _resolve_capability_registry,
    "repository_state": _resolve_repository_state,
    "failure_logs": _resolve_failure_logs,
    "python_coding_rules": lambda task, ctx: _resolve_task_input_source("python_coding_rules", task, ctx),
    "python_source_files": lambda task, ctx: _resolve_task_input_source("python_source_files", task, ctx),
    "approved_checklist": lambda task, ctx: _resolve_task_input_source("approved_checklist", task, ctx),
    "authorized_local_source": lambda task, ctx: _resolve_task_input_source("authorized_local_source", task, ctx),
    "approved_style_statute": lambda task, ctx: _resolve_task_input_source("approved_style_statute", task, ctx),
    "target_journal_rules": lambda task, ctx: _resolve_task_input_source("target_journal_rules", task, ctx),
}


# ---------------------------------------------------------------------------
# structural_dependency resolver (target_assignment_evidence, dependency_evidence_bundle)
# ---------------------------------------------------------------------------

def _resolve_structural_dependency(
    canonical_id: str, task: AgentAssignment, ctx: ResolutionContext, *, enforcing: bool,
) -> SourceResolution:
    if not task.dependencies:
        return SourceResolution(canonical_id, SourceAvailability.MISSING, reason="no_dependencies_declared")

    not_yet_run = [t for t in task.dependencies if t not in ctx.evidence_by_task_id]
    if not_yet_run:
        if enforcing:
            return SourceResolution(
                canonical_id, SourceAvailability.MISSING, reason="dependency_not_yet_run_at_enforcement",
                producer_task_ids=tuple(not_yet_run),
            )
        return SourceResolution(
            canonical_id, SourceAvailability.PENDING_PRODUCER, reason="scheduled_dependency_not_yet_run",
            producer_task_ids=tuple(not_yet_run),
        )

    records = [ctx.evidence_by_task_id[t] for t in task.dependencies]
    completed = [r for r in records if r.status == "completed"]
    if not completed:
        return SourceResolution(canonical_id, SourceAvailability.MISSING, reason="no_completed_dependency_evidence")
    return SourceResolution(
        canonical_id, SourceAvailability.AVAILABLE,
        producer_task_ids=tuple(task.dependencies),
        materialization={"evidence_ids": tuple(r.evidence_id for r in completed)},
    )


# ---------------------------------------------------------------------------
# assignment_produced resolver (implementation_diff, test_evidence,
# review_evidence, source_fact_cards)
# ---------------------------------------------------------------------------

def _resolve_assignment_produced(
    canonical_id: str, task: AgentAssignment, ctx: ResolutionContext, *, enforcing: bool,
) -> SourceResolution:
    """Declaring produces_sources on a family means that family is ALLOWED
    to produce this source - it never means a completed assignment of that
    family automatically produced it, and a bare produced_source marker is
    not sufficient either. AVAILABLE requires all three:
      A. the producer's family declares this source (checked below via
         ctx.family_contracts, before any dependency evidence is read);
      B. the marker row is present (extract_produced_source_ids);
      C. at least one concrete material row for this exact source_id
         passes its dedicated validator (evaluate_produced_source_material).
    A producer that ran but never marked it resolves to MISSING with
    reason declared_producer_did_not_produce_source. A producer that
    marked it but attached no valid material resolves to MISSING with the
    more specific reason produced_source_evidence_missing - a summary
    string, output_schema prose, or the family name are never material."""
    producer_task_ids: list[str] = []
    for dep_id in task.dependencies:
        family_name = ctx.task_family_by_id.get(dep_id)
        if family_name is None:
            continue
        contract = ctx.family_contracts.get(family_name, {})
        produces = contract.get("produces_sources") or []
        if canonical_id in produces:
            producer_task_ids.append(dep_id)

    if not producer_task_ids:
        return SourceResolution(canonical_id, SourceAvailability.MISSING, reason="no_declared_producer_in_dependencies")

    not_yet_run = [t for t in producer_task_ids if t not in ctx.evidence_by_task_id]
    if not_yet_run:
        if enforcing:
            return SourceResolution(
                canonical_id, SourceAvailability.MISSING, reason="producer_not_yet_run_at_enforcement",
                producer_task_ids=tuple(not_yet_run),
            )
        return SourceResolution(
            canonical_id, SourceAvailability.PENDING_PRODUCER, reason="scheduled_producer_not_yet_run",
            producer_task_ids=tuple(not_yet_run),
        )

    marked_but_no_material: list[str] = []
    for producer_task_id in producer_task_ids:
        record = ctx.evidence_by_task_id[producer_task_id]
        if canonical_id not in extract_produced_source_ids(record):
            continue
        if not evaluate_produced_source_material(canonical_id, record):
            marked_but_no_material.append(producer_task_id)
            continue
        return SourceResolution(
            canonical_id, SourceAvailability.AVAILABLE,
            producer_task_ids=(producer_task_id,),
            materialization={
                "source_id": canonical_id,
                "producer_task_id": producer_task_id,
                "evidence_id": record.evidence_id,
                "material": _material_rows_for(record, canonical_id),
            },
        )

    if marked_but_no_material:
        return SourceResolution(
            canonical_id, SourceAvailability.MISSING, reason="produced_source_evidence_missing",
            producer_task_ids=tuple(marked_but_no_material),
        )
    return SourceResolution(
        canonical_id, SourceAvailability.MISSING, reason="declared_producer_did_not_produce_source",
        producer_task_ids=tuple(producer_task_ids),
    )


# ---------------------------------------------------------------------------
# Public dispatcher
# ---------------------------------------------------------------------------

def resolve_required_sources(
    canonical_id: str, task: AgentAssignment, ctx: ResolutionContext, *, enforcing: bool,
) -> SourceResolution:
    """The one resolver, called identically by the planner (enforcing=False,
    a not-yet-run producer/dependency surfaces as PENDING_PRODUCER) and by
    the executor immediately before invocation (enforcing=True,
    PENDING_PRODUCER is not a valid terminal state and collapses to MISSING
    so the caller fails the assignment closed rather than proceeding)."""
    spec = SOURCE_VOCABULARY.get(canonical_id)
    if spec is None:
        raise UnknownSourceError(f"canonical_id not in SOURCE_VOCABULARY: {canonical_id!r}")

    if spec.kind is SourceKind.PLAN_SCOPE:
        return _PLAN_SCOPE_RESOLVERS[canonical_id](task, ctx)
    if spec.kind is SourceKind.STRUCTURAL_DEPENDENCY:
        return _resolve_structural_dependency(canonical_id, task, ctx, enforcing=enforcing)
    if spec.kind is SourceKind.ASSIGNMENT_PRODUCED:
        return _resolve_assignment_produced(canonical_id, task, ctx, enforcing=enforcing)
    raise AssertionError(f"unhandled SourceKind: {spec.kind!r}")  # pragma: no cover


def resolve_all(
    required_sources: list[str], task: AgentAssignment, ctx: ResolutionContext, *, enforcing: bool,
) -> dict[str, SourceResolution]:
    """Resolve every one of a family's declared required_sources exactly
    once, in declaration order. The returned dict is the single result
    reused both for the availability gate (planner preview or executor
    enforcement) and for materializing the worker's resolved_source_bundle
    - no source is ever resolved twice, and planner/executor never diverge
    on what a source's status or material actually is."""
    return {
        canonical_id: resolve_required_sources(canonical_id, task, ctx, enforcing=enforcing)
        for canonical_id in required_sources
    }
