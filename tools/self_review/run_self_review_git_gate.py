#!/usr/bin/env python3
"""Konoha v2.9 Self-Review, Optimization and Git Operation Gate.

This tool is intentionally conservative.

- Self-review and optimization reports are evidence only.
- Git plans are not permission.
- Git add/commit/push require separate explicit approval tokens.
- Git operations are limited to an approved path allowlist from a recorded plan.
- All subprocess calls use shell=False.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"

TOKENS = {
    "review": "RECORD_SELF_REVIEW",
    "optimize": "RECORD_OPTIMIZATION_PLAN",
    "git_plan": "PLAN_GIT_OPERATION",
    "stage": "APPROVE_GIT_STAGE",
    "commit": "APPROVE_GIT_COMMIT",
    "push": "APPROVE_GIT_PUSH",
}

BOUNDARIES = {
    "arbitrary_shell": "blocked",
    "model_invocation": "blocked",
    "adapter_invocation": "blocked",
    "private_context_access": "blocked_by_default",
    "repository_apply": "blocked_unless_separate_apply_gate",
    "git_operations": "gated",
    "git_push_network": "blocked_unless_explicit_push_gate_and_allow_network",
    "mission_closure": "blocked",
    "background_agents": "blocked",
}

AUTHORITY = {
    "self_review_is_evidence_only": True,
    "optimization_plan_is_not_permission": True,
    "git_plan_is_not_permission": True,
    "git_stage_commit_push_require_separate_tokens": True,
    "user_must_review_diff_before_git_operations": True,
}

SAFE_PATH_DENY_PREFIXES = (
    ".git",
    "secrets",
    "credentials",
    "alliance/kirigakure",
    "kirigakure",
)

SAFE_PATH_DENY_NAMES = (
    ".env",
    ".env.local",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_path_text(value: str) -> str:
    return value.replace("\\", "/")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Dict[str, Any], force: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise RuntimeError(f"refusing to overwrite existing file without --force: {path}")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str, force: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise RuntimeError(f"refusing to overwrite existing file without --force: {path}")
    path.write_text(content, encoding="utf-8")


def mission_dir(workspace_root: Path, mission_id: str) -> Path:
    return workspace_root / "missions" / mission_id


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def list_relative_files(root: Path, subdir: str, limit: int = 30) -> List[str]:
    folder = root / subdir
    if not folder.exists():
        return []
    results: List[str] = []
    for item in sorted(folder.rglob("*")):
        if item.is_file():
            results.append(item.relative_to(root).as_posix())
            if len(results) >= limit:
                break
    return results


def summarize_token_ledger(ledger_root: Optional[Path]) -> Dict[str, Any]:
    summary = {
        "ledger_found": False,
        "usage_records": 0,
        "actual_input_tokens": 0,
        "actual_output_tokens": 0,
        "estimated_input_tokens": 0,
        "estimated_output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "notes": [],
    }
    if ledger_root is None:
        summary["notes"].append("No ledger root provided.")
        return summary

    candidates = [
        ledger_root / "token_usage_ledger.json",
        ledger_root / "ledger" / "token_usage_ledger.json",
    ]
    ledger_path = next((p for p in candidates if p.exists()), None)
    if ledger_path is None:
        summary["notes"].append("Token ledger not found.")
        return summary

    try:
        data = load_json(ledger_path)
    except Exception as exc:
        summary["notes"].append(f"Token ledger could not be parsed: {exc}")
        return summary

    records = data.get("records") or data.get("usage_records") or data.get("entries") or []
    if isinstance(records, dict):
        records = list(records.values())
    if not isinstance(records, list):
        records = []

    summary["ledger_found"] = True
    summary["usage_records"] = len(records)

    for record in records:
        if not isinstance(record, dict):
            continue
        source = str(record.get("usage_source") or record.get("source") or "").lower()
        actual_in = int(record.get("actual_input_tokens") or record.get("input_tokens") or 0)
        actual_out = int(record.get("actual_output_tokens") or record.get("output_tokens") or 0)
        est_in = int(record.get("estimated_input_tokens") or 0)
        est_out = int(record.get("estimated_output_tokens") or 0)
        if "estimated" in source and not est_in and not est_out:
            est_in = actual_in
            est_out = actual_out
            actual_in = 0
            actual_out = 0
        summary["actual_input_tokens"] += actual_in
        summary["actual_output_tokens"] += actual_out
        summary["estimated_input_tokens"] += est_in
        summary["estimated_output_tokens"] += est_out
        try:
            summary["estimated_cost_usd"] += float(record.get("estimated_cost_usd") or record.get("cost_usd") or 0.0)
        except (TypeError, ValueError):
            pass

    summary["estimated_cost_usd"] = round(summary["estimated_cost_usd"], 6)
    if summary["estimated_input_tokens"] or summary["estimated_output_tokens"]:
        summary["notes"].append("Some token usage is estimated. Token estimates are not truth.")
    return summary


def build_self_review(workspace_root: Path, mission_id: str, review_id: str, ledger_root: Optional[Path]) -> Dict[str, Any]:
    root = mission_dir(workspace_root, mission_id)
    blockers: List[str] = []
    if not root.exists():
        blockers.append("mission workspace does not exist")

    evidence_files = list_relative_files(root, "evidence") if root.exists() else []
    report_files = list_relative_files(root, "reports") if root.exists() else []
    plan_files = list_relative_files(root, "plans") if root.exists() else []
    approval_files = list_relative_files(root, "approvals") if root.exists() else []
    learning_files = list_relative_files(root, "learning_proposals") if root.exists() else []

    token_summary = summarize_token_ledger(ledger_root)

    handholding_findings = []
    if count_files(root / "approvals") > 0:
        handholding_findings.append("Mission contains approval evidence; review whether approval prompts were necessary and well grouped.")
    else:
        handholding_findings.append("No approval evidence found; verify whether this was expected for the mission risk.")
    if count_files(root / "reports") < 1:
        handholding_findings.append("Few or no reports found; future missions should capture stronger evidence.")
    if token_summary["usage_records"] == 0:
        handholding_findings.append("No token usage records found; future model calls should record actual or estimated usage.")

    quality_assessment = {
        "evidence_sufficiency": "needs_review" if not evidence_files else "present",
        "reporting_sufficiency": "needs_review" if not report_files else "present",
        "plan_traceability": "needs_review" if not plan_files else "present",
        "token_accounting": "missing" if token_summary["usage_records"] == 0 else "present",
        "overall": "review_required",
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "self_review_report",
        "review_id": review_id,
        "mission_id": mission_id,
        "generated_at": utc_now(),
        "status": "blocked" if blockers else "ready_for_recording",
        "blockers": blockers,
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
        "mission_inventory": {
            "evidence_files_count": len(evidence_files),
            "report_files_count": len(report_files),
            "plan_files_count": len(plan_files),
            "approval_files_count": len(approval_files),
            "learning_proposal_files_count": len(learning_files),
            "sample_evidence_files": evidence_files,
            "sample_report_files": report_files,
            "sample_plan_files": plan_files,
        },
        "token_summary": token_summary,
        "quality_assessment": quality_assessment,
        "handholding_findings": handholding_findings,
        "recommended_next_steps": [
            "Human reviewer should verify that acceptance criteria were met.",
            "Record learning proposals only for repeated or high-value patterns.",
            "Run Git gates only after diff review, tests, and explicit approval.",
        ],
    }


def cmd_review(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace_root).resolve()
    ledger_root = Path(args.ledger_root).resolve() if args.ledger_root else None
    report = build_self_review(workspace_root, args.mission_id, args.review_id, ledger_root)
    preview = not args.confirm_review

    if preview:
        report["invocation"] = "preview_only"
        report["status"] = "preview"
    else:
        if args.approval_token != TOKENS["review"]:
            return fail("SELF-REVIEW FAILED", f"invalid approval token; expected {TOKENS['review']}", args.json)
        if report["blockers"]:
            return fail("SELF-REVIEW FAILED", "; ".join(report["blockers"]), args.json)
        report["invocation"] = "confirmed"
        report["status"] = "recorded"
        out = mission_dir(workspace_root, args.mission_id) / "reports" / f"{args.review_id}_self_review_report.json"
        write_json(out, report, force=args.force)
        report["output_path"] = str(out)

    return emit("SELF-REVIEW RECORDED" if not preview else "SELF-REVIEW PREVIEW", report, args.json)


def cmd_optimize(args: argparse.Namespace) -> int:
    workspace_root = Path(args.workspace_root).resolve()
    root = mission_dir(workspace_root, args.mission_id)
    blockers: List[str] = []
    if not root.exists():
        blockers.append("mission workspace does not exist")

    review_data: Dict[str, Any] = {}
    if args.review_report:
        review_path = Path(args.review_report).resolve()
        if not review_path.exists():
            blockers.append("review report does not exist")
        else:
            review_data = load_json(review_path)

    token_summary = review_data.get("token_summary") or {}
    optimizations = [
        {
            "area": "handholding",
            "recommendation": "Batch low-risk clarifications and reserve interruptions for approval boundaries.",
            "authority": "proposal_only",
        },
        {
            "area": "token_economy",
            "recommendation": "Use local or cheaper models for summarization, indexing, and low-risk drafting; reserve stronger models for architecture, debugging, and high-risk review.",
            "authority": "proposal_only",
        },
        {
            "area": "evidence",
            "recommendation": "Capture command outputs, validation results, and final acceptance evidence in mission reports.",
            "authority": "proposal_only",
        },
        {
            "area": "learning",
            "recommendation": "Promote only repeated, validated patterns through Scroll lifecycle proposals.",
            "authority": "proposal_only",
        },
    ]
    if token_summary and token_summary.get("estimated_input_tokens", 0) + token_summary.get("estimated_output_tokens", 0) > 0:
        optimizations.append({
            "area": "calibration",
            "recommendation": "Replace token estimates with provider-reported usage when available and calibrate estimator error.",
            "authority": "proposal_only",
        })

    payload = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "optimization_plan",
        "optimization_id": args.optimization_id,
        "mission_id": args.mission_id,
        "generated_at": utc_now(),
        "status": "blocked" if blockers else ("preview" if not args.confirm_optimization else "recorded"),
        "blockers": blockers,
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
        "optimizations": optimizations,
        "human_decision_required": True,
        "notes": [
            "Optimization plans are not permission.",
            "The human reviewer decides which recommendations become learning proposals or code changes.",
        ],
    }

    if not args.confirm_optimization:
        payload["invocation"] = "preview_only"
    else:
        if args.approval_token != TOKENS["optimize"]:
            return fail("OPTIMIZATION PLAN FAILED", f"invalid approval token; expected {TOKENS['optimize']}", args.json)
        if blockers:
            return fail("OPTIMIZATION PLAN FAILED", "; ".join(blockers), args.json)
        payload["invocation"] = "confirmed"
        out = root / "reports" / f"{args.optimization_id}_optimization_plan.json"
        write_json(out, payload, force=args.force)
        payload["output_path"] = str(out)

    return emit("OPTIMIZATION PLAN RECORDED" if args.confirm_optimization else "OPTIMIZATION PLAN PREVIEW", payload, args.json)


def validate_repo_root(repo_root: Path) -> None:
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        raise RuntimeError(f"repo root is not a git repository: {repo_root}")


def ensure_safe_git_paths(paths: Iterable[str]) -> List[str]:
    safe: List[str] = []
    for raw in paths:
        value = normalize_path_text(raw).strip()
        if not value:
            raise RuntimeError("empty git path is not allowed")
        p = Path(value)
        if p.is_absolute():
            raise RuntimeError(f"absolute git path is not allowed: {raw}")
        parts = tuple(part for part in value.split("/") if part not in ("", "."))
        if ".." in parts:
            raise RuntimeError(f"path traversal is not allowed: {raw}")
        if any(value == name or value.endswith("/" + name) for name in SAFE_PATH_DENY_NAMES):
            raise RuntimeError(f"sensitive file name is not allowed: {raw}")
        lowered = value.lower()
        for prefix in SAFE_PATH_DENY_PREFIXES:
            if lowered == prefix or lowered.startswith(prefix + "/"):
                raise RuntimeError(f"forbidden git path prefix: {raw}")
        if "/private/" in lowered or lowered.endswith("/private"):
            raise RuntimeError(f"private path is not allowed: {raw}")
        safe.append(value)
    if not safe:
        raise RuntimeError("at least one git path is required")
    return safe


def run_git(repo_root: Path, args: List[str]) -> Tuple[int, str, str]:
    completed = subprocess.run(
        ["git"] + args,
        cwd=str(repo_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def git_output(repo_root: Path, args: List[str]) -> Dict[str, Any]:
    code, out, err = run_git(repo_root, args)
    return {
        "args": ["git"] + args,
        "exit_code": code,
        "stdout": out.strip(),
        "stderr": err.strip(),
    }


def cmd_git_plan(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    sandbox_root = Path(args.sandbox_root).resolve() if args.sandbox_root else repo_root / "sandbox"
    try:
        validate_repo_root(repo_root)
        paths = ensure_safe_git_paths(args.paths)
    except Exception as exc:
        return fail("GIT OPERATION PLAN FAILED", str(exc), args.json)

    status = git_output(repo_root, ["status", "--short"])
    diff_stat = git_output(repo_root, ["diff", "--stat", "--"] + paths)
    branch_result = git_output(repo_root, ["branch", "--show-current"])

    payload = {
        "schema_version": SCHEMA_VERSION,
        "plan_type": "git_operation_plan",
        "plan_id": args.plan_id,
        "generated_at": utc_now(),
        "status": "preview" if not args.confirm_plan else "recorded",
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
        "repo_root": str(repo_root),
        "paths": paths,
        "remote": args.remote,
        "branch": args.branch or branch_result.get("stdout") or "",
        "commit_message": args.commit_message,
        "read_only_git_evidence": {
            "status_short": status,
            "diff_stat": diff_stat,
            "current_branch": branch_result,
        },
        "required_sequence": [
            "human reviews diff",
            "tests/audit commands pass",
            "APPROVE_GIT_STAGE",
            "APPROVE_GIT_COMMIT",
            "APPROVE_GIT_PUSH plus --allow-network for push",
        ],
        "notes": [
            "This plan is not permission.",
            "Stage, commit, and push require separate commands and separate approval tokens.",
        ],
    }

    if not args.confirm_plan:
        payload["invocation"] = "preview_only"
        return emit("GIT OPERATION PLAN PREVIEW", payload, args.json)

    if args.approval_token != TOKENS["git_plan"]:
        return fail("GIT OPERATION PLAN FAILED", f"invalid approval token; expected {TOKENS['git_plan']}", args.json)

    payload["invocation"] = "confirmed"
    output = Path(args.output).resolve() if args.output else sandbox_root / "reports" / f"{args.plan_id}_git_operation_plan.json"
    write_json(output, payload, force=args.force)
    payload["output_path"] = str(output)
    return emit("GIT OPERATION PLAN RECORDED", payload, args.json)


def load_plan(path: str) -> Dict[str, Any]:
    plan_path = Path(path).resolve()
    if not plan_path.exists():
        raise RuntimeError(f"plan does not exist: {plan_path}")
    plan = load_json(plan_path)
    if plan.get("plan_type") != "git_operation_plan":
        raise RuntimeError("plan is not a git_operation_plan")
    ensure_safe_git_paths(plan.get("paths") or [])
    return plan


def write_gate_report(plan_path: Path, suffix: str, payload: Dict[str, Any], force: bool = False) -> Path:
    out = plan_path.with_name(plan_path.stem.replace("_git_operation_plan", "") + f"_{suffix}_git_operation_gate_report.json")
    write_json(out, payload, force=force)
    return out


def git_gate_payload(plan: Dict[str, Any], operation: str, command_result: Dict[str, Any], status: str) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "git_operation_gate_report",
        "operation": operation,
        "plan_id": plan.get("plan_id"),
        "generated_at": utc_now(),
        "status": status,
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
        "paths": plan.get("paths") or [],
        "remote": plan.get("remote"),
        "branch": plan.get("branch"),
        "commit_message": plan.get("commit_message"),
        "command_result": command_result,
    }


def cmd_stage(args: argparse.Namespace) -> int:
    if not args.confirm_stage:
        return fail("GIT STAGE GATE FAILED", "stage requires --confirm-stage", args.json)
    if args.approval_token != TOKENS["stage"]:
        return fail("GIT STAGE GATE FAILED", f"invalid approval token; expected {TOKENS['stage']}", args.json)

    try:
        plan_path = Path(args.plan).resolve()
        plan = load_plan(args.plan)
        repo_root = Path(plan["repo_root"]).resolve()
        validate_repo_root(repo_root)
        paths = ensure_safe_git_paths(plan.get("paths") or [])
        code, out, err = run_git(repo_root, ["add", "--"] + paths)
        result = {"args": ["git", "add", "--"] + paths, "exit_code": code, "stdout": out.strip(), "stderr": err.strip()}
        payload = git_gate_payload(plan, "stage", result, "passed" if code == 0 else "failed")
        report_path = write_gate_report(plan_path, "stage", payload, force=args.force)
        payload["output_path"] = str(report_path)
        if code != 0:
            return emit("GIT STAGE GATE FAILED", payload, args.json, exit_code=1)
        return emit("GIT STAGE GATE PASSED", payload, args.json)
    except Exception as exc:
        return fail("GIT STAGE GATE FAILED", str(exc), args.json)


def cmd_commit(args: argparse.Namespace) -> int:
    if not args.confirm_commit:
        return fail("GIT COMMIT GATE FAILED", "commit requires --confirm-commit", args.json)
    if args.approval_token != TOKENS["commit"]:
        return fail("GIT COMMIT GATE FAILED", f"invalid approval token; expected {TOKENS['commit']}", args.json)

    try:
        plan_path = Path(args.plan).resolve()
        plan = load_plan(args.plan)
        repo_root = Path(plan["repo_root"]).resolve()
        validate_repo_root(repo_root)
        message = args.commit_message or plan.get("commit_message")
        if not message:
            raise RuntimeError("commit message is required")
        code, out, err = run_git(repo_root, ["commit", "-m", message])
        result = {"args": ["git", "commit", "-m", message], "exit_code": code, "stdout": out.strip(), "stderr": err.strip()}
        payload = git_gate_payload(plan, "commit", result, "passed" if code == 0 else "failed")
        report_path = write_gate_report(plan_path, "commit", payload, force=args.force)
        payload["output_path"] = str(report_path)
        if code != 0:
            return emit("GIT COMMIT GATE FAILED", payload, args.json, exit_code=1)
        return emit("GIT COMMIT GATE PASSED", payload, args.json)
    except Exception as exc:
        return fail("GIT COMMIT GATE FAILED", str(exc), args.json)


def cmd_push(args: argparse.Namespace) -> int:
    if not args.confirm_push:
        return fail("GIT PUSH GATE FAILED", "push requires --confirm-push", args.json)
    if args.approval_token != TOKENS["push"]:
        return fail("GIT PUSH GATE FAILED", f"invalid approval token; expected {TOKENS['push']}", args.json)
    if not args.allow_network:
        return fail("GIT PUSH GATE FAILED", "push requires --allow-network because Git push may contact a remote", args.json)

    try:
        plan_path = Path(args.plan).resolve()
        plan = load_plan(args.plan)
        repo_root = Path(plan["repo_root"]).resolve()
        validate_repo_root(repo_root)
        remote = args.remote or plan.get("remote") or "origin"
        branch = args.branch or plan.get("branch")
        if not branch:
            raise RuntimeError("branch is required for push")
        code, out, err = run_git(repo_root, ["push", remote, branch])
        result = {"args": ["git", "push", remote, branch], "exit_code": code, "stdout": out.strip(), "stderr": err.strip()}
        payload = git_gate_payload(plan, "push", result, "passed" if code == 0 else "failed")
        report_path = write_gate_report(plan_path, "push", payload, force=args.force)
        payload["output_path"] = str(report_path)
        if code != 0:
            return emit("GIT PUSH GATE FAILED", payload, args.json, exit_code=1)
        return emit("GIT PUSH GATE PASSED", payload, args.json)
    except Exception as exc:
        return fail("GIT PUSH GATE FAILED", str(exc), args.json)


def cmd_states(args: argparse.Namespace) -> int:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "self_review_git_gate_states",
        "tokens": TOKENS,
        "boundaries": BOUNDARIES,
        "authority": AUTHORITY,
        "git_gate_sequence": ["git-plan", "stage", "commit", "push"],
        "notes": [
            "Git plans are not permission.",
            "Git push requires --allow-network.",
            "Use temp repositories for smoke tests; do not test push on a real remote unless intended.",
        ],
    }
    return emit("SELF-REVIEW AND GIT GATE STATES", payload, args.json)


def emit(title: str, payload: Dict[str, Any], as_json: bool, exit_code: int = 0) -> int:
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(title)
        if payload.get("operation"):
            print(f"Operation: {payload['operation']}")
        if payload.get("plan_id"):
            print(f"Plan: {payload['plan_id']}")
        if payload.get("review_id"):
            print(f"Review: {payload['review_id']}")
        print(f"Status: {payload.get('status')}")
        print("Self-review: evidence_only")
        print("Optimization: proposal_only")
        print("Git operations: gated")
        print("Arbitrary shell: blocked")
        print("Model invocation: blocked")
        print("Adapter invocation: blocked")
        print("Private context access: blocked_by_default")
        if payload.get("output_path"):
            print("Output path:")
            print(f"- {payload['output_path']}")
    return exit_code


def fail(title: str, message: str, as_json: bool) -> int:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "failed",
        "blockers": [message],
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
        "generated_at": utc_now(),
    }
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(title)
        print(f"Blocker: {message}")
        print("Self-review: evidence_only")
        print("Git operations: gated")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Konoha self-review, optimization and Git operation gate.")
    sub = parser.add_subparsers(dest="command", required=True)

    review = sub.add_parser("review", help="Record or preview a mission self-review.")
    review.add_argument("--workspace-root", required=True)
    review.add_argument("--mission-id", required=True)
    review.add_argument("--review-id", required=True)
    review.add_argument("--ledger-root")
    review.add_argument("--confirm-review", action="store_true")
    review.add_argument("--approval-token")
    review.add_argument("--force", action="store_true")
    review.add_argument("--json", action="store_true")
    review.set_defaults(func=cmd_review)

    opt = sub.add_parser("optimize", help="Record or preview an optimization plan.")
    opt.add_argument("--workspace-root", required=True)
    opt.add_argument("--mission-id", required=True)
    opt.add_argument("--optimization-id", required=True)
    opt.add_argument("--review-report")
    opt.add_argument("--confirm-optimization", action="store_true")
    opt.add_argument("--approval-token")
    opt.add_argument("--force", action="store_true")
    opt.add_argument("--json", action="store_true")
    opt.set_defaults(func=cmd_optimize)

    plan = sub.add_parser("git-plan", help="Record or preview a Git operation plan.")
    plan.add_argument("--repo-root", required=True)
    plan.add_argument("--sandbox-root")
    plan.add_argument("--plan-id", required=True)
    plan.add_argument("--paths", nargs="+", required=True)
    plan.add_argument("--commit-message", required=True)
    plan.add_argument("--remote", default="origin")
    plan.add_argument("--branch")
    plan.add_argument("--confirm-plan", action="store_true")
    plan.add_argument("--approval-token")
    plan.add_argument("--output")
    plan.add_argument("--force", action="store_true")
    plan.add_argument("--json", action="store_true")
    plan.set_defaults(func=cmd_git_plan)

    stage = sub.add_parser("stage", help="Run git add from an approved plan.")
    stage.add_argument("--plan", required=True)
    stage.add_argument("--confirm-stage", action="store_true")
    stage.add_argument("--approval-token")
    stage.add_argument("--force", action="store_true")
    stage.add_argument("--json", action="store_true")
    stage.set_defaults(func=cmd_stage)

    commit = sub.add_parser("commit", help="Run git commit from an approved plan.")
    commit.add_argument("--plan", required=True)
    commit.add_argument("--commit-message")
    commit.add_argument("--confirm-commit", action="store_true")
    commit.add_argument("--approval-token")
    commit.add_argument("--force", action="store_true")
    commit.add_argument("--json", action="store_true")
    commit.set_defaults(func=cmd_commit)

    push = sub.add_parser("push", help="Run git push from an approved plan.")
    push.add_argument("--plan", required=True)
    push.add_argument("--remote")
    push.add_argument("--branch")
    push.add_argument("--confirm-push", action="store_true")
    push.add_argument("--allow-network", action="store_true")
    push.add_argument("--approval-token")
    push.add_argument("--force", action="store_true")
    push.add_argument("--json", action="store_true")
    push.set_defaults(func=cmd_push)

    states = sub.add_parser("states", help="List states, tokens and boundaries.")
    states.add_argument("--json", action="store_true")
    states.set_defaults(func=cmd_states)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return fail("SELF-REVIEW AND GIT GATE INTERRUPTED", "interrupted by user", getattr(args, "json", False))
    except Exception as exc:
        return fail("SELF-REVIEW AND GIT GATE FAILED", str(exc), getattr(args, "json", False))


if __name__ == "__main__":
    sys.exit(main())
