#!/usr/bin/env python3
"""End-to-end dry-run mission workflow for Konoha Agentic Academy.

This tool orchestrates existing Konoha tools through an allowlisted local chain:

1. optional project config validation;
2. dry-run runtime runner;
3. runtime package validator;
4. runtime package inspector;
5. runtime run registry;
6. optional public repo inspector;
7. mission workflow report written inside the sandbox run.

It does not execute missions, call adapters, run arbitrary shell commands, use the
network, access private Village context, perform Git writes, or write outside the
configured sandbox run.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,80}$")


BOUNDARIES = {
    "mode": "dry_run",
    "execution": "blocked",
    "filesystem_mutation": "sandbox_only",
    "git_operations": "blocked",
    "git_commit": "blocked",
    "git_push": "blocked",
    "private_context_access": "blocked",
    "adapter_execution": "blocked",
    "network_access": "blocked",
    "repository_apply": "blocked",
}


@dataclass
class StepResult:
    name: str
    status: str
    returncode: int
    command: list[str]
    stdout_tail: list[str]
    stderr_tail: list[str]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate_run_id(run_id: str) -> None:
    if not RUN_ID_RE.match(run_id):
        raise ValueError(
            "run_id must be 2-81 chars and contain only letters, numbers, dot, underscore, or dash"
        )
    if ".." in run_id or "/" in run_id or "\\" in run_id:
        raise ValueError("run_id must not contain path traversal or separators")


def resolve_under(root: Path, child: Path) -> Path:
    root_resolved = root.resolve()
    child_resolved = child.resolve()
    try:
        child_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"path escapes root: {child}") from exc
    return child_resolved


def repo_tool(repo_root: Path, relative_path: str) -> Path:
    tool_path = (repo_root / relative_path).resolve()
    if not tool_path.exists():
        raise FileNotFoundError(f"Required Konoha tool not found: {relative_path}")
    resolve_under(repo_root, tool_path)
    return tool_path


def tail_lines(text: str, limit: int = 12) -> list[str]:
    lines = text.splitlines()
    return lines[-limit:]


def run_command(command: list[str]) -> StepResult:
    completed = subprocess.run(  # noqa: S603 - command is assembled from allowlisted internal tools only.
        command,
        cwd=None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    return StepResult(
        name="",
        status="passed" if completed.returncode == 0 else "failed",
        returncode=completed.returncode,
        command=command,
        stdout_tail=tail_lines(completed.stdout),
        stderr_tail=tail_lines(completed.stderr),
    )


def add_step(results: list[StepResult], name: str, command: list[str]) -> bool:
    result = run_command(command)
    result.name = name
    results.append(result)
    return result.returncode == 0


def build_report(
    *,
    title: str,
    scope: str,
    run_id: str,
    repo_root: Path,
    sandbox_root: Path,
    run_dir: Path,
    package_path: Path,
    steps: list[StepResult],
) -> dict:
    status = "passed" if all(step.returncode == 0 for step in steps) else "failed"
    blockers = [
        {
            "step": step.name,
            "returncode": step.returncode,
            "stderr_tail": step.stderr_tail,
        }
        for step in steps
        if step.returncode != 0
    ]

    return {
        "schema_version": "0.23.0",
        "tool": "tools/mission_workflow/run_dry_run_mission.py",
        "generated_at": utc_now(),
        "mission": {
            "title": title,
            "scope": scope,
            "run_id": run_id,
        },
        "status": status,
        "repo_root": str(repo_root),
        "sandbox_root": str(sandbox_root),
        "run_dir": str(run_dir),
        "runtime_package": str(package_path),
        "boundaries": BOUNDARIES,
        "steps": [asdict(step) for step in steps],
        "blockers": blockers,
        "outputs": {
            "workflow_report": str(run_dir / "mission_workflow_report.json"),
            "runtime_package": str(package_path),
            "runtime_run_summary": str(run_dir / "runtime_run_summary.json"),
            "sandbox_run_manifest": str(run_dir / "sandbox_run_manifest.json"),
        },
    }


def write_report(run_dir: Path, report: dict) -> Path:
    report_path = resolve_under(run_dir, run_dir / "mission_workflow_report.json")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an end-to-end Konoha dry-run mission workflow inside sandbox."
    )
    parser.add_argument("--title", required=True, help="Mission title.")
    parser.add_argument("--scope", required=True, help="Mission scope.")
    parser.add_argument("--run-id", required=True, help="Sandbox run id.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument("--sandbox-root", default="sandbox", help="Sandbox root. Default: sandbox.")
    parser.add_argument("--config", default="", help="Optional Konoha project config path to validate first.")
    parser.add_argument("--skip-repo-inspection", action="store_true", help="Skip read-only repo inspection.")
    parser.add_argument("--force", action="store_true", help="Forward --force to the dry-run runtime runner.")
    parser.add_argument("--json", action="store_true", help="Print the final workflow report as JSON.")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    try:
        validate_run_id(args.run_id)
        repo_root = Path(args.repo_root).resolve()
        sandbox_root = Path(args.sandbox_root).resolve()
        resolve_under(repo_root, sandbox_root)

        run_dir = resolve_under(sandbox_root, sandbox_root / "runs" / args.run_id)
        package_path = run_dir / "runtime_package.json"

        tools = {
            "config_validator": repo_tool(repo_root, "tools/config_validator/validate_konoha_config.py"),
            "runtime_runner": repo_tool(repo_root, "tools/runtime_runner/run_dry_run_runtime.py"),
            "validator": repo_tool(repo_root, "tools/runtime_validator/validate_runtime_package.py"),
            "inspector": repo_tool(repo_root, "tools/runtime_inspector/inspect_runtime_package.py"),
            "registry": repo_tool(repo_root, "tools/runtime_registry/list_runtime_runs.py"),
            "repo_inspector": repo_tool(repo_root, "tools/repo_inspector/inspect_public_repo.py"),
        }
    except Exception as exc:
        print("DRY-RUN MISSION WORKFLOW FAILED")
        print(f"Reason: {exc}")
        return 1

    steps: list[StepResult] = []

    if args.config:
        config_path = Path(args.config).resolve()
        if not add_step(
            steps,
            "project_config_validation",
            [sys.executable, str(tools["config_validator"]), str(config_path)],
        ):
            report = build_report(
                title=args.title,
                scope=args.scope,
                run_id=args.run_id,
                repo_root=repo_root,
                sandbox_root=sandbox_root,
                run_dir=run_dir,
                package_path=package_path,
                steps=steps,
            )
            run_dir.mkdir(parents=True, exist_ok=True)
            write_report(run_dir, report)
            print("DRY-RUN MISSION WORKFLOW FAILED")
            print("Failed step: project_config_validation")
            return 1

    runtime_command = [
        sys.executable,
        str(tools["runtime_runner"]),
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
        runtime_command.append("--force")

    if not add_step(steps, "dry_run_runtime_runner", runtime_command):
        run_dir.mkdir(parents=True, exist_ok=True)
        report = build_report(
            title=args.title,
            scope=args.scope,
            run_id=args.run_id,
            repo_root=repo_root,
            sandbox_root=sandbox_root,
            run_dir=run_dir,
            package_path=package_path,
            steps=steps,
        )
        write_report(run_dir, report)
        print("DRY-RUN MISSION WORKFLOW FAILED")
        print("Failed step: dry_run_runtime_runner")
        return 1

    if not package_path.exists():
        run_dir.mkdir(parents=True, exist_ok=True)
        steps.append(
            StepResult(
                name="runtime_package_presence",
                status="failed",
                returncode=1,
                command=[],
                stdout_tail=[],
                stderr_tail=[f"Missing runtime package: {package_path}"],
            )
        )
        report = build_report(
            title=args.title,
            scope=args.scope,
            run_id=args.run_id,
            repo_root=repo_root,
            sandbox_root=sandbox_root,
            run_dir=run_dir,
            package_path=package_path,
            steps=steps,
        )
        write_report(run_dir, report)
        print("DRY-RUN MISSION WORKFLOW FAILED")
        print(f"Missing runtime package: {package_path}")
        return 1

    if not add_step(
        steps,
        "runtime_package_validation",
        [sys.executable, str(tools["validator"]), str(package_path)],
    ):
        report = build_report(
            title=args.title,
            scope=args.scope,
            run_id=args.run_id,
            repo_root=repo_root,
            sandbox_root=sandbox_root,
            run_dir=run_dir,
            package_path=package_path,
            steps=steps,
        )
        write_report(run_dir, report)
        print("DRY-RUN MISSION WORKFLOW FAILED")
        print("Failed step: runtime_package_validation")
        return 1

    if not add_step(
        steps,
        "runtime_package_inspection",
        [sys.executable, str(tools["inspector"]), str(package_path)],
    ):
        report = build_report(
            title=args.title,
            scope=args.scope,
            run_id=args.run_id,
            repo_root=repo_root,
            sandbox_root=sandbox_root,
            run_dir=run_dir,
            package_path=package_path,
            steps=steps,
        )
        write_report(run_dir, report)
        print("DRY-RUN MISSION WORKFLOW FAILED")
        print("Failed step: runtime_package_inspection")
        return 1

    add_step(
        steps,
        "runtime_run_registry",
        [sys.executable, str(tools["registry"]), "--sandbox-root", str(sandbox_root), "--json"],
    )

    if not args.skip_repo_inspection:
        add_step(
            steps,
            "read_only_repo_inspection",
            [sys.executable, str(tools["repo_inspector"]), "--repo-root", str(repo_root), "--json"],
        )

    report = build_report(
        title=args.title,
        scope=args.scope,
        run_id=args.run_id,
        repo_root=repo_root,
        sandbox_root=sandbox_root,
        run_dir=run_dir,
        package_path=package_path,
        steps=steps,
    )
    write_report(run_dir, report)

    if report["status"] == "passed":
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("DRY-RUN MISSION WORKFLOW PASSED")
            print(f"Run ID: {args.run_id}")
            print("Runtime runner: passed")
            print("Validation: passed")
            print("Inspection: passed")
            print("Execution: blocked")
            print("Filesystem mutation: sandbox only")
            print("Git operations: blocked")
            print("Private context access: blocked")
            print("Adapter execution: blocked")
            print("Network access: blocked")
            print(f"Report: {run_dir / 'mission_workflow_report.json'}")
        return 0

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("DRY-RUN MISSION WORKFLOW FAILED")
        for blocker in report["blockers"]:
            print(f"Failed step: {blocker['step']}")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
