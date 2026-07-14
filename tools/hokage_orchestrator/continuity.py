"""Compact deterministic continuity plus a human-readable Obsidian map."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class ContinuityStore:
    """Runtime continuity is compact; Obsidian remains the human map."""

    def __init__(
        self,
        state_root: Path,
        obsidian_root: Path,
        actor: str,
    ) -> None:
        self.state_root = state_root.resolve()
        self.obsidian_root = obsidian_root.resolve()
        self.actor = actor
        self.user_state_path = self.state_root / "user_state.json"
        self.active_mission_path = self.state_root / "active_mission.json"
        self.open_loops_path = self.state_root / "open_loops.json"
        self.last_handoff_path = self.state_root / "last_handoff.json"

    def load_user_state(self) -> Dict[str, Any]:
        if self.user_state_path.exists():
            return read_json(self.user_state_path)
        return {
            "schema_version": "1.0.0",
            "report_type": "konoha_user_continuity",
            "actor": self.actor,
            "first_seen_at": None,
            "last_session_at": None,
            "session_count": 0,
            "last_mission_id": None,
            "active_mission_id": None,
            "last_handoff": None,
            "authority": {
                "memory_is_evidence_only": True,
                "memory_does_not_authorize_action": True,
            },
        }

    def start_session(self) -> Dict[str, Any]:
        state = self.load_user_state()
        first_session = state.get("first_seen_at") is None
        now = utc_now()
        if first_session:
            state["first_seen_at"] = now
        state["last_session_at"] = now
        state["session_count"] = int(state.get("session_count", 0)) + 1
        write_json(self.user_state_path, state)
        self.write_dashboard(state)
        return {
            "first_session": first_session,
            "state": state,
            "greeting": self.greeting(state, first_session),
        }

    def greeting(
        self,
        state: Dict[str, Any],
        first_session: bool,
    ) -> str:
        if first_session:
            return (
                f"Bienvenido, {self.actor}. No encontré sesiones anteriores. "
                "Contame la misión en lenguaje natural."
            )

        active = state.get("active_mission_id")
        if active:
            return (
                f"Bienvenido de nuevo, {self.actor}. "
                f"La misión activa es {active}."
            )

        last = state.get("last_mission_id")
        loops = self.load_open_loops()
        if last and loops:
            return (
                f"Bienvenido de nuevo, {self.actor}. "
                f"La última misión fue {last}. "
                f"Quedaron {len(loops)} seguimiento(s) abiertos."
            )
        if last:
            return (
                f"Bienvenido de nuevo, {self.actor}. "
                f"La última misión fue {last} y no hay misión activa."
            )
        return (
            f"Bienvenido de nuevo, {self.actor}. "
            "No hay una misión activa."
        )

    def load_open_loops(self) -> list[Dict[str, Any]]:
        if not self.open_loops_path.exists():
            return []
        payload = read_json(self.open_loops_path)
        loops = payload.get("open_loops", [])
        return loops if isinstance(loops, list) else []

    def set_active_mission(
        self,
        mission_id: str,
        charter_path: Path,
        state_name: str,
    ) -> Dict[str, Any]:
        payload = {
            "schema_version": "1.0.0",
            "report_type": "konoha_active_mission",
            "mission_id": mission_id,
            "state": state_name,
            "charter_path": str(charter_path),
            "updated_at": utc_now(),
            "authority": {
                "state_is_evidence_only": True,
                "state_does_not_authorize_action": True,
            },
        }
        write_json(self.active_mission_path, payload)
        state = self.load_user_state()
        state["active_mission_id"] = mission_id
        state["last_mission_id"] = mission_id
        write_json(self.user_state_path, state)
        self.write_dashboard(state)
        return payload

    def update_active_state(self, state_name: str) -> Dict[str, Any]:
        if not self.active_mission_path.exists():
            raise FileNotFoundError("No active mission state exists.")
        payload = read_json(self.active_mission_path)
        payload["state"] = state_name
        payload["updated_at"] = utc_now()
        write_json(self.active_mission_path, payload)
        return payload

    def record_handoff(
        self,
        *,
        active_mission: Optional[Dict[str, Any]],
        next_safe_action: str,
    ) -> Dict[str, Any]:
        payload = {
            "schema_version": "1.0.0",
            "report_type": "konoha_session_handoff",
            "created_at": utc_now(),
            "actor": self.actor,
            "active_mission": active_mission,
            "open_loops": self.load_open_loops(),
            "next_safe_action": next_safe_action,
            "authority": {
                "handoff_is_evidence_only": True,
                "handoff_does_not_authorize_action": True,
            },
        }
        write_json(self.last_handoff_path, payload)
        state = self.load_user_state()
        state["last_handoff"] = str(self.last_handoff_path)
        write_json(self.user_state_path, state)
        self.write_session_note(payload)
        self.write_dashboard(state)
        return payload

    def mark_mission_closed(
        self,
        *,
        mission_id: str,
        closure_report: str,
    ) -> Dict[str, Any]:
        """Clear active state while retaining the last closed mission."""

        state = self.load_user_state()
        state["active_mission_id"] = None
        state["last_mission_id"] = mission_id
        state["last_closure_report"] = closure_report
        state["last_closed_at"] = utc_now()
        write_json(self.user_state_path, state)

        if self.active_mission_path.exists():
            active = read_json(self.active_mission_path)
            active["state"] = "closed"
            active["closed_at"] = state["last_closed_at"]
            active["closure_report"] = closure_report
            write_json(self.active_mission_path, active)

        self.write_dashboard(state)
        return state

    def write_dashboard(self, state: Dict[str, Any]) -> Path:
        path = self.obsidian_root / "00-home" / "dashboard.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        loops = self.load_open_loops()
        lines = [
            "# Konoha Dashboard",
            "",
            "## Estado actual",
            "",
            f"- Actor: `{self.actor}`",
            f"- Sesiones: `{state.get('session_count', 0)}`",
            f"- Última sesión: `{state.get('last_session_at') or 'none'}`",
            f"- Misión activa: `{state.get('active_mission_id') or 'none'}`",
            f"- Última misión: `{state.get('last_mission_id') or 'none'}`",
            "",
            "## Seguimientos abiertos",
            "",
        ]
        if loops:
            lines.extend(
                f"- [{item.get('status', 'open')}] "
                f"{item.get('summary', item.get('id', 'follow-up'))}"
                for item in loops
            )
        else:
            lines.append("- Ninguno registrado.")
        lines += [
            "",
            "## Authority",
            "",
            "- Memory is evidence only.",
            "- Memory does not authorize action.",
            "- Summaries are not truth.",
            "",
        ]
        path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
        return path

    def write_session_note(self, handoff: Dict[str, Any]) -> Path:
        stamp = utc_now().replace(":", "").replace("+00:00", "Z")
        path = (
            self.obsidian_root
            / "10-sessions"
            / f"{stamp}_session_handoff.md"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        active = handoff.get("active_mission") or {}
        lines = [
            "---",
            "type: konoha_session_handoff",
            f"created_at: {handoff['created_at']}",
            f"actor: {self.actor}",
            "---",
            "",
            "# Session handoff",
            "",
            f"- Active mission: `{active.get('mission_id', 'none')}`",
            f"- State: `{active.get('state', 'none')}`",
            f"- Next safe action: {handoff['next_safe_action']}",
            "",
            "Memory is evidence only and does not authorize action.",
            "",
        ]
        path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
        return path
