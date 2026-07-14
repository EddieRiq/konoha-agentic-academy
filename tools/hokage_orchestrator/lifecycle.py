"""Deterministic review, Teachback and closure lifecycle."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_hash(payload: Dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        newline="\n",
    )


def mission_relative(mission_dir: Path, path: Path) -> str:
    return path.resolve().relative_to(
        mission_dir.resolve()
    ).as_posix()


class LifecycleStore:
    """Persist lifecycle proposals independently from presentation text."""

    def __init__(self, mission_dir: Path) -> None:
        self.mission_dir = mission_dir.resolve()
        self.root = self.mission_dir / "conversation"
        self.review_proposal_path = (
            self.root / "review_proposal.json"
        )
        self.teachback_request_path = (
            self.root / "teachback_request.json"
        )
        self.closure_proposal_path = (
            self.root / "closure_proposal.json"
        )
        self.execution_summary_path = (
            self.mission_dir
            / "reports"
            / "conversation_execution_summary.json"
        )

    def load_optional(
        self,
        path: Path,
    ) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def validate_actions(
        self,
        action_queue: Dict[str, Any],
    ) -> Dict[str, Any]:
        actions = action_queue.get("actions", [])
        if not isinstance(actions, list) or not actions:
            raise ValueError(
                "Cannot review a mission without action evidence."
            )

        counts = {
            "completed": 0,
            "rejected": 0,
            "failed": 0,
            "proposed": 0,
            "running": 0,
        }
        evidence_paths: List[str] = []
        action_summaries: List[Dict[str, Any]] = []

        for action in actions:
            status = str(action.get("status", "unknown"))
            if status in counts:
                counts[status] += 1

            runtime = (
                action.get("evidence", {})
                .get("runtime_result", {})
            )
            paths = runtime.get("output_paths", [])
            if isinstance(paths, list):
                evidence_paths.extend(
                    str(item) for item in paths
                )

            action_summaries.append(
                {
                    "action_id": action.get("action_id"),
                    "skill_id": action.get("skill_id"),
                    "status": status,
                    "arguments_hash": action.get(
                        "arguments_hash"
                    ),
                    "runtime_status": runtime.get("status"),
                    "output_paths": paths,
                }
            )

        if counts["failed"]:
            raise ValueError(
                "Failed actions require resolution before review."
            )
        if counts["proposed"] or counts["running"]:
            raise ValueError(
                "Pending actions require approval or rejection "
                "before review."
            )
        if counts["completed"] < 1:
            raise ValueError(
                "At least one completed action is required."
            )

        for raw_path in evidence_paths:
            path = Path(raw_path)
            if not path.is_file():
                raise ValueError(
                    f"Action evidence is missing: {path}"
                )
            payload = json.loads(
                path.read_text(encoding="utf-8")
            )
            exit_code = payload.get("exit_code")
            status = payload.get("status")
            if exit_code not in {None, 0}:
                raise ValueError(
                    f"Action evidence failed with exit_code="
                    f"{exit_code}: {path}"
                )
            if status in {"failed", "blocked", "error"}:
                raise ValueError(
                    f"Action evidence status={status}: {path}"
                )

        summary = {
            "schema_version": "1.0.0",
            "report_type": (
                "conversational_execution_validation"
            ),
            "status": "passed",
            "status_code": "EXECUTION_EVIDENCE_VALIDATED",
            "generated_at": utc_now(),
            "mission_id": action_queue.get("mission_id"),
            "plan_id": action_queue.get("plan_id"),
            "counts": counts,
            "actions": action_summaries,
            "evidence_paths": evidence_paths,
            "authority": {
                "validation_is_evidence_only": True,
                "validation_does_not_authorize_review": True,
                "validation_does_not_close_mission": True,
            },
        }
        write_json(self.execution_summary_path, summary)
        return summary

    def build_review_proposal(
        self,
        action_queue: Dict[str, Any],
        actor: str,
    ) -> Dict[str, Any]:
        existing = self.load_optional(
            self.review_proposal_path
        )
        if existing is not None:
            return existing

        execution = self.validate_actions(action_queue)
        material = {
            "mission_id": execution["mission_id"],
            "execution_sha256": file_hash(
                self.execution_summary_path
            ),
            "counts": execution["counts"],
        }
        suffix = canonical_hash(material)[:10]
        review_id = f"review-{suffix}"
        summary = (
            "Human review of conversational mission evidence: "
            f"{execution['counts']['completed']} completed, "
            f"{execution['counts']['rejected']} rejected, "
            f"{execution['counts']['failed']} failed actions. "
            "All completed command evidence reports successful "
            "deterministic execution."
        )

        proposal = {
            "schema_version": "1.0.0",
            "report_type": "conversational_review_proposal",
            "review_id": review_id,
            "mission_id": execution["mission_id"],
            "created_at": utc_now(),
            "reviewed_by": actor,
            "decision": "approved",
            "review_summary": summary,
            "execution_evidence": mission_relative(
                self.mission_dir,
                self.execution_summary_path,
            ),
            "execution_sha256": material[
                "execution_sha256"
            ],
            "status": "proposed",
            "approval_phrase": (
                f"APROBAR REVIEW-{suffix.upper()}"
            ),
            "changes_phrase": (
                f"CAMBIOS REVIEW-{suffix.upper()}"
            ),
            "authority": {
                "proposal_is_not_human_review": True,
                "exact_human_approval_required": True,
                "review_does_not_close_mission": True,
            },
        }
        write_json(self.review_proposal_path, proposal)
        return proposal

    def mark_review_recorded(
        self,
        *,
        runtime_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        proposal = self.load_optional(
            self.review_proposal_path
        )
        if proposal is None:
            raise ValueError("Review proposal is missing.")

        paths = runtime_result.get("output_paths", [])
        if len(paths) != 1:
            raise ValueError(
                "Review runtime must return one evidence path."
            )
        review_path = Path(paths[0])
        if not review_path.is_file():
            raise ValueError(
                f"Review evidence is missing: {review_path}"
            )

        review = json.loads(
            review_path.read_text(encoding="utf-8")
        )
        if review.get("review_decision") != "approved":
            raise ValueError(
                "Recorded review is not approved."
            )
        if review.get("human_approval") is not True:
            raise ValueError(
                "Recorded review lacks human approval."
            )

        proposal["status"] = "recorded"
        proposal["recorded_at"] = utc_now()
        proposal["review_evidence"] = mission_relative(
            self.mission_dir,
            review_path,
        )
        proposal["review_sha256"] = file_hash(review_path)
        write_json(self.review_proposal_path, proposal)
        return proposal

    def build_teachback_request(
        self,
    ) -> Dict[str, Any]:
        existing = self.load_optional(
            self.teachback_request_path
        )
        if existing is not None:
            return existing

        review = self.load_optional(
            self.review_proposal_path
        )
        if review is None or review.get("status") != "recorded":
            raise ValueError(
                "Approved review evidence is required."
            )

        manifest = json.loads(
            (
                self.mission_dir
                / "mission_manifest.json"
            ).read_text(encoding="utf-8")
        )
        policy = manifest.get("teachback", {})
        required_level = int(
            policy.get("required_level", 1)
        )
        request = {
            "schema_version": "1.0.0",
            "report_type": "conversational_teachback_request",
            "mission_id": review["mission_id"],
            "created_at": utc_now(),
            "required": bool(
                policy.get("required", True)
            ),
            "required_level": required_level,
            "prompt": (
                "Explicá con tus palabras qué se ejecutó, "
                "qué evidencia demuestra el resultado y por qué "
                "las acciones siguientes siguen requiriendo "
                "aprobación humana."
            ),
            "response_prefix": "TEACHBACK:",
            "status": "awaiting_user_explanation",
            "execution_evidence": review[
                "execution_evidence"
            ],
            "review_evidence": review["review_evidence"],
            "authority": {
                "generated_prompt_is_not_teachback": True,
                "human_explanation_is_required": True,
                "teachback_does_not_close_mission": True,
            },
        }
        write_json(self.teachback_request_path, request)
        return request

    def mark_teachback_recorded(
        self,
        *,
        record_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        request = self.load_optional(
            self.teachback_request_path
        )
        if request is None:
            raise ValueError("Teachback request is missing.")

        record_path = record_result.get("record_path")
        if not record_path:
            raise ValueError(
                "Teachback result lacks record_path."
            )
        path = Path(record_path)
        if not path.is_file():
            raise ValueError(
                f"Teachback record is missing: {path}"
            )
        record = json.loads(
            path.read_text(encoding="utf-8")
        )
        if record.get("result") != "passed":
            raise ValueError(
                "Teachback record did not pass."
            )
        if record.get("completed_by_user") is not True:
            raise ValueError(
                "Teachback was not completed by the user."
            )

        request["status"] = "recorded"
        request["recorded_at"] = utc_now()
        request["teachback_record"] = mission_relative(
            self.mission_dir,
            path,
        )
        request["teachback_sha256"] = file_hash(path)
        write_json(self.teachback_request_path, request)
        return request

    def build_closure_proposal(
        self,
        actor: str,
    ) -> Dict[str, Any]:
        existing = self.load_optional(
            self.closure_proposal_path
        )
        if existing is not None:
            return existing

        review = self.load_optional(
            self.review_proposal_path
        )
        teachback = self.load_optional(
            self.teachback_request_path
        )
        if review is None or review.get("status") != "recorded":
            raise ValueError("Recorded review is required.")
        if (
            teachback is None
            or teachback.get("status") != "recorded"
        ):
            raise ValueError("Passed Teachback is required.")

        material = {
            "mission_id": review["mission_id"],
            "execution_sha256": review[
                "execution_sha256"
            ],
            "review_sha256": review["review_sha256"],
            "teachback_sha256": teachback[
                "teachback_sha256"
            ],
            "actor": actor,
        }
        suffix = canonical_hash(material)[:10]
        closure = {
            "schema_version": "1.0.0",
            "report_type": (
                "conversational_closure_proposal"
            ),
            "closure_id": f"closure-{suffix}",
            "mission_id": review["mission_id"],
            "created_at": utc_now(),
            "human_actor": actor,
            "closure_reason": (
                "Human approved closure after validated "
                "execution, review and Teachback evidence."
            ),
            "execution_evidence": review[
                "execution_evidence"
            ],
            "review_evidence": review["review_evidence"],
            "teachback_record": teachback[
                "teachback_record"
            ],
            "status": "proposed",
            "approval_phrase": (
                f"APROBAR CIERRE-{suffix.upper()}"
            ),
            "authority": {
                "proposal_is_not_closure": True,
                "closure_requires_exact_human_approval": True,
                "closure_does_not_authorize_new_work": True,
            },
        }
        write_json(self.closure_proposal_path, closure)
        return closure

    def mark_closed(
        self,
        closure_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        proposal = self.load_optional(
            self.closure_proposal_path
        )
        if proposal is None:
            raise ValueError("Closure proposal is missing.")
        if closure_result.get("status") != "passed":
            raise ValueError(
                "Mission closure did not pass."
            )
        if closure_result.get("status_code") != "MISSION_CLOSED":
            raise ValueError(
                "Unexpected mission closure status code."
            )

        proposal["status"] = "closed"
        proposal["closed_at"] = utc_now()
        proposal["closure_report"] = (
            closure_result.get("paths", {})
            .get("mission_closure_report")
        )
        proposal["memory_outputs"] = closure_result.get(
            "memory_outputs",
            [],
        )
        write_json(self.closure_proposal_path, proposal)
        return proposal
