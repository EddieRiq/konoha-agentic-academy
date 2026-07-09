#!/usr/bin/env python3
"""
Konoha Hokage Terminal Shell.

Terminal-first, SSH-friendly supervised mission shell.

This UI does not authorize execution. It only helps a human drive:
- mission creation;
- deterministic repo inspection;
- local model audit handoff;
- evidence and memory recording;
- next-step planning.

All sensitive operations still require explicit approval tokens in the underlying tools.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


SCHEMA_VERSION = "1.0.0"

BOUNDARIES = {
    "autonomous_background_agents": "blocked",
    "unapproved_command_execution": "blocked",
    "unapproved_git_operations": "blocked",
    "unapproved_model_invocation": "blocked",
    "private_context_access_by_default": "blocked",
    "arbitrary_shell": "blocked",
    "network_access_by_default": "blocked_except_explicit_ollama_pull_or_localhost_api",
    "web_ui": "not_required",
}

APPROVAL_TOKENS = {
    "start_mission": "START_HOKAGE_MISSION",
    "inspect_repo": "INSPECT_PUBLIC_REPO",
    "run_local_audit": "RUN_LOCAL_MODEL_AUDIT",
    "write_memory": "WRITE_LOCAL_OBSIDIAN_MEMORY",
}

DEFAULT_PERSONAS: Dict[str, Dict[str, Any]] = {
    "calm_mentor": {
        "persona_id": "calm_mentor",
        "display_name": "Calm Mentor",
        "tone": "clear_practical",
        "humor_level": "low",
        "verbosity": "medium",
        "desk_symbol": "(影)",
        "opening_line": "Primero evidencia, después entusiasmo.",
        "approval_style": "explicit",
        "must_not_override_safety": True,
    },
    "strict_auditor": {
        "persona_id": "strict_auditor",
        "display_name": "Strict Auditor",
        "tone": "formal_control",
        "humor_level": "none",
        "verbosity": "medium",
        "desk_symbol": "[監]",
        "opening_line": "Sin aprobación explícita, no hay acción.",
        "approval_style": "explicit",
        "must_not_override_safety": True,
    },
    "naruto_hokage": {
        "persona_id": "naruto_hokage",
        "display_name": "Naruto Hokage",
        "tone": "energetic_supportive",
        "humor_level": "medium",
        "verbosity": "medium",
        "desk_symbol": "(火)",
        "opening_line": "Vamos misión por misión. Nada de correr sin chakra aprobado.",
        "approval_style": "explicit",
        "must_not_override_safety": True,
    },
    "sarcastic_lab_ai": {
        "persona_id": "sarcastic_lab_ai",
        "display_name": "Sarcastic Lab AI",
        "tone": "dry_sarcastic",
        "humor_level": "medium",
        "verbosity": "medium",
        "desk_symbol": "[AI]",
        "opening_line": "Excelente. Otra misión donde seguramente la evidencia será opcional. Corrijamos eso.",
        "approval_style": "explicit",
        "must_not_override_safety": True,
    },
    "silent_operator": {
        "persona_id": "silent_operator",
        "display_name": "Silent Operator",
        "tone": "minimal",
        "humor_level": "none",
        "verbosity": "low",
        "desk_symbol": "[op]",
        "opening_line": "Ready.",
        "approval_style": "explicit",
        "must_not_override_safety": True,
    },
}


@dataclass
class ShellPaths:
    repo_root: Path
    workspace_root: Path
    memory_root: Path


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_slug(value: str, fallback: str = "mission") -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = value.strip("-._")
    return value[:80] or fallback


def read_text_if_exists(path: Path, max_chars: int = 200_000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        return text[:max_chars]
    return text


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def append_ndjson(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def clamp_lines(lines: Iterable[str], max_lines: int = 10) -> List[str]:
    out = list(lines)
    if len(out) > max_lines:
        return out[:max_lines] + [f"... ({len(out) - max_lines} more)"]
    return out


def frame(title: str, lines: Iterable[str], width: int = 76) -> str:
    title = f" {title} "
    inner_width = max(20, width - 2)
    top = "┌" + title[:inner_width].center(inner_width, "─") + "┐"
    body = []
    for raw in lines:
        if raw is None:
            raw = ""
        wrapped = textwrap.wrap(str(raw), width=inner_width - 2, replace_whitespace=False) or [""]
        for line in wrapped:
            body.append("│ " + line.ljust(inner_width - 2) + " │")
    bottom = "└" + "─" * inner_width + "┘"
    return "\n".join([top] + body + [bottom])


def print_header(persona: Dict[str, Any], plain: bool = False) -> None:
    title_lines = [
        "KONOHAGAKURE TERMINAL",
        "Hokage Mission Control v3.1.0",
        "Terminal-first · SSH-friendly · evidence before action",
    ]
    print(frame("Konoha", title_lines))
    print_hokage(persona, persona.get("opening_line", ""), plain=plain)


def print_hokage(persona: Dict[str, Any], message: str, plain: bool = False) -> None:
    symbol = persona.get("desk_symbol", "(影)")
    display = persona.get("display_name", persona.get("persona_id", "hokage"))
    lines = [
        f"{symbol} Persona: {display}",
        "",
        f'"{message}"',
    ]
    print(frame("Hokage Desk", lines))


def print_agents(agents: List[Dict[str, str]]) -> None:
    lines = []
    if not agents:
        lines = ["No active agents."]
    else:
        for agent in agents:
            lines.append(
                f"[{agent.get('name', 'agent')}] "
                f"{agent.get('state', 'idle'):22} "
                f"provider: {agent.get('provider', 'local')}"
            )
    print(frame("Active Agents", lines))


def animate(label: str, no_animation: bool = False, seconds: float = 0.5) -> None:
    if no_animation or not sys.stdout.isatty():
        print(f"... {label}")
        return
    frames = ["|", "/", "-", "\\"]
    deadline = time.time() + seconds
    i = 0
    while time.time() < deadline:
        sys.stdout.write(f"\r{frames[i % len(frames)]} {label}")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1
    sys.stdout.write("\r" + " " * (len(label) + 4) + "\r")
    sys.stdout.flush()
    print(f"✓ {label}")


def load_persona(persona_id: str, repo_root: Optional[Path] = None) -> Dict[str, Any]:
    if repo_root is not None:
        candidate_paths = [
            repo_root / "personas" / f"{persona_id}.json",
            repo_root / "tools" / "hokage_shell" / "personas" / f"{persona_id}.json",
        ]
        for path in candidate_paths:
            if path.exists():
                payload = read_json(path)
                base = DEFAULT_PERSONAS.get(persona_id, {})
                merged = {**base, **payload}
                merged.setdefault("persona_id", persona_id)
                merged.setdefault("must_not_override_safety", True)
                return merged

    if persona_id in DEFAULT_PERSONAS:
        return dict(DEFAULT_PERSONAS[persona_id])

    raise SystemExit(f"Unknown persona: {persona_id}. Run `personas` to list available personas.")


def list_personas(repo_root: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    personas = dict(DEFAULT_PERSONAS)
    if repo_root is not None:
        for folder in [repo_root / "personas", repo_root / "tools" / "hokage_shell" / "personas"]:
            if folder.exists():
                for path in sorted(folder.glob("*.json")):
                    try:
                        payload = read_json(path)
                        persona_id = payload.get("persona_id") or path.stem
                        personas[persona_id] = {**personas.get(persona_id, {}), **payload, "persona_id": persona_id}
                    except Exception:
                        continue
    return personas


def make_paths(repo_root: str, workspace_root: str, memory_root: str) -> ShellPaths:
    repo = Path(repo_root).resolve()
    workspace = Path(workspace_root).resolve()
    memory = Path(memory_root).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    memory.mkdir(parents=True, exist_ok=True)
    return ShellPaths(repo_root=repo, workspace_root=workspace, memory_root=memory)


def session_dir(paths: ShellPaths, mission_id: str) -> Path:
    return paths.workspace_root / "missions" / mission_id


def session_path(paths: ShellPaths, mission_id: str) -> Path:
    return session_dir(paths, mission_id) / "hokage_shell_session.json"


def events_path(paths: ShellPaths, mission_id: str) -> Path:
    return session_dir(paths, mission_id) / "events.ndjson"


def create_session(paths: ShellPaths, task: str, persona: Dict[str, Any], mission_id: Optional[str] = None) -> Dict[str, Any]:
    slug_base = safe_slug(task.splitlines()[0][:60], "mission")
    mission_id = safe_slug(mission_id or f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{slug_base}")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "hokage_shell_session",
        "mission_id": mission_id,
        "task": task,
        "state": "created",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "repo_root": str(paths.repo_root),
        "workspace_root": str(paths.workspace_root),
        "memory_root": str(paths.memory_root),
        "persona": {
            "persona_id": persona.get("persona_id"),
            "display_name": persona.get("display_name"),
            "tone": persona.get("tone"),
            "must_not_override_safety": bool(persona.get("must_not_override_safety", True)),
        },
        "authority": {
            "ui_is_not_permission": True,
            "hokage_orchestrates_but_does_not_execute": True,
            "model_output_is_evidence_only": True,
            "memory_does_not_authorize_action": True,
        },
        "boundaries": BOUNDARIES,
        "outputs": {},
        "token_usage": {},
        "next_recommended_action": "Request human approval before inspecting repository files.",
    }
    write_json(session_path(paths, mission_id), payload)
    append_event(paths, mission_id, "session_created", {"task": task, "persona": payload["persona"]})
    return payload


def update_session(paths: ShellPaths, mission_id: str, **updates: Any) -> Dict[str, Any]:
    payload = read_json(session_path(paths, mission_id))
    payload.update(updates)
    payload["updated_at"] = utc_now()
    write_json(session_path(paths, mission_id), payload)
    return payload


def append_event(paths: ShellPaths, mission_id: str, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    event = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "hokage_shell_event",
        "event_id": f"{utc_now()}-{safe_slug(event_type)}",
        "mission_id": mission_id,
        "event_type": event_type,
        "created_at": utc_now(),
        "data": data,
        "authority": {
            "event_is_evidence_only": True,
            "event_is_not_permission": True,
        },
    }
    append_ndjson(events_path(paths, mission_id), event)
    return event


def obsidian_safe_filename(value: str) -> str:
    return safe_slug(value).replace("_", "-")


def write_obsidian_mission_note(paths: ShellPaths, session: Dict[str, Any], summary: Dict[str, Any]) -> Path:
    mission_id = session["mission_id"]
    folder = paths.memory_root / "missions"
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}_{obsidian_safe_filename(mission_id)}.md"
    note_path = folder / filename

    tags = ["konoha", "hokage-shell", "mission"]
    if summary.get("deterministic_scan"):
        tags.append("repo-audit")
    if summary.get("local_model_audit"):
        tags.append("local-model")

    yaml_tags = "\n".join(f"  - {tag}" for tag in tags)
    deterministic_summary = summary.get("deterministic_scan") or {}
    markers = deterministic_summary.get("marker_summary", [])
    marker_lines = "\n".join(f"- {line}" for line in markers) if markers else "- Not run."

    local_audit_summary = summary.get("local_model_audit") or {}
    token_usage = local_audit_summary.get("usage") or {}
    token_lines = "\n".join(f"- {k}: {v}" for k, v in token_usage.items()) if token_usage else "- Not recorded."

    content = f"""---
type: mission
mission_id: {mission_id}
status: {session.get('state', 'created')}
persona: {session.get('persona', {}).get('persona_id', '')}
created_at: {session.get('created_at', '')}
tags:
{yaml_tags}
---

# Mission: {mission_id}

## User task

{session.get('task', '').strip()}

## Hokage state

- UI is not permission.
- Hokage orchestrates but does not execute.
- Model output is evidence only.
- Memory does not authorize action.

## Deterministic repo markers

{marker_lines}

## Token usage

{token_lines}

## Next step

{session.get('next_recommended_action', 'Review evidence and choose next action.')}
"""
    note_path.write_text(content, encoding="utf-8", newline="\n")
    return note_path


def scan_file_for_terms(path: Path, terms: Iterable[str]) -> List[Dict[str, Any]]:
    text = read_text_if_exists(path)
    hits: List[Dict[str, Any]] = []
    if not text:
        return hits
    lower_terms = [t.lower() for t in terms]
    for lineno, line in enumerate(text.splitlines(), start=1):
        lower = line.lower()
        for term, lower_term in zip(terms, lower_terms):
            if lower_term in lower:
                hits.append({"path": str(path), "line": lineno, "term": term, "text": line.strip()[:240]})
    return hits


def deterministic_repo_scan(repo_root: Path) -> Dict[str, Any]:
    candidates = [
        repo_root / "README.md",
        repo_root / "CHANGELOG.md",
        repo_root / "docs" / "roadmap.md",
        repo_root / "docs" / "guides" / "README.md",
    ]
    marker_groups = {
        "beta_runtime_status": ["Konoha Beta", "v3.0.0", "Real Supervised Task Runtime", "tools/beta_runtime"],
        "local_model_bootstrap": ["v3.0.1", "Local Model Bootstrap", "Ollama", "local model"],
        "repo_audit_guard": ["v3.0.2", "Deterministic Guard", "suppressed", "validated issues"],
        "terminal_shell": ["v3.1.0", "Hokage Terminal Shell", "terminal", "persona"],
    }

    coverage: Dict[str, List[Dict[str, Any]]] = {}
    for group, terms in marker_groups.items():
        hits: List[Dict[str, Any]] = []
        for path in candidates:
            hits.extend(scan_file_for_terms(path, terms))
        coverage[group] = hits

    readme_hits = coverage["beta_runtime_status"] + coverage["local_model_bootstrap"]
    status = "passed" if readme_hits else "needs_human_review"

    marker_summary = []
    for group, hits in coverage.items():
        marker_summary.append(f"{group}: {len(hits)} hit(s)")

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "hokage_deterministic_repo_scan",
        "generated_at": utc_now(),
        "repo_root": str(repo_root),
        "status": status,
        "files_considered": [str(p.relative_to(repo_root)) for p in candidates if p.exists()],
        "coverage": coverage,
        "marker_summary": marker_summary,
        "authority": {
            "deterministic_scan_is_evidence_only": True,
            "scan_does_not_authorize_patch": True,
        },
    }


def choose_ollama_model() -> Optional[str]:
    ollama = shutil.which("ollama")
    if not ollama:
        return None
    try:
        proc = subprocess.run([ollama, "ls"], text=True, capture_output=True, timeout=15)
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    first = lines[1].split()
    return first[0] if first else None


def run_local_model_audit(paths: ShellPaths, mission_id: str, model: Optional[str], no_animation: bool = False) -> Dict[str, Any]:
    script = paths.repo_root / "tools" / "local_model_audit" / "manage_local_model_audit.py"
    if not script.exists():
        return {
            "status": "skipped",
            "blockers": [f"local model audit tool not found: {script}"],
            "usage": {},
        }

    model = model or choose_ollama_model()
    if not model:
        return {
            "status": "skipped",
            "blockers": ["No Ollama model available. Run local model recommendation/download first."],
            "usage": {},
        }

    output_dir = session_dir(paths, mission_id) / "local_model_audit"
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_id = f"{mission_id}-hokage-shell-audit"

    cmd = [
        sys.executable,
        str(script),
        "audit-repo",
        "--repo-root",
        str(paths.repo_root),
        "--audit-id",
        audit_id,
        "--model",
        model,
        "--output-dir",
        str(output_dir),
        "--use-ollama",
        "--allow-localhost",
        "--confirm-audit",
        "--approval-token",
        "RUN_LOCAL_MODEL_AUDIT",
        "--force",
        "--json",
    ]

    animate(f"repo-auditor invoking local model {model}", no_animation=no_animation, seconds=0.8)
    proc = subprocess.run(cmd, cwd=str(paths.repo_root), text=True, capture_output=True, timeout=300)

    parsed: Optional[Dict[str, Any]] = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except Exception:
            parsed = None

    report_path = output_dir / f"{audit_id}_repo_consistency_audit.json"
    report = read_json(report_path) if report_path.exists() else {}

    return {
        "status": "passed" if proc.returncode == 0 else "failed",
        "model": model,
        "exit_code": proc.returncode,
        "stdout_preview": proc.stdout[-2000:],
        "stderr_preview": proc.stderr[-2000:],
        "parsed_stdout": parsed,
        "report_path": str(report_path) if report_path.exists() else None,
        "patch_plan_path": str(output_dir / f"{audit_id}_repo_patch_plan.json"),
        "usage": report.get("usage") or report.get("audit", {}).get("usage") or {},
        "validated_issues": report.get("validated_issues") or report.get("audit", {}).get("validated_issues"),
        "suppressed_issues": report.get("suppressed_issues") or report.get("audit", {}).get("suppressed_issues"),
        "inconsistencies": report.get("inconsistencies") or report.get("audit", {}).get("inconsistencies"),
    }


def memory_summary(memory_root: Path) -> Dict[str, Any]:
    notes = sorted(memory_root.glob("**/*.md")) if memory_root.exists() else []
    return {
        "memory_root": str(memory_root),
        "notes_count": len(notes),
        "latest_notes": [str(p.relative_to(memory_root)) for p in notes[-10:]],
    }


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    value = input(f"{prompt} {suffix} ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes", "s", "si", "sí"}


def run_smoke(args: argparse.Namespace) -> int:
    paths = make_paths(args.repo_root, args.workspace_root, args.memory_root)
    persona = load_persona(args.persona, paths.repo_root)
    session = create_session(paths, args.task, persona, args.mission_id)
    mission_id = session["mission_id"]

    deterministic = deterministic_repo_scan(paths.repo_root)
    scan_path = session_dir(paths, mission_id) / "deterministic_repo_scan.json"
    write_json(scan_path, deterministic)
    append_event(paths, mission_id, "deterministic_repo_scan_recorded", {"status": deterministic["status"], "path": str(scan_path)})

    summary: Dict[str, Any] = {
        "deterministic_scan": deterministic,
        "local_model_audit": None,
    }

    if args.run_local_audit:
        audit = run_local_model_audit(paths, mission_id, args.model, no_animation=args.no_animation)
        summary["local_model_audit"] = audit
        append_event(paths, mission_id, "local_model_audit_recorded", {"status": audit.get("status"), "usage": audit.get("usage")})

    session = update_session(
        paths,
        mission_id,
        state="needs_human_review",
        outputs={
            "deterministic_repo_scan": str(scan_path),
            "events": str(events_path(paths, mission_id)),
        },
        token_usage=(summary.get("local_model_audit") or {}).get("usage") or {},
        next_recommended_action="Review evidence. Do not apply patches unless validated issues exist and human approval is explicit.",
    )

    note_path = write_obsidian_mission_note(paths, session, summary)
    append_event(paths, mission_id, "obsidian_memory_written", {"path": str(note_path)})

    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "hokage_shell_smoke_report",
        "status": "passed",
        "command": "smoke",
        "mission_id": mission_id,
        "session_path": str(session_path(paths, mission_id)),
        "events_path": str(events_path(paths, mission_id)),
        "memory_note_path": str(note_path),
        "deterministic_status": deterministic["status"],
        "local_model_audit_status": (summary.get("local_model_audit") or {}).get("status"),
        "boundaries": BOUNDARIES,
    }

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print_header(persona, plain=args.plain)
        print_agents([
            {"name": "deterministic-guard", "state": deterministic["status"], "provider": "local"},
            {"name": "repo-auditor", "state": report.get("local_model_audit_status") or "not_run", "provider": "ollama"},
            {"name": "memory-writer", "state": "written", "provider": "obsidian-local"},
        ])
        print(frame("Smoke Report", [
            f"status: {report['status']}",
            f"mission_id: {mission_id}",
            f"session: {report['session_path']}",
            f"memory: {report['memory_note_path']}",
            f"deterministic: {report['deterministic_status']}",
            f"local_model_audit: {report.get('local_model_audit_status')}",
        ]))
    return 0


def run_personas(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve() if args.repo_root else None
    personas = list_personas(repo_root)
    if args.json:
        print(json.dumps({"personas": personas, "status": "passed"}, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        for persona_id, payload in sorted(personas.items()):
            print(f"{persona_id:18} {payload.get('display_name', ''):24} tone={payload.get('tone', '')}")
    return 0


def run_states(args: argparse.Namespace) -> int:
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "hokage_shell_states",
        "status": "passed",
        "commands": ["interactive", "smoke", "personas", "states"],
        "approval_tokens": APPROVAL_TOKENS,
        "boundaries": BOUNDARIES,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def interactive_loop(args: argparse.Namespace) -> int:
    paths = make_paths(args.repo_root, args.workspace_root, args.memory_root)
    persona = load_persona(args.persona, paths.repo_root)
    print_header(persona, plain=args.plain)

    active_mission_id: Optional[str] = None

    while True:
        print_agents([
            {"name": "hokage", "state": "waiting_user_input", "provider": "terminal"},
            {"name": "deterministic-guard", "state": "idle", "provider": "local"},
            {"name": "repo-auditor", "state": "idle", "provider": "ollama"},
            {"name": "memory", "state": "idle", "provider": "obsidian-local"},
        ])
        print(frame("Menu", [
            "1. Start new mission",
            "2. Run deterministic repo scan",
            "3. Run local model repo audit",
            "4. Memory summary",
            "5. Change persona",
            "6. Show approval tokens",
            "0. Exit",
        ]))
        choice = input("Mission> ").strip()

        if choice == "0":
            print_hokage(persona, "Cierro la consola. Sorprendentemente, sin romper nada.", plain=args.plain)
            return 0

        if choice == "1":
            task = input("Task> ").strip()
            if not task:
                print_hokage(persona, "Una misión vacía. Filosóficamente interesante, operativamente inútil.", plain=args.plain)
                continue
            print_hokage(persona, "Voy a crear Mission Charter local. No voy a inspeccionar archivos todavía.", plain=args.plain)
            if not ask_yes_no(f"Approve {APPROVAL_TOKENS['start_mission']}?"):
                print_hokage(persona, "Misión no iniciada. La prudencia ganó por una vez.", plain=args.plain)
                continue
            session = create_session(paths, task, persona)
            active_mission_id = session["mission_id"]
            note_path = write_obsidian_mission_note(paths, session, {"deterministic_scan": None, "local_model_audit": None})
            append_event(paths, active_mission_id, "obsidian_memory_written", {"path": str(note_path)})
            print_hokage(persona, f"Misión creada: {active_mission_id}", plain=args.plain)
            continue

        if choice == "2":
            if not active_mission_id:
                print_hokage(persona, "Primero iniciá una misión. Sí, el orden sigue importando.", plain=args.plain)
                continue
            print_hokage(persona, "Voy a inspeccionar archivos públicos del repo con chequeos determinísticos.", plain=args.plain)
            if not ask_yes_no(f"Approve {APPROVAL_TOKENS['inspect_repo']}?"):
                print_hokage(persona, "Inspección cancelada.", plain=args.plain)
                continue
            animate("deterministic-guard scanning README/docs", no_animation=args.no_animation)
            scan = deterministic_repo_scan(paths.repo_root)
            out = session_dir(paths, active_mission_id) / "deterministic_repo_scan.json"
            write_json(out, scan)
            append_event(paths, active_mission_id, "deterministic_repo_scan_recorded", {"status": scan["status"], "path": str(out)})
            print(frame("Deterministic Guard", scan["marker_summary"]))
            continue

        if choice == "3":
            if not active_mission_id:
                print_hokage(persona, "Primero iniciá una misión.", plain=args.plain)
                continue
            print_hokage(persona, "Voy a invocar Ollama local. La salida será evidencia, no verdad.", plain=args.plain)
            if not ask_yes_no(f"Approve {APPROVAL_TOKENS['run_local_audit']}?"):
                print_hokage(persona, "Local model audit cancelado.", plain=args.plain)
                continue
            model = input("Model [auto]: ").strip() or None
            audit = run_local_model_audit(paths, active_mission_id, model, no_animation=args.no_animation)
            append_event(paths, active_mission_id, "local_model_audit_recorded", {"status": audit.get("status"), "usage": audit.get("usage")})
            lines = [
                f"status: {audit.get('status')}",
                f"model: {audit.get('model')}",
                f"usage: {audit.get('usage')}",
                f"report: {audit.get('report_path')}",
                f"patch_plan: {audit.get('patch_plan_path')}",
            ]
            if audit.get("blockers"):
                lines += [f"blocker: {b}" for b in audit["blockers"]]
            print(frame("Repo Auditor", lines))
            continue

        if choice == "4":
            summary = memory_summary(paths.memory_root)
            print(frame("Obsidian Memory", [f"notes_count: {summary['notes_count']}"] + summary["latest_notes"]))
            continue

        if choice == "5":
            personas = list_personas(paths.repo_root)
            print(frame("Personas", [f"{k}: {v.get('display_name')} ({v.get('tone')})" for k, v in sorted(personas.items())]))
            new_id = input("Persona id> ").strip()
            if new_id:
                try:
                    persona = load_persona(new_id, paths.repo_root)
                    print_hokage(persona, persona.get("opening_line", "Persona changed."), plain=args.plain)
                except SystemExit as exc:
                    print(str(exc))
            continue

        if choice == "6":
            print(frame("Approval Tokens", [f"{k}: {v}" for k, v in APPROVAL_TOKENS.items()]))
            continue

        print_hokage(persona, "Opción desconocida. Innovador, pero no útil.", plain=args.plain)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Konoha Hokage Terminal Shell")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--workspace-root", default="./sandbox/hokage-shell", help="Shell workspace root.")
    parser.add_argument(
        "--memory-root",
        default="alliance/kirigakure/memory/obsidian",
        help="Private Obsidian-compatible memory root.",
    )
    parser.add_argument("--persona", default="sarcastic_lab_ai", help="Persona id.")
    parser.add_argument("--no-animation", action="store_true", help="Disable ASCII spinner animation.")
    parser.add_argument("--plain", action="store_true", help="Plain terminal mode.")

    sub = parser.add_subparsers(dest="command")

    interactive = sub.add_parser("interactive", help="Run interactive Hokage terminal shell.")
    interactive.set_defaults(func=interactive_loop)

    smoke = sub.add_parser("smoke", help="Run non-interactive shell smoke flow.")
    smoke.add_argument("--task", required=True, help="Mission task.")
    smoke.add_argument("--mission-id", default=None, help="Optional mission id.")
    smoke.add_argument("--run-local-audit", action="store_true", help="Invoke existing local model audit tool.")
    smoke.add_argument("--model", default=None, help="Ollama model to use.")
    smoke.add_argument("--json", action="store_true", help="Print JSON report.")
    smoke.set_defaults(func=run_smoke)

    personas = sub.add_parser("personas", help="List available personas.")
    personas.add_argument("--json", action="store_true", help="Print JSON.")
    personas.set_defaults(func=run_personas)

    states = sub.add_parser("states", help="Show commands and approval tokens.")
    states.set_defaults(func=run_states)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        args.command = "interactive"
        args.func = interactive_loop
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
