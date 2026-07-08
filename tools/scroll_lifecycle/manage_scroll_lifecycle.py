#!/usr/bin/env python3
"""Konoha Scroll Lifecycle and Learning Proposals.

This tool manages learning proposals and scroll lifecycle review evidence.
It does not rewrite doctrine, modify official Scroll definitions, execute tools,
invoke models, invoke adapters, access private context, or perform Git operations.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


SCHEMA_VERSION = "1.0.0"
PROPOSAL_TOKEN = "RECORD_LEARNING_PROPOSAL"
REVIEW_TOKEN = "REVIEW_SCROLL_PROPOSAL"
PROMOTION_PLAN_TOKEN = "PLAN_SCROLL_PROMOTION"

LIFECYCLE_STATES = [
    "draft",
    "review_required",
    "approved_for_experiment",
    "rejected",
    "deferred",
    "promotion_planned",
]

REVIEW_DECISIONS = [
    "approve_for_experiment",
    "reject",
    "defer",
    "request_changes",
    "plan_promotion",
]

BOUNDARIES = {
    "execution": "blocked",
    "model_invocation": "blocked",
    "adapter_invocation": "blocked",
    "repository_apply": "blocked",
    "git_operations": "blocked",
    "private_context_access": "blocked",
    "doctrine_rewrite": "blocked",
    "mission_closure": "blocked",
}

AUTHORITY = {
    "learning_proposals_are_evidence_only": True,
    "review_records_do_not_rewrite_doctrine": True,
    "promotion_plans_are_not_permission_to_modify_scrolls": True,
    "shikamaru_and_human_approval_required_for_doctrine_changes": True,
}


class ScrollLifecycleError(Exception):
    """Expected user-facing error."""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_id(value: str, field: str = "id") -> str:
    if not value:
        raise ScrollLifecycleError(f"{field} is required")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value):
        raise ScrollLifecycleError(
            f"{field} must contain only letters, numbers, dots, underscores, or hyphens"
        )
    return value


def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ScrollLifecycleError(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        raise ScrollLifecycleError(f"invalid JSON file {path}: {exc}") from exc


def write_json(path: Path, data: Dict[str, Any], force: bool = False) -> None:
    if path.exists() and not force:
        raise ScrollLifecycleError(f"refusing to overwrite existing file without --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str, force: bool = False) -> None:
    if path.exists() and not force:
        raise ScrollLifecycleError(f"refusing to overwrite existing file without --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def mission_dir(workspace_root: Path, mission_id: str) -> Path:
    safe_id(mission_id, "mission_id")
    path = workspace_root / "missions" / mission_id
    if not path.exists():
        raise ScrollLifecycleError(f"mission workspace does not exist: {path}")
    return path


def proposal_paths(mission: Path, proposal_id: str) -> Dict[str, Path]:
    safe_id(proposal_id, "proposal_id")
    return {
        "proposal_md": mission / "learning_proposals" / f"{proposal_id}.md",
        "proposal_json": mission / "learning_proposals" / f"{proposal_id}.json",
        "report": mission / "reports" / f"{proposal_id}_scroll_learning_proposal_report.json",
        "review_md": mission / "learning_proposals" / f"{proposal_id}_review.md",
        "review_report": mission / "reports" / f"{proposal_id}_scroll_lifecycle_review_report.json",
        "promotion_plan": mission / "learning_proposals" / f"{proposal_id}_promotion_plan.md",
        "promotion_report": mission / "reports" / f"{proposal_id}_scroll_promotion_plan_report.json",
    }


def relative_or_label(path_text: str, mission: Path) -> str:
    if not path_text:
        return ""
    path = Path(path_text)
    try:
        if path.is_absolute():
            return str(path.relative_to(mission))
    except ValueError:
        return "$EXTERNAL_PATH_REDACTED"
    return path_text.replace("\\", "/")


def proposal_markdown(data: Dict[str, Any]) -> str:
    evidence_lines = "\n".join(f"- `{item}`" for item in data.get("evidence", [])) or "- No evidence listed."
    return f"""---
type: scroll_learning_proposal
schema_version: "{SCHEMA_VERSION}"
proposal_id: "{data['proposal_id']}"
mission_id: "{data['mission_id']}"
scroll_name: "{data['scroll_name']}"
lifecycle_state: "{data['lifecycle_state']}"
created_at: "{data['created_at']}"
created_by: "{data['created_by']}"
authority: "evidence_only"
---

# Scroll Learning Proposal: {data['scroll_name']}

## Learning summary

{data['learning_summary']}

## Proposed behavior change

{data['proposed_behavior_change']}

## Evidence

{evidence_lines}

## Risk notes

{data['risk_notes']}

## Non-authority boundary

This learning proposal is evidence only.

It does not rewrite doctrine, modify official Scrolls, authorize execution, authorize model calls, authorize adapter calls, authorize repository apply, authorize Git operations, authorize private context access, or close a mission.

Promotion to doctrine requires Hokage review, possible Kage Summit, Shikamaru drafting, Jounin review, and explicit human approval.
"""


def review_markdown(data: Dict[str, Any]) -> str:
    return f"""---
type: scroll_lifecycle_review
schema_version: "{SCHEMA_VERSION}"
proposal_id: "{data['proposal_id']}"
mission_id: "{data['mission_id']}"
decision: "{data['decision']}"
reviewer: "{data['reviewer']}"
reviewed_at: "{data['reviewed_at']}"
authority: "review_record_only"
---

# Scroll Lifecycle Review: {data['proposal_id']}

## Decision

{data['decision']}

## Rationale

{data['rationale']}

## Required changes

{data['required_changes']}

## Non-authority boundary

This review record does not rewrite doctrine or modify official Scroll definitions.

Approved proposals are approved only for experiment or planning unless a separate doctrine change workflow is completed.
"""


def promotion_plan_markdown(data: Dict[str, Any]) -> str:
    return f"""---
type: scroll_promotion_plan
schema_version: "{SCHEMA_VERSION}"
proposal_id: "{data['proposal_id']}"
mission_id: "{data['mission_id']}"
planned_at: "{data['planned_at']}"
planner: "{data['planner']}"
authority: "plan_only"
---

# Scroll Promotion Plan: {data['proposal_id']}

## Target Scroll

{data['target_scroll']}

## Promotion rationale

{data['promotion_rationale']}

## Required approvals

- Hokage review
- Shikamaru drafting
- Jounin review
- Explicit human approval

## Explicit non-actions

This plan does not modify official Scrolls.
This plan does not rewrite doctrine.
This plan does not authorize execution.
This plan does not close a mission.
"""


def base_report(command: str, mission_id: Optional[str], status: str, invocation: str) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "scroll_lifecycle_report",
        "command": command,
        "status": status,
        "invocation": invocation,
        "generated_at": now_iso(),
        "mission_id": mission_id,
        "boundaries": BOUNDARIES,
        "authority": AUTHORITY,
    }


def cmd_states(args: argparse.Namespace) -> int:
    data = {
        "schema_version": SCHEMA_VERSION,
        "lifecycle_states": LIFECYCLE_STATES,
        "review_decisions": REVIEW_DECISIONS,
        "approval_tokens": {
            "record_learning_proposal": PROPOSAL_TOKEN,
            "review_scroll_proposal": REVIEW_TOKEN,
            "plan_scroll_promotion": PROMOTION_PLAN_TOKEN,
        },
        "boundaries": BOUNDARIES,
        "authority": AUTHORITY,
    }
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print("SCROLL LIFECYCLE STATES")
        for state in LIFECYCLE_STATES:
            print(f"- {state}")
        print("REVIEW DECISIONS")
        for decision in REVIEW_DECISIONS:
            print(f"- {decision}")
    return 0


def cmd_propose(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace_root)
    mission_id = safe_id(args.mission_id, "mission_id")
    proposal_id = safe_id(args.proposal_id, "proposal_id")
    mission = mission_dir(workspace_root, mission_id)
    paths = proposal_paths(mission, proposal_id)

    if not args.confirm_proposal:
        print("SCROLL LEARNING PROPOSAL PREVIEW")
        print("Invocation: preview_only")
        print("Doctrine rewrite: blocked")
        print("Repository apply: blocked")
        print("Git operations: blocked")
        print("Model invocation: blocked")
        print("Adapter invocation: blocked")
        print("Private context access: blocked")
        return 0

    if args.approval_token != PROPOSAL_TOKEN:
        raise ScrollLifecycleError("invalid approval token for learning proposal")

    evidence = [relative_or_label(item, mission) for item in (args.evidence_path or [])]
    data = {
        "schema_version": SCHEMA_VERSION,
        "proposal_id": proposal_id,
        "mission_id": mission_id,
        "scroll_name": args.scroll_name,
        "created_at": now_iso(),
        "created_by": args.actor,
        "lifecycle_state": "review_required",
        "learning_summary": args.learning_summary,
        "proposed_behavior_change": args.proposed_behavior_change,
        "risk_notes": args.risk_notes,
        "evidence": evidence,
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
    }

    report = base_report("propose-learning", mission_id, "passed", "confirmed")
    report.update(
        {
            "proposal_id": proposal_id,
            "scroll_name": args.scroll_name,
            "lifecycle_state": "review_required",
            "outputs": {
                "proposal_markdown": str(paths["proposal_md"]),
                "proposal_json": str(paths["proposal_json"]),
            },
        }
    )

    write_text(paths["proposal_md"], proposal_markdown(data), force=args.force)
    write_json(paths["proposal_json"], data, force=args.force)
    write_json(paths["report"], report, force=args.force)

    print("SCROLL LEARNING PROPOSAL RECORDED")
    print(f"Proposal: {proposal_id}")
    print("Doctrine rewrite: blocked")
    print("Repository apply: blocked")
    print("Git operations: blocked")
    print("Learning proposal authority: evidence_only")
    return 0


def load_proposal(path: Path) -> Dict[str, Any]:
    if path.suffix.lower() == ".json":
        data = read_json(path)
        if data.get("proposal_id"):
            return data
    # Minimal markdown frontmatter extraction for proposal_id/mission_id.
    text = path.read_text(encoding="utf-8")
    def match(key: str) -> str:
        found = re.search(rf"^{re.escape(key)}:\s*\"?([^\"\n]+)\"?\s*$", text, re.MULTILINE)
        return found.group(1).strip() if found else ""
    return {
        "proposal_id": match("proposal_id") or path.stem,
        "mission_id": match("mission_id"),
        "scroll_name": match("scroll_name"),
        "lifecycle_state": match("lifecycle_state") or "review_required",
        "source_path": str(path),
    }


def cmd_review(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace_root)
    mission_id = safe_id(args.mission_id, "mission_id")
    proposal_id = safe_id(args.proposal_id, "proposal_id")
    if args.decision not in REVIEW_DECISIONS:
        raise ScrollLifecycleError(f"invalid decision: {args.decision}")
    mission = mission_dir(workspace_root, mission_id)
    paths = proposal_paths(mission, proposal_id)
    if not paths["proposal_json"].exists() and not paths["proposal_md"].exists():
        raise ScrollLifecycleError(f"proposal does not exist for review: {proposal_id}")

    if not args.confirm_review:
        print("SCROLL LIFECYCLE REVIEW PREVIEW")
        print("Invocation: preview_only")
        print("Doctrine rewrite: blocked")
        print("Repository apply: blocked")
        print("Git operations: blocked")
        print("Review record authority: evidence_only")
        return 0

    if args.approval_token != REVIEW_TOKEN:
        raise ScrollLifecycleError("invalid approval token for scroll proposal review")

    reviewed_at = now_iso()
    review_data = {
        "schema_version": SCHEMA_VERSION,
        "proposal_id": proposal_id,
        "mission_id": mission_id,
        "decision": args.decision,
        "reviewer": args.reviewer,
        "reviewed_at": reviewed_at,
        "rationale": args.rationale,
        "required_changes": args.required_changes,
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
    }
    report = base_report("review-proposal", mission_id, "passed", "confirmed")
    report.update(
        {
            "proposal_id": proposal_id,
            "decision": args.decision,
            "outputs": {
                "review_markdown": str(paths["review_md"]),
                "review_report": str(paths["review_report"]),
            },
        }
    )

    write_text(paths["review_md"], review_markdown(review_data), force=args.force)
    write_json(paths["review_report"], report, force=args.force)

    print("SCROLL LIFECYCLE REVIEW RECORDED")
    print(f"Proposal: {proposal_id}")
    print(f"Decision: {args.decision}")
    print("Doctrine rewrite: blocked")
    print("Review record authority: evidence_only")
    return 0


def cmd_plan_promotion(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace_root)
    mission_id = safe_id(args.mission_id, "mission_id")
    proposal_id = safe_id(args.proposal_id, "proposal_id")
    mission = mission_dir(workspace_root, mission_id)
    paths = proposal_paths(mission, proposal_id)
    if not paths["review_report"].exists():
        raise ScrollLifecycleError("promotion planning requires a prior review report")

    if not args.confirm_plan:
        print("SCROLL PROMOTION PLAN PREVIEW")
        print("Invocation: preview_only")
        print("Doctrine rewrite: blocked")
        print("Repository apply: blocked")
        print("Git operations: blocked")
        print("Promotion plan authority: plan_only")
        return 0

    if args.approval_token != PROMOTION_PLAN_TOKEN:
        raise ScrollLifecycleError("invalid approval token for scroll promotion planning")

    data = {
        "schema_version": SCHEMA_VERSION,
        "proposal_id": proposal_id,
        "mission_id": mission_id,
        "planned_at": now_iso(),
        "planner": args.planner,
        "target_scroll": args.target_scroll,
        "promotion_rationale": args.promotion_rationale,
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
    }
    report = base_report("plan-promotion", mission_id, "passed", "confirmed")
    report.update(
        {
            "proposal_id": proposal_id,
            "target_scroll": args.target_scroll,
            "outputs": {
                "promotion_plan": str(paths["promotion_plan"]),
                "promotion_report": str(paths["promotion_report"]),
            },
        }
    )

    write_text(paths["promotion_plan"], promotion_plan_markdown(data), force=args.force)
    write_json(paths["promotion_report"], report, force=args.force)

    print("SCROLL PROMOTION PLAN RECORDED")
    print(f"Proposal: {proposal_id}")
    print("Doctrine rewrite: blocked")
    print("Promotion plan authority: plan_only")
    return 0


def cmd_index(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace_root)
    mission_id = safe_id(args.mission_id, "mission_id")
    mission = mission_dir(workspace_root, mission_id)
    proposal_dir = mission / "learning_proposals"

    proposals: List[Dict[str, Any]] = []
    if proposal_dir.exists():
        for path in sorted(proposal_dir.glob("*.json")):
            if path.name.endswith("_review.json"):
                continue
            try:
                data = read_json(path)
                proposals.append(
                    {
                        "proposal_id": data.get("proposal_id", path.stem),
                        "scroll_name": data.get("scroll_name", ""),
                        "lifecycle_state": data.get("lifecycle_state", ""),
                        "path": str(path),
                    }
                )
            except ScrollLifecycleError:
                continue

    index = {
        "schema_version": SCHEMA_VERSION,
        "index_type": "scroll_learning_proposal_index",
        "generated_at": now_iso(),
        "mission_id": mission_id,
        "proposal_count": len(proposals),
        "proposals": proposals,
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
    }

    if args.write_index:
        out = mission / "learning_proposals" / "scroll_learning_proposal_index.json"
        write_json(out, index, force=args.force)

    if args.json:
        print(json.dumps(index, indent=2, sort_keys=True))
    else:
        print("SCROLL LEARNING PROPOSAL INDEX")
        print(f"Mission: {mission_id}")
        print(f"Proposals: {len(proposals)}")
        for item in proposals:
            print(f"- {item['proposal_id']} [{item['lifecycle_state']}] {item['scroll_name']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage Konoha Scroll lifecycle learning proposals without rewriting doctrine."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    states = sub.add_parser("states", help="List lifecycle states and review decisions.")
    states.add_argument("--json", action="store_true")
    states.set_defaults(func=cmd_states)

    propose = sub.add_parser("propose-learning", help="Record a mission-local Scroll learning proposal.")
    propose.add_argument("--workspace-root", required=True)
    propose.add_argument("--mission-id", required=True)
    propose.add_argument("--proposal-id", required=True)
    propose.add_argument("--scroll-name", required=True)
    propose.add_argument("--learning-summary", required=True)
    propose.add_argument("--proposed-behavior-change", required=True)
    propose.add_argument("--risk-notes", default="No additional risk notes provided.")
    propose.add_argument("--evidence-path", action="append", default=[])
    propose.add_argument("--actor", default="human")
    propose.add_argument("--confirm-proposal", action="store_true")
    propose.add_argument("--approval-token", default="")
    propose.add_argument("--force", action="store_true")
    propose.set_defaults(func=cmd_propose)

    review = sub.add_parser("review-proposal", help="Record human/Jounin review of a Scroll proposal.")
    review.add_argument("--workspace-root", required=True)
    review.add_argument("--mission-id", required=True)
    review.add_argument("--proposal-id", required=True)
    review.add_argument("--decision", required=True, choices=REVIEW_DECISIONS)
    review.add_argument("--rationale", required=True)
    review.add_argument("--required-changes", default="No required changes recorded.")
    review.add_argument("--reviewer", default="human")
    review.add_argument("--confirm-review", action="store_true")
    review.add_argument("--approval-token", default="")
    review.add_argument("--force", action="store_true")
    review.set_defaults(func=cmd_review)

    promotion = sub.add_parser("plan-promotion", help="Create a plan-only Scroll promotion record.")
    promotion.add_argument("--workspace-root", required=True)
    promotion.add_argument("--mission-id", required=True)
    promotion.add_argument("--proposal-id", required=True)
    promotion.add_argument("--target-scroll", required=True)
    promotion.add_argument("--promotion-rationale", required=True)
    promotion.add_argument("--planner", default="shikamaru")
    promotion.add_argument("--confirm-plan", action="store_true")
    promotion.add_argument("--approval-token", default="")
    promotion.add_argument("--force", action="store_true")
    promotion.set_defaults(func=cmd_plan_promotion)

    index = sub.add_parser("index", help="Inspect mission-local Scroll learning proposals.")
    index.add_argument("--workspace-root", required=True)
    index.add_argument("--mission-id", required=True)
    index.add_argument("--write-index", action="store_true")
    index.add_argument("--json", action="store_true")
    index.add_argument("--force", action="store_true")
    index.set_defaults(func=cmd_index)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ScrollLifecycleError as exc:
        print("SCROLL LIFECYCLE FAILED")
        print("Blocker:", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
