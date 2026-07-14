#!/usr/bin/env python3
"""Konoha Conversational Hokage — v3.5.0 Slice 2."""

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

from tools.hokage_orchestrator.charter import (  # noqa: E402
    build_charter,
    charter_markdown,
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
from tools.hokage_orchestrator.skill_runtime import (  # noqa: E402
    ActionQueue,
    RuntimeBridge,
    validate_skills,
    verify_action_approval,
)

DEV_VERSION = "3.5.0-dev-slice3"


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


def mission_id_for(charter: Dict[str, Any]) -> str:
    suffix = charter["charter_id"].split("-", 1)[-1]
    return (
        f"mission-{suffix}-"
        f"{safe_slug(charter['objective'])[:28]}"
    )


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
    return "\n".join(
        [
            "",
            "Hokage propone una acción:",
            "",
            f"Acción: {action['action_id']}",
            f"Skill: {action['skill_id']}",
            f"Descripción: {action['description']}",
            f"Riesgo: {action['risk_level']}",
            f"Mutación: {action['mutates_files']}",
            f"Red: {action['network_required']}",
            f"Contexto privado: {action['private_context_required']}",
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
        self.local_model = local_model
        self.json_mode = json_mode
        self.continuity = ContinuityStore(
            state_root=state_root,
            obsidian_root=self.memory_root,
            actor=actor,
        )
        self.runtime: Optional[RuntimeBridge] = None
        self.pending_charter: Optional[Dict[str, Any]] = None
        self.active_mission: Optional[Dict[str, Any]] = None
        self.action_queue: Optional[ActionQueue] = None
        self.lifecycle: Optional[LifecycleStore] = None
        self.restore()

    def mission_dir(self, mission_id: str) -> Path:
        return self.workspace_root / "missions" / mission_id

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

        charter_path = Path(active.get("charter_path", ""))
        if charter_path.exists():
            charter = read_json(charter_path)
            if charter.get("state") == "proposed":
                self.pending_charter = charter

    def propose(self, request: str) -> Dict[str, Any]:
        intent = interpret_intent(request, self.repo_root)
        errors = validate_intent(intent, self.repo_root)
        if errors:
            return {
                "status": "needs_context",
                "status_code": "INTENT_VALIDATION_FAILED",
                "errors": errors,
            }

        charter = build_charter(intent, self.actor)
        mission_id = mission_id_for(charter)
        mission_dir = self.mission_dir(mission_id)
        mission_dir.mkdir(parents=True, exist_ok=True)

        intent_path = mission_dir / "conversational_intent.json"
        charter_path = mission_dir / "mission_charter.json"
        charter_md = mission_dir / "charter.md"

        write_json(intent_path, intent)
        write_json(charter_path, charter)
        charter_md.write_text(
            charter_markdown(charter),
            encoding="utf-8",
            newline="\n",
        )

        self.pending_charter = charter
        self.active_mission = self.continuity.set_active_mission(
            mission_id=mission_id,
            charter_path=charter_path,
            state_name="charter_proposed",
        )
        self.action_queue = ActionQueue(mission_dir)
        self.lifecycle = LifecycleStore(mission_dir)

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
        if self.pending_charter is None:
            return {
                "status": "failed",
                "status_code": "NO_PENDING_CHARTER",
            }

        if phrase.strip() != self.pending_charter["approval_phrase"]:
            return {
                "status": "failed",
                "status_code": "CHARTER_APPROVAL_MISMATCH",
                "expected": self.pending_charter["approval_phrase"],
            }

        mission_id = self.active_mission["mission_id"]
        plan_id = f"{mission_id}-plan"
        charter_path = (
            self.mission_dir(mission_id)
            / "mission_charter.json"
        )
        charter = read_json(charter_path)
        charter["state"] = "approved"
        charter["approved_at"] = utc_now()
        charter["approved_by"] = self.actor
        write_json(charter_path, charter)

        self.runtime = RuntimeBridge(self.repo_root)
        runtime_evidence = self.runtime.bootstrap(
            workspace_root=self.workspace_root,
            mission_id=mission_id,
            plan_id=plan_id,
            actor=self.actor,
            objective=charter["objective"],
        )

        proposals_path = (
            self.mission_dir(mission_id)
            / "plans"
            / f"{plan_id}_command_proposals.json"
        )
        proposals = read_json(proposals_path).get(
            "proposals",
            [],
        )

        self.action_queue = ActionQueue(
            self.mission_dir(mission_id)
        )
        queue = self.action_queue.initialize(
            mission_id=mission_id,
            plan_id=plan_id,
            charter=charter,
            runtime_proposals=proposals,
            local_model=self.local_model,
        )
        self.lifecycle = LifecycleStore(
            self.mission_dir(mission_id)
        )

        self.pending_charter = None
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
            "runtime_evidence": runtime_evidence,
            "authority": {
                "charter_approval_does_not_authorize_actions": True,
                "action_proposals_are_not_permission": True,
            },
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

        if not verify_action_approval(action, phrase):
            return {
                "status": "failed",
                "status_code": "ACTION_APPROVAL_MISMATCH",
                "expected": action["approval_phrase"],
            }

        self.action_queue.update(
            action["action_id"],
            status="running",
            evidence={
                "approved_by": self.actor,
                "approved_at": utc_now(),
                "arguments_hash": action["arguments_hash"],
            },
        )

        try:
            if self.runtime is None:
                self.runtime = RuntimeBridge(self.repo_root)
            runtime_result = self.runtime.execute(
                workspace_root=self.workspace_root,
                action=action,
            )
        except Exception as exc:
            failed = self.action_queue.update(
                action["action_id"],
                status="failed",
                evidence={
                    "failed_at": utc_now(),
                    "error": str(exc),
                },
            )
            self.active_mission = self.continuity.update_active_state(
                "action_failed"
            )
            return {
                "status": "failed",
                "status_code": "ACTION_EXECUTION_FAILED",
                "action": failed,
                "blockers": [str(exc)],
            }

        completed = self.action_queue.update(
            action["action_id"],
            status="completed",
            evidence={
                "completed_at": utc_now(),
                "runtime_result": runtime_result,
                "result_is_evidence_only": True,
            },
        )
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

        if phrase.strip() != action["rejection_phrase"]:
            return {
                "status": "failed",
                "status_code": "ACTION_REJECTION_MISMATCH",
                "expected": action["rejection_phrase"],
            }

        rejected = self.action_queue.update(
            action["action_id"],
            status="rejected",
            evidence={
                "rejected_by": self.actor,
                "rejected_at": utc_now(),
            },
        )
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

        return {
            "status": "passed",
            "status_code": "MISSION_CLOSED",
            "closure": recorded,
            "runtime_result": result,
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
            "action_queue": (
                self.action_queue.load()
                if self.action_queue
                else None
            ),
            "lifecycle": lifecycle,
            "authority": {
                "status_is_evidence_only": True,
                "status_is_not_permission": True,
            },
        }

    def next_safe_action_text(self) -> str:
        if self.pending_charter:
            return "Review the pending Mission Charter."
        if self.next_action():
            return "Review the next bounded action."
        if self.current_review():
            return "Review the deterministic execution summary."
        if self.current_teachback():
            return "Provide the required human Teachback."
        if self.current_closure():
            return "Review the explicit mission closure proposal."
        return "Describe the next mission."

    def interactive(self) -> int:
        session = self.continuity.start_session()
        print("KONOHA CONVERSATIONAL HOKAGE")
        print(f"version: {DEV_VERSION}")
        print("Evidence before action. Safety overrides autonomy.")
        print("")
        print(f"Hokage: {session['greeting']}")
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
                if self.pending_charter:
                    print(render_charter(self.pending_charter))
                elif action:
                    print(render_action(action))
                elif review:
                    print(render_review(review))
                elif teachback:
                    print(render_teachback(teachback))
                elif closure:
                    print(render_closure(closure))
                else:
                    print("Hokage: No hay propuesta pendiente.")
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
                    print(
                        "Hokage: Charter rechazado. "
                        "No se ejecutó ninguna herramienta."
                    )
                    self.pending_charter = None
                    continue

                print(
                    "Hokage: Hay un Charter pendiente. "
                    "Aprobalo, rechazalo o usá /details."
                )
                continue

            if action:
                if text == action["approval_phrase"]:
                    result = self.approve_action(action, text)
                    if result["status"] == "passed":
                        print(
                            "Hokage: Acción completada. "
                            "El resultado es evidencia solamente."
                        )
                        if result.get("next_action"):
                            print(render_action(result["next_action"]))
                        elif result.get("review_proposal"):
                            print(
                                render_review(
                                    result["review_proposal"]
                                )
                            )
                    else:
                        print(
                            "Hokage: La acción falló:\n- "
                            + "\n- ".join(result["blockers"])
                        )
                    continue

                if text == action["rejection_phrase"]:
                    result = self.reject_action(action, text)
                    print("Hokage: Acción rechazada. No se ejecutó.")
                    if result.get("next_action"):
                        print(render_action(result["next_action"]))
                    elif result.get("review_proposal"):
                        print(
                            render_review(
                                result["review_proposal"]
                            )
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
                        "review y Teachback validados. "
                        "Memoria privada actualizada."
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
    parser.add_argument("--local-model", default="qwen2.5-coder:7b")
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
