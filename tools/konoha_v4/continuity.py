from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_state_root() -> Path:
    """Return a durable state root outside the repository by default."""
    override = os.environ.get("KONOHA_STATE_ROOT")
    if override:
        return Path(override).expanduser()

    xdg_state_home = os.environ.get("XDG_STATE_HOME")
    base = (
        Path(xdg_state_home).expanduser()
        if xdg_state_home
        else Path.home() / ".local" / "state"
    )
    return base / "konoha" / "v4"


def plan_payload(plan: Any) -> dict[str, Any]:
    """Serialize MissionPlan-like objects without requiring the real dataclass."""
    if is_dataclass(plan):
        return asdict(plan)
    values = vars(plan)
    return {key: value for key, value in values.items()}


@dataclass
class MissionContinuity:
    schema_version: str
    mission_id: str
    original_request: str
    repo_baseline: dict[str, Any]
    requested_changes_history: list[dict[str, Any]] = field(default_factory=list)
    validator_findings_history: list[dict[str, Any]] = field(default_factory=list)
    plan_revisions: list[dict[str, Any]] = field(default_factory=list)
    approval: dict[str, Any] = field(
        default_factory=lambda: {
            "status": "pending",
            "approved_by": None,
            "approved_at": None,
        }
    )
    execution: dict[str, Any] = field(
        default_factory=lambda: {
            "started": False,
            "completed": False,
            "tools_executed": [],
        }
    )
    provider_sessions: dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(default_factory=utc_now)


class MissionContinuityStore:
    """Durable, Konoha-owned mission memory.

    Provider sessions may be recorded later, but they are never the source of
    approval, constraints, mission state, or completion.
    """

    def __init__(self, path: Path, state: MissionContinuity) -> None:
        self.path = path
        self.state = state

    @classmethod
    def create(
        cls,
        state_root: Path,
        mission_id: str,
        original_request: str,
        repo_baseline: dict[str, Any],
    ) -> "MissionContinuityStore":
        path = state_root / "missions" / mission_id / "continuity.json"
        if path.is_file():
            raw = json.loads(path.read_text(encoding="utf-8"))
            state = MissionContinuity(**raw)
            if state.original_request != original_request:
                raise ValueError(
                    "La continuidad existente no coincide con la misión original."
                )
            return cls(path, state)

        state = MissionContinuity(
            schema_version="1.0",
            mission_id=mission_id,
            original_request=original_request,
            repo_baseline=dict(repo_baseline),
        )
        store = cls(path, state)
        store.save()
        return store

    def save(self) -> None:
        self.state.updated_at = utc_now()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(asdict(self.state), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def record_plan(self, plan: Any, *, reason: str) -> None:
        payload = plan_payload(plan)
        self.state.plan_revisions.append(
            {
                "revision": len(self.state.plan_revisions) + 1,
                "plan_id": payload.get("plan_hash"),
                "reason": reason,
                "recorded_at": utc_now(),
                "plan": payload,
            }
        )
        self.save()

    def record_requested_change(self, text: str, previous_plan: Any) -> None:
        self.state.requested_changes_history.append(
            {
                "revision": len(self.state.requested_changes_history) + 1,
                "text": text,
                "previous_plan_id": getattr(previous_plan, "plan_hash", None),
                "recorded_at": utc_now(),
            }
        )
        self.save()

    def record_validator_findings(
        self,
        findings: list[str],
        *,
        plan: Any | None = None,
    ) -> None:
        self.state.validator_findings_history.append(
            {
                "revision": len(self.state.validator_findings_history) + 1,
                "plan_id": getattr(plan, "plan_hash", None),
                "findings": list(findings),
                "recorded_at": utc_now(),
            }
        )
        self.save()

    def record_approval(
        self,
        status: str,
        *,
        approved_by: str | None = None,
        approved_at: str | None = None,
    ) -> None:
        self.state.approval = {
            "status": status,
            "approved_by": approved_by,
            "approved_at": approved_at,
        }
        self.save()


    def record_execution_started(self, plan_id: str) -> None:
        self.state.execution = {
            "started": True,
            "completed": False,
            "plan_id": plan_id,
            "tools_executed": [],
            "started_at": utc_now(),
        }
        self.save()

    def record_execution_finished(self, evidence: list[Any]) -> None:
        self.state.execution.update(
            {
                "completed": True,
                "finished_at": utc_now(),
                "tools_executed": [
                    {
                        "task_id": getattr(item, "task_id", None),
                        "provider": getattr(item, "provider", None),
                        "model": getattr(item, "model", None),
                        "status": getattr(item, "status", None),
                    }
                    for item in evidence
                ],
            }
        )
        self.save()

    def planner_context(self) -> dict[str, Any]:
        previous_plan = (
            self.state.plan_revisions[-1]["plan"]
            if self.state.plan_revisions
            else None
        )
        return {
            "schema_version": self.state.schema_version,
            "mission_id": self.state.mission_id,
            "original_request": self.state.original_request,
            "repo_baseline": self.state.repo_baseline,
            "requested_changes_history": self.state.requested_changes_history,
            "validator_findings_history": self.state.validator_findings_history,
            "previous_plan": previous_plan,
            "approval": self.state.approval,
            "execution": self.state.execution,
            "provider_sessions": self.state.provider_sessions,
        }

    def validate_replanned_plan(self, plan: Any) -> list[str]:
        problems: list[str] = []
        if getattr(plan, "mission_id", None) != self.state.mission_id:
            problems.append(
                "continuity.mission_id cambió durante replanning; "
                "la misión debe conservar su identidad."
            )
        return problems
