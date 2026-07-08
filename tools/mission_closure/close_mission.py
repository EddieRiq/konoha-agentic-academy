#!/usr/bin/env python3
"""
Konoha Mission Closure Gate.

Closes a mission only when explicit teachback and human approval evidence are provided.
Writes mission-local closure reports and minimal Yamanaka-compatible memory notes.

Safety boundary:
- no shell
- no network
- no Git
- no private context discovery
- no mission action execution
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

APPROVAL_TOKEN = "CLOSE_MISSION_WITH_TEACHBACK"
TEACHBACK_CONFIRMATION = "I_CAN_EXPLAIN_AND_DEFEND_THIS_MISSION"

SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fail(message: str, *, json_mode: bool = False, report: Optional[Dict[str, Any]] = None) -> int:
    if json_mode:
        payload = report or base_report()
        payload["status"] = "failed"
        payload.setdefault("blockers", []).append(message)
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("MISSION CLOSURE FAILED")
        print("Blocker:", message)
    return 1


def base_report() -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "tool": "mission_closure_gate",
        "status": "preview",
        "target_release": "v2.0.0 - Integration, Memory and Mission Closure",
        "created_at": utc_now(),
        "mission_id": None,
        "closure_id": None,
        "state": {
            "execution": "blocked",
            "filesystem_mutation": "blocked",
            "repository_apply": "blocked",
            "git_operations": "blocked",
            "private_context_access": "blocked",
            "real_model_invocation": "blocked",
            "adapter_invocation": "blocked",
            "network_access": "blocked",
            "teachback": "required",
            "mission_closure": "human_approval_required",
        },
        "paths": {},
        "evidence": {},
        "memory_outputs": [],
        "mission_outputs": [],
        "notification_state": "ready_for_teachback",
        "blockers": [],
        "warnings": [],
    }


def validate_safe_id(value: str, field_name: str) -> None:
    if not value or not SAFE_ID_RE.match(value) or "/" in value or "\\" in value:
        raise ValueError(f"{field_name} must be alphanumeric plus '.', '_' or '-' and may not contain path separators")


def resolve_under(root: Path, *parts: str) -> Path:
    root_resolved = root.resolve()
    candidate = root_resolved.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"path escapes allowed root: {candidate}") from exc
    return candidate


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Dict[str, Any], *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def list_relative_files(root: Path, directory_name: str) -> List[str]:
    directory = root / directory_name
    if not directory.exists():
        return []
    paths: List[str] = []
    for item in sorted(directory.rglob("*")):
        if item.is_file():
            paths.append(item.relative_to(root).as_posix())
    return paths


def ensure_memory_layout(memory_root: Path) -> None:
    for rel in [
        "00-inbox",
        "10-missions",
        "20-decisions",
        "30-tactics",
        "40-failures",
        "50-scroll-proposals",
        "60-context-packs",
        "90-archive",
    ]:
        resolve_under(memory_root, rel).mkdir(parents=True, exist_ok=True)


def markdown_frontmatter(metadata: Dict[str, Any], body: str) -> str:
    lines = ["---"]
    for key in sorted(metadata):
        value = metadata[key]
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {json.dumps(item, ensure_ascii=False)}")
        else:
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.append("---")
    lines.append("")
    lines.append(body.rstrip())
    lines.append("")
    return "\n".join(lines)


def build_mission_memory_note(
    *,
    mission_id: str,
    closure_id: str,
    manifest: Dict[str, Any],
    teachback_summary: str,
    evidence: Dict[str, Any],
) -> str:
    title = manifest.get("title") or mission_id
    body = f"""# Mission memory: {title}

## Mission

- Mission ID: `{mission_id}`
- Closure ID: `{closure_id}`
- Status: closed with teachback

## Teachback

{teachback_summary}

## Evidence inventory

- Reports: {len(evidence.get("reports", []))}
- Plans: {len(evidence.get("plans", []))}
- Approvals: {len(evidence.get("approvals", []))}
- Evidence files: {len(evidence.get("evidence", []))}

## Next action

Review the closure report before using this mission as precedent.
"""
    metadata = {
        "type": "mission_memory",
        "mission_id": mission_id,
        "closure_id": closure_id,
        "status": "closed",
        "created_at": utc_now(),
        "source": "konoha_mission_closure_gate",
    }
    return markdown_frontmatter(metadata, body)


def build_decision_note(*, mission_id: str, closure_id: str, approval_actor: str, closure_reason: str) -> str:
    body = f"""# Mission closure decision

## Decision

Mission `{mission_id}` was closed after explicit human approval and teachback confirmation.

## Approval

- Closure ID: `{closure_id}`
- Human actor: `{approval_actor}`
- Reason: {closure_reason}

## Boundary

This closure records mission completion. It does not authorize new execution, repository apply, Git operations, model calls, adapter calls, private context access, or doctrine rewrite.
"""
    metadata = {
        "type": "decision",
        "decision": "mission_closed",
        "mission_id": mission_id,
        "closure_id": closure_id,
        "created_at": utc_now(),
        "source": "konoha_mission_closure_gate",
    }
    return markdown_frontmatter(metadata, body)


def build_context_pack(*, mission_id: str, closure_id: str, evidence: Dict[str, Any]) -> str:
    sections = []
    for key in ["reports", "plans", "approvals", "evidence"]:
        values = evidence.get(key, [])
        sections.append(f"## {key.title()}")
        if values:
            sections.extend(f"- `{value}`" for value in values)
        else:
            sections.append("- none recorded")
        sections.append("")
    body = f"""# Context pack: {mission_id}

Mission closure context pack generated by Konoha.

{chr(10).join(sections)}

## Boundary

This context pack is an index of evidence paths. It is not ground truth by itself and must be checked against source files when high-stakes decisions depend on it.
"""
    metadata = {
        "type": "context_pack",
        "mission_id": mission_id,
        "closure_id": closure_id,
        "created_at": utc_now(),
        "source": "konoha_mission_closure_gate",
    }
    return markdown_frontmatter(metadata, body)


def build_notification_state(*, mission_id: str, closure_id: str, status: str) -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "mission_id": mission_id,
        "closure_id": closure_id,
        "state": status,
        "requires_user_input": False,
        "requires_human_approval": False,
        "message": "Mission closed with teachback evidence.",
        "updated_at": utc_now(),
        "allowed_next_states": ["archived", "reopened_by_human"],
        "blocked_actions": [
            "automatic_push",
            "arbitrary_shell",
            "private_context_access",
            "background_agent",
            "automatic_doctrine_rewrite",
        ],
    }


def collect_evidence(mission_root: Path) -> Dict[str, List[str]]:
    return {
        "reports": list_relative_files(mission_root, "reports"),
        "plans": list_relative_files(mission_root, "plans"),
        "approvals": list_relative_files(mission_root, "approvals"),
        "evidence": list_relative_files(mission_root, "evidence"),
    }


def validate_workspace(mission_root: Path) -> Dict[str, Any]:
    manifest_path = mission_root / "mission_manifest.json"
    charter_path = mission_root / "charter.md"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing mission manifest: {manifest_path}")
    if not charter_path.exists():
        raise FileNotFoundError(f"missing mission charter: {charter_path}")
    return read_json(manifest_path)


def close_mission(args: argparse.Namespace) -> int:
    report = base_report()
    json_mode = bool(args.json)

    try:
        validate_safe_id(args.mission_id, "mission_id")
        closure_id = args.closure_id or f"{args.mission_id}_closure"
        validate_safe_id(closure_id, "closure_id")

        workspace_root = Path(args.workspace_root)
        memory_root = Path(args.memory_root)
        mission_root = resolve_under(workspace_root, "missions", args.mission_id)
        manifest = validate_workspace(mission_root)

        report["mission_id"] = args.mission_id
        report["closure_id"] = closure_id
        report["paths"] = {
            "workspace_root": str(workspace_root),
            "mission_root": str(mission_root),
            "memory_root": str(memory_root),
        }
        evidence = collect_evidence(mission_root)
        report["evidence"] = evidence

        if not args.confirm_close:
            report["status"] = "preview"
            report["state"]["filesystem_mutation"] = "blocked"
            report["notification_state"] = "ready_for_teachback"
            if json_mode:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print("MISSION CLOSURE PREVIEW")
                print(f"Mission: {args.mission_id}")
                print("Mission closure: preview_only")
                print("Teachback: required")
                print("Filesystem mutation: blocked")
                print("Repository apply: blocked")
                print("Git operations: blocked")
                print("Private context access: blocked")
                print("Real model invocation: blocked")
                print("Network access: blocked")
            return 0

        if args.approval_token != APPROVAL_TOKEN:
            return fail("invalid approval token for mission closure", json_mode=json_mode, report=report)
        if args.teachback_confirmation != TEACHBACK_CONFIRMATION:
            return fail("missing exact teachback confirmation", json_mode=json_mode, report=report)
        if not args.teachback_summary or len(args.teachback_summary.strip()) < 20:
            return fail("teachback summary must be at least 20 characters", json_mode=json_mode, report=report)
        if not args.closure_reason or len(args.closure_reason.strip()) < 10:
            return fail("closure reason must be at least 10 characters", json_mode=json_mode, report=report)

        ensure_memory_layout(memory_root)

        now = utc_now()
        teachback_record = {
            "schema_version": "1.0",
            "mission_id": args.mission_id,
            "closure_id": closure_id,
            "status": "passed",
            "teachback_confirmation": args.teachback_confirmation,
            "teachback_summary": args.teachback_summary,
            "human_actor": args.human_actor,
            "recorded_at": now,
            "non_authority": [
                "teachback does not authorize future actions",
                "teachback does not authorize repository apply",
                "teachback does not authorize Git operations",
                "teachback does not authorize doctrine rewrite",
            ],
        }

        closure_report = dict(report)
        closure_report["status"] = "passed"
        closure_report["created_at"] = now
        closure_report["state"]["filesystem_mutation"] = "mission workspace and explicit memory root only"
        closure_report["state"]["teachback"] = "passed"
        closure_report["state"]["mission_closure"] = "closed_by_human"
        closure_report["notification_state"] = "closed"
        closure_report["closure"] = {
            "human_actor": args.human_actor,
            "closure_reason": args.closure_reason,
            "teachback_confirmation": args.teachback_confirmation,
            "model_output_authority": "evidence_only",
            "tool_output_authority": "evidence_only",
            "mission_closure_authority": "human_approval_only",
        }

        mission_report_path = resolve_under(mission_root, "reports", f"{closure_id}_mission_closure_report.json")
        teachback_path = resolve_under(mission_root, "reports", f"{closure_id}_teachback_record.json")
        status_path = resolve_under(mission_root, "mission_status.json")
        notification_path = resolve_under(mission_root, "reports", f"{closure_id}_notification_state.json")

        mission_memory_path = resolve_under(memory_root, "10-missions", f"{args.mission_id}.md")
        decision_path = resolve_under(memory_root, "20-decisions", f"{args.mission_id}_closure_decision.md")
        context_pack_path = resolve_under(memory_root, "60-context-packs", f"{args.mission_id}_context_pack.md")

        write_json(mission_report_path, closure_report, force=args.force)
        write_json(teachback_path, teachback_record, force=args.force)
        write_json(status_path, {
            "schema_version": "1.0",
            "mission_id": args.mission_id,
            "closure_id": closure_id,
            "status": "closed",
            "closed_at": now,
            "closed_by": args.human_actor,
            "teachback": "passed",
            "notification_state": "closed",
        }, force=True)
        write_json(notification_path, build_notification_state(mission_id=args.mission_id, closure_id=closure_id, status="closed"), force=args.force)

        write_text(
            mission_memory_path,
            build_mission_memory_note(
                mission_id=args.mission_id,
                closure_id=closure_id,
                manifest=manifest,
                teachback_summary=args.teachback_summary,
                evidence=evidence,
            ),
            force=args.force,
        )
        write_text(
            decision_path,
            build_decision_note(
                mission_id=args.mission_id,
                closure_id=closure_id,
                approval_actor=args.human_actor,
                closure_reason=args.closure_reason,
            ),
            force=args.force,
        )
        write_text(
            context_pack_path,
            build_context_pack(mission_id=args.mission_id, closure_id=closure_id, evidence=evidence),
            force=args.force,
        )

        closure_report["mission_outputs"] = [
            str(mission_report_path),
            str(teachback_path),
            str(status_path),
            str(notification_path),
        ]
        closure_report["memory_outputs"] = [
            str(mission_memory_path),
            str(decision_path),
            str(context_pack_path),
        ]
        write_json(mission_report_path, closure_report, force=True)

        if json_mode:
            print(json.dumps(closure_report, indent=2, sort_keys=True))
        else:
            print("MISSION CLOSURE PASSED")
            print(f"Mission: {args.mission_id}")
            print("Teachback: passed")
            print("Mission status: closed")
            print("Filesystem mutation: mission workspace and explicit memory root only")
            print("Repository apply: blocked")
            print("Git operations: blocked")
            print("Private context access: blocked")
            print("Real model invocation: blocked")
            print("Network access: blocked")
            print(f"Report: {mission_report_path}")
        return 0

    except Exception as exc:
        return fail(str(exc), json_mode=json_mode, report=report)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Close a Konoha mission with teachback and Yamanaka memory evidence.")
    parser.add_argument("--workspace-root", required=True, help="Mission workspace root containing missions/<mission_id>.")
    parser.add_argument("--mission-id", required=True, help="Mission ID to close.")
    parser.add_argument("--memory-root", required=True, help="Explicit Yamanaka memory vault root to write closure notes.")
    parser.add_argument("--closure-id", default=None, help="Optional closure ID. Defaults to <mission_id>_closure.")
    parser.add_argument("--human-actor", default="human", help="Human actor recording closure.")
    parser.add_argument("--teachback-summary", default="", help="Human-readable teachback summary.")
    parser.add_argument("--teachback-confirmation", default="", help=f"Exact confirmation: {TEACHBACK_CONFIRMATION}")
    parser.add_argument("--closure-reason", default="", help="Reason for closing the mission.")
    parser.add_argument("--confirm-close", action="store_true", help="Actually close the mission and write reports/memory.")
    parser.add_argument("--approval-token", default="", help=f"Exact approval token: {APPROVAL_TOKEN}")
    parser.add_argument("--force", action="store_true", help="Overwrite closure outputs if they already exist.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return close_mission(args)


if __name__ == "__main__":
    raise SystemExit(main())
