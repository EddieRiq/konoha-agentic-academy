#!/usr/bin/env python3
"""
Konoha Proposed Artifact Workflow.

This tool orchestrates an explicitly bounded proposed-artifact workflow:

1. Prepare a dry-run runtime sandbox run.
2. Write a proposed artifact inside sandbox proposed_outputs/.
3. Preview the human-approved apply plan.
4. Optionally apply with explicit confirmation and approval token.
5. Write proposed_artifact_workflow_report.json inside the sandbox run.

Safety boundary:
- no arbitrary shell commands;
- no direct Git operations;
- no adapter invocation;
- no private context access;
- no repository apply without delegated apply-plan approval;
- all workflow records are written inside sandbox/runs/<run_id>/.
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


RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
APPROVAL_TOKEN = "APPLY_SANDBOX_PLAN"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fail(message: str, json_output: bool = False, report: Optional[Dict[str, Any]] = None) -> int:
    if json_output and report is not None:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("PROPOSED ARTIFACT WORKFLOW FAILED")
        print(message)
    return 1


def validate_run_id(run_id: str) -> None:
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError(
            "Unsafe run_id. Use 1-80 chars: letters, numbers, dot, underscore, hyphen. "
            "Path traversal and path separators are blocked."
        )
    if "/" in run_id or "\\" in run_id or ".." in run_id:
        raise ValueError("Unsafe run_id. Path separators and '..' are blocked.")


def resolve_under(root: Path, child: Path) -> Path:
    root_resolved = root.resolve()
    target = child.resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"Resolved path escapes root: {target}") from exc
    return target


def read_content(args: argparse.Namespace) -> str:
    if args.content_file:
        content_path = Path(args.content_file)
        return content_path.read_text(encoding="utf-8")
    return args.content or ""


def run_tool(command: List[str], cwd: Path) -> Dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        shell=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }


def step_record(name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": name,
        "passed": bool(result.get("passed")),
        "returncode": int(result.get("returncode", 1)),
        "stdout_excerpt": (result.get("stdout") or "")[:2000],
        "stderr_excerpt": (result.get("stderr") or "")[:2000],
    }


def write_report(run_dir: Path, report: Dict[str, Any]) -> Path:
    report_path = resolve_under(run_dir, run_dir / "proposed_artifact_workflow_report.json")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a sandbox-only proposed artifact workflow.",
    )
    parser.add_argument("--title", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--sandbox-root", default="./sandbox")
    parser.add_argument("--config", default=None)
    parser.add_argument("--artifact-path", required=True)
    parser.add_argument("--artifact-kind", default="markdown")
    parser.add_argument("--intended-repo-path", required=True)
    parser.add_argument("--content", default=None)
    parser.add_argument("--content-file", default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--preview-apply", action="store_true", help="Explicitly preview apply plan. Preview is also run by default.")
    parser.add_argument("--confirm-apply", action="store_true", help="Delegate approved apply to the apply-plan gate.")
    parser.add_argument("--approval-token", default="")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        validate_run_id(args.run_id)

        repo_root = Path(args.repo_root).resolve()
        sandbox_root = Path(args.sandbox_root).resolve()
        run_dir = resolve_under(sandbox_root, sandbox_root / "runs" / args.run_id)

        if args.confirm_apply and args.approval_token != APPROVAL_TOKEN:
            raise ValueError("Confirmed apply requires exact approval token APPLY_SANDBOX_PLAN.")

        content = read_content(args)
        if not content.strip():
            raise ValueError("Artifact content is required via --content or --content-file.")

        python_exe = sys.executable
        steps: List[Dict[str, Any]] = []
        raw_results: List[Dict[str, Any]] = []

        runtime_cmd = [
            python_exe,
            str(repo_root / "tools" / "runtime_runner" / "run_dry_run_runtime.py"),
            "--title",
            args.title,
            "--scope",
            args.scope,
            "--run-id",
            args.run_id,
            "--sandbox-root",
            str(sandbox_root),
        ]
        if args.force:
            runtime_cmd.append("--force")

        result = run_tool(runtime_cmd, repo_root)
        raw_results.append(result)
        steps.append(step_record("runtime_runner", result))
        if result["returncode"] != 0:
            report = build_report(args, run_dir, steps, "failed", applied=False)
            run_dir.mkdir(parents=True, exist_ok=True)
            write_report(run_dir, report)
            return fail("Runtime runner step failed.", args.json, report)

        writer_cmd = [
            python_exe,
            str(repo_root / "tools" / "artifact_writer" / "write_sandbox_artifact.py"),
            "--sandbox-root",
            str(sandbox_root),
            "--run-id",
            args.run_id,
            "--artifact-path",
            args.artifact_path,
            "--content",
            content,
            "--artifact-kind",
            args.artifact_kind,
            "--intended-repo-path",
            args.intended_repo_path,
        ]
        if args.force:
            writer_cmd.append("--force")

        result = run_tool(writer_cmd, repo_root)
        raw_results.append(result)
        steps.append(step_record("artifact_writer", result))
        if result["returncode"] != 0:
            report = build_report(args, run_dir, steps, "failed", applied=False)
            write_report(run_dir, report)
            return fail("Artifact writer step failed.", args.json, report)

        preview_cmd = [
            python_exe,
            str(repo_root / "tools" / "apply_plan" / "apply_sandbox_plan.py"),
            "--sandbox-root",
            str(sandbox_root),
            "--run-id",
            args.run_id,
            "--repo-root",
            str(repo_root),
        ]
        result = run_tool(preview_cmd, repo_root)
        raw_results.append(result)
        steps.append(step_record("apply_plan_preview", result))
        if result["returncode"] != 0:
            report = build_report(args, run_dir, steps, "failed", applied=False)
            write_report(run_dir, report)
            return fail("Apply plan preview step failed.", args.json, report)

        applied = False
        if args.confirm_apply:
            apply_cmd = preview_cmd + [
                "--confirm-apply",
                "--approval-token",
                args.approval_token,
            ]
            result = run_tool(apply_cmd, repo_root)
            raw_results.append(result)
            steps.append(step_record("apply_plan_confirm", result))
            if result["returncode"] != 0:
                report = build_report(args, run_dir, steps, "failed", applied=False)
                write_report(run_dir, report)
                return fail("Apply plan confirm step failed.", args.json, report)
            applied = True

        report = build_report(args, run_dir, steps, "passed", applied=applied)
        report_path = write_report(run_dir, report)

        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("PROPOSED ARTIFACT WORKFLOW PASSED")
            print(f"Run: {args.run_id}")
            print(f"Report: {report_path}")
            print("Execution: blocked")
            print("Filesystem mutation: sandbox only" if not applied else "Filesystem mutation: allowlisted apply only")
            print("Repository apply: applied with human approval" if applied else "Repository apply: preview_only")
            print("Git operations: blocked")
            print("Private context access: blocked")
            print("Adapter execution: blocked")
            print("Network access: blocked")

        return 0

    except Exception as exc:  # noqa: BLE001 - CLI boundary should report cleanly
        report = {
            "schema_version": "0.24.0",
            "status": "failed",
            "created_at": utc_now(),
            "error": str(exc),
            "boundaries": safety_boundaries(applied=False),
        }
        return fail(str(exc), args.json, report)


def safety_boundaries(applied: bool) -> Dict[str, str]:
    return {
        "execution": "blocked",
        "filesystem_mutation": "allowlisted_apply_only" if applied else "sandbox_only",
        "repository_apply": "human_approved" if applied else "preview_only",
        "git_operations": "blocked",
        "private_context_access": "blocked",
        "adapter_execution": "blocked",
        "network_access": "blocked",
        "runtime_authority": "not_authorized",
    }


def build_report(
    args: argparse.Namespace,
    run_dir: Path,
    steps: List[Dict[str, Any]],
    status: str,
    applied: bool,
) -> Dict[str, Any]:
    return {
        "schema_version": "0.24.0",
        "workflow": "proposed_artifact_workflow",
        "status": status,
        "created_at": utc_now(),
        "title": args.title,
        "scope": args.scope,
        "run_id": args.run_id,
        "run_dir": str(run_dir),
        "artifact": {
            "artifact_path": args.artifact_path,
            "artifact_kind": args.artifact_kind,
            "intended_repo_path": args.intended_repo_path,
        },
        "steps": steps,
        "outputs": {
            "runtime_package": str(run_dir / "runtime_package.json"),
            "apply_plan": str(run_dir / "apply_plan.json"),
            "artifact_write_report": str(run_dir / "artifact_write_report.json"),
            "workflow_report": str(run_dir / "proposed_artifact_workflow_report.json"),
        },
        "boundaries": safety_boundaries(applied=applied),
    }


if __name__ == "__main__":
    raise SystemExit(main())
