#!/usr/bin/env python3
"""
Hokage Planner Loop.

Planning-only loop:
Mission Workspace -> sandbox dry-run run -> Real Model Invocation Gate
-> mission-local plan proposal -> planner loop report.

The planner loop does not execute mission actions. Model output is evidence only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


APPROVAL_TOKEN = "INVOKE_REAL_MODEL"

BOUNDARIES = {
    "execution": "blocked",
    "filesystem_mutation": "mission workspace plans/reports and delegated sandbox outputs only",
    "repository_apply": "blocked",
    "git_operations": "blocked",
    "private_context_access": "blocked",
    "model_output_authority": "evidence_only",
    "real_model_invocation": "gated",
    "network_access": "blocked unless explicit provider gate approval is used",
}

SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_id(value: str, label: str) -> str:
    if not value:
        raise ValueError(f"{label} is required")
    if "/" in value or "\\" in value or value in {".", ".."}:
        raise ValueError(f"{label} must not contain path separators")
    if not SAFE_ID_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must be alphanumeric plus '.', '_' or '-'")
    return value


def resolve_under(root: Path, *parts: str) -> Path:
    root_resolved = root.resolve()
    candidate = root_resolved.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"path escapes root: {candidate}") from exc
    return candidate


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_text(path: Path, content: str, *, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise ValueError(f"output already exists; use --force: {path}")
    with path.open("w", encoding="utf-8") as handle:
        handle.write(content.rstrip() + "\n")


def mission_paths(workspace_root: Path, mission_id: str) -> Dict[str, Path]:
    mission_id = safe_id(mission_id, "mission_id")
    mission_root = resolve_under(workspace_root, "missions", mission_id)
    return {
        "mission_root": mission_root,
        "charter": mission_root / "charter.md",
        "manifest": mission_root / "mission_manifest.json",
        "plans": mission_root / "plans",
        "reports": mission_root / "reports",
    }


def validate_mission_workspace(paths: Dict[str, Path]) -> Dict[str, Any]:
    missing = []
    for key in ["mission_root", "charter", "manifest", "plans", "reports"]:
        if not paths[key].exists():
            missing.append(str(paths[key]))
    if missing:
        raise ValueError("mission workspace is incomplete: " + ", ".join(missing))

    manifest = read_json(paths["manifest"])
    charter_text = paths["charter"].read_text(encoding="utf-8")
    if not charter_text.strip():
        raise ValueError("Mission Charter is empty")

    return {
        "manifest": manifest,
        "charter_excerpt": charter_text[:500],
    }


def run_delegated_tool(repo_root: Path, script: str, args: List[str]) -> Dict[str, Any]:
    script_path = resolve_under(repo_root, script)
    if not script_path.exists():
        return {
            "script": script,
            "returncode": 1,
            "stdout": "",
            "stderr": f"missing delegated tool: {script}",
        }

    completed = subprocess.run(
        [sys.executable, str(script_path)] + args,
        cwd=str(repo_root.resolve()),
        capture_output=True,
        text=True,
        shell=False,
    )
    return {
        "script": script,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def make_plan_proposal(
    *,
    mission_id: str,
    run_id: str,
    charter_excerpt: str,
    model_output: str,
    request_path: Path,
) -> str:
    return f"""# Hokage Plan Proposal

Status: review_required
Mission ID: {mission_id}
Planner run ID: {run_id}
Source: Real Model Invocation Gate output
Request plan: {request_path.as_posix()}

## Non-authority rules

- This plan is a proposal only.
- Model output is evidence only.
- Model inference is never permission.
- This plan does not authorize execution.
- This plan does not authorize repository apply, Git staging, Git commit, Git push, private context access, or mission closure.
- Human approval is required before any sensitive transition.

## Mission Charter excerpt

```text
{charter_excerpt.strip()}
```

## Proposed plan from model evidence

{model_output.strip()}

## Required next step

Review this proposal through the Human Approval Console CLI before any downstream action.
"""


def build_report(
    *,
    status: str,
    mission_id: str,
    run_id: str,
    workspace_root: Path,
    sandbox_root: Path,
    steps: List[Dict[str, Any]],
    blockers: List[str],
    outputs: Dict[str, str],
    preview_only: bool,
) -> Dict[str, Any]:
    return {
        "report_type": "hokage_planner_loop_report",
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "status": status,
        "mission_id": mission_id,
        "run_id": run_id,
        "workspace_root": str(workspace_root),
        "sandbox_root": str(sandbox_root),
        "preview_only": preview_only,
        "steps": steps,
        "blockers": blockers,
        "outputs": outputs,
        "boundaries": BOUNDARIES,
        "human_review_required": True,
        "non_authority_statement": "Model output is evidence only and never grants permission to execute, apply, stage, commit, push, or close a mission.",
    }


def print_report_summary(report: Dict[str, Any]) -> None:
    if report["status"] == "passed" and report["preview_only"]:
        print("HOKAGE PLANNER LOOP PREVIEW PASSED")
    elif report["status"] == "passed":
        print("HOKAGE PLANNER LOOP PASSED")
    else:
        print("HOKAGE PLANNER LOOP FAILED")

    print(f"Mission: {report['mission_id']}")
    print(f"Run: {report['run_id']}")
    print(f"Preview only: {str(report['preview_only']).lower()}")
    print("Execution: blocked")
    print("Filesystem mutation: mission workspace plans/reports and delegated sandbox outputs only")
    print("Repository apply: blocked")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Model output authority: evidence_only")
    print("Real model invocation: gated")
    print("Network access: blocked unless explicit provider gate approval is used")
    for blocker in report["blockers"]:
        print(f"Blocker: {blocker}")


def run(args: argparse.Namespace) -> Dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    workspace_root = Path(args.workspace_root).resolve()
    sandbox_root = Path(args.sandbox_root).resolve()
    mission_id = safe_id(args.mission_id, "mission_id")
    run_id = safe_id(args.run_id, "run_id")

    paths = mission_paths(workspace_root, mission_id)
    steps: List[Dict[str, Any]] = []
    blockers: List[str] = []
    outputs: Dict[str, str] = {}

    preview_only = not args.confirm_invocation

    try:
        if args.confirm_invocation and args.approval_token != APPROVAL_TOKEN:
            raise ValueError("confirmed model invocation requires exact approval token INVOKE_REAL_MODEL")

        workspace_info = validate_mission_workspace(paths)

        runtime_args = [
            "--title",
            f"Hokage planner loop for {mission_id}",
            "--scope",
            "Prepare sandbox evidence for planning-only model invocation.",
            "--run-id",
            run_id,
            "--sandbox-root",
            str(sandbox_root),
        ]
        if args.force:
            runtime_args.append("--force")

        runtime_step = run_delegated_tool(
            repo_root,
            "tools/runtime_runner/run_dry_run_runtime.py",
            runtime_args,
        )
        steps.append(runtime_step)
        if runtime_step["returncode"] != 0:
            raise ValueError("dry-run runtime preparation failed")

        model_args = [
            "--contract",
            str(Path(args.contract)),
            "--request",
            str(Path(args.request)),
            "--sandbox-root",
            str(sandbox_root),
            "--run-id",
            run_id,
        ]
        if args.confirm_invocation:
            model_args.extend(["--confirm-invocation", "--approval-token", args.approval_token])
        if args.allow_network:
            model_args.append("--allow-network")
        if args.force:
            model_args.append("--force")

        model_step = run_delegated_tool(
            repo_root,
            "tools/model_invocation/invoke_model_gate.py",
            model_args,
        )
        steps.append(model_step)
        if model_step["returncode"] != 0:
            raise ValueError("model invocation gate failed")

        run_root = resolve_under(sandbox_root, "runs", run_id)
        report_path = paths["reports"] / f"{run_id}_hokage_planner_loop_report.json"
        sandbox_report_path = run_root / "hokage_planner_loop_report.json"
        outputs["mission_report"] = str(report_path)
        outputs["sandbox_report"] = str(sandbox_report_path)

        if args.confirm_invocation:
            model_output_path = run_root / "model_outputs" / "model_invocation_output.md"
            if not model_output_path.exists():
                raise ValueError(f"missing model output: {model_output_path}")

            model_output = model_output_path.read_text(encoding="utf-8")
            plan_path = paths["plans"] / f"{run_id}_hokage_plan_proposal.md"
            proposal = make_plan_proposal(
                mission_id=mission_id,
                run_id=run_id,
                charter_excerpt=workspace_info["charter_excerpt"],
                model_output=model_output,
                request_path=Path(args.request),
            )
            write_text(plan_path, proposal, force=args.force)
            outputs["plan_proposal"] = str(plan_path)
            outputs["model_output"] = str(model_output_path)

        status = "passed"
    except Exception as exc:
        status = "failed"
        blockers.append(str(exc))
        report_path = paths.get("reports", workspace_root / "reports") / f"{run_id}_hokage_planner_loop_report.json"
        sandbox_report_path = resolve_under(sandbox_root, "runs", run_id) / "hokage_planner_loop_report.json"
        outputs["mission_report"] = str(report_path)
        outputs["sandbox_report"] = str(sandbox_report_path)

    report = build_report(
        status=status,
        mission_id=mission_id,
        run_id=run_id,
        workspace_root=workspace_root,
        sandbox_root=sandbox_root,
        steps=steps,
        blockers=blockers,
        outputs=outputs,
        preview_only=preview_only,
    )

    try:
        write_json(Path(outputs["mission_report"]), report)
        write_json(Path(outputs["sandbox_report"]), report)
    except Exception as exc:
        report["status"] = "failed"
        report["blockers"].append(f"failed to write report: {exc}")

    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a planning-only Hokage loop using the gated model invocation boundary."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--workspace-root", required=True, help="Mission workspace root.")
    parser.add_argument("--mission-id", required=True, help="Mission ID inside workspace.")
    parser.add_argument("--sandbox-root", default="./sandbox", help="Sandbox root.")
    parser.add_argument("--run-id", required=True, help="Planner loop sandbox run ID.")
    parser.add_argument(
        "--contract",
        default="examples/model_invocation/model_invocation_contract.example.json",
        help="Model invocation contract JSON.",
    )
    parser.add_argument(
        "--request",
        default="examples/model_invocation/mock_model_request_plan.example.json",
        help="Model request plan JSON.",
    )
    parser.add_argument("--confirm-invocation", action="store_true", help="Invoke the model gate instead of preview.")
    parser.add_argument("--approval-token", default="", help="Required exact token for confirmed invocation.")
    parser.add_argument("--allow-network", action="store_true", help="Forward explicit network approval to model gate.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated outputs.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = run(args)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_report_summary(report)

    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
