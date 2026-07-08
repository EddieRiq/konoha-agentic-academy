#!/usr/bin/env python3
"""Run Konoha integrated dry-run smoke tests.

This tool orchestrates existing Konoha tools through explicit, allowlisted
Python subprocess calls. It is a smoke-test runner, not a mission executor.

Safety boundary:
- no shell=True;
- no arbitrary command execution;
- no Git write operations;
- no adapter invocation;
- no private context access;
- writes only integration reports under the configured sandbox root.
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

RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,80}$")


class IntegrationError(RuntimeError):
    """Raised when the integration smoke test cannot be prepared safely."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_run_id(run_id: str) -> str:
    if not RUN_ID_PATTERN.match(run_id):
        raise IntegrationError("run_id contains unsafe characters")
    if ".." in run_id or "/" in run_id or "\\" in run_id:
        raise IntegrationError("run_id must not contain path traversal or separators")
    return run_id


def resolve_under(root: Path, relative_path: str) -> Path:
    root_resolved = root.resolve()
    candidate = (root_resolved / relative_path).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise IntegrationError(f"path escapes allowed root: {relative_path}") from exc
    return candidate


def tool_path(repo_root: Path, relative_path: str) -> Path:
    path = resolve_under(repo_root, relative_path)
    if not path.exists():
        raise IntegrationError(f"required tool not found: {relative_path}")
    return path


def run_step(name: str, command: List[str], cwd: Path) -> Dict[str, Any]:
    started_at = utc_now()
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        shell=False,
    )
    return {
        "name": name,
        "command": command,
        "returncode": completed.returncode,
        "passed": completed.returncode == 0,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "started_at": started_at,
        "completed_at": utc_now(),
    }


def build_steps(
    repo_root: Path,
    sandbox_root: Path,
    run_id: str,
    config_path: Optional[Path],
    include_repo_inspector: bool,
    include_git_readiness: bool,
    include_artifact_workflow: bool,
) -> List[Dict[str, Any]]:
    python_exe = sys.executable

    runtime_package_path = sandbox_root / "runs" / run_id / "runtime_package.json"
    artifact_run_id = f"{run_id}-artifact"

    steps: List[Dict[str, Any]] = []

    if config_path is not None:
        steps.append(
            {
                "name": "config_validation",
                "command": [
                    python_exe,
                    str(tool_path(repo_root, "tools/config_validator/validate_konoha_config.py")),
                    str(config_path),
                ],
            }
        )

    steps.append(
        {
            "name": "dry_run_runtime",
            "command": [
                python_exe,
                str(tool_path(repo_root, "tools/runtime_runner/run_dry_run_runtime.py")),
                "--title",
                "v0.26 integrated smoke test",
                "--scope",
                "Run the integrated safe dry-run toolchain.",
                "--run-id",
                run_id,
                "--sandbox-root",
                str(sandbox_root),
                "--force",
            ],
        }
    )

    steps.append(
        {
            "name": "package_validation",
            "command": [
                python_exe,
                str(tool_path(repo_root, "tools/runtime_validator/validate_runtime_package.py")),
                str(runtime_package_path),
            ],
        }
    )

    steps.append(
        {
            "name": "package_inspection",
            "command": [
                python_exe,
                str(tool_path(repo_root, "tools/runtime_inspector/inspect_runtime_package.py")),
                str(runtime_package_path),
            ],
        }
    )

    steps.append(
        {
            "name": "run_registry",
            "command": [
                python_exe,
                str(tool_path(repo_root, "tools/runtime_registry/list_runtime_runs.py")),
                "--sandbox-root",
                str(sandbox_root),
            ],
        }
    )

    if include_repo_inspector:
        steps.append(
            {
                "name": "repo_inspection",
                "command": [
                    python_exe,
                    str(tool_path(repo_root, "tools/repo_inspector/inspect_public_repo.py")),
                    "--repo-root",
                    str(repo_root),
                ],
            }
        )

    if include_git_readiness:
        steps.append(
            {
                "name": "git_readiness",
                "command": [
                    python_exe,
                    str(tool_path(repo_root, "tools/git_readiness/inspect_git_readiness.py")),
                    "--repo-root",
                    str(repo_root),
                    "--allow-dirty",
                ],
            }
        )

    if include_artifact_workflow:
        steps.append(
            {
                "name": "proposed_artifact_workflow",
                "command": [
                    python_exe,
                    str(tool_path(repo_root, "tools/artifact_workflow/run_proposed_artifact_workflow.py")),
                    "--title",
                    "v0.26 integrated artifact workflow smoke test",
                    "--scope",
                    "Prepare a proposed artifact in sandbox and preview the apply plan.",
                    "--run-id",
                    artifact_run_id,
                    "--repo-root",
                    str(repo_root),
                    "--sandbox-root",
                    str(sandbox_root),
                    "--artifact-path",
                    "docs/integration_note.md",
                    "--content",
                    "# Integration note from v0.26 smoke test",
                    "--artifact-kind",
                    "markdown",
                    "--intended-repo-path",
                    f"sandbox/tmp/{artifact_run_id}/integration_note.md",
                    "--force",
                ],
            }
        )

    return steps


def write_report(sandbox_root: Path, run_id: str, report: Dict[str, Any]) -> Path:
    validate_run_id(run_id)
    reports_dir = resolve_under(sandbox_root, "reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = resolve_under(reports_dir, f"{run_id}_integrated_test_report.json")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


def build_report(
    repo_root: Path,
    sandbox_root: Path,
    run_id: str,
    steps: List[Dict[str, Any]],
    report_path: Optional[Path] = None,
) -> Dict[str, Any]:
    passed = all(step.get("passed") for step in steps)
    failed_steps = [step["name"] for step in steps if not step.get("passed")]

    return {
        "schema_version": "0.1.0",
        "tool": "integrated_smoke_tests",
        "status": "passed" if passed else "failed",
        "passed": passed,
        "run_id": run_id,
        "repo_root": str(repo_root),
        "sandbox_root": str(sandbox_root),
        "report_path": str(report_path) if report_path else None,
        "created_at": utc_now(),
        "steps": steps,
        "failed_steps": failed_steps,
        "safety": {
            "execution": "blocked",
            "filesystem_mutation": "sandbox_reports_only",
            "git_operations": "read_only_or_blocked",
            "git_write_operations": "blocked",
            "private_context_access": "blocked",
            "adapter_execution": "blocked",
            "network_access": "blocked",
        },
    }


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run integrated Konoha dry-run smoke tests without mission execution."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--sandbox-root", default="sandbox", help="Sandbox root for smoke-test outputs.")
    parser.add_argument("--run-id", default="v0-26-integrated-smoke", help="Safe run ID.")
    parser.add_argument("--config", default="konoha.config.example.json", help="Optional Konoha config path.")
    parser.add_argument("--skip-config", action="store_true", help="Skip config validation.")
    parser.add_argument("--skip-repo-inspector", action="store_true", help="Skip read-only repo inspection.")
    parser.add_argument("--skip-git-readiness", action="store_true", help="Skip Git read-only readiness inspection.")
    parser.add_argument("--skip-artifact-workflow", action="store_true", help="Skip proposed artifact workflow preview.")
    parser.add_argument("--json", action="store_true", help="Print JSON report to stdout.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    try:
        run_id = validate_run_id(args.run_id)
        repo_root = Path(args.repo_root).resolve()
        sandbox_root = Path(args.sandbox_root).resolve()

        if not repo_root.exists():
            raise IntegrationError(f"repo root does not exist: {repo_root}")

        config_path: Optional[Path] = None
        if not args.skip_config:
            config_path = Path(args.config)
            if not config_path.is_absolute():
                config_path = (repo_root / config_path).resolve()
            if not config_path.exists():
                raise IntegrationError(f"config not found: {config_path}")

        steps_to_run = build_steps(
            repo_root=repo_root,
            sandbox_root=sandbox_root,
            run_id=run_id,
            config_path=config_path,
            include_repo_inspector=not args.skip_repo_inspector,
            include_git_readiness=not args.skip_git_readiness,
            include_artifact_workflow=not args.skip_artifact_workflow,
        )

        results: List[Dict[str, Any]] = []
        for step in steps_to_run:
            result = run_step(step["name"], step["command"], repo_root)
            results.append(result)
            if not result["passed"]:
                break

        report = build_report(repo_root, sandbox_root, run_id, results)
        report_path = write_report(sandbox_root, run_id, report)
        report["report_path"] = str(report_path)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            if report["passed"]:
                print("INTEGRATED SMOKE TESTS PASSED")
            else:
                print("INTEGRATED SMOKE TESTS FAILED")
                print("Failed steps: " + ", ".join(report["failed_steps"]))
            print("Execution: blocked")
            print("Filesystem mutation: sandbox reports only")
            print("Git operations: read-only or blocked")
            print("Git write operations: blocked")
            print("Private context access: blocked")
            print("Adapter execution: blocked")
            print("Network access: blocked")
            print(f"Report: {report_path}")

        return 0 if report["passed"] else 1

    except IntegrationError as exc:
        error_report = {
            "schema_version": "0.1.0",
            "tool": "integrated_smoke_tests",
            "status": "failed",
            "passed": False,
            "error": str(exc),
            "safety": {
                "execution": "blocked",
                "filesystem_mutation": "blocked",
                "git_write_operations": "blocked",
                "private_context_access": "blocked",
                "adapter_execution": "blocked",
                "network_access": "blocked",
            },
        }
        if args.json:
            print(json.dumps(error_report, indent=2, sort_keys=True))
        else:
            print("INTEGRATED SMOKE TESTS FAILED")
            print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
