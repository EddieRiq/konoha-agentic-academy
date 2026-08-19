"""Conversational skills, immutable approvals and beta-runtime bridge."""

from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from . import authority


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(payload: Dict[str, Any]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def arguments_hash(arguments: Dict[str, Any]) -> str:
    return hashlib.sha256(
        canonical_json(arguments).encode("utf-8")
    ).hexdigest()


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


SKILLS: Dict[str, Dict[str, Any]] = {
    "inspect_python_runtime": {
        "title": "Inspect Python runtime",
        "description": "Execute the planned Python version inspection.",
        "runtime_kind": "execute-command",
        "command_id": "inspect-python",
        "risk_level": "low",
        "mutates_files": False,
        "external_network": False,
        "local_transport": False,
        "private_context": False,
        "internal_token": "EXECUTE_APPROVED_COMMAND",
    },
    "inspect_git_status": {
        "title": "Inspect Git status",
        "description": "Execute the planned read-only Git status inspection.",
        "runtime_kind": "execute-command",
        "command_id": "inspect-git-status",
        "risk_level": "low",
        "mutates_files": False,
        "external_network": False,
        "local_transport": False,
        "private_context": False,
        "internal_token": "EXECUTE_APPROVED_COMMAND",
    },
    "run_deterministic_audit_checks": {
        "title": "Run deterministic audit checks",
        "description": (
            "Run repository tests before any local-model invocation."
        ),
        "runtime_kind": "orchestrator",
        "risk_level": "low",
        "mutates_files": False,
        "external_network": False,
        "local_transport": False,
        "private_context": False,
    },
    "run_technical_plan": {
        "title": "Produce a technical plan",
        "description": (
            "Invoke the decision-selected provider (codex or ollama) to "
            "produce a bounded technical plan."
        ),
        "runtime_kind": "orchestrator",
        "risk_level": "medium",
        "mutates_files": False,
        "external_network": False,
        "local_transport": False,
        "private_context": False,
    },
    "invoke_local_model_audit": {
        "title": "Run local-model repository audit",
        "description": (
            "Invoke the approved Ollama model after deterministic checks, "
            "then normalize and validate all findings."
        ),
        "runtime_kind": "orchestrator",
        "risk_level": "medium",
        "mutates_files": False,
        "external_network": False,
        "local_transport": False,
        "private_context": False,
    },
    "apply_validated_patch": {
        "title": "Apply validated documentation patch",
        "description": (
            "Apply only the exact approved patch plan and changed paths."
        ),
        "runtime_kind": "orchestrator",
        "risk_level": "medium",
        "mutates_files": True,
        "external_network": False,
        "local_transport": False,
        "private_context": False,
    },
    "run_post_patch_tests": {
        "title": "Run post-patch tests",
        "description": (
            "Run the full focused regression suite after patch application."
        ),
        "runtime_kind": "orchestrator",
        "risk_level": "low",
        "mutates_files": False,
        "external_network": False,
        "local_transport": False,
        "private_context": False,
    },
}


def validate_skills() -> List[str]:
    errors: List[str] = []
    allowed_kinds = {"execute-command", "orchestrator"}
    mutating_allowed = {"apply_validated_patch"}
    capability_keys = (
        "mutates_files",
        "external_network",
        "local_transport",
        "private_context",
    )

    for skill_id, skill in SKILLS.items():
        if skill["runtime_kind"] not in allowed_kinds:
            errors.append(f"{skill_id}: unsupported runtime kind")

        for key in capability_keys:
            if not isinstance(skill.get(key), bool):
                errors.append(f"{skill_id}: {key} must be an exact bool")

        if (
            skill.get("mutates_files") is True
            and skill_id not in mutating_allowed
        ):
            errors.append(
                f"{skill_id}: unexpected mutating skill"
            )
        if skill.get("external_network") is not False:
            errors.append(
                f"{skill_id}: external network must remain blocked"
            )

    return errors


PROVIDER_SKILL_IDS = frozenset({"run_technical_plan", "invoke_local_model_audit"})

_PROVIDER_CAPABILITIES: Dict[str, Dict[str, Dict[str, bool]]] = {
    "run_technical_plan": {
        "codex": {
            "mutates_files": False,
            "external_network": True,
            "local_transport": False,
            "private_context": False,
        },
        "ollama": {
            "mutates_files": False,
            "external_network": False,
            "local_transport": True,
            "private_context": False,
        },
    },
    "invoke_local_model_audit": {
        "ollama": {
            "mutates_files": False,
            "external_network": False,
            "local_transport": True,
            "private_context": False,
        },
    },
}


def effective_capabilities(
    skill_id: str, provider: Optional[str]
) -> Dict[str, bool]:
    """Single source of truth for a skill's capability profile, consumed by
    authority.py's fail-closed constraint checks. Provider skills resolve
    capability strictly from the provider actually selected - an unknown,
    missing or incompatible provider fails closed with ValueError, never a
    silent fallback to any other provider. Every other skill has one fixed,
    registry-declared profile and must be called with provider=None."""

    if skill_id not in SKILLS:
        raise KeyError(skill_id)

    if skill_id in PROVIDER_SKILL_IDS:
        if not isinstance(provider, str) or not provider:
            raise ValueError(f"{skill_id} requires an explicit provider")
        provider_caps = _PROVIDER_CAPABILITIES[skill_id].get(provider)
        if provider_caps is None:
            raise ValueError(
                f"{skill_id} does not support provider {provider!r}"
            )
        return dict(provider_caps)

    if provider is not None:
        raise ValueError(
            f"{skill_id} is not a provider skill; provider must be None"
        )

    skill = SKILLS[skill_id]
    return {
        "mutates_files": skill["mutates_files"],
        "external_network": skill["external_network"],
        "local_transport": skill["local_transport"],
        "private_context": skill["private_context"],
    }


def make_action(
    *,
    mission_id: str,
    plan_id: str,
    skill_id: str,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    skill = SKILLS[skill_id]
    digest = hashlib.sha256(
        (
            mission_id
            + "|"
            + skill_id
            + "|"
            + arguments_hash(arguments)
        ).encode("utf-8")
    ).hexdigest()[:10]
    identifier = f"action-{digest}"
    suffix = digest.upper()

    return {
        "schema_version": "1.0.0",
        "report_type": "conversational_action_proposal",
        "action_id": identifier,
        "mission_id": mission_id,
        "plan_id": plan_id,
        "skill_id": skill_id,
        "title": skill["title"],
        "description": skill["description"],
        "arguments": arguments,
        "arguments_hash": arguments_hash(arguments),
        "risk_level": skill["risk_level"],
        "mutates_files": skill["mutates_files"],
        # Legacy (schema_version 1.0.0) conversational_action_proposal
        # fields. Every skill the 1.0 flow ever proposes an action for is
        # network-blocked and outside private context - a fixed invariant,
        # not read from the registry's 1.1 capability schema.
        "network_required": False,
        "private_context_required": False,
        "status": "proposed",
        "approval_phrase": f"APROBAR ACCION-{suffix}",
        "rejection_phrase": f"RECHAZAR ACCION-{suffix}",
        "created_at": utc_now(),
        "authority": {
            "proposal_is_not_permission": True,
            "approval_is_bound_to_arguments_hash": True,
        },
    }


def verify_action_approval(
    action: Dict[str, Any],
    phrase: str,
) -> bool:
    if phrase.strip() != action["approval_phrase"]:
        return False
    return (
        arguments_hash(action["arguments"])
        == action["arguments_hash"]
    )


ACTION_SCHEMA_VERSION = "1.1.0"
_CLAIM_SCHEMA_VERSION = "1.1.0"
_CLAIM_REPORT_TYPE = "conversational_execution_claim"
_CLAIM_REQUIRED_KEYS = frozenset(
    {
        "schema_version",
        "report_type",
        "mission_id",
        "plan_id",
        "action_id",
        "arguments_hash",
        "approved_by",
        "approved_at",
        "claimed_at",
    }
)
_CLAIM_BINDING_FIELDS = ("mission_id", "plan_id", "action_id", "arguments_hash")


def action_queue_path(mission_dir: Path) -> Path:
    return mission_dir / "action_queue.json"


def _action_queue_lock_path(mission_dir: Path) -> Path:
    return mission_dir / "action_queue.lock"


def _action_claim_path(mission_dir: Path, action_id: str) -> Path:
    return mission_dir / "action_claims" / f"{action_id}.json"


def _action_lease_path(mission_dir: Path, action_id: str) -> Path:
    return mission_dir / "action_leases" / f"{action_id}.lock"


def interrupted_recovery_phrase(action_id: str) -> str:
    suffix = action_id.split("-", 1)[-1].upper()
    return f"BLOQUEAR INTERRUMPIDA-{suffix}"


class _QueueLock:
    """Exclusive flock over one mission's action queue file, held for the
    full duration of every queue-mutating operation so the read that feeds
    a CAS decision and the write that follows it never race with a
    concurrent caller. Released automatically by the OS if this process
    dies while holding it - deliberately relied on instead of any
    time-based expiry."""

    def __init__(self, mission_dir: Path, *, timeout_seconds: float = 10.0) -> None:
        self._path = _action_queue_lock_path(mission_dir)
        self._timeout_seconds = timeout_seconds
        self._fd: Optional[int] = None

    def __enter__(self) -> "_QueueLock":
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self._path), os.O_CREAT | os.O_RDWR)
        deadline = time.monotonic() + self._timeout_seconds
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN):
                    os.close(fd)
                    raise
                if time.monotonic() >= deadline:
                    os.close(fd)
                    raise authority.AuthorityBindingError(
                        "action_queue_lock_timeout",
                        f"could not acquire action queue lock at {self._path}",
                    ) from exc
                time.sleep(0.05)
        self._fd = fd
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if self._fd is not None:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
            finally:
                os.close(self._fd)
                self._fd = None
        return False


class _ExecutionLease:
    """Exclusive flock over one action's lease file, held for the entire
    dispatch. There is no time-based expiry and no takeover: the OS
    releases the flock automatically if this process dies mid-dispatch,
    and an interrupted action_id is never silently retried - it is
    recovered by a human via block_interrupted_action_checked() and a
    brand-new action."""

    def __init__(self, mission_dir: Path, action_id: str) -> None:
        self._path = _action_lease_path(mission_dir, action_id)
        self._fd: Optional[int] = None

    def acquire(self) -> "_ExecutionLease":
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self._path), os.O_CREAT | os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(fd)
            raise authority.AuthorityBindingError(
                "execution_still_active",
                f"execution lease already held for this action: {self._path}",
            ) from exc
        self._fd = fd
        return self

    def release(self) -> None:
        if self._fd is not None:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
            finally:
                os.close(self._fd)
                self._fd = None


def _lease_is_held(mission_dir: Path, action_id: str) -> bool:
    """Non-mutating probe: try (and immediately release) a non-blocking
    lock on the lease file. Used only by recovery to tell an actively
    running dispatch apart from one interrupted by process death."""

    path = _action_lease_path(mission_dir, action_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return True
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


def _publish_execution_claim(
    mission_dir: Path,
    action: Dict[str, Any],
    *,
    approved_by: str,
    approved_at: str,
) -> Dict[str, Any]:
    """Publish the write-once execution claim for this action. This call
    ends in exactly one of two ways: a fresh claim was just created and
    approval may proceed, or an execution_already_claimed error is raised
    - an existing claim is NEVER returned as though this approval attempt
    could continue. Only mission_id/plan_id/action_id/arguments_hash make
    two claims "the same" claim; approved_by/approved_at/claimed_at are
    evidence of the first claim only. identity_fields=() is passed to
    authority.publish_once() so it never performs its own match/raise -
    every existing-claim check below is ours, so the diagnostic code is
    always the specific one this design requires, not publish_once's
    single generic error_code."""

    payload = {
        "schema_version": _CLAIM_SCHEMA_VERSION,
        "report_type": _CLAIM_REPORT_TYPE,
        "mission_id": action["mission_id"],
        "plan_id": action["plan_id"],
        "action_id": action["action_id"],
        "arguments_hash": action["arguments_hash"],
        "approved_by": approved_by,
        "approved_at": approved_at,
        "claimed_at": utc_now(),
    }

    published, created = authority.publish_once(
        _action_claim_path(mission_dir, action["action_id"]),
        payload,
        identity_fields=(),
        error_code="execution_claim_invalid",
    )

    if not isinstance(published, dict) or set(published) != _CLAIM_REQUIRED_KEYS:
        raise authority.AuthorityBindingError(
            "execution_claim_invalid", "execution claim has an unexpected shape"
        )
    if (
        published.get("schema_version") != _CLAIM_SCHEMA_VERSION
        or published.get("report_type") != _CLAIM_REPORT_TYPE
    ):
        raise authority.AuthorityBindingError(
            "execution_claim_invalid",
            "execution claim schema_version/report_type mismatch",
        )
    if any(published.get(field) != payload[field] for field in _CLAIM_BINDING_FIELDS):
        raise authority.AuthorityBindingError(
            "execution_claim_binding_mismatch",
            "an execution claim already exists for this action_id with different binding",
        )

    if not created:
        raise authority.AuthorityBindingError(
            "execution_already_claimed",
            "an execution claim already exists for this action; recover it via "
            "find_recovery_candidates()/block_interrupted_action_checked(), never "
            "by re-approving",
        )

    return published


def verify_execution_claim(mission_dir: Path, action: Dict[str, Any]) -> Dict[str, Any]:
    """Fail-closed check that a persisted, write-once execution claim
    exists and is bound to this exact action. Called before pre_dispatch,
    before every running->completed/failed transition, before restore of a
    running action, and by recovery - never trusts action_queue.json alone
    for whether an action was really claimed."""

    path = _action_claim_path(mission_dir, action["action_id"])
    if not path.is_file():
        raise authority.AuthorityBindingError(
            "execution_claim_missing", f"no execution claim at {path}"
        )
    try:
        claim = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise authority.AuthorityBindingError(
            "execution_claim_invalid", f"execution claim unreadable: {exc}"
        ) from exc

    if not isinstance(claim, dict) or set(claim) != _CLAIM_REQUIRED_KEYS:
        raise authority.AuthorityBindingError(
            "execution_claim_invalid", "execution claim has an unexpected shape"
        )
    if (
        claim.get("schema_version") != _CLAIM_SCHEMA_VERSION
        or claim.get("report_type") != _CLAIM_REPORT_TYPE
    ):
        raise authority.AuthorityBindingError(
            "execution_claim_invalid",
            "execution claim schema_version/report_type mismatch",
        )

    if any(claim.get(field) != action.get(field) for field in _CLAIM_BINDING_FIELDS):
        raise authority.AuthorityBindingError(
            "execution_claim_binding_mismatch",
            "execution claim does not match this action's identity/arguments_hash",
        )

    evidence = action.get("evidence")
    if isinstance(evidence, dict):
        if (
            claim.get("approved_by") != evidence.get("approved_by")
            or claim.get("approved_at") != evidence.get("approved_at")
            or claim.get("arguments_hash") != evidence.get("arguments_hash")
        ):
            raise authority.AuthorityBindingError(
                "execution_claim_binding_mismatch",
                "execution claim does not match action.evidence",
            )

    return claim


def _build_action(
    *,
    mission_id: str,
    plan_id: str,
    skill_id: str,
    tier: str,
    charter: Dict[str, Any],
    decision: Dict[str, Any],
    extra_arguments: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build one 1.1 action proposal. arguments always binds charter_id,
    charter_digest, decision_id, decision_digest, plan_id, skill_id, tier;
    provider skills additionally bind provider, model, strategy,
    selection_source, external_network, local_transport - all read from
    the approved Decision's selection and effective_capabilities(), never
    invented here."""

    if skill_id not in SKILLS:
        raise KeyError(skill_id)

    arguments: Dict[str, Any] = dict(extra_arguments or {})
    arguments.update(
        {
            "skill_id": skill_id,
            "tier": tier,
            "plan_id": plan_id,
            "charter_id": charter["charter_id"],
            "charter_digest": authority.canonical_digest(charter),
            "decision_id": decision["decision_id"],
            "decision_digest": authority.canonical_digest(decision),
        }
    )

    if skill_id in PROVIDER_SKILL_IDS:
        selection = decision["selection"]
        provider = selection["provider"]
        caps = effective_capabilities(skill_id, provider)
        arguments.update(
            {
                "provider": provider,
                "model": selection["model"],
                "strategy": selection["strategy"],
                "selection_source": selection["selection_source"],
                "external_network": caps["external_network"],
                "local_transport": caps["local_transport"],
            }
        )

    args_hash = authority.compute_arguments_hash(arguments)
    action_id = authority.compute_action_id(
        mission_id=mission_id, skill_id=skill_id, arguments_hash=args_hash
    )
    suffix = action_id.split("-", 1)[-1].upper()
    skill = SKILLS[skill_id]

    return {
        "schema_version": ACTION_SCHEMA_VERSION,
        "report_type": "conversational_action_proposal",
        "action_id": action_id,
        "mission_id": mission_id,
        "plan_id": plan_id,
        "skill_id": skill_id,
        "tier": tier,
        "title": skill["title"],
        "description": skill["description"],
        "arguments": arguments,
        "arguments_hash": args_hash,
        "risk_level": skill["risk_level"],
        "status": "proposed",
        "approval_phrase": f"APROBAR ACCION-{suffix}",
        "rejection_phrase": f"RECHAZAR ACCION-{suffix}",
        "created_at": utc_now(),
        "authority": {
            "proposal_is_not_permission": True,
            "approval_is_bound_to_arguments_hash": True,
        },
    }


class ActionQueue:
    """The real 1.1 mission action runtime: one authority-checked queue per
    mission, protected end-to-end by a queue-level flock plus a per-action
    execution lease and a permanent, write-once execution claim. There is
    no generic public update()/save()/append_action() - every state
    transition goes through a narrow, CAS-checked method that re-validates
    authority and the execution claim before writing."""

    def __init__(self, mission_dir: Path) -> None:
        self.mission_dir = mission_dir.resolve()
        self.path = action_queue_path(self.mission_dir)

    def load(self) -> Dict[str, Any]:
        """Raw, unauthenticated read - never mutates, never validates
        schema_version. This is the window through which a legacy 1.0
        queue (or one at any other stale schema_version) stays visible,
        read-only; every mutating method below refuses to act on it."""

        if not self.path.exists():
            return {
                "schema_version": ACTION_SCHEMA_VERSION,
                "report_type": "conversational_action_queue",
                "actions": [],
                "authority": {
                    "action_proposals_are_not_permission": True
                },
            }
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write_locked(self, payload: Dict[str, Any]) -> None:
        payload["updated_at"] = utc_now()
        authority.atomic_write_json(self.path, payload)

    def _require_current_schema(self, payload: Dict[str, Any]) -> None:
        version = payload.get("schema_version")
        if version != ACTION_SCHEMA_VERSION:
            raise authority.AuthorityBindingError(
                "charter_schema_migration_required",
                f"action_queue schema_version={version!r}; this runtime only "
                f"executes {ACTION_SCHEMA_VERSION!r} queues",
            )

    def _find_locked(self, payload: Dict[str, Any], action_id: str) -> Dict[str, Any]:
        for action in payload.get("actions", []):
            if action.get("action_id") == action_id:
                return action
        raise KeyError(action_id)

    def next_pending(self) -> Optional[Dict[str, Any]]:
        for action in self.load().get("actions", []):
            if action.get("status") == "proposed":
                return action
        return None

    def _restore_locked(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._require_current_schema(payload)
        for action in payload.get("actions", []):
            authority.validate_action_authority(
                mission_dir=self.mission_dir, action=action, phase="restore"
            )
            if action.get("status") == "running":
                verify_execution_claim(self.mission_dir, action)
        return payload

    def restore(self) -> Dict[str, Any]:
        """Re-validate every action against current authority and claim
        state without ever auto-dispatching anything. A queue at a stale
        schema_version fails closed and stays visible only via load().
        Every running action must have a valid execution claim - a running
        action with no claim fails closed as execution_claim_missing, the
        same rule find_recovery_candidates() enforces."""

        with _QueueLock(self.mission_dir):
            return self._restore_locked(self.load())

    def initialize(self, *, mission_id: str, plan_id: str) -> Dict[str, Any]:
        with _QueueLock(self.mission_dir):
            if self.path.exists():
                # Any existing file - legacy schema, or a 1.1 queue with
                # zero actions because proposed_skills was empty - goes
                # through the same validated path. Never reinitialize
                # (and thereby overwrite) a queue just because it happens
                # to have no actions yet; _restore_locked() is what
                # actually enforces "legacy stays read-only".
                return self._restore_locked(self.load())

            charter, decision = authority.load_authoritative_state(self.mission_dir)
            if charter["mission_id"] != mission_id:
                raise authority.AuthorityBindingError(
                    "mission_binding_mismatch",
                    "initialize() mission_id does not match the approved charter",
                )

            actions = [
                _build_action(
                    mission_id=mission_id,
                    plan_id=plan_id,
                    skill_id=skill_id,
                    tier="initial",
                    charter=charter,
                    decision=decision,
                )
                for skill_id in charter["proposed_skills"]
            ]
            for action in actions:
                authority.validate_action_authority(
                    mission_dir=self.mission_dir, action=action, phase="queue_init"
                )

            payload = {
                "schema_version": ACTION_SCHEMA_VERSION,
                "report_type": "conversational_action_queue",
                "mission_id": mission_id,
                "plan_id": plan_id,
                "actions": actions,
                "authority": {
                    "action_proposals_are_not_permission": True,
                    "approval_is_bound_to_arguments_hash": True,
                },
            }
            self._write_locked(payload)
            return payload

    def append_action_checked(
        self,
        *,
        mission_id: str,
        plan_id: str,
        skill_id: str,
        extra_arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        with _QueueLock(self.mission_dir):
            payload = self.load()
            self._require_current_schema(payload)
            if payload.get("mission_id") != mission_id:
                raise authority.AuthorityBindingError(
                    "mission_binding_mismatch",
                    "append_action_checked() mission_id does not match the queue",
                )

            charter, decision = authority.load_authoritative_state(self.mission_dir)
            candidate = _build_action(
                mission_id=mission_id,
                plan_id=plan_id,
                skill_id=skill_id,
                tier="followup",
                charter=charter,
                decision=decision,
                extra_arguments=extra_arguments,
            )

            for existing in payload.get("actions", []):
                if existing.get("action_id") != candidate["action_id"]:
                    continue
                if (
                    existing.get("arguments_hash") != candidate["arguments_hash"]
                    or existing.get("arguments") != candidate["arguments"]
                    or existing.get("mission_id") != candidate["mission_id"]
                    or existing.get("plan_id") != candidate["plan_id"]
                    or existing.get("skill_id") != candidate["skill_id"]
                    or existing.get("tier") != candidate["tier"]
                ):
                    raise authority.AuthorityBindingError(
                        "arguments_hash_mismatch",
                        f"action_id {candidate['action_id']} already exists with different content",
                    )
                authority.validate_action_authority(
                    mission_dir=self.mission_dir, action=existing, phase="restore"
                )
                return existing

            authority.validate_action_authority(
                mission_dir=self.mission_dir, action=candidate, phase="followup_append"
            )
            payload.setdefault("actions", []).append(candidate)
            self._write_locked(payload)
            return candidate

    def _transition_locked(
        self,
        payload: Dict[str, Any],
        action_id: str,
        *,
        expected_status: str,
        expected_arguments_hash: str,
        new_status: str,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        action = self._find_locked(payload, action_id)
        if action.get("status") != expected_status:
            raise authority.AuthorityBindingError(
                "approval_binding_mismatch",
                f"expected status {expected_status!r}, found {action.get('status')!r}",
            )
        if action.get("arguments_hash") != expected_arguments_hash:
            raise authority.AuthorityBindingError(
                "arguments_hash_mismatch",
                "expected_arguments_hash does not match the current action",
            )
        verify_execution_claim(self.mission_dir, action)
        action["status"] = new_status
        action["updated_at"] = utc_now()
        if evidence is not None:
            action["evidence"] = evidence
        self._write_locked(payload)
        return action

    def _mark_blocked_locked(
        self,
        payload: Dict[str, Any],
        action_id: str,
        *,
        expected_status: str,
        expected_arguments_hash: str,
        reason: str,
    ) -> Dict[str, Any]:
        action = self._find_locked(payload, action_id)
        if action.get("status") != expected_status:
            raise authority.AuthorityBindingError(
                "approval_binding_mismatch",
                f"expected status {expected_status!r}, found {action.get('status')!r}",
            )
        if action.get("arguments_hash") != expected_arguments_hash:
            raise authority.AuthorityBindingError(
                "arguments_hash_mismatch",
                "expected_arguments_hash does not match the current action",
            )
        verify_execution_claim(self.mission_dir, action)
        authority.validate_action_authority(
            mission_dir=self.mission_dir, action=action, phase="restore"
        )
        action["status"] = "blocked"
        action["updated_at"] = utc_now()
        action["blocked_reason"] = reason
        self._write_locked(payload)
        return action

    def approve_and_dispatch(
        self,
        action_id: str,
        *,
        phrase: str,
        approved_by: str,
        dispatch: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """The only path from an approved proposal to a completed or failed
        action. Fixed order: queue lock -> authority restore check -> claim
        publish_once -> execution lease -> CAS proposed->running -> persist
        approval evidence -> authority pre_dispatch -> verify claim ->
        release queue lock -> dispatch while holding only the lease ->
        reacquire queue lock -> CAS running->completed/failed -> release
        lease in finally. A pre_dispatch/claim failure after the claim is
        published never reverts to "proposed": the claim and evidence are
        preserved and the action is marked blocked instead, so a retry is
        always a brand-new action_id, never a takeover of this one. A
        second approve_and_dispatch() on the same proposed+claimed action
        (e.g. after a crash between claim and the running CAS) fails
        closed at the claim publish step with execution_already_claimed -
        only human recovery can move that action forward."""

        approved_at = utc_now()

        with _QueueLock(self.mission_dir):
            payload = self.load()
            self._require_current_schema(payload)
            proposal = self._find_locked(payload, action_id)

            authority.validate_action_authority(
                mission_dir=self.mission_dir, action=proposal, phase="restore"
            )
            if proposal.get("status") != "proposed":
                raise authority.AuthorityBindingError(
                    "approval_binding_mismatch",
                    f"only a proposed action can be dispatched, found {proposal.get('status')!r}",
                )
            if phrase.strip() != proposal.get("approval_phrase"):
                raise authority.AuthorityBindingError(
                    "approval_binding_mismatch",
                    "approval phrase does not match action.approval_phrase",
                )
            if not isinstance(approved_by, str) or not approved_by:
                raise authority.AuthorityBindingError(
                    "approval_binding_mismatch", "approved_by must be a non-empty string"
                )

            arguments_hash = proposal["arguments_hash"]
            _publish_execution_claim(
                self.mission_dir, proposal, approved_by=approved_by, approved_at=approved_at
            )

            lease = _ExecutionLease(self.mission_dir, action_id)
            lease.acquire()
            try:
                evidence = {
                    "approved_by": approved_by,
                    "approved_at": approved_at,
                    "arguments_hash": arguments_hash,
                }
                action = self._transition_locked(
                    payload,
                    action_id,
                    expected_status="proposed",
                    expected_arguments_hash=arguments_hash,
                    new_status="running",
                    evidence=evidence,
                )
                try:
                    authority.validate_action_authority(
                        mission_dir=self.mission_dir, action=action, phase="pre_dispatch"
                    )
                    verify_execution_claim(self.mission_dir, action)
                except Exception:
                    self._mark_blocked_locked(
                        payload,
                        action_id,
                        expected_status="running",
                        expected_arguments_hash=arguments_hash,
                        reason="authority or claim check failed after claim and before dispatch",
                    )
                    raise
            except Exception:
                lease.release()
                raise
        # Queue lock released; the execution lease alone protects this
        # action_id while dispatch() actually runs.

        try:
            result = dispatch(action)
        except Exception:
            with _QueueLock(self.mission_dir):
                failed_payload = self.load()
                self._require_current_schema(failed_payload)
                self._transition_locked(
                    failed_payload,
                    action_id,
                    expected_status="running",
                    expected_arguments_hash=arguments_hash,
                    new_status="failed",
                    evidence={**evidence, "result": None},
                )
            raise
        else:
            with _QueueLock(self.mission_dir):
                completed_payload = self.load()
                self._require_current_schema(completed_payload)
                completed = self._transition_locked(
                    completed_payload,
                    action_id,
                    expected_status="running",
                    expected_arguments_hash=arguments_hash,
                    new_status="completed",
                    evidence={**evidence, "result": result},
                )
            return completed
        finally:
            lease.release()

    def reject_action_checked(
        self,
        action_id: str,
        *,
        phrase: str,
        expected_arguments_hash: str,
    ) -> Dict[str, Any]:
        """Only a proposed action with no execution claim can be rejected
        directly. A claimed action must go through recovery instead - a
        claim is permanent evidence that a human already approved it. A
        corrupt or mis-bound claim is never swallowed as an ordinary
        "already claimed" outcome - it fails with its own specific code."""

        with _QueueLock(self.mission_dir):
            payload = self.load()
            self._require_current_schema(payload)
            action = self._find_locked(payload, action_id)

            if action.get("status") != "proposed":
                raise authority.AuthorityBindingError(
                    "approval_binding_mismatch",
                    f"only a proposed action can be rejected, found {action.get('status')!r}",
                )
            if action.get("arguments_hash") != expected_arguments_hash:
                raise authority.AuthorityBindingError(
                    "arguments_hash_mismatch",
                    "expected_arguments_hash does not match the current action",
                )

            if _action_claim_path(self.mission_dir, action_id).exists():
                verify_execution_claim(self.mission_dir, action)
                raise authority.AuthorityBindingError(
                    "execution_already_claimed",
                    "a claimed action cannot be rejected directly; use recovery",
                )

            authority.validate_action_authority(
                mission_dir=self.mission_dir, action=action, phase="restore"
            )

            if phrase.strip() != action.get("rejection_phrase"):
                raise authority.AuthorityBindingError(
                    "approval_binding_mismatch",
                    "rejection phrase does not match action.rejection_phrase",
                )

            action["status"] = "rejected"
            action["updated_at"] = utc_now()
            self._write_locked(payload)
            return action

    def find_recovery_candidates(self) -> List[Dict[str, Any]]:
        """Classify every non-terminal action for human recovery review.
        Never mutates the queue and never retries a running action_id
        automatically - a claim/lease combination only ever routes to a
        human decision.

        proposed, no claim            -> normal_pending
        proposed, valid claim         -> interrupted_claimed
        running, valid claim, leased  -> active_running
        running, valid claim, free    -> interrupted_running
        running, no claim             -> raises execution_claim_missing

        A running action can only ever reach that status through
        approve_and_dispatch(), which always publishes the claim before
        the CAS to running - so a running action with no claim is
        corruption, never a normal recovery case, and is never returned as
        a recovery_status label. A corrupt or mis-bound claim likewise
        fails closed instead of being classified."""

        with _QueueLock(self.mission_dir):
            payload = self.load()
            self._require_current_schema(payload)
            candidates: List[Dict[str, Any]] = []

            for action in payload.get("actions", []):
                status = action.get("status")
                if status not in {"proposed", "running"}:
                    continue

                action_id = action["action_id"]
                has_claim = _action_claim_path(self.mission_dir, action_id).exists()

                if status == "proposed":
                    if has_claim:
                        verify_execution_claim(self.mission_dir, action)
                        recovery_status = "interrupted_claimed"
                    else:
                        recovery_status = "normal_pending"
                else:
                    if not has_claim:
                        raise authority.AuthorityBindingError(
                            "execution_claim_missing",
                            f"running action {action_id} has no execution claim; "
                            "this is corruption, not a recoverable state",
                        )
                    verify_execution_claim(self.mission_dir, action)
                    recovery_status = (
                        "active_running"
                        if _lease_is_held(self.mission_dir, action_id)
                        else "interrupted_running"
                    )

                candidates.append(
                    {
                        "action_id": action_id,
                        "status": status,
                        "recovery_status": recovery_status,
                    }
                )

            return candidates

    def block_interrupted_action_checked(
        self,
        action_id: str,
        *,
        phrase: str,
        expected_arguments_hash: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Human-directed recovery for an action left interrupted mid-flow
        (proposed+claim, or running with a free lease). Requires an
        explicit human phrase bound to this action_id -
        interrupted_recovery_phrase(action_id) - reason/hash alone is never
        enough to block an interrupted action. Moves it straight to
        blocked - never back to proposed, never re-dispatched under the
        same action_id. A retry is a brand-new action with a fresh
        approval."""

        with _QueueLock(self.mission_dir):
            payload = self.load()
            self._require_current_schema(payload)
            action = self._find_locked(payload, action_id)
            status = action.get("status")

            if status not in {"proposed", "running"}:
                raise authority.AuthorityBindingError(
                    "approval_binding_mismatch",
                    f"only a proposed or running action can be recovered, found {status!r}",
                )
            if action.get("arguments_hash") != expected_arguments_hash:
                raise authority.AuthorityBindingError(
                    "arguments_hash_mismatch",
                    "expected_arguments_hash does not match the current action",
                )
            if phrase.strip() != interrupted_recovery_phrase(action_id):
                raise authority.AuthorityBindingError(
                    "approval_binding_mismatch",
                    "recovery phrase does not match interrupted_recovery_phrase(action_id)",
                )

            verify_execution_claim(self.mission_dir, action)
            authority.validate_action_authority(
                mission_dir=self.mission_dir, action=action, phase="restore"
            )

            lease = _ExecutionLease(self.mission_dir, action_id)
            lease.acquire()
            try:
                verify_execution_claim(self.mission_dir, action)
                return self._mark_blocked_locked(
                    payload,
                    action_id,
                    expected_status=status,
                    expected_arguments_hash=expected_arguments_hash,
                    reason=reason,
                )
            finally:
                lease.release()


class RuntimeBridge:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.runtime = (
            self.repo_root
            / "tools"
            / "beta_runtime"
            / "run_konoha_beta.py"
        )
        if not self.runtime.exists():
            raise FileNotFoundError(self.runtime)

    def invoke(self, arguments: List[str]) -> Dict[str, Any]:
        completed = subprocess.run(
            [sys.executable, str(self.runtime), *arguments, "--json"],
            cwd=str(self.repo_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=False,
            timeout=300,
        )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Beta runtime returned non-JSON output: "
                + completed.stdout[-1000:]
                + " stderr="
                + completed.stderr[-1000:]
            ) from exc

        if completed.returncode != 0:
            blockers = payload.get("blockers", [])
            raise RuntimeError(
                "Beta runtime failed: " + "; ".join(blockers)
            )
        if payload.get("status") in {"failed", "blocked", "error"}:
            raise RuntimeError(
                f"Beta runtime status={payload.get('status')}"
            )
        return payload

    def bootstrap(
        self,
        *,
        workspace_root: Path,
        mission_id: str,
        plan_id: str,
        actor: str,
        objective: str,
    ) -> Dict[str, Any]:
        start = self.invoke(
            [
                "start",
                "--workspace-root",
                str(workspace_root),
                "--mission-id",
                mission_id,
                "--title",
                "Conversational Hokage mission",
                "--task",
                objective,
                "--task-domain",
                "conversational",
                "--actor",
                actor,
                "--confirm-start",
                "--approval-token",
                "START_BETA_MISSION",
                "--force",
            ]
        )
        plan = self.invoke(
            [
                "plan",
                "--workspace-root",
                str(workspace_root),
                "--mission-id",
                mission_id,
                "--plan-id",
                plan_id,
                "--task-domain",
                "conversational",
                "--confirm-plan",
                "--approval-token",
                "PLAN_BETA_MISSION",
                "--force",
            ]
        )
        return {"start": start, "plan": plan}

    def review(
        self,
        *,
        workspace_root: Path,
        mission_id: str,
        review_id: str,
        review_summary: str,
        human_actor: str,
    ) -> Dict[str, Any]:
        return self.invoke(
            [
                "review",
                "--workspace-root",
                str(workspace_root),
                "--mission-id",
                mission_id,
                "--review-id",
                review_id,
                "--decision",
                "approved",
                "--review-summary",
                review_summary,
                "--human-actor",
                human_actor,
                "--confirm-review",
                "--approval-token",
                "RECORD_BETA_REVIEW",
                "--force",
            ]
        )

    def invoke_teachback(
        self,
        arguments: List[str],
    ) -> Dict[str, Any]:
        tool = (
            self.repo_root
            / "tools"
            / "teachback"
            / "manage_teachback.py"
        )
        if not tool.exists():
            raise FileNotFoundError(tool)

        completed = subprocess.run(
            [sys.executable, str(tool), *arguments, "--json"],
            cwd=str(self.repo_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=False,
            timeout=120,
        )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Teachback tool returned non-JSON output: "
                + completed.stdout[-1000:]
                + " stderr="
                + completed.stderr[-1000:]
            ) from exc

        if completed.returncode != 0:
            blocker = payload.get("blocker")
            raise RuntimeError(
                "Teachback failed: "
                + str(blocker or payload)
            )
        if payload.get("status") != "passed":
            raise RuntimeError(
                "Teachback semantic status is not passed."
            )
        return payload

    def record_teachback(
        self,
        *,
        workspace_root: Path,
        mission_id: str,
        teachback_id: str,
        achieved_level: int,
        summary: str,
        human_actor: str,
        source_execution: str,
        source_review: str,
    ) -> Dict[str, Any]:
        return self.invoke_teachback(
            [
                "record",
                "--workspace-root",
                str(workspace_root),
                "--mission-id",
                mission_id,
                "--teachback-id",
                teachback_id,
                "--result",
                "passed",
                "--achieved-level",
                str(achieved_level),
                "--completed-by-user",
                "--summary",
                summary,
                "--human-evidence",
                summary,
                "--source-execution",
                source_execution,
                "--source-review",
                source_review,
                "--human-actor",
                human_actor,
                "--confirm-record",
                "--approval-token",
                "RECORD_TEACHBACK_EVIDENCE",
            ]
        )

    def close(
        self,
        *,
        workspace_root: Path,
        mission_id: str,
        memory_root: Path,
        closure_id: str,
        execution_evidence: str,
        review_evidence: str,
        teachback_record: str,
        human_actor: str,
        closure_reason: str,
    ) -> Dict[str, Any]:
        return self.invoke(
            [
                "close",
                "--workspace-root",
                str(workspace_root),
                "--mission-id",
                mission_id,
                "--memory-root",
                str(memory_root),
                "--closure-id",
                closure_id,
                "--execution-evidence",
                execution_evidence,
                "--review-evidence",
                review_evidence,
                "--teachback-record",
                teachback_record,
                "--human-actor",
                human_actor,
                "--closure-reason",
                closure_reason,
                "--confirm-close",
                "--approval-token",
                "CLOSE_MISSION_WITH_TEACHBACK",
                "--force",
            ]
        )

    def execute(
        self,
        *,
        workspace_root: Path,
        action: Dict[str, Any],
    ) -> Dict[str, Any]:
        skill = SKILLS[action["skill_id"]]

        if skill["runtime_kind"] != "execute-command":
            # Fail closed before any subprocess is spawned. There is no
            # implicit provider fallback here: orchestrator-kind skills
            # (run_deterministic_audit_checks, run_technical_plan,
            # invoke_local_model_audit, apply_validated_patch,
            # run_post_patch_tests) are dispatched by orchestration logic
            # outside RuntimeBridge, never by this generic bridge.
            raise authority.AuthorityBindingError(
                "skill_forbidden",
                "RuntimeBridge.execute() only dispatches execute-command "
                f"skills; {action['skill_id']!r} has runtime_kind="
                f"{skill['runtime_kind']!r}",
            )

        return self.invoke(
            [
                "execute-command",
                "--workspace-root",
                str(workspace_root),
                "--mission-id",
                action["mission_id"],
                "--plan-id",
                action["plan_id"],
                "--command-id",
                skill["command_id"],
                "--result-id",
                f"{action['action_id']}-result",
                "--working-dir",
                str(self.repo_root),
                "--timeout",
                "60",
                "--confirm-execute",
                "--approval-token",
                skill["internal_token"],
                "--force",
            ]
        )
