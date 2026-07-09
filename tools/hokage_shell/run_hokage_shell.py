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
        "Hokage Mission Control v3.1.1",
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
        "terminal_shell": ["v3.1.0", "v3.1.1", "Hokage Terminal Shell", "terminal", "persona"],
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
        audit = {
            "status": "skipped",
            "blockers": [f"local model audit tool not found: {script}"],
            "usage": {},
        }
        summary = summarize_audit_result(audit, paths.repo_root)
        report_path = write_local_audit_markdown(paths, mission_id, audit, summary)
        audit["markdown_report_path"] = str(report_path)
        return audit

    model = model or choose_ollama_model()
    if not model:
        audit = {
            "status": "skipped",
            "blockers": ["No Ollama model available. Run local model recommendation/download first."],
            "usage": {},
        }
        summary = summarize_audit_result(audit, paths.repo_root)
        report_path = write_local_audit_markdown(paths, mission_id, audit, summary)
        audit["markdown_report_path"] = str(report_path)
        return audit

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
    patch_plan_path = output_dir / f"{audit_id}_repo_patch_plan.json"
    report = read_json(report_path) if report_path.exists() else {}
    root = _audit_root(report)

    audit = {
        "status": "passed" if proc.returncode == 0 else "failed",
        "model": model,
        "exit_code": proc.returncode,
        "stdout_preview": proc.stdout[-2000:],
        "stderr_preview": proc.stderr[-2000:],
        "parsed_stdout": parsed,
        "report_path": str(report_path) if report_path.exists() else None,
        "patch_plan_path": str(patch_plan_path) if patch_plan_path.exists() else str(patch_plan_path),
        "usage": root.get("usage") or {},
        "validated_issues": root.get("validated_issues"),
        "suppressed_issues": root.get("suppressed_issues"),
        "inconsistencies": root.get("inconsistencies"),
    }
    summary = summarize_audit_result(audit, paths.repo_root)
    markdown_report = write_local_audit_markdown(paths, mission_id, audit, summary)
    audit["markdown_report_path"] = str(markdown_report)
    audit["summary"] = summary
    return audit

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



def step_reports_dir(paths: ShellPaths, mission_id: str) -> Path:
    folder = session_dir(paths, mission_id) / "step_reports"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def next_step_report_path(paths: ShellPaths, mission_id: str, slug: str) -> Path:
    folder = step_reports_dir(paths, mission_id)
    count = len(sorted(folder.glob("*.md"))) + 1
    return folder / f"{count:03d}_{safe_slug(slug)}.md"


def short_path(path_value: Optional[str], repo_root: Optional[Path] = None) -> str:
    if not path_value:
        return "not_written"
    path = Path(path_value)
    try:
        if repo_root is not None:
            return str(path.resolve().relative_to(repo_root.resolve()))
    except Exception:
        pass
    try:
        return str(path.relative_to(Path.cwd()))
    except Exception:
        return str(path)


def _audit_root(report: Dict[str, Any]) -> Dict[str, Any]:
    return report.get("audit") if isinstance(report.get("audit"), dict) else report


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _issue_lines(issues: List[Any], label: str) -> List[str]:
    if not issues:
        return [f"- {label}: none."]
    lines = []
    for issue in issues:
        if isinstance(issue, dict):
            issue_id = issue.get("id", "issue")
            severity = issue.get("severity", "unknown")
            status = issue.get("status") or issue.get("suppression_reason") or ""
            detail = f" ({status})" if status else ""
            evidence = issue.get("evidence") or issue.get("reason") or ""
            lines.append(f"- {issue_id} [{severity}]{detail}: {evidence}")
        else:
            lines.append(f"- {issue}")
    return lines


def load_patch_plan(path_value: Optional[str]) -> Dict[str, Any]:
    if not path_value:
        return {}
    path = Path(path_value)
    if not path.exists():
        return {}
    try:
        return read_json(path)
    except Exception:
        return {}


def summarize_audit_result(audit: Dict[str, Any], repo_root: Optional[Path] = None) -> Dict[str, Any]:
    report: Dict[str, Any] = {}
    report_path = audit.get("report_path")
    if report_path and Path(report_path).exists():
        try:
            report = read_json(Path(report_path))
        except Exception:
            report = {}
    root = _audit_root(report)

    validated = _as_list(root.get("validated_issues") or audit.get("validated_issues"))
    suppressed = _as_list(root.get("suppressed_issues") or audit.get("suppressed_issues"))
    suggested = _as_list(
        root.get("model_suggested_issues")
        or root.get("inconsistencies")
        or audit.get("inconsistencies")
    )
    patch_plan = load_patch_plan(audit.get("patch_plan_path"))
    operations = _as_list(patch_plan.get("operations"))
    usage = root.get("usage") or audit.get("usage") or {}

    if audit.get("status") == "skipped":
        recommendation = "Audit skipped. Resolve blockers before review."
    elif validated:
        recommendation = "Human review required. Patch may be proposed from validated issues only."
    elif suppressed:
        recommendation = "No patch recommended. Suggested issue(s) were suppressed by deterministic evidence."
    elif operations:
        recommendation = "Patch plan contains operations. Review before approval."
    else:
        recommendation = "No patch recommended."

    return {
        "status": audit.get("status"),
        "model": audit.get("model") or root.get("model"),
        "provider": root.get("provider") or "ollama",
        "usage": usage,
        "validated_count": len(validated),
        "suppressed_count": len(suppressed),
        "suggested_count": len(suggested),
        "patch_operations_count": len(operations),
        "validated_issues": validated,
        "suppressed_issues": suppressed,
        "suggested_issues": suggested,
        "patch_operations": operations,
        "recommendation": recommendation,
        "report_path": report_path,
        "patch_plan_path": audit.get("patch_plan_path"),
        "markdown_report_path": audit.get("markdown_report_path"),
        "blockers": _as_list(audit.get("blockers")),
    }


def audit_summary_lines(summary: Dict[str, Any]) -> List[str]:
    usage = summary.get("usage") or {}
    lines = [
        f"status: {summary.get('status')}",
        f"model: {summary.get('model') or 'not_available'}",
        f"suggested issues: {summary.get('suggested_count', 0)}",
        f"validated issues: {summary.get('validated_count', 0)}",
        f"suppressed issues: {summary.get('suppressed_count', 0)}",
        f"patch operations: {summary.get('patch_operations_count', 0)}",
        f"recommendation: {summary.get('recommendation')}",
    ]
    if usage:
        lines.append(
            "tokens: "
            f"input={usage.get('input_tokens', 'n/a')} "
            f"output={usage.get('output_tokens', 'n/a')} "
            f"source={usage.get('usage_source', 'n/a')}"
        )
    for blocker in summary.get("blockers") or []:
        lines.append(f"blocker: {blocker}")
    return lines


def write_deterministic_scan_markdown(paths: ShellPaths, mission_id: str, scan: Dict[str, Any], scan_json_path: Path) -> Path:
    report_path = next_step_report_path(paths, mission_id, "deterministic_repo_scan")
    lines = [
        f"# Step: deterministic repo scan",
        "",
        "## Summary",
        "",
        f"- status: `{scan.get('status')}`",
        "- deterministic scan is evidence only.",
        "- scan does not authorize patching.",
        "",
        "## Marker coverage",
        "",
    ]
    for item in scan.get("marker_summary", []):
        lines.append(f"- {item}")
    lines += [
        "",
        "## Files considered",
        "",
    ]
    for item in scan.get("files_considered", []):
        lines.append(f"- `{item}`")
    lines += [
        "",
        "## Evidence JSON",
        "",
        f"- `{short_path(str(scan_json_path), paths.repo_root)}`",
        "",
        "## Next step",
        "",
        "Review marker coverage. Invoke local model audit only if human approval is explicit.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return report_path


def write_local_audit_markdown(paths: ShellPaths, mission_id: str, audit: Dict[str, Any], summary: Dict[str, Any]) -> Path:
    report_path = next_step_report_path(paths, mission_id, "local_model_audit_review")
    usage = summary.get("usage") or {}
    lines = [
        "# Step: local model repo audit review",
        "",
        "## Summary",
        "",
        f"- status: `{summary.get('status')}`",
        f"- provider: `{summary.get('provider')}`",
        f"- model: `{summary.get('model') or 'not_available'}`",
        f"- suggested issues: `{summary.get('suggested_count', 0)}`",
        f"- validated issues: `{summary.get('validated_count', 0)}`",
        f"- suppressed issues: `{summary.get('suppressed_count', 0)}`",
        f"- patch operations: `{summary.get('patch_operations_count', 0)}`",
        f"- recommendation: **{summary.get('recommendation')}**",
        "",
        "Local model output is evidence only. Patch plans are not permission.",
        "",
        "## Token usage",
        "",
    ]
    if usage:
        for key in sorted(usage):
            lines.append(f"- {key}: `{usage[key]}`")
    else:
        lines.append("- Not recorded.")
    lines += [
        "",
        "## Model suggested issues",
        "",
        *_issue_lines(summary.get("suggested_issues", []), "model suggested issues"),
        "",
        "## Validated issues",
        "",
        *_issue_lines(summary.get("validated_issues", []), "validated issues"),
        "",
        "## Suppressed issues",
        "",
        *_issue_lines(summary.get("suppressed_issues", []), "suppressed issues"),
        "",
        "## Patch operations",
        "",
    ]
    operations = summary.get("patch_operations") or []
    if operations:
        for idx, op in enumerate(operations, start=1):
            if isinstance(op, dict):
                lines.append(f"{idx}. `{op.get('operation', 'operation')}` on `{op.get('path', 'unknown')}`")
            else:
                lines.append(f"{idx}. {op}")
    else:
        lines.append("- No patch operation recommended.")
    lines += [
        "",
        "## Evidence files",
        "",
        f"- audit JSON: `{short_path(summary.get('report_path'), paths.repo_root)}`",
        f"- patch plan JSON: `{short_path(summary.get('patch_plan_path'), paths.repo_root)}`",
        "",
        "## Review controls",
        "",
        "- View this report before approving anything.",
        "- View raw JSON only when technical inspection is needed.",
        "- Apply patches only through the approved patch flow.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return report_path


def latest_step_report(paths: ShellPaths, mission_id: Optional[str]) -> Optional[Path]:
    if not mission_id:
        return None
    folder = step_reports_dir(paths, mission_id)
    reports = sorted(folder.glob("*.md"))
    return reports[-1] if reports else None


def latest_audit_json(paths: ShellPaths, mission_id: Optional[str]) -> Optional[Path]:
    if not mission_id:
        return None
    folder = session_dir(paths, mission_id)
    candidates = sorted(folder.glob("**/*_repo_consistency_audit.json"))
    return candidates[-1] if candidates else None


def latest_patch_plan_json(paths: ShellPaths, mission_id: Optional[str]) -> Optional[Path]:
    if not mission_id:
        return None
    folder = session_dir(paths, mission_id)
    candidates = sorted(folder.glob("**/*_repo_patch_plan.json"))
    return candidates[-1] if candidates else None


def render_file_preview(path: Path, max_lines: int = 80) -> str:
    text = read_text_if_exists(path, max_chars=80_000)
    lines = text.splitlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f"... ({len(text.splitlines()) - max_lines} more lines; open with viewer for full report)"]
    return "\n".join(lines)


def view_file(path: Optional[Path], *, title: str = "Details", prefer_pager: bool = True) -> None:
    if path is None or not path.exists():
        print(frame(title, ["No detail file available."]))
        return

    if prefer_pager and sys.stdout.isatty():
        for cmd in (["glow", str(path)], ["bat", "--paging=always", str(path)], ["less", "-R", str(path)]):
            if shutil.which(cmd[0]):
                subprocess.run(cmd)
                return

    print(frame(title, render_file_preview(path).splitlines(), width=96))


def print_review_summary(paths: ShellPaths, mission_id: Optional[str]) -> None:
    report = latest_step_report(paths, mission_id)
    if report is None:
        print(frame("Review Latest Result", ["No report available yet. Run a scan or audit first."]))
        return
    preview = render_file_preview(report, max_lines=28).splitlines()
    print(frame("Review Latest Result", preview, width=96))


def review_latest_result(paths: ShellPaths, mission_id: Optional[str]) -> None:
    if not mission_id:
        print(frame("Review Latest Result", ["No active mission. Start or continue a mission first."]))
        return
    while True:
        print_review_summary(paths, mission_id)
        print(frame("Review Options", [
            "v. view markdown report",
            "j. view raw audit JSON",
            "p. view patch plan JSON",
            "b. back",
        ]))
        choice = input("Review> ").strip().lower()
        if choice in {"", "b", "back"}:
            return
        if choice == "v":
            view_file(latest_step_report(paths, mission_id), title="Markdown Report")
            continue
        if choice == "j":
            view_file(latest_audit_json(paths, mission_id), title="Raw Audit JSON")
            continue
        if choice == "p":
            view_file(latest_patch_plan_json(paths, mission_id), title="Patch Plan JSON")
            continue
        print(frame("Review", ["Unknown option."]))


def print_timeline(paths: ShellPaths, mission_id: Optional[str]) -> None:
    if not mission_id:
        print(frame("Mission Timeline", ["No active mission."]))
        return
    path = events_path(paths, mission_id)
    if not path.exists():
        print(frame("Mission Timeline", ["No events recorded yet."]))
        return
    lines: List[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(raw)
            lines.append(f"{event.get('created_at')} · {event.get('event_type')}")
        except Exception:
            lines.append(raw[:120])
    print(frame("Mission Timeline", clamp_lines(lines, max_lines=24), width=96))


def latest_mission_id(paths: ShellPaths) -> Optional[str]:
    folder = paths.workspace_root / "missions"
    missions = sorted([p for p in folder.glob("*") if p.is_dir()]) if folder.exists() else []
    return missions[-1].name if missions else None


def run_smoke(args: argparse.Namespace) -> int:
    paths = make_paths(args.repo_root, args.workspace_root, args.memory_root)
    persona = load_persona(args.persona, paths.repo_root)
    session = create_session(paths, args.task, persona, args.mission_id)
    mission_id = session["mission_id"]

    deterministic = deterministic_repo_scan(paths.repo_root)
    scan_path = session_dir(paths, mission_id) / "deterministic_repo_scan.json"
    write_json(scan_path, deterministic)
    scan_md_path = write_deterministic_scan_markdown(paths, mission_id, deterministic, scan_path)
    append_event(paths, mission_id, "deterministic_repo_scan_recorded", {"status": deterministic["status"], "path": str(scan_path), "markdown_report": str(scan_md_path)})

    summary: Dict[str, Any] = {
        "deterministic_scan": deterministic,
        "local_model_audit": None,
    }

    if args.run_local_audit:
        audit = run_local_model_audit(paths, mission_id, args.model, no_animation=args.no_animation)
        summary["local_model_audit"] = audit
        append_event(paths, mission_id, "local_model_audit_recorded", {"status": audit.get("status"), "usage": audit.get("usage"), "markdown_report": audit.get("markdown_report_path")})

    session = update_session(
        paths,
        mission_id,
        state="needs_human_review",
        outputs={
            "deterministic_repo_scan": str(scan_path),
            "deterministic_repo_scan_markdown": str(scan_md_path),
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
        "latest_report_path": str(latest_step_report(paths, mission_id) or ""),
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
        "commands": ["interactive", "smoke", "review", "personas", "states"],
        "approval_tokens": APPROVAL_TOKENS,
        "boundaries": BOUNDARIES,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def interactive_loop(args: argparse.Namespace) -> int:
    paths = make_paths(args.repo_root, args.workspace_root, args.memory_root)
    persona = load_persona(args.persona, paths.repo_root)
    print_header(persona, plain=args.plain)

    active_mission_id: Optional[str] = latest_mission_id(paths) if args.continue_latest else None
    if active_mission_id:
        print_hokage(persona, f"Continuando misión local: {active_mission_id}", plain=args.plain)

    while True:
        print_agents([
            {"name": "hokage", "state": "waiting_user_input", "provider": "terminal"},
            {"name": "deterministic-guard", "state": "idle", "provider": "local"},
            {"name": "repo-auditor", "state": "idle", "provider": "ollama"},
            {"name": "memory", "state": "idle", "provider": "obsidian-local"},
        ])
        mission_label = active_mission_id or "none"
        print(frame("Menu", [
            f"active mission: {mission_label}",
            "1. Start new mission",
            "2. Run deterministic repo scan",
            "3. Run local model repo audit",
            "4. Review latest result",
            "5. View mission timeline",
            "6. Memory summary",
            "7. Change persona",
            "8. Show approval tokens",
            "9. Continue latest mission",
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
            md = write_deterministic_scan_markdown(paths, active_mission_id, scan, out)
            append_event(paths, active_mission_id, "deterministic_repo_scan_recorded", {"status": scan["status"], "path": str(out), "markdown_report": str(md)})
            lines = [
                f"status: {scan.get('status')}",
                "summary: marker coverage recorded",
                "next: review result or run local model audit",
            ] + scan["marker_summary"]
            print(frame("Deterministic Guard", lines))
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
            append_event(paths, active_mission_id, "local_model_audit_recorded", {"status": audit.get("status"), "usage": audit.get("usage"), "markdown_report": audit.get("markdown_report_path")})
            summary = audit.get("summary") or summarize_audit_result(audit, paths.repo_root)
            print(frame("Repo Auditor Summary", audit_summary_lines(summary)))
            if summary.get("suppressed_count", 0) > 0 and summary.get("validated_count", 0) == 0:
                print_hokage(persona, "El agente local parece haber producido un falso positivo. Qué giro tan completamente inesperado. No recomiendo patch.", plain=args.plain)
            print(frame("Next", [
                "Use option 4 to review the Markdown report.",
                "Raw JSON and patch plan are hidden unless requested.",
            ]))
            continue

        if choice == "4":
            review_latest_result(paths, active_mission_id)
            continue

        if choice == "5":
            print_timeline(paths, active_mission_id)
            continue

        if choice == "6":
            summary = memory_summary(paths.memory_root)
            print(frame("Obsidian Memory", [f"notes_count: {summary['notes_count']}"] + summary["latest_notes"]))
            continue

        if choice == "7":
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

        if choice == "8":
            print(frame("Approval Tokens", [f"{k}: {v}" for k, v in APPROVAL_TOKENS.items()]))
            continue

        if choice == "9":
            latest = latest_mission_id(paths)
            if latest:
                active_mission_id = latest
                print_hokage(persona, f"Continuando misión local: {active_mission_id}", plain=args.plain)
            else:
                print_hokage(persona, "No hay misión local para continuar.", plain=args.plain)
            continue

        print_hokage(persona, "Opción desconocida. Innovador, pero no útil.", plain=args.plain)


def run_review(args: argparse.Namespace) -> int:
    paths = make_paths(args.repo_root, args.workspace_root, args.memory_root)
    mission_id = args.mission_id or latest_mission_id(paths)
    report = latest_step_report(paths, mission_id)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "hokage_shell_review_report",
        "status": "passed" if report else "not_found",
        "mission_id": mission_id,
        "latest_report_path": str(report) if report else None,
        "latest_audit_json": str(latest_audit_json(paths, mission_id)) if latest_audit_json(paths, mission_id) else None,
        "latest_patch_plan_json": str(latest_patch_plan_json(paths, mission_id)) if latest_patch_plan_json(paths, mission_id) else None,
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(frame("Review Latest Result", [
            f"status: {payload['status']}",
            f"mission_id: {payload.get('mission_id')}",
            f"latest_report: {short_path(payload.get('latest_report_path'), paths.repo_root)}",
            f"latest_audit_json: {short_path(payload.get('latest_audit_json'), paths.repo_root)}",
            f"latest_patch_plan_json: {short_path(payload.get('latest_patch_plan_json'), paths.repo_root)}",
        ]))
        if args.view and report:
            view_file(report, title="Markdown Report")
    return 0

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
    parser.add_argument("--continue-latest", action="store_true", help="Continue the latest local mission in interactive mode.")

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

    review = sub.add_parser("review", help="Review latest mission report.")
    review.add_argument("--mission-id", default=None, help="Mission id. Defaults to latest mission.")
    review.add_argument("--json", action="store_true", help="Print JSON.")
    review.add_argument("--view", action="store_true", help="Open or print latest Markdown report.")
    review.set_defaults(func=run_review)

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
