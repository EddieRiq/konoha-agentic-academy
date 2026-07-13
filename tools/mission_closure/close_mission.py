#!/usr/bin/env python3
"""Konoha Mission Closure Gate.

Closes a mission only after explicit execution evidence, approved human review,
structured Teachback evidence, and a separate human closure approval.

Safety boundary:
- no shell
- no network
- no Git
- no private context discovery
- no mission action execution
- --force never overrides contradictory closure evidence
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.teachback.manage_teachback import (  # noqa: E402
    TeachbackError,
    manifest_teachback_policy,
    validate_teachback_record,
)

APPROVAL_TOKEN = "CLOSE_MISSION_WITH_TEACHBACK"
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")

BOUNDARIES = {
    "execution": "blocked",
    "filesystem_mutation": (
        "mission workspace and explicit memory root only"
    ),
    "repository_apply": "blocked",
    "git_operations": "blocked",
    "private_context_access": "blocked",
    "real_model_invocation": "blocked",
    "adapter_invocation": "blocked",
    "network_access": "blocked",
    "mission_closure": "human_approval_required",
}


class MissionClosureError(RuntimeError):
    """Invalid evidence, unsafe path or conflicting closure."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_safe_id(value: str, field_name: str) -> str:
    if (
        not value
        or not SAFE_ID_RE.fullmatch(value)
        or "/" in value
        or "\\" in value
    ):
        raise MissionClosureError(
            f"{field_name} must be alphanumeric plus '.', '_' or '-' "
            "and may not contain path separators"
        )
    return value


def resolve_under(root: Path, *parts: str) -> Path:
    root_resolved = root.resolve()
    candidate = root_resolved.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise MissionClosureError(
            f"path escapes allowed root: {candidate}"
        ) from exc
    return candidate


def read_json(path: Path, label: str = "JSON file") -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MissionClosureError(
            f"{label} not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise MissionClosureError(
            f"{label} JSON invalid at line {exc.lineno}, "
            f"column {exc.colno}"
        ) from exc
    if not isinstance(payload, dict):
        raise MissionClosureError(f"{label} must be a JSON object")
    return payload


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temp.replace(path)


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(content, encoding="utf-8", newline="\n")
    temp.replace(path)


def ensure_new_or_identical_json(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    if path.exists():
        existing = read_json(path, "existing output")
        if canonical_hash(existing) != canonical_hash(payload):
            raise MissionClosureError(
                f"conflicting output already exists: {path}"
            )
        return
    atomic_write_json(path, payload)


def ensure_new_or_identical_text(path: Path, content: str) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing != content:
            raise MissionClosureError(
                f"conflicting output already exists: {path}"
            )
        return
    atomic_write_text(path, content)


def list_relative_files(
    root: Path,
    directory_name: str,
) -> List[str]:
    directory = root / directory_name
    if not directory.exists():
        return []
    return [
        item.relative_to(root).as_posix()
        for item in sorted(directory.rglob("*"))
        if item.is_file()
    ]


def ensure_memory_layout(memory_root: Path) -> None:
    for relative in [
        "00-inbox",
        "10-missions",
        "20-decisions",
        "30-tactics",
        "40-failures",
        "50-scroll-proposals",
        "60-context-packs",
        "90-archive",
    ]:
        resolve_under(memory_root, relative).mkdir(
            parents=True,
            exist_ok=True,
        )


def markdown_frontmatter(
    metadata: Dict[str, Any],
    body: str,
) -> str:
    lines = ["---"]
    for key in sorted(metadata):
        value = metadata[key]
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(
                    f"  - {json.dumps(item, ensure_ascii=False)}"
                )
        else:
            lines.append(
                f"{key}: {json.dumps(value, ensure_ascii=False)}"
            )
    lines.extend(["---", "", body.rstrip(), ""])
    return "\n".join(lines)


def build_mission_memory_note(
    *,
    mission_id: str,
    closure_id: str,
    manifest: Mapping[str, Any],
    teachback: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> str:
    title = manifest.get("title") or mission_id
    body = f"""# Mission memory: {title}

## Mission

- Mission ID: `{mission_id}`
- Closure ID: `{closure_id}`
- Status: closed after execution, review and Teachback evidence

## Teachback

- Result: `{teachback.get('result')}`
- Required level: `{teachback.get('required_level')}`
- Achieved level: `{teachback.get('achieved_level')}`
- Completed by user: `{teachback.get('completed_by_user')}`

{teachback.get('summary') or ''}

## Evidence inventory

- Reports: {len(evidence.get('reports', []))}
- Plans: {len(evidence.get('plans', []))}
- Approvals: {len(evidence.get('approvals', []))}
- Evidence files: {len(evidence.get('evidence', []))}

## Next action

Review source evidence before using this mission as precedent.
"""
    return markdown_frontmatter(
        {
            "type": "mission_memory",
            "mission_id": mission_id,
            "closure_id": closure_id,
            "status": "closed",
            "created_at": utc_now(),
            "source": "konoha_mission_closure_gate",
        },
        body,
    )


def build_decision_note(
    *,
    mission_id: str,
    closure_id: str,
    approval_actor: str,
    closure_reason: str,
    closure_fingerprint: str,
) -> str:
    body = f"""# Mission closure decision

## Decision

Mission `{mission_id}` was closed after explicit human approval and validated
execution, review and Teachback evidence.

## Approval

- Closure ID: `{closure_id}`
- Human actor: `{approval_actor}`
- Reason: {closure_reason}
- Evidence fingerprint: `{closure_fingerprint}`

## Boundary

This closure records mission completion. It does not authorize new execution,
repository apply, Git operations, model calls, adapter calls, private context
access, or doctrine rewrite.
"""
    return markdown_frontmatter(
        {
            "type": "decision",
            "decision": "mission_closed",
            "mission_id": mission_id,
            "closure_id": closure_id,
            "created_at": utc_now(),
            "source": "konoha_mission_closure_gate",
        },
        body,
    )


def build_context_pack(
    *,
    mission_id: str,
    closure_id: str,
    evidence: Mapping[str, Any],
) -> str:
    sections: List[str] = []
    for key in ["reports", "plans", "approvals", "evidence"]:
        values = evidence.get(key, [])
        sections.append(f"## {key.title()}")
        sections.extend(
            [f"- `{value}`" for value in values]
            if values
            else ["- none recorded"]
        )
        sections.append("")
    body = f"""# Context pack: {mission_id}

Mission closure context pack generated by Konoha.

{chr(10).join(sections)}

## Boundary

This context pack is an index of evidence paths. It is not ground truth by
itself and must be checked against source files when high-stakes decisions
depend on it.
"""
    return markdown_frontmatter(
        {
            "type": "context_pack",
            "mission_id": mission_id,
            "closure_id": closure_id,
            "created_at": utc_now(),
            "source": "konoha_mission_closure_gate",
        },
        body,
    )


def build_notification_state(
    *,
    mission_id: str,
    closure_id: str,
) -> Dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "mission_id": mission_id,
        "closure_id": closure_id,
        "state": "closed",
        "requires_user_input": False,
        "requires_human_approval": False,
        "message": (
            "Mission closed with execution, review and "
            "Teachback evidence."
        ),
        "updated_at": utc_now(),
        "allowed_next_states": [
            "archived",
            "reopened_by_human",
        ],
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
        "reports": list_relative_files(
            mission_root,
            "reports",
        ),
        "plans": list_relative_files(mission_root, "plans"),
        "approvals": list_relative_files(
            mission_root,
            "approvals",
        ),
        "evidence": list_relative_files(
            mission_root,
            "evidence",
        ),
    }


def validate_workspace(
    mission_root: Path,
    mission_id: str,
) -> Dict[str, Any]:
    manifest_path = mission_root / "mission_manifest.json"
    charter_path = mission_root / "charter.md"
    if not manifest_path.is_file():
        raise MissionClosureError(
            f"missing mission manifest: {manifest_path}"
        )
    if not charter_path.is_file():
        raise MissionClosureError(
            f"missing mission charter: {charter_path}"
        )
    manifest = read_json(manifest_path, "mission manifest")
    manifest_id = manifest.get("mission_id")
    if manifest_id != mission_id:
        raise MissionClosureError(
            "mission manifest mission_id does not match request"
        )
    return manifest


def resolve_evidence_file(
    mission_root: Path,
    raw: str,
    label: str,
) -> Tuple[str, Path, Dict[str, Any]]:
    if not raw:
        raise MissionClosureError(f"{label} is required")
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = mission_root / candidate
    candidate = candidate.resolve()
    try:
        relative = candidate.relative_to(mission_root.resolve())
    except ValueError as exc:
        raise MissionClosureError(
            f"{label} must stay under mission workspace"
        ) from exc
    payload = read_json(candidate, label)
    return relative.as_posix(), candidate, payload


def validate_execution_evidence(
    payload: Mapping[str, Any],
) -> None:
    status = payload.get("status")
    exit_code = payload.get("exit_code")
    result = payload.get("result")
    result_exit = (
        result.get("exit_code")
        if isinstance(result, dict)
        else None
    )

    passed = (
        status in {"passed", "completed", "success", "closed"}
        or exit_code == 0
        or result_exit == 0
    )
    if not passed:
        raise MissionClosureError(
            "BLOCKED_EXECUTION_INCOMPLETE: execution evidence "
            "does not report a successful completed state"
        )


def review_decision(payload: Mapping[str, Any]) -> Optional[str]:
    candidates: List[Any] = [
        payload.get("review_decision"),
        payload.get("decision"),
        payload.get("status"),
    ]
    review = payload.get("review")
    if isinstance(review, dict):
        candidates.extend(
            [
                review.get("decision"),
                review.get("status"),
            ]
        )
    quality = payload.get("quality_assessment")
    if isinstance(quality, dict):
        candidates.append(quality.get("status"))

    for value in candidates:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {
                "approved",
                "passed",
                "changes_requested",
                "rejected",
                "needs_human_review",
            }:
                return normalized
    return None


def validate_review_evidence(
    payload: Mapping[str, Any],
) -> None:
    decision = review_decision(payload)
    human_approval = payload.get("human_approval")
    reviewed_by = (
        payload.get("reviewed_by")
        or payload.get("human_actor")
    )

    if decision not in {"approved", "passed"}:
        raise MissionClosureError(
            "BLOCKED_REVIEW_INCOMPLETE: review evidence "
            "is not approved"
        )
    if human_approval is False:
        raise MissionClosureError(
            "BLOCKED_REVIEW_INCOMPLETE: review explicitly "
            "denies human approval"
        )
    if not isinstance(reviewed_by, str) or not reviewed_by.strip():
        raise MissionClosureError(
            "BLOCKED_REVIEW_INCOMPLETE: review evidence "
            "must identify the human reviewer"
        )


def validate_teachback_for_closure(
    payload: Mapping[str, Any],
    *,
    mission_id: str,
    manifest: Mapping[str, Any],
    execution_path: str,
    review_path: str,
) -> Dict[str, Any]:
    try:
        record = validate_teachback_record(
            payload,
            expected_mission_id=mission_id,
            manifest=manifest,
        )
    except TeachbackError as exc:
        raise MissionClosureError(str(exc)) from exc

    if record["result"] not in {"passed", "skipped"}:
        status = (
            "NEEDS_CLARIFICATION"
            if record["result"] == "needs_clarification"
            else "TEACHBACK_FAILED"
        )
        raise MissionClosureError(
            f"{status}: Teachback is not eligible for closure"
        )
    if record["result"] == "passed" and (
        record.get("completed_by_user") is not True
    ):
        raise MissionClosureError(
            "TEACHBACK_FAILED: completed_by_user must be true"
        )

    if record.get("source_execution") != execution_path:
        raise MissionClosureError(
            "BLOCKED_TEACHBACK_CONFLICT: Teachback execution "
            "source differs from closure evidence"
        )
    if record.get("source_review") != review_path:
        raise MissionClosureError(
            "BLOCKED_TEACHBACK_CONFLICT: Teachback review "
            "source differs from closure evidence"
        )
    return record


def build_fingerprint(
    *,
    mission_id: str,
    closure_id: str,
    human_actor: str,
    closure_reason: str,
    execution_relative: str,
    execution_hash: str,
    review_relative: str,
    review_hash: str,
    teachback_relative: str,
    teachback_hash: str,
) -> Tuple[str, Dict[str, Any]]:
    material = {
        "mission_id": mission_id,
        "closure_id": closure_id,
        "human_actor": human_actor,
        "closure_reason": closure_reason,
        "execution": {
            "path": execution_relative,
            "sha256": execution_hash,
        },
        "review": {
            "path": review_relative,
            "sha256": review_hash,
        },
        "teachback": {
            "path": teachback_relative,
            "sha256": teachback_hash,
        },
    }
    return canonical_hash(material), material


def base_report() -> Dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "tool": "mission_closure_gate",
        "status": "preview",
        "status_code": "READY_FOR_CLOSURE_REVIEW",
        "target_release": (
            "v3.2.6 - Repository Consolidation, "
            "Teachback Closure and CLI Coherence"
        ),
        "created_at": utc_now(),
        "mission_id": None,
        "closure_id": None,
        "state": {
            **BOUNDARIES,
            "teachback": "structured_evidence_required",
        },
        "paths": {},
        "evidence": {},
        "validated_sources": {},
        "teachback": None,
        "closure_fingerprint": None,
        "closure_material": None,
        "memory_outputs": [],
        "mission_outputs": [],
        "notification_state": "ready_for_teachback",
        "blockers": [],
        "warnings": [],
        "idempotent_reentry": False,
    }


def print_report(
    report: Mapping[str, Any],
    *,
    json_mode: bool,
) -> None:
    if json_mode:
        print(
            json.dumps(
                report,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
        )
        return

    if report.get("status") == "passed":
        print("MISSION CLOSURE PASSED")
        print(f"Mission: {report.get('mission_id')}")
        print(
            "Teachback: "
            f"{(report.get('teachback') or {}).get('result')}"
        )
        print(
            "Mission status: "
            f"{report.get('notification_state')}"
        )
        print(
            "Idempotent reentry: "
            f"{report.get('idempotent_reentry')}"
        )
        print("Repository apply: blocked")
        print("Git operations: blocked")
        print("Private context access: blocked")
        print("Network access: blocked")
        output = (
            report.get("paths", {})
            .get("mission_closure_report")
        )
        if output:
            print(f"Report: {output}")
        return

    if report.get("status") == "preview":
        print("MISSION CLOSURE PREVIEW")
        print(f"Mission: {report.get('mission_id')}")
        print(f"Status code: {report.get('status_code')}")
        print("Filesystem mutation: blocked")
        print("Repository apply: blocked")
        print("Git operations: blocked")
        print("Network access: blocked")
        return

    print("MISSION CLOSURE FAILED")
    for blocker in report.get("blockers", []):
        print(f"Blocker: {blocker}")


def close_mission(args: argparse.Namespace) -> int:
    report = base_report()
    try:
        mission_id = validate_safe_id(
            args.mission_id,
            "mission_id",
        )
        closure_id = validate_safe_id(
            args.closure_id
            or f"{mission_id}_closure",
            "closure_id",
        )

        workspace_root = Path(args.workspace_root)
        memory_root = Path(args.memory_root)
        mission_root = resolve_under(
            workspace_root,
            "missions",
            mission_id,
        )
        manifest = validate_workspace(
            mission_root,
            mission_id,
        )
        policy = manifest_teachback_policy(manifest)

        execution_relative, execution_file, execution = (
            resolve_evidence_file(
                mission_root,
                args.execution_evidence,
                "execution evidence",
            )
        )
        review_relative, review_file, review = (
            resolve_evidence_file(
                mission_root,
                args.review_evidence,
                "review evidence",
            )
        )
        teachback_relative, teachback_file, teachback_raw = (
            resolve_evidence_file(
                mission_root,
                args.teachback_record,
                "teachback record",
            )
        )

        validate_execution_evidence(execution)
        validate_review_evidence(review)
        teachback = validate_teachback_for_closure(
            teachback_raw,
            mission_id=mission_id,
            manifest=manifest,
            execution_path=execution_relative,
            review_path=review_relative,
        )

        report["mission_id"] = mission_id
        report["closure_id"] = closure_id
        report["paths"] = {
            "workspace_root": str(workspace_root),
            "mission_root": str(mission_root),
            "memory_root": str(memory_root),
        }
        report["evidence"] = collect_evidence(mission_root)
        report["validated_sources"] = {
            "execution": {
                "path": execution_relative,
                "sha256": sha256_file(execution_file),
            },
            "review": {
                "path": review_relative,
                "sha256": sha256_file(review_file),
                "decision": review_decision(review),
            },
            "teachback": {
                "path": teachback_relative,
                "sha256": sha256_file(teachback_file),
                "result": teachback["result"],
                "required_level": teachback["required_level"],
                "achieved_level": teachback["achieved_level"],
            },
        }
        report["teachback"] = teachback
        report["state"]["execution"] = "validated_complete"
        report["state"]["review"] = "validated_approved"
        report["state"]["teachback"] = teachback["result"]
        report["status_code"] = "READY_FOR_HUMAN_CLOSURE"
        report["notification_state"] = (
            "ready_for_human_closure"
        )

        fingerprint, material = build_fingerprint(
            mission_id=mission_id,
            closure_id=closure_id,
            human_actor=args.human_actor.strip() or "human",
            closure_reason=args.closure_reason.strip(),
            execution_relative=execution_relative,
            execution_hash=sha256_file(execution_file),
            review_relative=review_relative,
            review_hash=sha256_file(review_file),
            teachback_relative=teachback_relative,
            teachback_hash=sha256_file(teachback_file),
        )
        report["closure_fingerprint"] = fingerprint
        report["closure_material"] = material

        mission_report_path = resolve_under(
            mission_root,
            "reports",
            f"{closure_id}_mission_closure_report.json",
        )
        status_path = resolve_under(
            mission_root,
            "mission_status.json",
        )
        notification_path = resolve_under(
            mission_root,
            "reports",
            f"{closure_id}_notification_state.json",
        )
        report["paths"].update(
            {
                "mission_closure_report": str(
                    mission_report_path
                ),
                "mission_status": str(status_path),
                "notification": str(notification_path),
            }
        )

        if mission_report_path.exists():
            existing = read_json(
                mission_report_path,
                "existing closure report",
            )
            if (
                existing.get("status") == "passed"
                and existing.get("closure_fingerprint")
                == fingerprint
            ):
                response = dict(existing)
                response["idempotent_reentry"] = True
                print_report(
                    response,
                    json_mode=bool(args.json),
                )
                return 0
            raise MissionClosureError(
                "BLOCKED_TEACHBACK_CONFLICT: mission already "
                "has different closure evidence"
            )

        if not args.confirm_close:
            report["status"] = "preview"
            print_report(report, json_mode=bool(args.json))
            return 0

        if args.approval_token != APPROVAL_TOKEN:
            raise MissionClosureError(
                "invalid approval token for mission closure"
            )
        if len(args.closure_reason.strip()) < 10:
            raise MissionClosureError(
                "closure reason must be at least 10 characters"
            )
        if not args.human_actor.strip():
            raise MissionClosureError(
                "human_actor must not be empty"
            )

        if status_path.exists():
            existing_status = read_json(
                status_path,
                "existing mission status",
            )
            if existing_status.get("status") == "closed":
                raise MissionClosureError(
                    "BLOCKED_TEACHBACK_CONFLICT: mission status "
                    "is already closed without matching report"
                )

        now = utc_now()
        closure_report = dict(report)
        closure_report.update(
            {
                "status": "passed",
                "status_code": "MISSION_CLOSED",
                "created_at": now,
                "notification_state": "closed",
                "idempotent_reentry": False,
                "closure": {
                    "human_actor": args.human_actor,
                    "closure_reason": args.closure_reason,
                    "mission_closure_authority": (
                        "human_approval_only"
                    ),
                    "model_output_authority": "evidence_only",
                    "tool_output_authority": "evidence_only",
                    "force_does_not_override_conflict": True,
                },
            }
        )
        closure_report["state"]["mission_closure"] = (
            "closed_by_human"
        )

        mission_status = {
            "schema_version": "1.0.0",
            "mission_id": mission_id,
            "closure_id": closure_id,
            "status": "closed",
            "execution_status": "done",
            "review_status": "approved",
            "teachback_status": teachback["result"],
            "closed_at": now,
            "closed_by": args.human_actor,
            "closure_fingerprint": fingerprint,
            "notification_state": "closed",
        }
        notification = build_notification_state(
            mission_id=mission_id,
            closure_id=closure_id,
        )

        ensure_memory_layout(memory_root)
        mission_memory_path = resolve_under(
            memory_root,
            "10-missions",
            f"{mission_id}.md",
        )
        decision_path = resolve_under(
            memory_root,
            "20-decisions",
            f"{mission_id}_closure_decision.md",
        )
        context_pack_path = resolve_under(
            memory_root,
            "60-context-packs",
            f"{mission_id}_context_pack.md",
        )

        memory_note = build_mission_memory_note(
            mission_id=mission_id,
            closure_id=closure_id,
            manifest=manifest,
            teachback=teachback,
            evidence=closure_report["evidence"],
        )
        decision_note = build_decision_note(
            mission_id=mission_id,
            closure_id=closure_id,
            approval_actor=args.human_actor,
            closure_reason=args.closure_reason,
            closure_fingerprint=fingerprint,
        )
        context_pack = build_context_pack(
            mission_id=mission_id,
            closure_id=closure_id,
            evidence=closure_report["evidence"],
        )

        closure_report["mission_outputs"] = [
            str(mission_report_path),
            str(status_path),
            str(notification_path),
        ]
        closure_report["memory_outputs"] = [
            str(mission_memory_path),
            str(decision_path),
            str(context_pack_path),
        ]

        ensure_new_or_identical_text(
            mission_memory_path,
            memory_note,
        )
        ensure_new_or_identical_text(
            decision_path,
            decision_note,
        )
        ensure_new_or_identical_text(
            context_pack_path,
            context_pack,
        )
        ensure_new_or_identical_json(
            status_path,
            mission_status,
        )
        ensure_new_or_identical_json(
            notification_path,
            notification,
        )
        ensure_new_or_identical_json(
            mission_report_path,
            closure_report,
        )

        print_report(
            closure_report,
            json_mode=bool(args.json),
        )
        return 0

    except (
        MissionClosureError,
        TeachbackError,
        OSError,
        ValueError,
    ) as exc:
        report["status"] = "failed"
        report["status_code"] = "BLOCKED_MISSION_CLOSURE"
        report.setdefault("blockers", []).append(str(exc))
        print_report(report, json_mode=bool(args.json))
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Close a Konoha mission using execution, review, "
            "Teachback and human approval evidence."
        )
    )
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--mission-id", required=True)
    parser.add_argument("--memory-root", required=True)
    parser.add_argument("--closure-id")
    parser.add_argument("--execution-evidence", required=True)
    parser.add_argument("--review-evidence", required=True)
    parser.add_argument("--teachback-record", required=True)
    parser.add_argument("--human-actor", default="human")
    parser.add_argument("--closure-reason", default="")
    parser.add_argument("--confirm-close", action="store_true")
    parser.add_argument("--approval-token", default="")
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Compatibility flag. Never overrides contradictory "
            "existing closure evidence."
        ),
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return close_mission(args)


if __name__ == "__main__":
    raise SystemExit(main())
