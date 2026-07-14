"""Conversational skills, immutable approvals and beta-runtime bridge."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


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
        "network_required": False,
        "private_context_required": False,
        "internal_token": "EXECUTE_APPROVED_COMMAND",
    },
    "inspect_git_status": {
        "title": "Inspect Git status",
        "description": "Execute the planned read-only Git status inspection.",
        "runtime_kind": "execute-command",
        "command_id": "inspect-git-status",
        "risk_level": "low",
        "mutates_files": False,
        "network_required": False,
        "private_context_required": False,
        "internal_token": "EXECUTE_APPROVED_COMMAND",
    },
    "invoke_local_model": {
        "title": "Invoke approved local model",
        "description": (
            "Invoke Ollama using the bounded runtime prompt. "
            "The result remains evidence only."
        ),
        "runtime_kind": "agent",
        "provider": "ollama",
        "risk_level": "medium",
        "mutates_files": False,
        "network_required": False,
        "private_context_required": False,
        "internal_token": "INVOKE_LOCAL_MODEL",
    },
    "run_deterministic_audit_checks": {
        "title": "Run deterministic audit checks",
        "description": (
            "Run repository tests before any local-model invocation."
        ),
        "runtime_kind": "orchestrator",
        "risk_level": "low",
        "mutates_files": False,
        "network_required": False,
        "private_context_required": False,
        "internal_token": None,
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
        "network_required": False,
        "private_context_required": False,
        "internal_token": None,
    },
    "apply_validated_patch": {
        "title": "Apply validated documentation patch",
        "description": (
            "Apply only the exact approved patch plan and changed paths."
        ),
        "runtime_kind": "orchestrator",
        "risk_level": "medium",
        "mutates_files": True,
        "network_required": False,
        "private_context_required": False,
        "internal_token": None,
    },
    "run_post_patch_tests": {
        "title": "Run post-patch tests",
        "description": (
            "Run the full focused regression suite after patch application."
        ),
        "runtime_kind": "orchestrator",
        "risk_level": "low",
        "mutates_files": False,
        "network_required": False,
        "private_context_required": False,
        "internal_token": None,
    },

}


def validate_skills() -> List[str]:
    errors: List[str] = []
    allowed_kinds = {"execute-command", "agent", "orchestrator"}
    mutating_allowed = {"apply_validated_patch"}

    for skill_id, skill in SKILLS.items():
        if skill["runtime_kind"] not in allowed_kinds:
            errors.append(f"{skill_id}: unsupported runtime kind")
        if (
            skill["mutates_files"] is True
            and skill_id not in mutating_allowed
        ):
            errors.append(
                f"{skill_id}: unexpected mutating skill"
            )
        if skill["network_required"] is not False:
            errors.append(
                f"{skill_id}: external network must remain blocked"
            )

    return errors


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
        "network_required": skill["network_required"],
        "private_context_required": skill["private_context_required"],
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


class ActionQueue:
    def __init__(self, mission_dir: Path) -> None:
        self.path = (
            mission_dir.resolve()
            / "conversation"
            / "action_queue.json"
        )

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {
                "schema_version": "1.0.0",
                "report_type": "conversational_action_queue",
                "actions": [],
                "authority": {
                    "action_proposals_are_not_permission": True
                },
            }
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, payload: Dict[str, Any]) -> None:
        payload["updated_at"] = utc_now()
        write_json(self.path, payload)

    def initialize(
        self,
        *,
        mission_id: str,
        plan_id: str,
        charter: Dict[str, Any],
        runtime_proposals: List[Dict[str, Any]],
        local_model: str,
    ) -> Dict[str, Any]:
        current = self.load()
        if current.get("actions"):
            return current

        requested = set(charter.get("proposed_skills", []))
        actions: List[Dict[str, Any]] = []

        if "invoke_local_model" in requested:
            actions.extend(
                [
                    make_action(
                        mission_id=mission_id,
                        plan_id=plan_id,
                        skill_id="run_deterministic_audit_checks",
                        arguments={
                            "suite_profile": "repo_audit_pre_model",
                            "external_network": "blocked",
                        },
                    ),
                    make_action(
                        mission_id=mission_id,
                        plan_id=plan_id,
                        skill_id="invoke_local_model_audit",
                        arguments={
                            "provider": "ollama",
                            "model": local_model,
                            "host": "http://localhost:11434",
                            "scope": "one_repo_audit_invocation",
                            "timeout_seconds": 600,
                        },
                    ),
                ]
            )
        else:
            by_command = {
                item.get("command_id"): item
                for item in runtime_proposals
            }
            mappings = [
                ("inspect_python_runtime", "inspect-python"),
                ("inspect_git_status", "inspect-git-status"),
            ]
            for skill_id, command_id in mappings:
                proposal = by_command.get(command_id)
                if proposal is None:
                    continue
                actions.append(
                    make_action(
                        mission_id=mission_id,
                        plan_id=plan_id,
                        skill_id=skill_id,
                        arguments={
                            "command_id": command_id,
                            "command": proposal["command"],
                            "reason": proposal.get("reason", ""),
                        },
                    )
                )

        payload = {
            "schema_version": "1.0.0",
            "report_type": "conversational_action_queue",
            "mission_id": mission_id,
            "plan_id": plan_id,
            "actions": actions,
            "authority": {
                "action_proposals_are_not_permission": True,
                "approval_is_bound_to_arguments_hash": True,
            },
        }
        self.save(payload)
        return payload

    def append_action(
        self,
        *,
        mission_id: str,
        plan_id: str,
        skill_id: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        payload = self.load()
        action = make_action(
            mission_id=mission_id,
            plan_id=plan_id,
            skill_id=skill_id,
            arguments=arguments,
        )

        for existing in payload.get("actions", []):
            if existing.get("action_id") == action["action_id"]:
                return existing

        payload.setdefault("actions", []).append(action)
        self.save(payload)
        return action

    def next_pending(self) -> Optional[Dict[str, Any]]:
        for action in self.load().get("actions", []):
            if action.get("status") == "proposed":
                return action
        return None

    def update(
        self,
        action_id: str,
        *,
        status: str,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = self.load()
        selected: Optional[Dict[str, Any]] = None
        for action in payload.get("actions", []):
            if action.get("action_id") == action_id:
                action["status"] = status
                action["updated_at"] = utc_now()
                if evidence is not None:
                    action["evidence"] = evidence
                selected = action
                break
        if selected is None:
            raise KeyError(action_id)
        self.save(payload)
        return selected


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

        if skill["runtime_kind"] == "execute-command":
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

        prompt = (
            workspace_root
            / "missions"
            / action["mission_id"]
            / "inputs"
            / f"{action['plan_id']}_agent_prompt.md"
        )
        return self.invoke(
            [
                "agent",
                "--workspace-root",
                str(workspace_root),
                "--mission-id",
                action["mission_id"],
                "--invocation-id",
                f"{action['action_id']}-invocation",
                "--provider",
                "ollama",
                "--model",
                str(action["arguments"]["model"]),
                "--prompt-file",
                str(prompt),
                "--working-dir",
                str(self.repo_root),
                "--timeout",
                str(action["arguments"]["timeout_seconds"]),
                "--confirm-invoke",
                "--approval-token",
                skill["internal_token"],
                "--allow-local-model",
                "--force",
            ]
        )
