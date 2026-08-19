#!/usr/bin/env python3
"""Konoha Conversational Hokage — v3.5.0-RC1."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_IMPORT_ROOT = SCRIPT_DIR.parents[1]
if str(REPO_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_IMPORT_ROOT))

from tools.hokage_orchestrator.audit_flow import (  # noqa: E402
    AuditFlowError,
    RealSupervisedAuditFlow,
)
from tools.hokage_orchestrator import authority  # noqa: E402
from tools.hokage_orchestrator.charter import (  # noqa: E402
    approve_charter_1_1,
    build_charter_1_1,
    charter_id,
    charter_markdown,
    real_proposed_skills,
)
from tools.hokage_orchestrator.continuity import (  # noqa: E402
    ContinuityStore,
    read_json,
    utc_now,
    write_json,
)
from tools.hokage_orchestrator.intent import (  # noqa: E402
    interpret_intent,
    validate_intent,
)
from tools.hokage_orchestrator.lifecycle import (  # noqa: E402
    LifecycleStore,
)
from tools.hokage_orchestrator.bootstrap_runtime import (  # noqa: E402
    HokageBootstrapRuntime,
)
from tools.hokage_orchestrator import skill_runtime  # noqa: E402
from tools.hokage_orchestrator.skill_runtime import (  # noqa: E402
    ActionQueue,
    RuntimeBridge,
    validate_skills,
)
from tools.hokage_orchestrator.mission_decision import build_decision_1_1  # noqa: E402
from tools.hokage_orchestrator.village_runtime import VillageInitializer

DEV_VERSION = "3.6.0"


def discover_repo_root(start: Path) -> Path:
    configured = os.environ.get("KONOHA_REPO_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()

    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() and (
            candidate / "tools" / "konoha_cli.py"
        ).exists():
            return candidate
    return current


def is_git_ignored(repo_root: Path, relative: str) -> bool:
    try:
        completed = subprocess.run(
            ["git", "check-ignore", "-q", "--", relative],
            cwd=str(repo_root),
            check=False,
            shell=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def default_private_roots(repo_root: Path) -> tuple[Path, Path]:
    configured_state = os.environ.get("KONOHA_STATE_ROOT")
    configured_memory = os.environ.get("KONOHA_MEMORY_ROOT")
    if configured_state or configured_memory:
        return (
            Path(
                configured_state
                or repo_root / "memory" / "local" / "runtime"
            ).resolve(),
            Path(
                configured_memory
                or repo_root / "memory" / "local" / "obsidian"
            ).resolve(),
        )

    kirigakure = repo_root / "alliance" / "kirigakure"
    if kirigakure.exists() and is_git_ignored(
        repo_root,
        "alliance/kirigakure",
    ):
        return (
            (kirigakure / "memory" / "runtime").resolve(),
            (kirigakure / "memory" / "obsidian").resolve(),
        )

    return (
        (repo_root / "memory" / "local" / "runtime").resolve(),
        (repo_root / "memory" / "local" / "obsidian").resolve(),
    )


def safe_slug(value: str) -> str:
    """Return a beta-runtime-safe ASCII identifier fragment."""

    ascii_text = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", errors="ignore")
        .decode("ascii")
        .lower()
    )
    normalized = re.sub(r"[^a-z0-9_-]+", "-", ascii_text)
    slug = normalized.strip("-_")[:48] or "mission"
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", slug):
        raise ValueError(f"Unsafe generated slug: {slug!r}")
    return slug


def mission_id_for_intent(intent: Dict[str, Any]) -> str:
    """mission_id must exist before the Decision/Charter do (Decision 1.1
    needs it as an input), so this is derived from intent alone via the
    same charter_id(intent) formula build_charter_1_1() uses internally -
    identical intent always yields the identical mission_id regardless of
    which builder ends up constructing the Charter."""

    suffix = charter_id(intent).split("-", 1)[-1]
    return (
        f"mission-{suffix}-"
        f"{safe_slug(intent['objective'])[:28]}"
    )


_MUTATION_FORBIDDEN_CONSTRAINT = "no filesystem mutation before explicit approval"
_NETWORK_BLOCKED_CONSTRAINT = "network access blocked"
_LOCAL_MODEL_ONLY_CONSTRAINT = "local model only"
_PRIVATE_CONTEXT_RESTRICTED_CONSTRAINT = "private context requires a scoped approval"


def human_constraints_from_intent(intent: Dict[str, Any]) -> Dict[str, bool]:
    """Deterministic mapping from intent.py's existing free-text
    constraints vocabulary to the closed 4-key human_constraints shape
    Decision/Charter 1.1 require. intent.py is out of this block's scope
    to extend, so this reads only tokens interpret_intent() already
    produces - no new vocabulary is invented."""

    constraints = set(intent.get("constraints", []))
    return {
        "mutation_forbidden": _MUTATION_FORBIDDEN_CONSTRAINT in constraints,
        "network_blocked": _NETWORK_BLOCKED_CONSTRAINT in constraints,
        "local_model_only": _LOCAL_MODEL_ONLY_CONSTRAINT in constraints,
        "private_context_restricted": (
            _PRIVATE_CONTEXT_RESTRICTED_CONSTRAINT in constraints
        ),
    }


class _PendingCharterMissionResolutionError(Exception):
    """Raised by _pending_charter_mission_id() when the pending Charter's
    mission_id cannot be resolved unambiguously. code is one of
    CHARTER_REJECTION_BINDING_MISMATCH (two or more distinct non-null
    candidates) or CHARTER_REJECTION_MISSION_UNKNOWN (zero candidates) -
    never a guess, never derived from charter_id."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def render_charter(charter: Dict[str, Any]) -> str:
    lines = [
        "",
        "Hokage:",
        "Entendí la misión y preparé un Charter.",
        "",
        f"Charter: {charter['charter_id']}",
        f"Riesgo: {charter['risk_level']}",
        f"Objetivo: {charter['objective']}",
        "",
        "Targets:",
    ]
    lines.extend(f"- {item}" for item in charter["scope"]["targets"])
    lines += ["", "Skills propuestos:"]
    lines.extend(f"- {item}" for item in charter["proposed_skills"])
    lines += [
        "",
        "Este Charter no autoriza ejecución.",
        f"Para aprobar: {charter['approval_phrase']}",
        f"Para rechazar: {charter['rejection_phrase']}",
        "",
    ]
    return "\n".join(lines)


def render_action(action: Dict[str, Any]) -> str:
    provider = action.get("arguments", {}).get("provider")
    caps = skill_runtime.effective_capabilities(action["skill_id"], provider)
    return "\n".join(
        [
            "",
            "Hokage propone una acción:",
            "",
            f"Acción: {action['action_id']}",
            f"Skill: {action['skill_id']}",
            f"Descripción: {action['description']}",
            f"Riesgo: {action['risk_level']}",
            f"Mutación: {caps['mutates_files']}",
            f"Red: {caps['external_network']}",
            f"Contexto privado: {caps['private_context']}",
            f"Argument hash: {action['arguments_hash'][:16]}",
            "",
            "La propuesta no es permiso.",
            f"Para aprobar: {action['approval_phrase']}",
            f"Para rechazar: {action['rejection_phrase']}",
            "",
        ]
    )



def render_review(review: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "",
            "Hokage propone review humano:",
            "",
            f"Review: {review['review_id']}",
            f"Resumen: {review['review_summary']}",
            f"Evidencia: {review['execution_evidence']}",
            "",
            "La propuesta no es aprobación humana.",
            f"Para aprobar: {review['approval_phrase']}",
            f"Para pedir cambios: {review['changes_phrase']}",
            "",
        ]
    )


def render_teachback(request: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "",
            "Hokage solicita Teachback:",
            "",
            f"Nivel requerido: {request['required_level']}",
            request["prompt"],
            "",
            "Respondé en una sola entrada:",
            "TEACHBACK: <tu explicación>",
            "",
            "La explicación debe ser tuya. "
            "Un resumen generado no completa Teachback.",
            "",
        ]
    )


def render_closure(closure: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "",
            "Hokage propone cierre de misión:",
            "",
            f"Cierre: {closure['closure_id']}",
            f"Razón: {closure['closure_reason']}",
            f"Ejecución: {closure['execution_evidence']}",
            f"Review: {closure['review_evidence']}",
            f"Teachback: {closure['teachback_record']}",
            "",
            "El cierre no autoriza trabajo nuevo.",
            f"Para cerrar: {closure['approval_phrase']}",
            "",
        ]
    )



def render_model_grant(grant: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "",
            "Hokage solicita un grant local de modelo:",
            "",
            f"Grant: {grant['grant_id']}",
            f"Proveedor: {grant['provider']}",
            f"Modelo: {grant['model']}",
            f"Scope: {grant['scope']}",
            f"Acción: {grant['action_id']}",
            f"Arguments hash: {grant['arguments_hash'][:16]}",
            "",
            "El grant es de un solo uso.",
            "No autoriza descargas ni red externa.",
            "El output del modelo será evidencia solamente.",
            f"Para aprobar: {grant['approval_phrase']}",
            "",
        ]
    )


def render_patch_proposal(proposal: Dict[str, Any]) -> str:
    preview = proposal.get("patch_preview") or "(sin cambios)"
    lines = [
        "",
        "Hokage propone un patch validado:",
        "",
        f"Patch: {proposal['patch_id']}",
        f"Operaciones: {proposal['operation_count']}",
        (
            "Paths: "
            + ", ".join(proposal.get("changed_paths", []))
        ),
        f"SHA-256: {proposal['patch_sha256']}",
        "",
        "Patch exacto:",
        "",
        preview.rstrip(),
        "",
        "La propuesta no es permiso.",
        "El approval queda ligado al SHA-256 mostrado.",
    ]
    if proposal.get("approval_phrase"):
        lines.extend(
            [
                f"Para aplicar: {proposal['approval_phrase']}",
                f"Para rechazar: {proposal['rejection_phrase']}",
            ]
        )
    else:
        lines.append("No hay un patch validado para aplicar.")
    lines.append("")
    return "\n".join(lines)


def render_audit_summary(result: Dict[str, Any]) -> str:
    audit = result["audit"]
    proposal = result["patch_proposal"]
    usage = audit.get("usage", {})
    return "\n".join(
        [
            "",
            "Hokage completó el audit local:",
            "",
            f"Modelo: {audit.get('model')}",
            (
                "Tokens: input="
                f"{usage.get('input_tokens')} "
                "output="
                f"{usage.get('output_tokens')}"
            ),
            (
                "Hallazgos sugeridos por modelo: "
                f"{len(audit.get('model_suggested_issues', []))}"
            ),
            (
                "Hallazgos validados: "
                f"{len(audit.get('validated_issues', []))}"
            ),
            (
                "Hallazgos suprimidos: "
                f"{len(audit.get('suppressed_issues', []))}"
            ),
            f"Operaciones de patch: {proposal['operation_count']}",
            "",
            "El modelo no autorizó ninguna modificación.",
            "",
        ]
    )

class ConversationalHokage:
    def __init__(
        self,
        *,
        repo_root: Path,
        workspace_root: Path,
        state_root: Path,
        memory_root: Path,
        actor: str,
        local_model: str = "qwen2.5-coder:7b",
        json_mode: bool = False,
    ) -> None:
        errors = validate_skills()
        if errors:
            raise ValueError(
                "Invalid conversational skill registry: "
                + "; ".join(errors)
            )

        self.repo_root = repo_root.resolve()
        self.workspace_root = workspace_root.resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.memory_root = memory_root.resolve()
        self.actor = actor
        self.village = VillageInitializer(
            repo_root=self.repo_root,
        )
        self.village_status = self.village.inspect()
        self.local_model = local_model
        self.json_mode = json_mode

        self.continuity = ContinuityStore(
            state_root=state_root,
            obsidian_root=self.memory_root,
            actor=actor,
        )
        self.runtime: Optional[RuntimeBridge] = None
        self.pending_charter: Optional[Dict[str, Any]] = None
        self.pending_decision: Optional[Dict[str, Any]] = None
        self.active_mission: Optional[Dict[str, Any]] = None
        self.action_queue: Optional[ActionQueue] = None
        self.lifecycle: Optional[LifecycleStore] = None
        self.audit_flow: Optional[RealSupervisedAuditFlow] = None
        self.resume_diagnostic: Optional[str] = None
        self.bootstrap_runtime = HokageBootstrapRuntime(
            state_root=state_root,
            actor=actor,
        )
        self.bootstrap_evidence = self.bootstrap_runtime.collect()
        self.local_model_configuration = (
            self.bootstrap_runtime.local_model_configuration(
                self.bootstrap_evidence["snapshot"]
            )
        )
        if self.local_model_configuration["selected_model"]:
            self.local_model = self.local_model_configuration[
                "selected_model"
            ]
            local_model = self.local_model
        # The authoritative, persisted Decision 1.1 for an APPROVED
        # Charter only - set once via restore()/approve_charter(), never
        # recomputed. self.pending_decision (below, set elsewhere) is a
        # distinct, narrower concept: the Decision belonging to a Charter
        # that is still only proposed, not yet approved.
        self.authoritative_decision: Optional[Dict[str, Any]] = None
        self.restore()

    def mission_dir(self, mission_id: str) -> Path:
        return self.workspace_root / "missions" / mission_id

    def _make_audit_flow(
        self,
        mission_id: str,
    ) -> RealSupervisedAuditFlow:
        return RealSupervisedAuditFlow(
            repo_root=self.repo_root,
            workspace_root=self.workspace_root,
            mission_dir=self.mission_dir(mission_id),
            memory_root=self.memory_root,
            mission_id=mission_id,
            actor=self.actor,
            model=self.local_model,
        )

    def restore(self) -> None:
        user_state = self.continuity.load_user_state()
        active_id = user_state.get("active_mission_id")
        if not active_id:
            return

        active_path = self.continuity.active_mission_path
        if not active_path.exists():
            return

        active = read_json(active_path)
        mission_id = active.get("mission_id")
        if mission_id != active_id:
            return

        self.active_mission = active
        mission_dir = self.mission_dir(mission_id)
        self.action_queue = ActionQueue(mission_dir)
        self.lifecycle = LifecycleStore(mission_dir)
        self.audit_flow = self._make_audit_flow(mission_id)

        charter_path = authority.mission_charter_path(mission_dir)
        if not charter_path.exists():
            return
        charter = read_json(charter_path)

        if charter.get("state") == "proposed":
            self.pending_charter = charter
            decision_path = authority.mission_decision_path(mission_dir)
            if decision_path.exists():
                self.pending_decision = read_json(decision_path)
            return

        if charter.get("state") == "approved":
            # Re-derive and re-validate the full authority chain, then
            # restore the queue - never auto-dispatching anything. A
            # failure here is surfaced through status_payload(), not
            # raised out of the constructor. The re-derived Decision is
            # exactly what was persisted and validated - never recomputed
            # or fabricated - and is kept so /status can show it without
            # re-deriving it a second time.
            try:
                _, decision = authority.load_authoritative_state(mission_dir)
                self.authoritative_decision = decision
                self.action_queue.restore()
            except authority.AuthorityBindingError as exc:
                self.resume_diagnostic = f"{exc.code}: {exc.detail}"

    def propose(self, request: str) -> Dict[str, Any]:
        intent = interpret_intent(request, self.repo_root)
        errors = validate_intent(intent, self.repo_root)
        if errors:
            return {
                "status": "needs_context",
                "status_code": "INTENT_VALIDATION_FAILED",
                "errors": errors,
            }

        mission_id = mission_id_for_intent(intent)
        human_constraints = human_constraints_from_intent(intent)

        proposed_skills = real_proposed_skills(intent)
        provider_skill_ids = sorted(
            set(proposed_skills) & skill_runtime.PROVIDER_SKILL_IDS
        )
        if len(provider_skill_ids) > 1:
            return {
                "status": "failed",
                "status_code": "AMBIGUOUS_PROVIDER_SKILL",
                "provider_skill_ids": provider_skill_ids,
            }
        provider_skill_id = provider_skill_ids[0] if provider_skill_ids else None

        decision = build_decision_1_1(
            mission_id=mission_id,
            intent=intent,
            bootstrap_snapshot=self.bootstrap_evidence,
            local_model=self.local_model,
            human_constraints=human_constraints,
            provider_skill_id=provider_skill_id,
        )
        charter = build_charter_1_1(
            intent,
            decision,
            actor=self.actor,
            human_constraints=human_constraints,
        )
        mission_dir = self.mission_dir(mission_id)
        mission_dir.mkdir(parents=True, exist_ok=True)

        intent_path = mission_dir / "conversational_intent.json"
        charter_path = authority.mission_charter_path(mission_dir)
        charter_md = mission_dir / "charter.md"

        write_json(intent_path, intent)
        authority.atomic_write_json(
            authority.mission_decision_path(mission_dir), decision
        )
        authority.atomic_write_json(charter_path, charter)
        charter_md.write_text(
            charter_markdown(charter),
            encoding="utf-8",
            newline="\n",
        )

        self.pending_charter = charter
        self.pending_decision = decision
        self.active_mission = self.continuity.set_active_mission(
            mission_id=mission_id,
            charter_path=charter_path,
            state_name="charter_proposed",
        )
        self.action_queue = ActionQueue(mission_dir)
        self.lifecycle = LifecycleStore(mission_dir)
        self.audit_flow = self._make_audit_flow(mission_id)

        return {
            "status": "passed",
            "status_code": "CHARTER_PROPOSED",
            "mission_id": mission_id,
            "charter": charter,
            "paths": {
                "intent": str(intent_path),
                "charter": str(charter_path),
                "charter_json": str(charter_path),
            },
            "authority": {
                "charter_is_not_permission": True,
                "no_tool_execution_occurred": True,
            },
        }

    def approve_charter(self, phrase: str) -> Dict[str, Any]:
        if self.pending_charter is None or self.pending_decision is None:
            return {
                "status": "failed",
                "status_code": "NO_PENDING_CHARTER",
            }

        mission_id = self.active_mission["mission_id"]
        mission_dir = self.mission_dir(mission_id)

        try:
            charter = approve_charter_1_1(
                mission_dir,
                self.pending_charter,
                self.pending_decision,
                approval_phrase=phrase,
                approved_by=self.actor,
            )
        except authority.AuthorityBindingError as exc:
            return {
                "status": "failed",
                "status_code": "CHARTER_APPROVAL_MISMATCH",
                "expected": self.pending_charter["approval_phrase"],
                "detail": f"{exc.code}: {exc.detail}",
            }

        plan_id = f"{mission_id}-plan"

        # RuntimeBridge.execute() shells out to run_konoha_beta.py's
        # execute-command, which looks the actual command string up from
        # plans/{plan_id}_command_proposals.json by command_id - that
        # file, not the action's own arguments, is where the command
        # comes from. bootstrap() must still run to produce it; its
        # return value is otherwise unused here - ActionQueue.initialize()
        # takes no runtime_proposals/local_model arguments in 1.1.
        if self.runtime is None:
            self.runtime = RuntimeBridge(self.repo_root)
        self.runtime.bootstrap(
            workspace_root=self.workspace_root,
            mission_id=mission_id,
            plan_id=plan_id,
            actor=self.actor,
            objective=charter["objective"],
        )

        self.action_queue = ActionQueue(mission_dir)
        queue = self.action_queue.initialize(
            mission_id=mission_id,
            plan_id=plan_id,
        )
        self.lifecycle = LifecycleStore(mission_dir)
        self.audit_flow = self._make_audit_flow(mission_id)

        # The Decision that was just bound into the receipt is now the
        # authoritative one for this mission - captured here, not
        # recomputed, exactly the object approve_charter_1_1() validated.
        self.authoritative_decision = self.pending_decision

        self.pending_charter = None
        self.pending_decision = None
        self.active_mission = self.continuity.update_active_state(
            "awaiting_action_approval"
        )

        return {
            "status": "passed",
            "status_code": "CHARTER_APPROVED_ACTIONS_PROPOSED",
            "mission_id": mission_id,
            "plan_id": plan_id,
            "action_count": len(queue.get("actions", [])),
            "next_action": self.action_queue.next_pending(),
            "authority": {
                "charter_approval_does_not_authorize_actions": True,
                "action_proposals_are_not_permission": True,
            },
        }

    def _pending_charter_mission_id(self) -> str:
        """Resolve the pending Charter's mission_id from every available
        source of evidence, never by deriving/guessing it from
        charter_id. Fails closed (raises _PendingCharterMissionResolution
        Error) if the available sources disagree or if none exist -
        either way, the caller must not mutate continuity."""

        candidates = []

        if self.pending_charter is not None:
            value = self.pending_charter.get("mission_id")
            if value:
                candidates.append(value)

        if isinstance(self.active_mission, dict):
            value = self.active_mission.get("mission_id")
            if value:
                candidates.append(value)

        user_state_id = self.continuity.load_user_state().get(
            "active_mission_id"
        )
        if user_state_id:
            candidates.append(user_state_id)

        distinct = set(candidates)
        if len(distinct) > 1:
            raise _PendingCharterMissionResolutionError(
                "CHARTER_REJECTION_BINDING_MISMATCH"
            )
        if not distinct:
            raise _PendingCharterMissionResolutionError(
                "CHARTER_REJECTION_MISSION_UNKNOWN"
            )
        return next(iter(distinct))

    def reject_charter(self, phrase: str) -> Dict[str, Any]:
        if self.pending_charter is None:
            return {
                "status": "failed",
                "status_code": "NO_PENDING_CHARTER",
            }

        if phrase.strip() != self.pending_charter["rejection_phrase"]:
            return {
                "status": "failed",
                "status_code": "CHARTER_REJECTION_MISMATCH",
                "expected": self.pending_charter["rejection_phrase"],
            }

        try:
            mission_id = self._pending_charter_mission_id()
        except _PendingCharterMissionResolutionError as exc:
            return {
                "status": "failed",
                "status_code": exc.code,
            }

        # mission_charter.json/mission_decision.json/conversational_
        # intent.json stay on disk untouched as historical evidence -
        # authority.py's Charter schema has no "rejected" state at the
        # Charter level by design (rejection is an action-level state,
        # never a charter-level one). Only continuity's own active-
        # mission tracking is cleared here, which is what actually made
        # a rejected mission reappear as active on restart.
        self.continuity.mark_mission_rejected(mission_id=mission_id)

        self.pending_charter = None
        self.pending_decision = None
        self.active_mission = None

        return {
            "status": "passed",
            "status_code": "CHARTER_REJECTED",
            "mission_id": mission_id,
        }

    def next_action(self) -> Optional[Dict[str, Any]]:
        if self.action_queue is None:
            return None
        return self.action_queue.next_pending()

    def current_review(self) -> Optional[Dict[str, Any]]:
        if self.lifecycle is None:
            return None
        proposal = self.lifecycle.load_optional(
            self.lifecycle.review_proposal_path
        )
        if proposal and proposal.get("status") == "proposed":
            return proposal
        return None

    def current_teachback(self) -> Optional[Dict[str, Any]]:
        if self.lifecycle is None:
            return None
        request = self.lifecycle.load_optional(
            self.lifecycle.teachback_request_path
        )
        if (
            request
            and request.get("status")
            == "awaiting_user_explanation"
        ):
            return request
        return None

    def current_closure(self) -> Optional[Dict[str, Any]]:
        if self.lifecycle is None:
            return None
        closure = self.lifecycle.load_optional(
            self.lifecycle.closure_proposal_path
        )
        if closure and closure.get("status") == "proposed":
            return closure
        return None

    def current_model_grant(
        self,
        action: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        action = action or self.next_action()
        if (
            action is None
            or action.get("skill_id")
            != "invoke_local_model_audit"
            or self.audit_flow is None
        ):
            return None
        return self.audit_flow.build_model_grant(action)

    def current_patch_proposal(
        self,
        action: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        action = action or self.next_action()
        if (
            action is None
            or action.get("skill_id")
            != "apply_validated_patch"
            or self.audit_flow is None
        ):
            return None
        proposal = self.audit_flow.load_patch_proposal()
        if proposal and proposal.get("status") == "proposed":
            return proposal
        return None

    def _prepare_review(self) -> Dict[str, Any]:
        if self.action_queue is None or self.lifecycle is None:
            raise ValueError(
                "Action queue and lifecycle are required."
            )
        review = self.lifecycle.build_review_proposal(
            self.action_queue.load(),
            self.actor,
        )
        self.active_mission = self.continuity.update_active_state(
            "awaiting_review_approval"
        )
        return review

    # proposed+claim ("interrupted_claimed") and a held lease are never a
    # wrong approval phrase - only human recovery
    # (ActionQueue.find_recovery_candidates() /
    # block_interrupted_action_checked()) resolves them, never a plain
    # approve_and_dispatch() retry.
    _RECOVERY_SIGNAL_CODES = frozenset(
        {"execution_already_claimed", "execution_still_active"}
    )
    # A missing/invalid/mis-bound execution claim is authority corruption,
    # not a recoverable state - it must never be routed through
    # find_recovery_candidates() as though it were an ordinary
    # interruption.
    _INTEGRITY_FAILURE_CODES = frozenset(
        {
            "execution_claim_missing",
            "execution_claim_invalid",
            "execution_claim_binding_mismatch",
        }
    )

    def _find_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        if self.action_queue is None:
            return None
        for candidate in self.action_queue.load().get("actions", []):
            if candidate.get("action_id") == action_id:
                return candidate
        return None

    def _recovery_candidates(self) -> Optional[list]:
        if self.action_queue is None:
            return None
        try:
            return self.action_queue.find_recovery_candidates()
        except authority.AuthorityBindingError:
            return None

    def _append_post_patch_tests(
        self,
        action: Dict[str, Any],
    ) -> Dict[str, Any]:
        if self.action_queue is None:
            raise ValueError("Action queue is missing.")
        return self.action_queue.append_action_checked(
            mission_id=action["mission_id"],
            plan_id=action["plan_id"],
            skill_id="run_post_patch_tests",
            extra_arguments={
                "suite_profile": "v3.6.0_post_patch",
                "external_network": "blocked",
            },
        )

    def _append_followups_if_needed(
        self,
        completed: Dict[str, Any],
    ) -> None:
        skill_id = completed["skill_id"]
        if skill_id == "invoke_local_model_audit":
            result = completed.get("evidence", {}).get("result") or {}
            proposal = result.get("patch_proposal") or {}
            if proposal.get("operation_count", 0) > 0:
                patch_sha256 = proposal.get("patch_sha256")
                patch_id = proposal.get("patch_id")
                if not patch_sha256 or not patch_id:
                    raise ValueError(
                        "Patch proposal is missing its binding material "
                        "(patch_sha256/patch_id); refusing to propose "
                        "apply_validated_patch without it."
                    )
                self.action_queue.append_action_checked(
                    mission_id=completed["mission_id"],
                    plan_id=completed["plan_id"],
                    skill_id="apply_validated_patch",
                    extra_arguments={
                        "patch_id": patch_id,
                        "patch_sha256": patch_sha256,
                        "patch_plan": proposal["patch_plan"],
                        "changed_paths": proposal["changed_paths"],
                    },
                )
            else:
                self._append_post_patch_tests(completed)
        elif skill_id == "apply_validated_patch":
            self._append_post_patch_tests(completed)

    @staticmethod
    def _patch_binding_matches(
        action: Dict[str, Any],
        proposal: Dict[str, Any],
    ) -> bool:
        expected = action["arguments"]
        return (
            expected.get("patch_id") == proposal.get("patch_id")
            and expected.get("patch_sha256") == proposal.get("patch_sha256")
            and expected.get("changed_paths") == proposal.get("changed_paths")
        )

    def _dispatch_for(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """The single orchestrator dispatcher. execute-command skills go
        to RuntimeBridge.execute(); every orchestrator-kind skill is
        routed here explicitly and never reaches RuntimeBridge. Only
        called by ActionQueue.approve_and_dispatch(), after the queue
        lock, execution claim and lease are already established - the
        specialized audit_flow checks below are deterministic validations
        of that already-authorized dispatch, never a second authority. No
        specialized helper here re-derives or auto-satisfies a phrase of
        its own: the only human execution gate is the action["approval_
        phrase"] ActionQueue.approve_and_dispatch() already verified."""

        skill_id = action["skill_id"]
        skill = skill_runtime.SKILLS[skill_id]

        if skill["runtime_kind"] == "execute-command":
            if self.runtime is None:
                self.runtime = RuntimeBridge(self.repo_root)
            return self.runtime.execute(
                workspace_root=self.workspace_root,
                action=action,
            )

        if self.audit_flow is None:
            raise AuditFlowError("Audit flow is missing.")

        if skill_id == "run_deterministic_audit_checks":
            payload = self.audit_flow.run_deterministic_checks()
            return {
                "status": "passed",
                "summary": "Deterministic checks passed before model use.",
                "output_paths": [
                    str(self.audit_flow.deterministic_report_path)
                ],
                "report": payload,
            }

        if skill_id == "run_post_patch_tests":
            payload = self.audit_flow.run_post_patch_tests()
            return {
                "status": "passed",
                "summary": "Post-patch tests passed.",
                "output_paths": [
                    str(self.audit_flow.post_patch_tests_path)
                ],
                "report": payload,
            }

        if skill_id == "invoke_local_model_audit":
            # Model output is evidence only: run_model_audit() below only
            # ever produces a proposal for human review, it never applies
            # anything. build_model_grant() binds grant["approval_phrase"]
            # to this same action's approval_phrase - reusing the
            # already-human-verified value below is not a second
            # authority, it is the same one.
            grant = self.audit_flow.build_model_grant(action)
            self.audit_flow.approve_model_grant(
                action=action,
                phrase=action["approval_phrase"],
            )
            audit_result = self.audit_flow.run_model_audit(action=action)
            return {
                "status": "passed",
                "summary": (
                    "Real Ollama audit completed and findings were "
                    "deterministically classified."
                ),
                "output_paths": audit_result["output_paths"],
                "audit": audit_result["audit"],
                "patch_proposal": audit_result["patch_proposal"],
            }

        if skill_id == "apply_validated_patch":
            proposal = self.audit_flow.load_patch_proposal()
            if proposal is None:
                raise AuditFlowError("Patch proposal is missing.")
            # The action's own binding material must still match the
            # live proposal exactly - this is what keeps the generic
            # action["approval_phrase"] indirectly bound to this exact
            # patch (patch_sha256/patch_id/changed_paths -> arguments ->
            # arguments_hash -> action_id -> approval_phrase).
            # proposal["approval_phrase"] itself is never used as
            # evidence of human approval here - _apply_patch_locked()
            # applies the patch with no phrase check of its own, since
            # the human already authorized this exact action via
            # ActionQueue.approve_and_dispatch().
            if not self._patch_binding_matches(action, proposal):
                raise AuditFlowError(
                    "Patch proposal no longer matches the action's bound "
                    "patch_id/patch_sha256/changed_paths."
                )
            patch_result = self.audit_flow._apply_patch_locked(proposal)
            return {
                "status": "passed",
                "summary": "Exact validated patch applied.",
                "output_paths": patch_result["output_paths"],
                "changed_paths": patch_result["changed_paths"],
            }

        if skill_id == "run_technical_plan":
            # KNOWN_LIMITATION: run_technical_plan is registered and
            # dispatch-routed, and its Decision 1.1 provider/model/
            # strategy binding is validated below, but there is no
            # TechnicalPlanFlow/provider-path producer anywhere in this
            # repository yet. Never silently sent to RuntimeBridge.
            # execute(); never inferred/faked here. Not currently
            # reachable via real_proposed_skills() in this block, so
            # this only matters for a future, explicitly-scoped block.
            provider = action["arguments"].get("provider")
            model = action["arguments"].get("model")
            strategy = action["arguments"].get("strategy")
            if not provider or not model or not strategy:
                raise AuditFlowError(
                    "run_technical_plan action is missing its Decision "
                    "1.1 provider/model/strategy binding."
                )
            raise AuditFlowError(
                "run_technical_plan has no orchestrator implementation "
                "in this repository yet."
            )

        raise AuditFlowError(
            f"No orchestrator dispatcher for skill_id={skill_id!r}."
        )

    def approve_action(
        self,
        action: Dict[str, Any],
        phrase: str,
    ) -> Dict[str, Any]:
        if self.action_queue is None:
            return {
                "status": "failed",
                "status_code": "NO_ACTION_QUEUE",
            }

        action_id = action["action_id"]
        try:
            completed = self.action_queue.approve_and_dispatch(
                action_id,
                phrase=phrase,
                approved_by=self.actor,
                dispatch=self._dispatch_for,
            )
        except authority.AuthorityBindingError as exc:
            detail = f"{exc.code}: {exc.detail}"
            if exc.code == "approval_binding_mismatch":
                return {
                    "status": "failed",
                    "status_code": "ACTION_APPROVAL_MISMATCH",
                    "expected": action["approval_phrase"],
                    "detail": detail,
                }
            if exc.code in self._RECOVERY_SIGNAL_CODES:
                return {
                    "status": "failed",
                    "status_code": "RECOVERY_REQUIRED",
                    "detail": detail,
                    "recovery": self._recovery_candidates(),
                }
            if exc.code in self._INTEGRITY_FAILURE_CODES:
                current = self._find_action(action_id)
                self.active_mission = self.continuity.update_active_state(
                    "action_failed"
                )
                return {
                    "status": "failed",
                    "status_code": "AUTHORITY_INTEGRITY_FAILURE",
                    "action": current,
                    "blockers": [detail],
                }
            current = self._find_action(action_id)
            self.active_mission = self.continuity.update_active_state(
                "action_failed"
            )
            return {
                "status": "failed",
                "status_code": "ACTION_BLOCKED",
                "action": current,
                "blockers": [detail],
            }
        except Exception as exc:
            # approve_and_dispatch() already persisted running->failed
            # and re-raised the dispatcher's own exception - this never
            # mutates status again, it only reloads and reports it.
            current = self._find_action(action_id)
            self.active_mission = self.continuity.update_active_state(
                "action_failed"
            )
            return {
                "status": "failed",
                "status_code": "ACTION_EXECUTION_FAILED",
                "action": current,
                "blockers": [str(exc)],
            }

        self._append_followups_if_needed(completed)
        next_action = self.next_action()
        review = None

        if next_action:
            self.active_mission = self.continuity.update_active_state(
                "awaiting_action_approval"
            )
        else:
            review = self._prepare_review()

        return {
            "status": "passed",
            "status_code": "ACTION_COMPLETED",
            "action": completed,
            "next_action": next_action,
            "review_proposal": review,
            "authority": {
                "result_is_evidence_only": True,
                "result_does_not_authorize_next_action": True,
            },
        }

    def reject_action(
        self,
        action: Dict[str, Any],
        phrase: str,
    ) -> Dict[str, Any]:
        if self.action_queue is None:
            return {
                "status": "failed",
                "status_code": "NO_ACTION_QUEUE",
            }

        try:
            rejected = self.action_queue.reject_action_checked(
                action["action_id"],
                phrase=phrase,
                expected_arguments_hash=action["arguments_hash"],
            )
        except authority.AuthorityBindingError as exc:
            detail = f"{exc.code}: {exc.detail}"
            if exc.code in self._RECOVERY_SIGNAL_CODES:
                return {
                    "status": "failed",
                    "status_code": "RECOVERY_REQUIRED",
                    "detail": detail,
                    "recovery": self._recovery_candidates(),
                }
            if exc.code in self._INTEGRITY_FAILURE_CODES:
                return {
                    "status": "failed",
                    "status_code": "AUTHORITY_INTEGRITY_FAILURE",
                    "blockers": [detail],
                }
            return {
                "status": "failed",
                "status_code": "ACTION_REJECTION_MISMATCH",
                "expected": action["rejection_phrase"],
                "detail": detail,
            }

        if action["skill_id"] == "apply_validated_patch" and self.audit_flow:
            # State synchronization only, via the non-authorizing locked
            # helper - reject_action_checked() above was already the one
            # human rejection gate for this action. If the live proposal
            # no longer matches this action's bound patch_id/patch_sha256/
            # changed_paths, it belongs to a different/mutated patch and
            # is deliberately left untouched rather than synced.
            proposal = self.audit_flow.load_patch_proposal()
            if proposal is not None and self._patch_binding_matches(
                action, proposal
            ):
                self.audit_flow._reject_patch_locked(proposal)
            self._append_post_patch_tests(rejected)

        next_action = self.next_action()
        review = None
        if next_action:
            self.active_mission = self.continuity.update_active_state(
                "awaiting_action_approval"
            )
        else:
            review = self._prepare_review()

        return {
            "status": "passed",
            "status_code": "ACTION_REJECTED",
            "action": rejected,
            "next_action": next_action,
            "review_proposal": review,
        }

    def approve_review(
        self,
        review: Dict[str, Any],
        phrase: str,
    ) -> Dict[str, Any]:
        if phrase.strip() != review["approval_phrase"]:
            return {
                "status": "failed",
                "status_code": "REVIEW_APPROVAL_MISMATCH",
                "expected": review["approval_phrase"],
            }
        if self.runtime is None:
            self.runtime = RuntimeBridge(self.repo_root)
        if self.lifecycle is None:
            raise ValueError("Lifecycle store is missing.")

        runtime_result = self.runtime.review(
            workspace_root=self.workspace_root,
            mission_id=review["mission_id"],
            review_id=review["review_id"],
            review_summary=review["review_summary"],
            human_actor=self.actor,
        )
        recorded = self.lifecycle.mark_review_recorded(
            runtime_result=runtime_result
        )
        teachback = self.lifecycle.build_teachback_request()
        self.active_mission = self.continuity.update_active_state(
            "awaiting_teachback"
        )
        return {
            "status": "passed",
            "status_code": "REVIEW_APPROVED",
            "review": recorded,
            "teachback_request": teachback,
            "authority": {
                "review_does_not_close_mission": True,
                "teachback_requires_human_explanation": True,
            },
        }

    def request_review_changes(
        self,
        review: Dict[str, Any],
        phrase: str,
    ) -> Dict[str, Any]:
        if phrase.strip() != review["changes_phrase"]:
            return {
                "status": "failed",
                "status_code": "REVIEW_CHANGES_MISMATCH",
                "expected": review["changes_phrase"],
            }
        review["status"] = "changes_requested"
        review["changes_requested_at"] = utc_now()
        write_json(
            self.lifecycle.review_proposal_path,
            review,
        )
        self.active_mission = self.continuity.update_active_state(
            "review_changes_requested"
        )
        return {
            "status": "passed",
            "status_code": "REVIEW_CHANGES_REQUESTED",
            "review": review,
        }

    def record_teachback(
        self,
        request: Dict[str, Any],
        text: str,
    ) -> Dict[str, Any]:
        prefix = "TEACHBACK:"
        if not text.upper().startswith(prefix):
            return {
                "status": "failed",
                "status_code": "TEACHBACK_PREFIX_REQUIRED",
                "expected": prefix,
            }
        explanation = text[len(prefix):].strip()
        if len(explanation) < 20:
            return {
                "status": "failed",
                "status_code": "TEACHBACK_TOO_SHORT",
                "minimum_characters": 20,
            }

        if self.runtime is None:
            self.runtime = RuntimeBridge(self.repo_root)
        if self.lifecycle is None:
            raise ValueError("Lifecycle store is missing.")

        mission_id = request["mission_id"]
        record_result = self.runtime.record_teachback(
            workspace_root=self.workspace_root,
            mission_id=mission_id,
            teachback_id=f"{mission_id}-teachback",
            achieved_level=int(request["required_level"]),
            summary=explanation,
            human_actor=self.actor,
            source_execution=request["execution_evidence"],
            source_review=request["review_evidence"],
        )
        recorded = self.lifecycle.mark_teachback_recorded(
            record_result=record_result
        )
        closure = self.lifecycle.build_closure_proposal(
            self.actor
        )
        self.active_mission = self.continuity.update_active_state(
            "awaiting_closure_approval"
        )
        return {
            "status": "passed",
            "status_code": "TEACHBACK_RECORDED",
            "teachback": recorded,
            "closure_proposal": closure,
            "authority": {
                "teachback_does_not_close_mission": True,
                "closure_requires_separate_approval": True,
            },
        }

    def approve_closure(
        self,
        closure: Dict[str, Any],
        phrase: str,
    ) -> Dict[str, Any]:
        if phrase.strip() != closure["approval_phrase"]:
            return {
                "status": "failed",
                "status_code": "CLOSURE_APPROVAL_MISMATCH",
                "expected": closure["approval_phrase"],
            }

        if self.runtime is None:
            self.runtime = RuntimeBridge(self.repo_root)
        if self.lifecycle is None:
            raise ValueError("Lifecycle store is missing.")

        result = self.runtime.close(
            workspace_root=self.workspace_root,
            mission_id=closure["mission_id"],
            memory_root=self.memory_root,
            closure_id=closure["closure_id"],
            execution_evidence=closure["execution_evidence"],
            review_evidence=closure["review_evidence"],
            teachback_record=closure["teachback_record"],
            human_actor=self.actor,
            closure_reason=closure["closure_reason"],
        )
        recorded = self.lifecycle.mark_closed(result)
        audit_memory = None
        if self.audit_flow is not None:
            audit_memory = self.audit_flow.write_private_memory_note()

        closure_report = str(
            result.get("paths", {}).get(
                "mission_closure_report",
                "",
            )
        )
        self.continuity.mark_mission_closed(
            mission_id=closure["mission_id"],
            closure_report=closure_report,
        )

        self.active_mission = None
        self.pending_charter = None
        self.action_queue = None
        self.lifecycle = None
        self.audit_flow = None
        self.authoritative_decision = None

        return {
            "status": "passed",
            "status_code": "MISSION_CLOSED",
            "closure": recorded,
            "runtime_result": result,
            "audit_memory": (
                str(audit_memory)
                if audit_memory is not None
                else None
            ),
            "authority": {
                "closure_does_not_authorize_new_work": True,
                "memory_is_evidence_only": True,
            },
        }

    def status_payload(self) -> Dict[str, Any]:
        lifecycle = None
        if self.lifecycle is not None:
            lifecycle = {
                "review": self.lifecycle.load_optional(
                    self.lifecycle.review_proposal_path
                ),
                "teachback": self.lifecycle.load_optional(
                    self.lifecycle.teachback_request_path
                ),
                "closure": self.lifecycle.load_optional(
                    self.lifecycle.closure_proposal_path
                ),
            }

        audit = None
        if self.audit_flow is not None:
            audit = {
                "deterministic_checks": (
                    str(self.audit_flow.deterministic_report_path)
                    if self.audit_flow.deterministic_report_path.exists()
                    else None
                ),
                "model_grant": (
                    read_json(self.audit_flow.model_grant_path)
                    if self.audit_flow.model_grant_path.exists()
                    else None
                ),
                "normalized_audit": (
                    read_json(self.audit_flow.normalized_audit_path)
                    if self.audit_flow.normalized_audit_path.exists()
                    else None
                ),
                "patch_proposal": (
                    self.audit_flow.load_patch_proposal()
                ),
                "post_patch_tests": (
                    read_json(self.audit_flow.post_patch_tests_path)
                    if self.audit_flow.post_patch_tests_path.exists()
                    else None
                ),
            }

        return {
            "schema_version": "1.0.0",
            "report_type": "conversational_hokage_status",
            "version": DEV_VERSION,
            "active_mission": self.active_mission,
            "pending_charter": (
                self.pending_charter["charter_id"]
                if self.pending_charter
                else None
            ),
            # The same persisted truth source restore()/recovery reads -
            # a raw load() of action_queue.json, never a second in-memory
            # state that could diverge from mission_authority.json /
            # mission_decision.json / mission_charter.json / the
            # execution claims on disk.
            "action_queue": (
                self.action_queue.load()
                if self.action_queue
                else None
            ),
            "recovery": self._recovery_candidates(),
            "resume_diagnostic": self.resume_diagnostic,
            "audit_flow": audit,
            "lifecycle": lifecycle,
            "bootstrap": self.bootstrap_evidence,
            # The approved, persisted Decision takes priority once it
            # exists; before approval, the still-pending Decision (if
            # any) is shown instead. Neither is ever recomputed here -
            # both are exactly what restore()/propose()/approve_charter()
            # already loaded or built.
            "mission_decision": (
                self.authoritative_decision
                if self.authoritative_decision is not None
                else self.pending_decision
            ),
            "private_village": self.village_status,
            "authority": {
                "status_is_evidence_only": True,
                "status_is_not_permission": True,
            },
        }

    def next_safe_action_text(self) -> str:
        if self.pending_charter:
            return "Review the pending Mission Charter."
        action = self.next_action()
        if action is not None:
            if action["skill_id"] == "invoke_local_model_audit":
                return "Review the scoped local-model session grant."
            if action["skill_id"] == "apply_validated_patch":
                return "Review the exact validated patch proposal."
            return "Review the next bounded action."
        if self.current_review():
            return "Review the deterministic execution summary."
        if self.current_teachback():
            return "Provide the required human Teachback."
        if self.current_closure():
            return "Review the explicit mission closure proposal."
        return "Describe the next mission."

    def _render_pending(
        self,
        action: Optional[Dict[str, Any]],
    ) -> str:
        if self.pending_charter:
            return render_charter(self.pending_charter)
        if action:
            if action["skill_id"] == "invoke_local_model_audit":
                grant = self.current_model_grant(action)
                return render_model_grant(grant)
            if action["skill_id"] == "apply_validated_patch":
                proposal = self.current_patch_proposal(action)
                return render_patch_proposal(proposal)
            return render_action(action)
        review = self.current_review()
        if review:
            return render_review(review)
        teachback = self.current_teachback()
        if teachback:
            return render_teachback(teachback)
        closure = self.current_closure()
        if closure:
            return render_closure(closure)
        return "Hokage: No hay propuesta pendiente."

    def interactive(self) -> int:
        session = self.continuity.start_session()
        print("KONOHA CONVERSATIONAL HOKAGE")
        print(f"version: {DEV_VERSION}")
        print("Evidence before action. Safety overrides autonomy.")
        print("")
        print(f"Hokage: {session['greeting']}")
        bootstrap_state = self.bootstrap_evidence["state"]
        snapshot = self.bootstrap_evidence["snapshot"]
        if bootstrap_state["first_use"]:
            print("Hokage: Primera ejecución detectada; bootstrap privado completo.")
        else:
            print(f"Hokage: Reentrada detectada; sesión {bootstrap_state['session_count']}.")
        ready = [p["provider"] for p in snapshot["providers"] if p["status"] == "ready"]
        print("Hokage: Providers listos: " + (", ".join(ready) if ready else "ninguno"))
        local_model_config = self.bootstrap_runtime.local_model_configuration(snapshot)
        print(
            "Hokage: Perfil local recomendado: "
            + local_model_config["recommended_profile"]
            + " (recomendación, no selección)."
        )
        print(
            "Hokage: Modelo local activo: "
            + (local_model_config["selected_model"] or "ninguno")
        )
        print(
            "Hokage: Usá /local-model para revisar o cambiar "
            "la selección privada."
        )
        print("Hokage: Presupuesto pendiente de límites manuales; ahorro mínimo objetivo 30%.")
        if not self.village_status["ready"]:
            print(
                "Hokage: No hay una aldea privada lista. "
                "La creación requiere aprobación humana exacta."
            )
            print(
                "Hokage: " + self.village_status["approval_phrase"]
            )
        print("Escribí /help para controles de recuperación.")
        print("")

        while True:
            action = self.next_action()
            review = self.current_review()
            teachback = self.current_teachback()
            closure = self.current_closure()

            try:
                text = input("Mission> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("")
                text = "/exit"

            if not text:
                continue

            lowered = text.lower()

            if (
                not self.village_status["ready"]
                and text == self.village_status["approval_phrase"]
            ):
                self.village_status = self.village.initialize(text)
                print(
                    "Hokage: Aldea privada inicializada en "
                    + self.village_status["village_root"]
                )
                continue


            if lowered.startswith("/local-model"):
                parts = text.split(maxsplit=1)
                requested = parts[1] if len(parts) == 2 else "show"
                try:
                    configuration = (
                        self.bootstrap_runtime.select_local_model(
                            requested,
                            self.bootstrap_evidence["snapshot"],
                        )
                    )
                except ValueError as exc:
                    print(f"Hokage: {exc}")
                    continue

                self.local_model_configuration = configuration
                selected = configuration["selected_model"]
                if selected:
                    self.local_model = selected

                print(
                    "Hokage: Perfil recomendado: "
                    + configuration["recommended_profile"]
                )
                print(
                    "Hokage: Modelo local activo: "
                    + (selected or "ninguno")
                )
                print(
                    "Hokage: Modelos instalados: "
                    + (
                        ", ".join(configuration["installed_models"])
                        if configuration["installed_models"]
                        else "ninguno"
                    )
                )
                print(
                    "Hokage: Estado: "
                    + configuration["selection_status"]
                )
                continue

            if lowered in {"/exit", "/quit"}:
                self.continuity.record_handoff(
                    active_mission=self.active_mission,
                    next_safe_action=self.next_safe_action_text(),
                )
                print(
                    "Hokage: Sesión cerrada. Handoff privado escrito en "
                    f"{self.continuity.last_handoff_path}"
                )
                return 0

            if lowered == "/help":
                print(
                    "Hokage:\n"
                    "/status  estado completo\n"
                    "/pending propuesta pendiente\n"
                    "/actions cola de acciones\n"
                    "/details detalle pendiente\n"
                    "/local-model [modelo|clear] selección local\n"
                    "/exit    cerrar y escribir handoff"
                )
                continue

            if lowered == "/status":
                print(
                    json.dumps(
                        self.status_payload(),
                        indent=2,
                        ensure_ascii=False,
                    )
                )
                continue

            if lowered in {"/pending", "/details"}:
                print(self._render_pending(action))
                continue

            if lowered == "/actions":
                print(
                    json.dumps(
                        (
                            self.action_queue.load()
                            if self.action_queue
                            else {"actions": []}
                        ),
                        indent=2,
                        ensure_ascii=False,
                    )
                )
                continue

            if self.pending_charter:
                if text == self.pending_charter["approval_phrase"]:
                    result = self.approve_charter(text)
                    print(
                        "Hokage: Charter aprobado. "
                        "La misión y el plan supervisado fueron creados."
                    )
                    if result.get("next_action"):
                        print(render_action(result["next_action"]))
                    continue

                if text == self.pending_charter["rejection_phrase"]:
                    self.reject_charter(text)
                    print(
                        "Hokage: Charter rechazado. "
                        "No se ejecutó ninguna herramienta."
                    )
                    continue

                print(
                    "Hokage: Hay un Charter pendiente. "
                    "Aprobalo, rechazalo o usá /details."
                )
                continue

            if action:
                # A single human execution gate for every skill_id:
                # action["approval_phrase"]/action["rejection_phrase"].
                # invoke_local_model_audit and apply_validated_patch no
                # longer have their own separate phrase - the grant/patch
                # proposal are deterministic records bound to this same
                # action, not a second authority to satisfy.
                if text == action["approval_phrase"]:
                    result = self.approve_action(action, text)
                    if result["status"] == "passed":
                        skill_id = action["skill_id"]
                        if skill_id == "invoke_local_model_audit":
                            print(
                                render_audit_summary(
                                    result["action"]["evidence"]["result"]
                                )
                            )
                        elif skill_id == "apply_validated_patch":
                            print(
                                "Hokage: Patch exacto aplicado. "
                                "Git no fue autorizado."
                            )
                        else:
                            print(
                                "Hokage: Acción completada. "
                                "El resultado es evidencia solamente."
                            )
                        if result.get("next_action"):
                            print(
                                self._render_pending(
                                    result["next_action"]
                                )
                            )
                        elif result.get("review_proposal"):
                            print(
                                render_review(
                                    result["review_proposal"]
                                )
                            )
                    else:
                        print(
                            f"Hokage: La acción no se completó "
                            f"({result['status_code']}):\n- "
                            + "\n- ".join(
                                result.get("blockers")
                                or [result.get("detail", "")]
                            )
                        )
                    continue

                if text == action["rejection_phrase"]:
                    result = self.reject_action(action, text)
                    if result["status"] == "passed":
                        print(
                            "Hokage: Acción rechazada. No se ejecutó."
                        )
                        if result.get("next_action"):
                            print(
                                self._render_pending(
                                    result["next_action"]
                                )
                            )
                        elif result.get("review_proposal"):
                            print(
                                render_review(
                                    result["review_proposal"]
                                )
                            )
                    else:
                        print(
                            f"Hokage: El rechazo no se completó "
                            f"({result['status_code']}): "
                            + result.get("detail", "")
                        )
                    continue

                print(
                    "Hokage: Hay una acción pendiente. "
                    "Aprobala, rechazala o usá /details."
                )
                continue

            if review:
                if text == review["approval_phrase"]:
                    result = self.approve_review(review, text)
                    print(
                        "Hokage: Review humano aprobado y registrado."
                    )
                    print(
                        render_teachback(
                            result["teachback_request"]
                        )
                    )
                    continue

                if text == review["changes_phrase"]:
                    self.request_review_changes(review, text)
                    print(
                        "Hokage: Cambios solicitados. "
                        "La misión no puede continuar a Teachback."
                    )
                    continue

                print(
                    "Hokage: Hay un review pendiente. "
                    "Aprobalo, pedí cambios o usá /details."
                )
                continue

            if teachback:
                result = self.record_teachback(
                    teachback,
                    text,
                )
                if result["status"] == "passed":
                    print(
                        "Hokage: Teachback humano registrado. "
                        "El cierre sigue siendo un gate separado."
                    )
                    print(
                        render_closure(
                            result["closure_proposal"]
                        )
                    )
                else:
                    print(
                        "Hokage: Teachback no registrado. "
                        f"Estado: {result['status_code']}."
                    )
                    print(render_teachback(teachback))
                continue

            if closure:
                if text == closure["approval_phrase"]:
                    result = self.approve_closure(
                        closure,
                        text,
                    )
                    print(
                        "Hokage: Misión cerrada con ejecución, "
                        "audit, patch, tests, review y Teachback "
                        "validados. Memoria privada actualizada."
                    )
                    continue

                print(
                    "Hokage: Hay un cierre pendiente. "
                    "Usá la frase exacta o /details."
                )
                continue

            result = self.propose(text)
            if result["status_code"] == "CHARTER_PROPOSED":
                print(render_charter(result["charter"]))
            else:
                print(
                    "Hokage: No pude validar la intención:\n- "
                    + "\n- ".join(result.get("errors", []))
                )

    def one_shot(self, request: str) -> Dict[str, Any]:
        self.continuity.start_session()
        return self.propose(request)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Open the conversational Hokage product shell."
    )
    parser.add_argument("--repo-root")
    parser.add_argument("--workspace-root")
    parser.add_argument("--state-root")
    parser.add_argument("--memory-root")
    parser.add_argument("--actor", default="Eduardo")
    parser.add_argument(
        "--local-model",
        default=os.environ.get(
            "KONOHA_LOCAL_MODEL",
            "qwen2.5-coder:7b",
        ),
    )
    parser.add_argument("--request")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = discover_repo_root(
        Path(args.repo_root) if args.repo_root else Path.cwd()
    )
    default_state, default_memory = default_private_roots(repo_root)

    shell = ConversationalHokage(
        repo_root=repo_root,
        workspace_root=Path(
            args.workspace_root
            or os.environ.get("KONOHA_WORKSPACE_ROOT")
            or repo_root / "sandbox" / "workspace"
        ),
        state_root=Path(args.state_root or default_state),
        memory_root=Path(args.memory_root or default_memory),
        actor=args.actor,
        local_model=args.local_model,
        json_mode=args.json,
    )

    if args.request:
        result = shell.one_shot(args.request)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(render_charter(result["charter"]))
        return 0 if result.get("status") == "passed" else 2

    return shell.interactive()


if __name__ == "__main__":
    raise SystemExit(main())
