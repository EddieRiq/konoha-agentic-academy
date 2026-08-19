"""Canonical digests and the single post-approval authority checkpoint.

mission_charter.json and mission_decision.json are the two authoritative
content files, but neither can prove on its own that it was not rewritten
together with the other after approval - a digest cross-check between the
two only catches a change to one of them in isolation. mission_authority.json
is the independent, write-once receipt that closes that gap: it freezes
charter_digest and decision_digest at the moment of approval, in a third
file nothing else ever touches, published exactly once via an O_CREAT|O_EXCL
exclusive create (never a check-then-replace, which would race under
concurrent approval attempts). Every post-approval check re-derives both
digests from the current mission_charter.json / mission_decision.json and
compares them against this receipt. The bounded, honest guarantee: any
action bound before a rewrite of the charter, the decision, or the receipt
detects that rewrite. A rewrite of all three files together, before any of
them is ever read again, is not something an application-level receipt can
detect - that would require filesystem-level tamper-proofing, out of scope
here and not claimed.

Construction (build_charter, before anything is persisted) and post-approval
execution are two different functions. validate_charter_construction() takes
in-memory candidate objects and touches no file - at construction time there
may be no approved mission_charter.json yet, or the one on disk may be a
stale prior proposal that must not be consulted while building a new one.
validate_action_authority() is the only function that reads from disk, and
it always re-reads fresh; nothing here trusts a cached copy (action_queue.json's
own charter_binding field exists for display only).

Both authoritative files are structurally validated (closed key sets, exact
types, current schema_version) before any authorization decision uses their
content - there are no permissive dict.get(key, default) reads in an
authorization path. A file at a different schema_version fails closed with
charter_schema_migration_required; it stays readable elsewhere (status /
resume, read-only) but nothing here authorizes a new or restored action
against it.

The CHARTER_ALLOWED_KEYS / DECISION_ALLOWED_KEYS / SELECTION_ALLOWED_KEYS /
RECEIPT_ALLOWED_KEYS sets below are this module's stand-in for the real
schemas/runtime/*.v2.schema.json additionalProperties:false contract until
schema_loader.py exists; they must be kept in sync with those schema files
by hand for now (test_schema_versioning.py cross-checks them).

validate_action_authority()'s phase argument distinguishes when an approval
must already be on record: queue_init / followup_append validate authority,
digests, capabilities and identity but require no approval evidence yet (the
action was just created). restore re-validates a previously created action
and additionally checks its approval evidence only if the action's own
status already claims to be approved ("running" in this codebase's action
status vocabulary) - a still-pending ("proposed") action restores without
pretending it was approved. pre_dispatch is the strictest phase: it requires
status=="running" and complete, self-consistent approval evidence, and fails
closed if either is missing or incomplete.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

CHARTER_SCHEMA_VERSION = "1.1.0"
DECISION_SCHEMA_VERSION = "1.1.0"
AUTHORITY_RECEIPT_SCHEMA_VERSION = "1.1.0"

REQUIRED_HUMAN_CONSTRAINT_KEYS = (
    "mutation_forbidden",
    "network_blocked",
    "local_model_only",
    "private_context_restricted",
)

CAPABILITY_KEYS = ("mutates_files", "external_network", "local_transport", "private_context")

SELECTION_REQUIRED_KEYS = frozenset({"provider", "model", "strategy", "selection_source"})
SELECTION_ALLOWED_KEYS = frozenset(
    SELECTION_REQUIRED_KEYS
    | {"rationale", "provider_readiness", "selection_is_proposal_only", "blocked_diagnostic"}
)

CHARTER_REQUIRED_KEYS = frozenset(
    {
        "schema_version",
        "report_type",
        "charter_id",
        "mission_id",
        "state",
        "human_constraints",
        "proposed_skills",
        "forbidden_skills",
        "allowed_followup_skills",
        "memory_write_allowed",
        "decision_id",
        "decision_digest",
        "approval_phrase",
    }
)
CHARTER_ALLOWED_KEYS = frozenset(
    CHARTER_REQUIRED_KEYS
    | {
        "created_at",
        "actor",
        "objective",
        "scope",
        "out_of_scope",
        "constraints",
        "risk_level",
        "approval_gates",
        "success_criteria",
        "authority",
        "rejection_phrase",
        "approved_at",
        "approved_by",
    }
)

DECISION_REQUIRED_KEYS = frozenset({"schema_version", "report_type", "decision_id", "mission_id", "selection"})
DECISION_ALLOWED_KEYS = frozenset(
    DECISION_REQUIRED_KEYS
    | {
        "created_at",
        "classification",
        "economy",
        "supervision",
        "review_checkpoints",
        "telemetry_contract",
        "authority",
    }
)

RECEIPT_REQUIRED_KEYS = frozenset(
    {
        "schema_version",
        "report_type",
        "mission_id",
        "charter_id",
        "charter_digest",
        "decision_id",
        "decision_digest",
        "approved_at",
        "approval_phrase_hash",
    }
)
RECEIPT_ALLOWED_KEYS = RECEIPT_REQUIRED_KEYS


def canonical_json(payload: Dict[str, Any]) -> str:
    """Sorted-key, compact-separator JSON - independent of how a file
    happens to be pretty-printed on disk. Two structurally identical dicts
    always produce the same string, regardless of key insertion order or
    the indentation atomic_write_json uses for human readability."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_digest(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def compute_arguments_hash(arguments: Dict[str, Any]) -> str:
    return canonical_digest(arguments)


def compute_action_id(*, mission_id: str, skill_id: str, arguments_hash: str) -> str:
    material = f"{mission_id}|{skill_id}|{arguments_hash}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:10]
    return f"action-{digest}"


def atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def mission_charter_path(mission_dir: Path) -> Path:
    return mission_dir / "mission_charter.json"


def mission_decision_path(mission_dir: Path) -> Path:
    return mission_dir / "mission_decision.json"


def mission_authority_receipt_path(mission_dir: Path) -> Path:
    return mission_dir / "mission_authority.json"


class AuthorityBindingError(RuntimeError):
    """Fail-closed diagnostic for the authority checkpoint. code is always
    one of a fixed, code-owned vocabulary - never derived from free text."""

    STABLE_CODES = frozenset(
        {
            "charter_binding_mismatch",
            "decision_binding_mismatch",
            "mission_binding_mismatch",
            "provider_selection_mismatch",
            "model_selection_mismatch",
            "strategy_selection_mismatch",
            "selection_source_mismatch",
            "capability_binding_mismatch",
            "capability_constraint_violation",
            "skill_forbidden",
            "authority_receipt_missing",
            "authority_receipt_invalid",
            "charter_immutable_violation",
            "decision_immutable_violation",
            "arguments_hash_mismatch",
            "approval_binding_mismatch",
            "charter_schema_migration_required",
            "execution_claim_missing",
            "execution_claim_invalid",
            "execution_already_claimed",
            "execution_claim_binding_mismatch",
            "action_queue_lock_timeout",
            "execution_still_active",
        }
    )

    def __init__(self, code: str, detail: str = "") -> None:
        if code not in self.STABLE_CODES:
            raise ValueError(f"unknown AuthorityBindingError code: {code!r}")
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


def read_authoritative_json(path: Path, *, error_code: str) -> Dict[str, Any]:
    """Read one file, normalizing every failure mode (missing, unreadable,
    invalid JSON, non-object payload) into a single AuthorityBindingError -
    never lets FileNotFoundError, OSError, json.JSONDecodeError or
    AttributeError escape the checkpoint."""

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise AuthorityBindingError(error_code, f"file missing: {path}") from exc
    except OSError as exc:
        raise AuthorityBindingError(error_code, f"file unreadable: {path}: {exc}") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AuthorityBindingError(error_code, f"file is not valid JSON: {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise AuthorityBindingError(error_code, f"file is not a JSON object: {path}")
    return payload


def _required(source: Dict[str, Any], key: str, code: str) -> Any:
    """Fetch a required field. Absence is always an immediate, named
    failure - never silently compared as though it were a matching None."""
    if key not in source:
        raise AuthorityBindingError(code, f"missing required field: {key}")
    return source[key]


def publish_once(
    path: Path,
    payload: Dict[str, Any],
    *,
    identity_fields: Tuple[str, ...],
    error_code: str,
) -> Tuple[Dict[str, Any], bool]:
    """Publish payload to path via a real atomic exclusive create
    (os.open with O_CREAT|O_EXCL|O_WRONLY) - not a check-then-replace,
    which would race under concurrent publishers. If path already exists,
    the existing content is read back and compared on identity_fields
    only (never on volatile fields such as timestamps); a match on those
    fields returns (existing, False) - idempotent reentry, the ORIGINAL
    content is kept, nothing is overwritten; a difference raises
    AuthorityBindingError(error_code, ...). A fresh publish fsyncs the
    written bytes before closing the descriptor, then returns
    (payload, True)."""

    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")

    try:
        descriptor = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        existing = read_authoritative_json(path, error_code=error_code)
        if any(existing.get(field) != payload.get(field) for field in identity_fields):
            raise AuthorityBindingError(error_code, f"a different payload was already published at {path}")
        return existing, False
    except OSError as exc:
        raise AuthorityBindingError(error_code, f"could not create {path}: {exc}") from exc

    try:
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    except OSError as exc:
        raise AuthorityBindingError(error_code, f"could not write {path}: {exc}") from exc
    finally:
        os.close(descriptor)

    return payload, True


def _resolve_capabilities(skill_runtime_module: Any, skill_id: str, provider: Optional[str]) -> Dict[str, bool]:
    """Wrap skill_runtime.effective_capabilities() and normalize every
    failure mode - unknown provider, missing capability, wrong type - into
    a single capability_binding_mismatch. Never lets KeyError, TypeError or
    ValueError escape the checkpoint."""

    try:
        caps = skill_runtime_module.effective_capabilities(skill_id, provider)
    except (KeyError, TypeError, ValueError) as exc:
        raise AuthorityBindingError(
            "capability_binding_mismatch",
            f"effective_capabilities({skill_id!r}, {provider!r}) raised {exc!r}",
        ) from exc

    if not isinstance(caps, dict) or set(caps) != set(CAPABILITY_KEYS):
        raise AuthorityBindingError(
            "capability_binding_mismatch",
            f"effective_capabilities({skill_id!r}, {provider!r}) must return exactly {CAPABILITY_KEYS}",
        )
    for key in CAPABILITY_KEYS:
        if not isinstance(caps[key], bool):
            raise AuthorityBindingError(
                "capability_binding_mismatch",
                f"effective_capabilities({skill_id!r}, {provider!r}).{key} must be an exact bool",
            )
    return caps


def _validate_skill_list(charter: Dict[str, Any], key: str) -> None:
    value = charter.get(key)
    if not isinstance(value, list):
        raise AuthorityBindingError("charter_binding_mismatch", f"charter.{key} must be a list")
    if not all(isinstance(item, str) and item for item in value):
        raise AuthorityBindingError("charter_binding_mismatch", f"charter.{key} must contain only non-empty strings")
    if len(value) != len(set(value)):
        raise AuthorityBindingError("charter_binding_mismatch", f"charter.{key} must not contain duplicates")


def _validate_charter_shape(charter: Dict[str, Any], *, require_approved: bool) -> None:
    if not isinstance(charter, dict):
        raise AuthorityBindingError("charter_binding_mismatch", "charter must be an object")
    if charter.get("report_type") != "conversational_mission_charter":
        raise AuthorityBindingError("charter_binding_mismatch", "unexpected report_type")

    version = charter.get("schema_version")
    if version != CHARTER_SCHEMA_VERSION:
        raise AuthorityBindingError("charter_schema_migration_required", f"charter schema_version={version!r}")

    missing = CHARTER_REQUIRED_KEYS - set(charter)
    if missing:
        raise AuthorityBindingError("charter_binding_mismatch", f"charter missing required keys: {sorted(missing)}")
    extra = set(charter) - CHARTER_ALLOWED_KEYS
    if extra:
        raise AuthorityBindingError("charter_binding_mismatch", f"charter has unexpected keys: {sorted(extra)}")

    state = charter.get("state")
    if require_approved and state != "approved":
        raise AuthorityBindingError("charter_binding_mismatch", "charter is not approved")
    if not require_approved and state not in {"proposed", "approved"}:
        raise AuthorityBindingError("charter_binding_mismatch", f"unexpected charter.state={state!r}")

    for key in ("charter_id", "mission_id", "decision_id", "decision_digest", "approval_phrase"):
        value = charter.get(key)
        if not isinstance(value, str) or not value:
            raise AuthorityBindingError("charter_binding_mismatch", f"charter.{key} must be a non-empty string")

    human_constraints = charter.get("human_constraints")
    if not isinstance(human_constraints, dict) or set(human_constraints) != set(REQUIRED_HUMAN_CONSTRAINT_KEYS):
        raise AuthorityBindingError(
            "charter_binding_mismatch",
            "charter.human_constraints must be an object with exactly the four closed boolean keys",
        )
    for key in REQUIRED_HUMAN_CONSTRAINT_KEYS:
        if not isinstance(human_constraints[key], bool):
            raise AuthorityBindingError("charter_binding_mismatch", f"charter.human_constraints.{key} must be a bool")

    for key in ("proposed_skills", "forbidden_skills", "allowed_followup_skills"):
        _validate_skill_list(charter, key)

    if not isinstance(charter.get("memory_write_allowed"), bool):
        raise AuthorityBindingError("charter_binding_mismatch", "charter.memory_write_allowed must be a bool")


def _validate_decision_shape(decision: Dict[str, Any]) -> None:
    if not isinstance(decision, dict):
        raise AuthorityBindingError("decision_binding_mismatch", "decision must be an object")
    if decision.get("report_type") != "hokage_mission_decision":
        raise AuthorityBindingError("decision_binding_mismatch", "unexpected report_type")

    version = decision.get("schema_version")
    if version != DECISION_SCHEMA_VERSION:
        raise AuthorityBindingError("charter_schema_migration_required", f"decision schema_version={version!r}")

    missing = DECISION_REQUIRED_KEYS - set(decision)
    if missing:
        raise AuthorityBindingError("decision_binding_mismatch", f"decision missing required keys: {sorted(missing)}")
    extra = set(decision) - DECISION_ALLOWED_KEYS
    if extra:
        raise AuthorityBindingError("decision_binding_mismatch", f"decision has unexpected keys: {sorted(extra)}")

    for key in ("decision_id", "mission_id"):
        value = decision.get(key)
        if not isinstance(value, str) or not value:
            raise AuthorityBindingError("decision_binding_mismatch", f"decision.{key} must be a non-empty string")

    selection = decision.get("selection")
    if not isinstance(selection, dict):
        raise AuthorityBindingError("decision_binding_mismatch", "decision.selection must be an object")

    missing_selection = SELECTION_REQUIRED_KEYS - set(selection)
    if missing_selection:
        raise AuthorityBindingError(
            "decision_binding_mismatch", f"decision.selection missing required keys: {sorted(missing_selection)}"
        )
    extra_selection = set(selection) - SELECTION_ALLOWED_KEYS
    if extra_selection:
        raise AuthorityBindingError(
            "decision_binding_mismatch", f"decision.selection has unexpected keys: {sorted(extra_selection)}"
        )
    for key in SELECTION_REQUIRED_KEYS:
        value = selection.get(key)
        if not isinstance(value, str) or not value:
            raise AuthorityBindingError("decision_binding_mismatch", f"decision.selection.{key} must be a non-empty string")


def _validate_receipt_shape(receipt: Dict[str, Any]) -> None:
    if not isinstance(receipt, dict):
        raise AuthorityBindingError("authority_receipt_invalid", "receipt must be an object")
    if receipt.get("report_type") != "conversational_mission_authority_receipt":
        raise AuthorityBindingError("authority_receipt_invalid", "unexpected report_type")

    version = receipt.get("schema_version")
    if version != AUTHORITY_RECEIPT_SCHEMA_VERSION:
        raise AuthorityBindingError("charter_schema_migration_required", f"receipt schema_version={version!r}")

    missing = RECEIPT_REQUIRED_KEYS - set(receipt)
    if missing:
        raise AuthorityBindingError("authority_receipt_invalid", f"receipt missing required keys: {sorted(missing)}")
    extra = set(receipt) - RECEIPT_ALLOWED_KEYS
    if extra:
        raise AuthorityBindingError("authority_receipt_invalid", f"receipt has unexpected keys: {sorted(extra)}")

    for key in RECEIPT_REQUIRED_KEYS:
        value = receipt.get(key)
        if not isinstance(value, str) or not value:
            raise AuthorityBindingError("authority_receipt_invalid", f"receipt.{key} must be a non-empty string")


def _validate_charter_skill_registration(charter: Dict[str, Any]) -> None:
    from . import skill_runtime  # local import: skill_runtime imports authority too

    proposed = set(charter["proposed_skills"])
    forbidden = set(charter["forbidden_skills"])
    followups = set(charter["allowed_followup_skills"])
    registered = set(skill_runtime.SKILLS)

    unregistered = (proposed | forbidden | followups) - registered
    if unregistered:
        raise AuthorityBindingError("skill_forbidden", f"unregistered skill ids: {sorted(unregistered)}")

    proposed_conflict = proposed & forbidden
    if proposed_conflict:
        raise AuthorityBindingError(
            "skill_forbidden", f"proposed_skills overlaps forbidden_skills: {sorted(proposed_conflict)}"
        )

    followup_conflict = followups & forbidden
    if followup_conflict:
        raise AuthorityBindingError(
            "skill_forbidden", f"allowed_followup_skills overlaps forbidden_skills: {sorted(followup_conflict)}"
        )


def write_authority_receipt(
    mission_dir: Path,
    *,
    mission_id: str,
    charter: Dict[str, Any],
    decision: Dict[str, Any],
    approved_at: str,
    approval_phrase: str,
) -> Dict[str, Any]:
    """Write the independent, write-once approval receipt. Called exactly
    once, immediately after mission_charter.json is written with
    state="approved". Publishes via O_CREAT|O_EXCL - an atomic, race-free
    exclusive create, not a check-then-replace - so two concurrent approval
    attempts cannot both "win": whichever process's O_CREAT|O_EXCL succeeds
    publishes the receipt: every other caller (including a retry of this
    same call) falls into the FileExistsError branch and must verify
    against what was actually published, never overwrite it. An identical
    re-publish attempt is treated as reentry and returns the ORIGINAL
    receipt (keeping its original approved_at); a differing one fails
    closed with authority_receipt_invalid."""

    _validate_charter_shape(charter, require_approved=True)
    _validate_decision_shape(decision)

    if not isinstance(mission_id, str) or not mission_id:
        raise AuthorityBindingError("mission_binding_mismatch", "mission_id argument must be a non-empty string")
    if mission_id != charter["mission_id"] or mission_id != decision["mission_id"]:
        raise AuthorityBindingError("mission_binding_mismatch", "mission_id argument does not match charter/decision")

    if charter["decision_id"] != decision["decision_id"]:
        raise AuthorityBindingError("decision_binding_mismatch", "charter.decision_id does not match decision.decision_id")
    if charter["decision_digest"] != canonical_digest(decision):
        raise AuthorityBindingError("decision_binding_mismatch", "charter.decision_digest does not match decision")

    if not isinstance(approved_at, str) or not approved_at:
        raise AuthorityBindingError("authority_receipt_invalid", "approved_at must be a non-empty string")
    if not isinstance(approval_phrase, str) or not approval_phrase:
        raise AuthorityBindingError("authority_receipt_invalid", "approval_phrase must be a non-empty string")
    if approval_phrase != charter["approval_phrase"]:
        raise AuthorityBindingError("authority_receipt_invalid", "approval_phrase does not match charter.approval_phrase")

    receipt = {
        "schema_version": AUTHORITY_RECEIPT_SCHEMA_VERSION,
        "report_type": "conversational_mission_authority_receipt",
        "mission_id": mission_id,
        "charter_id": charter["charter_id"],
        "charter_digest": canonical_digest(charter),
        "decision_id": decision["decision_id"],
        "decision_digest": canonical_digest(decision),
        "approved_at": approved_at,
        "approval_phrase_hash": hashlib.sha256(approval_phrase.encode("utf-8")).hexdigest(),
    }

    published, _ = publish_once(
        mission_authority_receipt_path(mission_dir),
        receipt,
        identity_fields=(
            "mission_id",
            "charter_id",
            "charter_digest",
            "decision_id",
            "decision_digest",
            "approval_phrase_hash",
        ),
        error_code="authority_receipt_invalid",
    )
    _validate_receipt_shape(published)
    return published


def verify_authority_receipt(mission_dir: Path, *, charter: Dict[str, Any], decision: Dict[str, Any]) -> None:
    """The actual detector for a coordinated rewrite of both authoritative
    files - something a two-file cross-check alone cannot prove."""

    path = mission_authority_receipt_path(mission_dir)
    if not path.is_file():
        raise AuthorityBindingError("authority_receipt_missing", f"no authority receipt at {path}")

    receipt = read_authoritative_json(path, error_code="authority_receipt_invalid")
    _validate_receipt_shape(receipt)

    if receipt["mission_id"] != charter["mission_id"] or receipt["mission_id"] != decision["mission_id"]:
        raise AuthorityBindingError("mission_binding_mismatch", "receipt.mission_id does not match charter/decision")
    if receipt["charter_id"] != charter["charter_id"]:
        raise AuthorityBindingError("charter_immutable_violation", "receipt.charter_id does not match current charter")
    if receipt["charter_digest"] != canonical_digest(charter):
        raise AuthorityBindingError("charter_immutable_violation", "mission_charter.json changed after approval")
    if receipt["decision_id"] != decision["decision_id"]:
        raise AuthorityBindingError("decision_immutable_violation", "receipt.decision_id does not match current decision")
    if receipt["decision_digest"] != canonical_digest(decision):
        raise AuthorityBindingError("decision_immutable_violation", "mission_decision.json changed after approval")


def load_authoritative_state(mission_dir: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Read both authoritative files fresh, validate their closed shape and
    skill registration, verify the Charter->Decision cross-reference and the
    mission_dir naming convention, then verify the independent receipt - in
    that order - before returning."""

    charter = read_authoritative_json(mission_charter_path(mission_dir), error_code="charter_binding_mismatch")
    _validate_charter_shape(charter, require_approved=True)
    _validate_charter_skill_registration(charter)

    decision = read_authoritative_json(mission_decision_path(mission_dir), error_code="decision_binding_mismatch")
    _validate_decision_shape(decision)

    if charter["decision_id"] != decision["decision_id"] or charter["decision_digest"] != canonical_digest(decision):
        raise AuthorityBindingError(
            "decision_binding_mismatch", "charter's recorded decision does not match mission_decision.json"
        )
    if charter["mission_id"] != decision["mission_id"]:
        raise AuthorityBindingError("mission_binding_mismatch", "charter.mission_id != decision.mission_id")
    if mission_dir.name != charter["mission_id"]:
        raise AuthorityBindingError(
            "mission_binding_mismatch", f"mission_dir name {mission_dir.name!r} != charter.mission_id"
        )

    verify_authority_receipt(mission_dir, charter=charter, decision=decision)

    return charter, decision


def validate_charter_construction(
    charter_candidate: Dict[str, Any],
    decision_candidate: Dict[str, Any],
) -> None:
    """Pre-persistence check on in-memory candidates only - no file I/O.
    Called from build_charter() before mission_charter.json exists (or
    while it still holds a stale prior proposal that must not be read)."""

    from . import skill_runtime  # local import: skill_runtime imports authority too

    _validate_charter_shape(charter_candidate, require_approved=False)
    _validate_decision_shape(decision_candidate)
    _validate_charter_skill_registration(charter_candidate)

    if charter_candidate["mission_id"] != decision_candidate["mission_id"]:
        raise AuthorityBindingError(
            "mission_binding_mismatch", "candidate charter.mission_id != candidate decision.mission_id"
        )
    if charter_candidate["decision_id"] != decision_candidate["decision_id"]:
        raise AuthorityBindingError(
            "decision_binding_mismatch", "candidate charter.decision_id does not match candidate decision"
        )
    if charter_candidate["decision_digest"] != canonical_digest(decision_candidate):
        raise AuthorityBindingError(
            "decision_binding_mismatch", "candidate charter.decision_digest does not match candidate decision"
        )

    human_constraints = charter_candidate["human_constraints"]
    selection = decision_candidate["selection"]
    provider = selection["provider"]

    if human_constraints["local_model_only"] and provider in {"codex", "claude"}:
        raise AuthorityBindingError("capability_constraint_violation", "provider_not_local")

    if charter_candidate["memory_write_allowed"] != (not human_constraints["private_context_restricted"]):
        raise AuthorityBindingError(
            "capability_constraint_violation",
            "memory_write_allowed must be the exact negation of private_context_restricted",
        )

    proposed = set(charter_candidate["proposed_skills"])
    followups = set(charter_candidate["allowed_followup_skills"])
    for skill_id in sorted(proposed | followups):
        provider_for_skill = provider if skill_id in skill_runtime.PROVIDER_SKILL_IDS else None
        caps = _resolve_capabilities(skill_runtime, skill_id, provider_for_skill)
        if human_constraints["mutation_forbidden"] and caps["mutates_files"]:
            raise AuthorityBindingError("capability_constraint_violation", f"{skill_id}: mutates_files")
        if human_constraints["network_blocked"] and caps["external_network"]:
            raise AuthorityBindingError("capability_constraint_violation", f"{skill_id}: external_network")
        if human_constraints["private_context_restricted"] and caps["private_context"]:
            raise AuthorityBindingError("capability_constraint_violation", f"{skill_id}: private_context")


def _validate_approval_evidence(action: Dict[str, Any]) -> None:
    evidence = action.get("evidence")
    if not isinstance(evidence, dict):
        raise AuthorityBindingError("approval_binding_mismatch", "action has no persisted approval evidence")

    approved_by = evidence.get("approved_by")
    approved_at = evidence.get("approved_at")
    recorded_hash = evidence.get("arguments_hash")

    if not isinstance(approved_by, str) or not approved_by:
        raise AuthorityBindingError("approval_binding_mismatch", "evidence.approved_by is missing or empty")
    if not isinstance(approved_at, str) or not approved_at:
        raise AuthorityBindingError("approval_binding_mismatch", "evidence.approved_at is missing or empty")
    if not isinstance(recorded_hash, str) or not recorded_hash:
        raise AuthorityBindingError("approval_binding_mismatch", "evidence.arguments_hash is missing or empty")
    if recorded_hash != action["arguments_hash"]:
        raise AuthorityBindingError(
            "approval_binding_mismatch", "evidence.arguments_hash does not match action.arguments_hash"
        )


_PHASES = frozenset({"queue_init", "followup_append", "restore", "pre_dispatch"})
_PHASE_TIER = {"queue_init": "initial", "followup_append": "followup"}


def validate_action_authority(*, mission_dir: Path, action: Dict[str, Any], phase: str) -> None:
    """The single post-approval authority checkpoint, validating the
    complete action - identity, argument integrity, recorded approval, and
    every charter/decision/mission/capability binding - not just its
    arguments. phase is one of "queue_init", "followup_append", "restore",
    "pre_dispatch" (see module docstring for what each phase does and does
    not require)."""

    from . import skill_runtime  # local import: skill_runtime imports authority too

    if phase not in _PHASES:
        raise ValueError(f"unknown phase: {phase!r}")
    if not isinstance(action, dict):
        raise AuthorityBindingError("arguments_hash_mismatch", "action must be an object")

    mission_id = _required(action, "mission_id", "mission_binding_mismatch")
    action_id = _required(action, "action_id", "arguments_hash_mismatch")
    skill_id = _required(action, "skill_id", "charter_binding_mismatch")
    action_tier = _required(action, "tier", "charter_binding_mismatch")
    plan_id = _required(action, "plan_id", "arguments_hash_mismatch")
    arguments = _required(action, "arguments", "arguments_hash_mismatch")
    arguments_hash = _required(action, "arguments_hash", "arguments_hash_mismatch")

    for name, value, code in (
        ("mission_id", mission_id, "mission_binding_mismatch"),
        ("action_id", action_id, "arguments_hash_mismatch"),
        ("skill_id", skill_id, "charter_binding_mismatch"),
        ("tier", action_tier, "charter_binding_mismatch"),
        ("plan_id", plan_id, "arguments_hash_mismatch"),
        ("arguments_hash", arguments_hash, "arguments_hash_mismatch"),
    ):
        if not isinstance(value, str) or not value:
            raise AuthorityBindingError(code, f"action.{name} must be a non-empty string")
    if not isinstance(arguments, dict):
        raise AuthorityBindingError("arguments_hash_mismatch", "action.arguments must be an object")
    if action_tier not in {"initial", "followup"}:
        raise AuthorityBindingError("charter_binding_mismatch", f"action.tier must be initial/followup, got {action_tier!r}")

    expected_tier = _PHASE_TIER.get(phase, action_tier)
    if action_tier != expected_tier:
        raise AuthorityBindingError(
            "charter_binding_mismatch", f"action.tier {action_tier!r} != expected {expected_tier!r} for phase {phase!r}"
        )

    expected_hash = compute_arguments_hash(arguments)
    if expected_hash != arguments_hash:
        raise AuthorityBindingError(
            "arguments_hash_mismatch", "action.arguments_hash does not match recomputed hash of action.arguments"
        )

    expected_action_id = compute_action_id(mission_id=mission_id, skill_id=skill_id, arguments_hash=arguments_hash)
    if expected_action_id != action_id:
        raise AuthorityBindingError(
            "arguments_hash_mismatch", "action.action_id does not match mission_id|skill_id|arguments_hash"
        )

    arg_skill_id = _required(arguments, "skill_id", "charter_binding_mismatch")
    arg_tier = _required(arguments, "tier", "charter_binding_mismatch")
    arg_plan_id = _required(arguments, "plan_id", "arguments_hash_mismatch")
    if not isinstance(arg_plan_id, str) or not arg_plan_id:
        raise AuthorityBindingError("arguments_hash_mismatch", "arguments.plan_id must be a non-empty string")
    if arg_skill_id != skill_id:
        raise AuthorityBindingError("charter_binding_mismatch", f"arguments.skill_id {arg_skill_id!r} != {skill_id!r}")
    if arg_tier != action_tier:
        raise AuthorityBindingError("charter_binding_mismatch", f"arguments.tier {arg_tier!r} != {action_tier!r}")
    if arg_plan_id != plan_id:
        raise AuthorityBindingError("arguments_hash_mismatch", f"arguments.plan_id {arg_plan_id!r} != {plan_id!r}")

    if phase == "pre_dispatch":
        status = action.get("status")
        if status != "running":
            raise AuthorityBindingError(
                "approval_binding_mismatch", f"action.status must be 'running' at dispatch, got {status!r}"
            )
        _validate_approval_evidence(action)
    elif phase == "restore" and action.get("status") == "running":
        _validate_approval_evidence(action)

    charter, decision = load_authoritative_state(mission_dir)

    if mission_id != charter["mission_id"]:
        raise AuthorityBindingError("mission_binding_mismatch", "action.mission_id != charter.mission_id")

    if skill_id not in skill_runtime.SKILLS:
        raise AuthorityBindingError("skill_forbidden", f"{skill_id} is not registered")
    if skill_id in set(charter["forbidden_skills"]):
        raise AuthorityBindingError("skill_forbidden", f"{skill_id} is forbidden by this charter")
    if action_tier == "initial":
        if skill_id not in set(charter["proposed_skills"]):
            raise AuthorityBindingError("skill_forbidden", f"{skill_id} was not proposed")
    else:
        if skill_id not in set(charter["allowed_followup_skills"]):
            raise AuthorityBindingError("skill_forbidden", f"{skill_id} is not an allowed follow-up for this charter")

    charter_id = _required(arguments, "charter_id", "charter_binding_mismatch")
    charter_digest = _required(arguments, "charter_digest", "charter_binding_mismatch")
    if charter_id != charter["charter_id"] or charter_digest != canonical_digest(charter):
        raise AuthorityBindingError("charter_binding_mismatch", "charter identity or digest changed")

    decision_id = _required(arguments, "decision_id", "decision_binding_mismatch")
    decision_digest = _required(arguments, "decision_digest", "decision_binding_mismatch")
    if decision_id != decision["decision_id"] or decision_digest != canonical_digest(decision):
        raise AuthorityBindingError("decision_binding_mismatch", "decision identity or digest changed")

    human_constraints = charter["human_constraints"]
    is_provider_skill = skill_id in skill_runtime.PROVIDER_SKILL_IDS

    if is_provider_skill:
        provider = _required(arguments, "provider", "provider_selection_mismatch")
        model = _required(arguments, "model", "model_selection_mismatch")
        strategy = _required(arguments, "strategy", "strategy_selection_mismatch")
        selection_source = _required(arguments, "selection_source", "selection_source_mismatch")
        external_network = _required(arguments, "external_network", "capability_binding_mismatch")
        local_transport = _required(arguments, "local_transport", "capability_binding_mismatch")

        for name, value, code in (
            ("provider", provider, "provider_selection_mismatch"),
            ("model", model, "model_selection_mismatch"),
            ("strategy", strategy, "strategy_selection_mismatch"),
            ("selection_source", selection_source, "selection_source_mismatch"),
        ):
            if not isinstance(value, str) or not value:
                raise AuthorityBindingError(code, f"arguments.{name} must be a non-empty string")
        if not isinstance(external_network, bool) or not isinstance(local_transport, bool):
            raise AuthorityBindingError(
                "capability_binding_mismatch", "external_network/local_transport must be exact booleans"
            )

        selection = decision["selection"]
        if provider != selection["provider"]:
            raise AuthorityBindingError("provider_selection_mismatch")
        if model != selection["model"]:
            raise AuthorityBindingError("model_selection_mismatch")
        if strategy != selection["strategy"]:
            raise AuthorityBindingError("strategy_selection_mismatch")
        if selection_source != selection["selection_source"]:
            raise AuthorityBindingError("selection_source_mismatch")

        caps = _resolve_capabilities(skill_runtime, skill_id, provider)
        if external_network != caps["external_network"] or local_transport != caps["local_transport"]:
            raise AuthorityBindingError("capability_binding_mismatch")
        if human_constraints["local_model_only"] and provider in {"codex", "claude"}:
            raise AuthorityBindingError("capability_constraint_violation", "provider_not_local")
    else:
        caps = _resolve_capabilities(skill_runtime, skill_id, None)

    if human_constraints["mutation_forbidden"] and caps["mutates_files"]:
        raise AuthorityBindingError("capability_constraint_violation", "mutates_files")
    if human_constraints["network_blocked"] and caps["external_network"]:
        raise AuthorityBindingError("capability_constraint_violation", "external_network")
    if human_constraints["private_context_restricted"] and caps["private_context"]:
        raise AuthorityBindingError("capability_constraint_violation", "private_context")
