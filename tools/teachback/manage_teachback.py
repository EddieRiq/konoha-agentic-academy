#!/usr/bin/env python3
"""Record and inspect structured Konoha Teachback evidence.

The tool records human evidence only. It does not evaluate model output as
truth, execute mission actions, access network, mutate Git, or authorize
mission closure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

SCHEMA_VERSION = "1.0.0"
REPORT_TYPE = "teachback_record"
APPROVAL_TOKEN = "RECORD_TEACHBACK_EVIDENCE"
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
VALID_RESULTS = {
    "passed",
    "needs_clarification",
    "failed",
    "skipped",
}
RISK_LEVELS = {"low", "medium", "high", "critical"}
RISK_DEFAULT_LEVEL = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

BOUNDARIES = {
    "mission_execution": "blocked",
    "repository_apply": "blocked",
    "git_operations": "blocked",
    "network_access": "blocked",
    "model_invocation": "blocked",
    "private_context_discovery": "blocked",
    "mission_closure": "separate_explicit_gate",
    "filesystem_mutation": "mission reports only",
}


class TeachbackError(RuntimeError):
    """Invalid Teachback evidence or unsafe path."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_safe_id(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not SAFE_ID_RE.fullmatch(value)
        or "/" in value
        or "\\" in value
    ):
        raise TeachbackError(
            f"{label} must be alphanumeric plus '.', '_' or '-' "
            "and may not contain path separators"
        )
    return value


def resolve_under(root: Path, *parts: str) -> Path:
    base = root.resolve()
    candidate = base.joinpath(*parts).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise TeachbackError(
            f"path escapes allowed root: {candidate}"
        ) from exc
    return candidate


def read_json_object(path: Path, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TeachbackError(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TeachbackError(
            f"{label} JSON invalid at line {exc.lineno}, "
            f"column {exc.colno}"
        ) from exc
    if not isinstance(payload, dict):
        raise TeachbackError(f"{label} JSON must be an object")
    return payload


def canonical_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    ignored = {
        "recorded_at",
        "idempotent_reentry",
        "record_path",
    }
    return {
        key: value
        for key, value in payload.items()
        if key not in ignored
    }


def canonical_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        canonical_payload(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_json_new(path: Path, payload: Mapping[str, Any]) -> None:
    if path.exists():
        raise TeachbackError(f"output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def mission_paths(
    workspace_root: Path,
    mission_id: str,
) -> Tuple[Path, Path, Path]:
    mission_id = normalize_safe_id(mission_id, "mission_id")
    mission_root = resolve_under(
        workspace_root,
        "missions",
        mission_id,
    )
    manifest_path = resolve_under(
        mission_root,
        "mission_manifest.json",
    )
    charter_path = resolve_under(mission_root, "charter.md")
    if not mission_root.is_dir():
        raise TeachbackError(
            f"mission workspace not found: {mission_root}"
        )
    if not manifest_path.is_file():
        raise TeachbackError(
            f"mission manifest not found: {manifest_path}"
        )
    if not charter_path.is_file():
        raise TeachbackError(
            f"mission charter not found: {charter_path}"
        )
    return mission_root, manifest_path, charter_path


def manifest_risk(manifest: Mapping[str, Any]) -> str:
    task_info = manifest.get("task_info")
    candidates = [
        manifest.get("risk_level"),
        task_info.get("risk_level")
        if isinstance(task_info, dict)
        else None,
        manifest.get("risk"),
    ]
    for value in candidates:
        if isinstance(value, str) and value.lower() in RISK_LEVELS:
            return value.lower()
    return "medium"


def manifest_teachback_policy(
    manifest: Mapping[str, Any],
) -> Dict[str, Any]:
    risk = manifest_risk(manifest)
    raw = manifest.get("teachback")
    policy = dict(raw) if isinstance(raw, dict) else {}

    required = policy.get("required")
    if not isinstance(required, bool):
        required = True

    required_level = policy.get("required_level")
    if not isinstance(required_level, int):
        required_level = RISK_DEFAULT_LEVEL[risk]
    if required_level < 0 or required_level > 4:
        raise TeachbackError(
            "mission manifest teachback.required_level must be 0..4"
        )

    skip_allowed = policy.get("skip_allowed")
    if not isinstance(skip_allowed, bool):
        skip_allowed = not required and risk == "low"

    return {
        "required": required,
        "required_level": required_level,
        "skip_allowed": skip_allowed,
        "risk_level": risk,
        "source": (
            "mission_manifest"
            if isinstance(raw, dict)
            else "risk_default"
        ),
    }


def normalize_string_list(
    values: Optional[Iterable[str]],
    label: str,
) -> List[str]:
    result: List[str] = []
    for value in values or []:
        if not isinstance(value, str):
            raise TeachbackError(f"{label} values must be text")
        cleaned = value.strip()
        if not cleaned:
            raise TeachbackError(
                f"{label} values must not be empty"
            )
        if cleaned not in result:
            result.append(cleaned)
    return result


def validate_source_path(
    mission_root: Path,
    raw: Optional[str],
    label: str,
) -> Optional[str]:
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = mission_root / candidate
    candidate = candidate.resolve()
    try:
        relative = candidate.relative_to(mission_root.resolve())
    except ValueError as exc:
        raise TeachbackError(
            f"{label} must stay under the mission workspace"
        ) from exc
    if not candidate.is_file():
        raise TeachbackError(
            f"{label} not found: {candidate}"
        )
    return relative.as_posix()


def validate_teachback_record(
    payload: Mapping[str, Any],
    *,
    expected_mission_id: Optional[str] = None,
    manifest: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    required_fields = {
        "schema_version",
        "report_type",
        "teachback_id",
        "mission_id",
        "required",
        "required_level",
        "achieved_level",
        "result",
        "completed_by_user",
        "summary",
        "gaps",
        "next_explanation_needed",
        "human_actor",
        "human_evidence",
        "source_execution",
        "source_review",
        "skip_reason",
        "recorded_at",
        "non_authority",
    }
    missing = sorted(required_fields - set(payload))
    if missing:
        raise TeachbackError(
            "teachback record missing fields: "
            + ", ".join(missing)
        )

    if payload.get("schema_version") != SCHEMA_VERSION:
        raise TeachbackError(
            f"teachback schema_version must be {SCHEMA_VERSION}"
        )
    if payload.get("report_type") != REPORT_TYPE:
        raise TeachbackError(
            f"teachback report_type must be {REPORT_TYPE}"
        )

    mission_id = normalize_safe_id(
        str(payload.get("mission_id", "")),
        "mission_id",
    )
    normalize_safe_id(
        str(payload.get("teachback_id", "")),
        "teachback_id",
    )
    if expected_mission_id and mission_id != expected_mission_id:
        raise TeachbackError(
            "teachback mission_id does not match closure mission"
        )

    result = payload.get("result")
    if result not in VALID_RESULTS:
        raise TeachbackError(
            "teachback result must be passed, "
            "needs_clarification, failed or skipped"
        )

    required = payload.get("required")
    completed = payload.get("completed_by_user")
    if not isinstance(required, bool):
        raise TeachbackError("teachback required must be boolean")
    if not isinstance(completed, bool):
        raise TeachbackError(
            "teachback completed_by_user must be boolean"
        )

    required_level = payload.get("required_level")
    achieved_level = payload.get("achieved_level")
    for label, value in (
        ("required_level", required_level),
        ("achieved_level", achieved_level),
    ):
        if not isinstance(value, int) or not 0 <= value <= 4:
            raise TeachbackError(
                f"teachback {label} must be an integer 0..4"
            )

    summary = payload.get("summary")
    if not isinstance(summary, str):
        raise TeachbackError("teachback summary must be text")
    summary = summary.strip()

    gaps = payload.get("gaps")
    human_evidence = payload.get("human_evidence")
    if not isinstance(gaps, list) or not all(
        isinstance(item, str) and item.strip()
        for item in gaps
    ):
        raise TeachbackError(
            "teachback gaps must be a list of non-empty strings"
        )
    if not isinstance(human_evidence, list) or not all(
        isinstance(item, str) and item.strip()
        for item in human_evidence
    ):
        raise TeachbackError(
            "teachback human_evidence must be a list of "
            "non-empty strings"
        )

    next_needed = payload.get("next_explanation_needed")
    skip_reason = payload.get("skip_reason")
    if next_needed is not None and not isinstance(
        next_needed,
        str,
    ):
        raise TeachbackError(
            "next_explanation_needed must be text or null"
        )
    if skip_reason is not None and not isinstance(
        skip_reason,
        str,
    ):
        raise TeachbackError(
            "skip_reason must be text or null"
        )

    if result == "passed":
        if not completed:
            raise TeachbackError(
                "passed teachback requires completed_by_user=true"
            )
        if achieved_level < required_level:
            raise TeachbackError(
                "passed teachback requires achieved_level "
                "at or above required_level"
            )
        if gaps:
            raise TeachbackError(
                "passed teachback requires gaps=[]"
            )
        if len(summary) < 20:
            raise TeachbackError(
                "passed teachback summary must be at least "
                "20 characters"
            )
        if not human_evidence:
            raise TeachbackError(
                "passed teachback requires human_evidence"
            )
        if skip_reason:
            raise TeachbackError(
                "passed teachback cannot include skip_reason"
            )

    elif result == "needs_clarification":
        if completed:
            raise TeachbackError(
                "needs_clarification requires "
                "completed_by_user=false"
            )
        if not gaps:
            raise TeachbackError(
                "needs_clarification requires at least one gap"
            )
        if not next_needed or not next_needed.strip():
            raise TeachbackError(
                "needs_clarification requires "
                "next_explanation_needed"
            )

    elif result == "failed":
        if completed:
            raise TeachbackError(
                "failed teachback requires "
                "completed_by_user=false"
            )
        if not gaps:
            raise TeachbackError(
                "failed teachback requires at least one gap"
            )

    elif result == "skipped":
        if required:
            raise TeachbackError(
                "required teachback cannot be skipped"
            )
        if achieved_level != 0:
            raise TeachbackError(
                "skipped teachback requires achieved_level=0"
            )
        if gaps:
            raise TeachbackError(
                "skipped teachback requires gaps=[]"
            )
        if not skip_reason or len(skip_reason.strip()) < 10:
            raise TeachbackError(
                "skipped teachback requires a skip_reason "
                "of at least 10 characters"
            )

    if manifest is not None:
        policy = manifest_teachback_policy(manifest)
        if required != policy["required"]:
            raise TeachbackError(
                "teachback required flag conflicts with "
                "mission manifest"
            )
        if required_level != policy["required_level"]:
            raise TeachbackError(
                "teachback required_level conflicts with "
                "mission manifest"
            )
        if result == "skipped":
            if not policy["skip_allowed"]:
                raise TeachbackError(
                    "mission manifest does not allow "
                    "teachback skip"
                )
            if policy["risk_level"] in {"high", "critical"}:
                raise TeachbackError(
                    "high or critical risk teachback "
                    "cannot be skipped"
                )

    return dict(payload)


def build_record(
    *,
    mission_id: str,
    teachback_id: str,
    policy: Mapping[str, Any],
    achieved_level: int,
    result: str,
    completed_by_user: bool,
    summary: str,
    gaps: Sequence[str],
    next_explanation_needed: Optional[str],
    human_actor: str,
    human_evidence: Sequence[str],
    source_execution: Optional[str],
    source_review: Optional[str],
    skip_reason: Optional[str],
) -> Dict[str, Any]:
    record = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "teachback_id": teachback_id,
        "mission_id": mission_id,
        "required": policy["required"],
        "required_level": policy["required_level"],
        "achieved_level": achieved_level,
        "result": result,
        "completed_by_user": completed_by_user,
        "summary": summary.strip(),
        "gaps": list(gaps),
        "next_explanation_needed": (
            next_explanation_needed.strip()
            if isinstance(next_explanation_needed, str)
            and next_explanation_needed.strip()
            else None
        ),
        "human_actor": human_actor.strip() or "human",
        "human_evidence": list(human_evidence),
        "source_execution": source_execution,
        "source_review": source_review,
        "skip_reason": (
            skip_reason.strip()
            if isinstance(skip_reason, str)
            and skip_reason.strip()
            else None
        ),
        "recorded_at": utc_now(),
        "non_authority": [
            "teachback evidence does not authorize mission actions",
            "teachback evidence does not authorize repository apply",
            "teachback evidence does not authorize Git operations",
            "teachback evidence does not authorize model invocation",
            "teachback evidence does not close the mission",
        ],
    }
    return record


def record_teachback(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace_root)
    mission_root, manifest_path, _ = mission_paths(
        workspace_root,
        args.mission_id,
    )
    manifest = read_json_object(
        manifest_path,
        "mission manifest",
    )
    policy = manifest_teachback_policy(manifest)
    teachback_id = normalize_safe_id(
        args.teachback_id
        or f"{args.mission_id}_teachback",
        "teachback_id",
    )

    source_execution = validate_source_path(
        mission_root,
        args.source_execution,
        "source_execution",
    )
    source_review = validate_source_path(
        mission_root,
        args.source_review,
        "source_review",
    )

    record = build_record(
        mission_id=args.mission_id,
        teachback_id=teachback_id,
        policy=policy,
        achieved_level=args.achieved_level,
        result=args.result,
        completed_by_user=args.completed_by_user,
        summary=args.summary,
        gaps=normalize_string_list(args.gap, "gap"),
        next_explanation_needed=args.next_explanation_needed,
        human_actor=args.human_actor,
        human_evidence=normalize_string_list(
            args.human_evidence,
            "human_evidence",
        ),
        source_execution=source_execution,
        source_review=source_review,
        skip_reason=args.skip_reason,
    )
    validate_teachback_record(
        record,
        expected_mission_id=args.mission_id,
        manifest=manifest,
    )

    output = resolve_under(
        mission_root,
        "reports",
        f"{teachback_id}_teachback_record.json",
    )

    if not args.confirm_record:
        preview = {
            **record,
            "status": "preview",
            "record_path": str(output),
            "recorded_at": None,
        }
        print_payload(preview, args.json)
        return 0

    if args.approval_token != APPROVAL_TOKEN:
        raise TeachbackError(
            f"invalid Teachback approval token; expected "
            f"{APPROVAL_TOKEN}"
        )

    if output.exists():
        existing = read_json_object(
            output,
            "existing teachback record",
        )
        validate_teachback_record(
            existing,
            expected_mission_id=args.mission_id,
            manifest=manifest,
        )
        if canonical_hash(existing) != canonical_hash(record):
            raise TeachbackError(
                "BLOCKED_TEACHBACK_CONFLICT: existing record "
                "contains different human evidence"
            )
        response = {
            **existing,
            "status": "passed",
            "idempotent_reentry": True,
            "record_path": str(output),
        }
        print_payload(response, args.json)
        return 0

    write_json_new(output, record)
    response = {
        **record,
        "status": "passed",
        "idempotent_reentry": False,
        "record_path": str(output),
    }
    print_payload(response, args.json)
    return 0


def status_teachback(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace_root)
    mission_root, manifest_path, _ = mission_paths(
        workspace_root,
        args.mission_id,
    )
    manifest = read_json_object(
        manifest_path,
        "mission manifest",
    )
    policy = manifest_teachback_policy(manifest)

    if args.teachback_record:
        record_path = Path(args.teachback_record)
        if not record_path.is_absolute():
            record_path = mission_root / record_path
        record_path = record_path.resolve()
        try:
            record_path.relative_to(mission_root.resolve())
        except ValueError as exc:
            raise TeachbackError(
                "teachback record must stay under mission workspace"
            ) from exc
        candidates = [record_path]
    else:
        reports = mission_root / "reports"
        candidates = (
            sorted(
                reports.glob("*_teachback_record.json"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
            if reports.is_dir()
            else []
        )

    if not candidates:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "report_type": "teachback_status_report",
            "status": "not_recorded",
            "status_code": "READY_FOR_TEACHBACK",
            "mission_id": args.mission_id,
            "policy": policy,
            "record_path": None,
            "close_eligible": False,
            "boundaries": BOUNDARIES,
        }
        print_payload(payload, args.json)
        return 0

    record_path = candidates[0]
    record = read_json_object(
        record_path,
        "teachback record",
    )
    validate_teachback_record(
        record,
        expected_mission_id=args.mission_id,
        manifest=manifest,
    )

    result = record["result"]
    if result == "passed":
        status_code = "READY_FOR_HUMAN_CLOSURE"
        close_eligible = True
    elif result == "skipped":
        status_code = "READY_FOR_HUMAN_CLOSURE"
        close_eligible = True
    elif result == "needs_clarification":
        status_code = "NEEDS_CLARIFICATION"
        close_eligible = False
    else:
        status_code = "TEACHBACK_FAILED"
        close_eligible = False

    payload = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "teachback_status_report",
        "status": "passed",
        "status_code": status_code,
        "mission_id": args.mission_id,
        "policy": policy,
        "record": record,
        "record_path": str(record_path),
        "close_eligible": close_eligible,
        "boundaries": BOUNDARIES,
    }
    print_payload(payload, args.json)
    return 0


def prepare_teachback(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace_root)
    _, manifest_path, _ = mission_paths(
        workspace_root,
        args.mission_id,
    )
    manifest = read_json_object(
        manifest_path,
        "mission manifest",
    )
    policy = manifest_teachback_policy(manifest)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "teachback_preparation_report",
        "status": "passed",
        "status_code": (
            "READY_FOR_TEACHBACK"
            if policy["required"]
            else "TEACHBACK_OPTIONAL"
        ),
        "mission_id": args.mission_id,
        "policy": policy,
        "required_understanding": {
            "level_0": "No reusable deliverable.",
            "level_1": "What, where, purpose and next action.",
            "level_2": "Operation, inputs, outputs and failures.",
            "level_3": "Rationale, alternatives, trade-offs and risks.",
            "level_4": "Defense-ready explanation for reviewers.",
        },
        "boundaries": BOUNDARIES,
        "authority": {
            "preparation_is_not_completion": True,
            "model_explanation_is_evidence_only": True,
            "human_explanation_is_required_when_teachback_is_required": True,
        },
    }
    print_payload(payload, args.json)
    return 0


def print_payload(
    payload: Mapping[str, Any],
    json_mode: bool,
) -> None:
    if json_mode:
        print(
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
        )
        return

    print("KONOHA TEACHBACK")
    print(f"mission_id: {payload.get('mission_id')}")
    print(
        "status_code: "
        f"{payload.get('status_code') or payload.get('status')}"
    )
    if "result" in payload:
        print(f"result: {payload.get('result')}")
        print(
            "levels: "
            f"{payload.get('achieved_level')}/"
            f"{payload.get('required_level')}"
        )
        print(
            "completed_by_user: "
            f"{payload.get('completed_by_user')}"
        )
    if payload.get("record_path"):
        print(f"record: {payload.get('record_path')}")
    print("mission_closure: separate explicit gate")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record and inspect structured Konoha Teachback evidence."
    )
    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    prepare = sub.add_parser(
        "prepare",
        help="Inspect mission Teachback requirements.",
    )
    prepare.add_argument("--workspace-root", required=True)
    prepare.add_argument("--mission-id", required=True)
    prepare.add_argument("--json", action="store_true")
    prepare.set_defaults(func=prepare_teachback)

    record = sub.add_parser(
        "record",
        help="Preview or record human Teachback evidence.",
    )
    record.add_argument("--workspace-root", required=True)
    record.add_argument("--mission-id", required=True)
    record.add_argument("--teachback-id")
    record.add_argument(
        "--result",
        required=True,
        choices=sorted(VALID_RESULTS),
    )
    record.add_argument(
        "--achieved-level",
        required=True,
        type=int,
        choices=range(0, 5),
    )
    record.add_argument(
        "--completed-by-user",
        action="store_true",
    )
    record.add_argument("--summary", default="")
    record.add_argument(
        "--human-evidence",
        action="append",
        default=[],
    )
    record.add_argument(
        "--gap",
        action="append",
        default=[],
    )
    record.add_argument("--next-explanation-needed")
    record.add_argument("--skip-reason")
    record.add_argument("--source-execution")
    record.add_argument("--source-review")
    record.add_argument("--human-actor", default="human")
    record.add_argument("--confirm-record", action="store_true")
    record.add_argument("--approval-token", default="")
    record.add_argument("--json", action="store_true")
    record.set_defaults(func=record_teachback)

    status = sub.add_parser(
        "status",
        help="Inspect latest Teachback evidence.",
    )
    status.add_argument("--workspace-root", required=True)
    status.add_argument("--mission-id", required=True)
    status.add_argument("--teachback-record")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=status_teachback)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except TeachbackError as exc:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "report_type": "teachback_gate_report",
            "status": "failed",
            "status_code": "BLOCKED_TEACHBACK",
            "blocker": str(exc),
            "boundaries": BOUNDARIES,
        }
        if getattr(args, "json", False):
            print(
                json.dumps(
                    payload,
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print("KONOHA TEACHBACK FAILED")
            print(f"Blocker: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
