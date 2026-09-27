"""Canonical required_sources / produces_sources contract for Konoha v4.2.0.

One vocabulary, one resolver, called identically at planning time (preview)
and at executor pre-invocation time (enforcing) - see resolve_required_sources.
No free-text or substring interpretation anywhere in this module: every
canonical source resolves through a named, dedicated, testable function.

Deliberately NOT imported into or re-exported from models.py (avoids a
circular import: this module needs AgentAssignment/EvidenceRecord from
models.py, and a future executor.py will need SourceAvailability from here -
models.py stays exactly as it is).

ResolutionContext carries acquired authority and plan data. Named filesystem
resolvers perform scoped material reads or currentness checks. The retained-
result helpers are strictly pure: no I/O, resolver calls or refreshes. All
file sources reuse context_acquisition.PRIVATE_MARKERS and explicit exclusions.
"""

from __future__ import annotations

import errno
import os
import stat
from dataclasses import dataclass
from copy import deepcopy
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping

from tools.konoha_v4.context_acquisition import PRIVATE_MARKERS
from tools.konoha_v4.models import AgentAssignment, EvidenceRecord
from tools.repo_evidence.acquire_repo_evidence import (
    RepositoryEvidencePack,
    bounded_evidence_view,
    is_evidence_current,
    _run_git,
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
    """Inputs to resolution; construction itself performs no I/O."""
    plan_approval_status: str
    plan_acceptance_criteria: tuple[str, ...]
    user_mission_request: str | None
    repo_root: Path | None
    repo_evidence_pack: RepositoryEvidencePack | None
    family_contracts: Mapping[str, Mapping[str, Any]]
    task_family_by_id: Mapping[str, str]
    evidence_by_task_id: Mapping[str, EvidenceRecord]
    failure_log_dir: Path | None = None
    # Repo-relative (posix) paths or directory prefixes, in the same
    # coordinates as Authorization.excluded_paths in repo evidence.
    excluded_paths: tuple[str, ...] = ()
    mission_plan: Mapping[str, Any] | None = None
    capability_registry: Mapping[str, Any] | None = None


# Bounds for concrete material delivered to a worker.
MAX_MATERIAL_FILE_BYTES = 20_000
MAX_MATERIAL_LIST_ITEMS = 10
MAX_MATERIAL_TEXT_CHARS = 2_000
MAX_PERSISTED_OUTPUT_BYTES = 200_000


def bounded_text(value: str) -> dict[str, Any]:
    return {"text": value[:MAX_MATERIAL_TEXT_CHARS], "total_chars": len(value),
            "truncated": len(value) > MAX_MATERIAL_TEXT_CHARS}


def bounded_list(values: list | tuple) -> dict[str, Any]:
    items = [bounded_value(v) for v in values[:MAX_MATERIAL_LIST_ITEMS]]
    return {"total": len(values), "included": len(items),
            "truncated": len(items) < len(values), "items": items}


def bounded_value(value: Any, depth: int = 0) -> Any:
    """Defensive projection; metadata makes every truncation explicit."""
    if depth > 6:
        return {"omitted": "depth_limit"}
    if isinstance(value, str):
        return bounded_text(value)
    if isinstance(value, (list, tuple)):
        items = [bounded_value(v, depth + 1) for v in value[:MAX_MATERIAL_LIST_ITEMS]]
        return {"total": len(value), "included": len(items), "truncated": len(items) < len(value), "items": items}
    if isinstance(value, Mapping):
        keys = [k for k in value if isinstance(k, str)][:MAX_MATERIAL_LIST_ITEMS]
        return {"fields": {k[:MAX_MATERIAL_TEXT_CHARS]: bounded_value(value[k], depth + 1) for k in keys},
                "total_fields": len(value), "truncated": len(keys) < len(value)}
    return value if value is None or isinstance(value, (bool, int, float)) else None


def _record_payload(record: EvidenceRecord) -> dict[str, Any] | None:
    if record.status != "completed" or not isinstance(record.output, str):
        return None
    if len(record.output) > MAX_PERSISTED_OUTPUT_BYTES:
        return None
    try:
        if len(record.output.encode("utf-8")) > MAX_PERSISTED_OUTPUT_BYTES:
            return None
        # The executor accepts a single JSON fence too. Reuse its parser
        # lazily to avoid an import cycle, with the same input bound.
        from tools.konoha_v4.executor import _parse_assignment_result_text
        payload = _parse_assignment_result_text(record.output)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        return None
    return payload if isinstance(payload, dict) else None


def find_available_sources_without_material(resolved: Mapping[str, SourceResolution]) -> tuple[str, ...]:
    """Pure audit of retained results; never resolves or reads a source."""
    return tuple(key for key, value in resolved.items()
                 if value.availability is SourceAvailability.AVAILABLE
                 and (not isinstance(value.materialization, Mapping) or not value.materialization))


def materialize_resolved_sources(resolved: Mapping[str, SourceResolution]) -> dict[str, Any]:
    """Pure delivery from the exact gated mapping, with no reacquisition."""
    if find_available_sources_without_material(resolved):
        raise ValueError("available_source_without_material")
    return {key: deepcopy(dict(value.materialization)) for key, value in resolved.items()
            if value.availability is SourceAvailability.AVAILABLE}



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
        "Bounded text of at least one non-empty regular file directly under repo_root/memory/failures/ (was: 'failure logs').",
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
    payload = _record_payload(record)
    if payload is None:
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
    payload = _record_payload(record)
    if payload is None:
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
            parsed.append({k: v[:MAX_MATERIAL_TEXT_CHARS] for k, v in
                           _parse_kv_observation(observation).items()
                           if k in {"locator", "command", "result", "verdict", "fact"}})
            if len(parsed) == MAX_MATERIAL_LIST_ITEMS:
                break
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
    payload = _record_payload(record)
    if payload is None:
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
# Descriptor-relative bounded file material for canonical file sources
# ---------------------------------------------------------------------------

_DIR_OPEN_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


def _unavailable_file_text() -> dict[str, Any]:
    return {"available": False, "total_bytes": None, "included_bytes": 0, "truncated": False, "text": ""}


def _is_plain_basename(name: str) -> bool:
    """Exactly one path component: no separator, no "."/"..", not empty."""
    return bool(name) and name not in (".", "..") and "/" not in name and "\x00" not in name


def _bounded_file_text(
    path: str,
    *,
    dir_fd: int | None = None,
    expected_identity: tuple[int, int] | None = None,
    limit: int = MAX_MATERIAL_FILE_BYTES,
) -> dict[str, Any]:
    """Bounded, honest read of one regular file (POSIX/Linux-oriented).

    Size and file type come from fstat on the SAME descriptor that is read.
    At most limit + 1 bytes are ever read (the extra byte only proves
    truncation) - an oversized file is never read in full. The leaf is
    opened O_NOFOLLOW and O_NONBLOCK, so a symlink is refused and a FIFO
    cannot block the open; anything that is not a regular file is refused.
    When dir_fd is given, path must be exactly one plain basename and is
    rejected BEFORE any open otherwise - os.open(dir_fd=...) would happily
    resolve "../x" or "sub/x" relative to the held descriptor. When
    expected_identity=(st_dev, st_ino) is given, the opened descriptor must
    have exactly that identity. Any I/O failure is reported as
    available=False (total_bytes None), never as an empty valid file.
    included_bytes counts bytes, text is decoded with errors="replace" so a
    cut multi-byte character can make len(text) differ from included_bytes.
    """
    if dir_fd is not None and not _is_plain_basename(path):
        return _unavailable_file_text()

    flags = os.O_RDONLY | _NOFOLLOW | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags, dir_fd=dir_fd)
    except (OSError, ValueError):
        return _unavailable_file_text()

    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            return _unavailable_file_text()
        if expected_identity is not None and (st.st_dev, st.st_ino) != tuple(expected_identity):
            return _unavailable_file_text()
        chunks: list[bytes] = []
        remaining = limit + 1
        while remaining > 0:
            chunk = os.read(fd, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
    except OSError:
        return _unavailable_file_text()
    finally:
        os.close(fd)

    included = raw[:limit]
    return {
        "available": True,
        "total_bytes": st.st_size,
        "included_bytes": len(included),
        "truncated": len(raw) > limit or st.st_size > limit,
        "text": included.decode("utf-8", errors="replace"),
    }


# ---------------------------------------------------------------------------
# plan_scope resolvers
# ---------------------------------------------------------------------------

def _resolve_mission_plan(task: AgentAssignment, ctx: ResolutionContext) -> SourceResolution:
    if ctx.plan_approval_status != "approved":
        return SourceResolution("mission_plan", SourceAvailability.MISSING, reason="plan_not_yet_approved")
    if not isinstance(ctx.mission_plan, Mapping) or not ctx.mission_plan:
        return SourceResolution("mission_plan", SourceAvailability.MISSING, reason="mission_plan_material_unavailable")
    return SourceResolution("mission_plan", SourceAvailability.AVAILABLE,
                            materialization={"mission_plan": bounded_value(ctx.mission_plan)})


def _resolve_acceptance_criteria(task: AgentAssignment, ctx: ResolutionContext) -> SourceResolution:
    if ctx.plan_acceptance_criteria and all(isinstance(v, str) and v.strip() for v in ctx.plan_acceptance_criteria):
        return SourceResolution(
            "acceptance_criteria", SourceAvailability.AVAILABLE,
            materialization={"acceptance_criteria": bounded_list(ctx.plan_acceptance_criteria)},
        )
    return SourceResolution("acceptance_criteria", SourceAvailability.MISSING, reason="plan_acceptance_criteria_empty")


def _resolve_user_mission_request(task: AgentAssignment, ctx: ResolutionContext) -> SourceResolution:
    raw = ctx.user_mission_request
    if isinstance(raw, str) and raw.strip():
        if len(raw) > MAX_MATERIAL_TEXT_CHARS:
            return SourceResolution("user_mission_request", SourceAvailability.MISSING, reason="original_request_exceeds_material_bound")
        return SourceResolution("user_mission_request", SourceAvailability.AVAILABLE,
                                materialization={"text": raw, "original": True, "truncated": False})
    return SourceResolution("user_mission_request", SourceAvailability.MISSING, reason="user_mission_request_empty")


def _resolve_capability_registry(task: AgentAssignment, ctx: ResolutionContext) -> SourceResolution:
    contract = ctx.family_contracts.get(task.family)
    if not isinstance(contract, Mapping) or not contract:
        return SourceResolution("capability_registry", SourceAvailability.MISSING, reason="family_contract_unavailable")
    return SourceResolution("capability_registry", SourceAvailability.AVAILABLE,
        materialization={"family": task.family, "contract": bounded_value(contract),
                         "capabilities": bounded_value(ctx.capability_registry)})


def _resolve_repository_state(task: AgentAssignment, ctx: ResolutionContext) -> SourceResolution:
    if ctx.repo_evidence_pack is None:
        return SourceResolution("repository_state", SourceAvailability.MISSING, reason="repository_evidence_not_acquired")
    if ctx.repo_root is None:
        return SourceResolution("repository_state", SourceAvailability.MISSING, reason="repo_root_unavailable_for_currentness_check")
    if ctx.repo_evidence_pack.authorized_repo_root != str(ctx.repo_root.resolve()):
        return SourceResolution("repository_state", SourceAvailability.UNAUTHORIZED, reason="repository_root_mismatch")
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


def _is_excluded_by_config(rel: str, excluded_paths: tuple[str, ...]) -> bool:
    """Same file-or-directory-prefix rule Authorization.excluded_paths uses
    in tools/repo_evidence/acquire_repo_evidence.py, in the same
    repo-relative coordinates."""
    return any(rel == p or rel.startswith(p.rstrip("/") + "/") for p in excluded_paths)


def _resolve_failure_logs(task: AgentAssignment, ctx: ResolutionContext) -> SourceResolution:
    """AVAILABLE only when bounded, non-empty text of at least one regular
    file directly under the canonical repo_root/memory/failures was
    actually read. The declared ctx.failure_log_dir must be exactly that
    directory (lexically and after resolution); the directory chain
    repo_root -> memory -> failures is then opened descriptor-relative
    without following symlinks, and the final directory descriptor stays
    open for listing and every read, so a later swap of memory or
    memory/failures cannot redirect a read. Candidates are classified
    without following symlinks (only regular, non-empty, non-dotfile,
    non-private, non-excluded files count), sorted and sliced to
    MAX_MATERIAL_LIST_ITEMS BEFORE any content is opened. Every selected
    file is re-opened by basename against the held descriptor and must
    still have its selection-time (st_dev, st_ino) and non-empty content;
    any selected hole fails the whole source closed."""
    if ctx.repo_root is None:
        return SourceResolution(
            "failure_logs", SourceAvailability.MISSING, reason="repo_root_unavailable_for_failure_log_check",
        )
    directory = ctx.failure_log_dir
    if directory is None or not directory.is_dir():
        return SourceResolution("failure_logs", SourceAvailability.MISSING, reason="failure_log_directory_absent")

    try:
        root = ctx.repo_root.resolve(strict=True)
    except OSError:
        return SourceResolution(
            "failure_logs", SourceAvailability.MISSING, reason="repo_root_unavailable_for_failure_log_check",
        )
    canonical = root / "memory" / "failures"
    declared = Path(os.path.abspath(directory))
    accepted_lexical = (canonical, Path(os.path.abspath(ctx.repo_root)) / "memory" / "failures")
    try:
        resolved_matches = directory.resolve(strict=True) == canonical
    except OSError:
        resolved_matches = False
    if declared not in accepted_lexical or not resolved_matches:
        return SourceResolution(
            "failure_logs", SourceAvailability.UNAUTHORIZED, reason="failure_log_directory_not_canonical",
        )

    fds: list[int] = []
    try:
        try:
            root_fd = os.open(str(root), _DIR_OPEN_FLAGS)
            fds.append(root_fd)
            memory_fd = os.open("memory", _DIR_OPEN_FLAGS | _NOFOLLOW, dir_fd=root_fd)
            fds.append(memory_fd)
            failures_fd = os.open("failures", _DIR_OPEN_FLAGS | _NOFOLLOW, dir_fd=memory_fd)
            fds.append(failures_fd)
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                return SourceResolution(
                    "failure_logs", SourceAvailability.UNAUTHORIZED, reason="failure_log_directory_not_canonical",
                )
            return SourceResolution("failure_logs", SourceAvailability.MISSING, reason="failure_log_directory_absent")

        try:
            names = sorted(os.listdir(failures_fd))
        except OSError:
            return SourceResolution("failure_logs", SourceAvailability.MISSING, reason="failure_log_files_unreadable")

        # (basename, canonical locator, st_dev, st_ino) - metadata only; no
        # file content is opened while classifying.
        candidates: list[tuple[str, str, int, int]] = []
        for name in names:
            if name.startswith(".") or not _is_plain_basename(name):
                continue
            rel = f"memory/failures/{name}"
            if any(marker in rel for marker in PRIVATE_MARKERS) or _is_excluded_by_config(rel, ctx.excluded_paths):
                continue
            try:
                st = os.stat(name, dir_fd=failures_fd, follow_symlinks=False)
            except OSError:
                continue
            # Symlinks, directories, FIFOs and other special files are not
            # regular files here; a zero-byte file is not concrete material.
            if not stat.S_ISREG(st.st_mode) or st.st_size == 0:
                continue
            candidates.append((name, rel, st.st_dev, st.st_ino))

        if not candidates:
            return SourceResolution("failure_logs", SourceAvailability.MISSING, reason="failure_log_directory_empty")

        items: list[dict[str, Any]] = []
        for name, rel, dev, ino in candidates[:MAX_MATERIAL_LIST_ITEMS]:
            info = _bounded_file_text(name, dir_fd=failures_fd, expected_identity=(dev, ino))
            if not info["available"] or not info["total_bytes"] or info["included_bytes"] <= 0:
                return SourceResolution(
                    "failure_logs", SourceAvailability.MISSING, reason="failure_log_files_unreadable",
                )
            items.append({"path": rel, **info})
    finally:
        for fd in reversed(fds):
            os.close(fd)

    return SourceResolution(
        "failure_logs", SourceAvailability.AVAILABLE,
        materialization={
            "failure_logs": {
                "total": len(candidates),
                "included": len(items),
                "truncated": len(items) < len(candidates),
                "items": items,
            },
        },
    )


def _resolve_task_input_source(canonical_id: str, task: AgentAssignment, ctx: ResolutionContext) -> SourceResolution:
    """Generic resolver for every plan_scope source satisfied by an
    explicit task.inputs-attached document (python_coding_rules,
    python_source_files, approved_checklist, authorized_local_source,
    approved_style_statute, target_journal_rules).

    Known limitation: AgentAssignment.inputs is an
    untyped list[str] today - nothing tags a given input path as "the
    python_coding_rules one" versus "the approved_checklist one". This
    resolver can only prove "bounded material from declared, authorized
    inputs was delivered", not that it is semantically the right document. A
    future per-input tag on AgentAssignment could sharpen this; inventing
    that tag is out of scope here (no models.py/schema change in this
    block; see also target_assignment_evidence's docstring for the same
    kind of honest limit).
    """
    if not task.inputs:
        return SourceResolution(canonical_id, SourceAvailability.MISSING, reason="no_task_inputs_declared")
    if ctx.repo_root is None:
        return SourceResolution(canonical_id, SourceAvailability.MISSING, reason="repo_root_unavailable_for_input_check")

    items: list[dict[str, Any]] = []
    # Validate every declared locator before slicing: an unauthorized suffix
    # cannot hide behind the material bound. Then read only the selected set.
    for rel in task.inputs:
        if (not isinstance(rel, str) or not rel or Path(rel).is_absolute()
                or ".." in Path(rel).parts or "\\" in rel or "\x00" in rel
                or any(part.startswith(".") for part in Path(rel).parts)
                or any(marker in rel for marker in PRIVATE_MARKERS)
                or _is_excluded_by_config(rel, ctx.excluded_paths)):
            return SourceResolution(canonical_id, SourceAvailability.UNAUTHORIZED, reason="input_path_unauthorized")
    for rel in task.inputs[:MAX_MATERIAL_LIST_ITEMS]:
        ignored, _, _ = _run_git(["check-ignore", "-q", "--", rel], ctx.repo_root)
        if ignored == 0:
            return SourceResolution(canonical_id, SourceAvailability.UNAUTHORIZED, reason="task_input_ignored")
        fds: list[int] = []
        try:
            fd = os.open(str(ctx.repo_root.resolve(strict=True)), _DIR_OPEN_FLAGS | _NOFOLLOW)
            fds.append(fd)
            parts = Path(rel).parts
            for part in parts[:-1]:
                fd = os.open(part, _DIR_OPEN_FLAGS | _NOFOLLOW, dir_fd=fd)
                fds.append(fd)
            st = os.stat(parts[-1], dir_fd=fd, follow_symlinks=False)
            if stat.S_ISLNK(st.st_mode):
                return SourceResolution(canonical_id, SourceAvailability.UNAUTHORIZED, reason="input_symlink_refused")
            info = _bounded_file_text(parts[-1], dir_fd=fd, expected_identity=(st.st_dev, st.st_ino))
            if not info["available"] or not info["included_bytes"]:
                return SourceResolution(canonical_id, SourceAvailability.MISSING, reason="task_input_material_unavailable")
            items.append({"path": rel, **info})
        except (OSError, ValueError) as exc:
            unauthorized = isinstance(exc, OSError) and exc.errno in (errno.ELOOP, errno.ENOTDIR)
            return SourceResolution(canonical_id, SourceAvailability.UNAUTHORIZED if unauthorized else SourceAvailability.MISSING,
                                    reason="task_input_material_unavailable")
        finally:
            for fd in reversed(fds):
                os.close(fd)
    return SourceResolution(canonical_id, SourceAvailability.AVAILABLE,
        materialization={"input_locators": tuple(i["path"] for i in items),
                         "files": {"total": len(task.inputs), "included": len(items),
                                   "truncated": len(items) < len(task.inputs), "items": items}})


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

    if any(ctx.evidence_by_task_id[dep].status != "completed" for dep in task.dependencies):
        return SourceResolution(canonical_id, SourceAvailability.MISSING, reason="dependency_not_completed")
    items = []
    for dep in task.dependencies[:MAX_MATERIAL_LIST_ITEMS]:
        record = ctx.evidence_by_task_id[dep]
        payload = _record_payload(record)
        if payload is None or not isinstance(payload.get("summary"), str) or not payload["summary"].strip():
            return SourceResolution(canonical_id, SourceAvailability.MISSING, reason="dependency_material_unavailable")
        rows = payload.get("evidence")
        if not isinstance(rows, list) or not all(isinstance(row, dict) and
                isinstance(row.get("source"), str) and isinstance(row.get("observation"), str) for row in rows):
            return SourceResolution(canonical_id, SourceAvailability.MISSING, reason="dependency_material_unavailable")
        items.append({"task_id": dep, "evidence_id": record.evidence_id,
                      "summary": bounded_text(payload["summary"]), "evidence": bounded_list(rows),
                      "authority": "provider_claim_only"})
    return SourceResolution(canonical_id, SourceAvailability.AVAILABLE,
        producer_task_ids=tuple(task.dependencies),
        materialization={"dependencies": {"total": len(task.dependencies), "included": len(items),
                         "truncated": len(items) < len(task.dependencies), "items": items}})


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
                "bounded": True, "authority": "provider_claim_only",
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
