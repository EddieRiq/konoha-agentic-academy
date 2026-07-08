#!/usr/bin/env python3
"""Konoha v1.0 release readiness checker.

This checker adds no runtime authority. It verifies that the public local-first
dry-run runtime has the expected release surface and delegates only to
allowlisted internal checks.

It may write one release-readiness report under sandbox/reports.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Sequence


APPROVAL_STATUS = {
    "execution": "blocked",
    "filesystem_mutation": "sandbox reports and delegated sandbox outputs only",
    "repository_apply": "blocked",
    "git_operations": "read-only or blocked",
    "git_write_operations": "blocked",
    "private_context_access": "blocked",
    "adapter_execution": "mock only through adapter gate",
    "real_adapter_execution": "blocked",
    "network_access": "blocked",
}

SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9._-]+$")

REQUIRED_PUBLIC_PATHS = [
    "README.md",
    "CHANGELOG.md",
    "docs/roadmap.md",
    "konoha.config.example.json",
    "tools/konoha_cli.py",
    "tools/config_validator/validate_konoha_config.py",
    "tools/runtime_validator/validate_runtime_package.py",
    "tools/runtime_builder/create_dry_run_package.py",
    "tools/runtime_inspector/inspect_runtime_package.py",
    "tools/sandbox_boundary/prepare_sandbox_run.py",
    "tools/runtime_runner/run_dry_run_runtime.py",
    "tools/runtime_registry/list_runtime_runs.py",
    "tools/repo_inspector/inspect_public_repo.py",
    "tools/artifact_writer/write_sandbox_artifact.py",
    "tools/apply_plan/apply_sandbox_plan.py",
    "tools/git_readiness/inspect_git_readiness.py",
    "tools/git_staging/stage_allowlisted_files.py",
    "tools/git_commit/create_git_commit.py",
    "tools/mission_workflow/run_dry_run_mission.py",
    "tools/artifact_workflow/run_proposed_artifact_workflow.py",
    "tools/integration/run_integrated_smoke_tests.py",
    "tools/mock_adapter/run_mock_adapter.py",
    "tools/adapter_gate/invoke_adapter_gate.py",
    "tools/dogfood/run_dogfood_mission_suite.py",
    "schemas/runtime/konoha_project_config.schema.json",
    "schemas/runtime/mission_workflow_report.schema.json",
    "schemas/runtime/proposed_artifact_workflow_report.schema.json",
    "schemas/runtime/integrated_test_report.schema.json",
    "schemas/runtime/mock_adapter_invocation_report.schema.json",
    "schemas/runtime/adapter_invocation_gate_report.schema.json",
    "schemas/runtime/dogfood_mission_suite_report.schema.json",
    "docs/guides/project_config_and_policy_contract.md",
    "docs/guides/end_to_end_dry_run_mission_workflow.md",
    "docs/guides/proposed_artifact_workflow.md",
    "docs/guides/integrated_tests_and_ci.md",
    "docs/guides/mock_adapter_clerk_interface.md",
    "docs/guides/adapter_invocation_gate_disabled_by_default.md",
    "docs/guides/dogfood_mission_suite.md",
]

REQUIRED_BOUNDARY_PHRASES = [
    "Execution: blocked",
    "Git operations",
    "Private context access",
    "Network access",
]


def fail(message: str) -> int:
    print("V1 RELEASE READINESS FAILED")
    print(f"Blocker: {message}")
    return 1


def validate_run_id(run_id: str) -> None:
    if not run_id or not SAFE_RUN_ID.match(run_id):
        raise ValueError("run_id must be alphanumeric plus '.', '_' or '-' and may not contain path separators")
    if "/" in run_id or "\\" in run_id or ".." in run_id:
        raise ValueError("run_id may not contain path traversal")


def resolve_under(root: Path, child: str) -> Path:
    root_resolved = root.resolve()
    candidate = (root_resolved / child).resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError(f"path escapes root: {child}")
    return candidate


def write_json_lf(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def truncate_text(value: str, limit: int = 4000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "\n...[truncated]..."


def run_command(name: str, command: Sequence[str], cwd: Path) -> Dict:
    completed = subprocess.run(
        list(command),
        cwd=str(cwd),
        text=True,
        capture_output=True,
        shell=False,
    )
    return {
        "name": name,
        "command": list(command),
        "returncode": completed.returncode,
        "passed": completed.returncode == 0,
        "stdout": truncate_text(completed.stdout),
        "stderr": truncate_text(completed.stderr),
    }


def check_required_paths(repo_root: Path) -> Dict:
    missing: List[str] = []
    present: List[str] = []
    for relative in REQUIRED_PUBLIC_PATHS:
        path = resolve_under(repo_root, relative)
        if path.exists():
            present.append(relative)
        else:
            missing.append(relative)

    return {
        "name": "required_public_paths",
        "passed": not missing,
        "present_count": len(present),
        "missing_count": len(missing),
        "missing": missing,
    }


def check_boundary_phrases(repo_root: Path) -> Dict:
    candidate_paths = [
        "README.md",
        "docs/guides/v1_release_readiness.md",
        "docs/reference/release_safety_boundaries.md",
        "docs/reference/capability_matrix.md",
        "docs/guides/dogfood_mission_suite.md",
        "docs/guides/adapter_invocation_gate_disabled_by_default.md",
        "docs/guides/git_commit_gate.md",
    ]

    matched: Dict[str, List[str]] = {}
    for relative in candidate_paths:
        path = resolve_under(repo_root, relative)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        found = [phrase for phrase in REQUIRED_BOUNDARY_PHRASES if phrase in text]
        if found:
            matched[relative] = found

    missing_phrases = [
        phrase
        for phrase in REQUIRED_BOUNDARY_PHRASES
        if not any(phrase in phrases for phrases in matched.values())
    ]

    return {
        "name": "boundary_phrase_check",
        "passed": not missing_phrases,
        "matched": matched,
        "missing_phrases": missing_phrases,
    }


def build_steps(repo_root: Path, sandbox_root: Path, run_id: str, allow_dirty: bool, skip_smoke: bool) -> List[Dict]:
    steps: List[Dict] = []

    steps.append(
        run_command(
            "unit_tests",
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
            repo_root,
        )
    )

    if not skip_smoke:
        steps.append(
            run_command(
                "integrated_smoke_tests",
                [
                    sys.executable,
                    "tools/integration/run_integrated_smoke_tests.py",
                    "--repo-root",
                    ".",
                    "--sandbox-root",
                    str(sandbox_root),
                    "--run-id",
                    f"{run_id}-integration",
                ],
                repo_root,
            )
        )

        steps.append(
            run_command(
                "dogfood_mission_suite",
                [
                    sys.executable,
                    "tools/dogfood/run_dogfood_mission_suite.py",
                    "--repo-root",
                    ".",
                    "--sandbox-root",
                    str(sandbox_root),
                    "--run-id",
                    f"{run_id}-dogfood",
                ],
                repo_root,
            )
        )

    steps.append(
        run_command(
            "repo_inspection",
            [
                sys.executable,
                "tools/repo_inspector/inspect_public_repo.py",
                "--repo-root",
                ".",
                "--json",
            ],
            repo_root,
        )
    )

    git_readiness_command = [
        sys.executable,
        "tools/git_readiness/inspect_git_readiness.py",
        "--repo-root",
        ".",
        "--json",
    ]
    if allow_dirty:
        git_readiness_command.append("--allow-dirty")

    steps.append(run_command("git_readiness", git_readiness_command, repo_root))

    return steps


def build_report(args: argparse.Namespace) -> Dict:
    validate_run_id(args.run_id)

    repo_root = Path(args.repo_root).resolve()
    sandbox_root = Path(args.sandbox_root).resolve()

    if not repo_root.exists():
        raise ValueError(f"repo root does not exist: {repo_root}")

    path_check = check_required_paths(repo_root)
    boundary_check = check_boundary_phrases(repo_root)

    delegated_steps: List[Dict] = []
    if path_check["passed"]:
        delegated_steps = build_steps(
            repo_root=repo_root,
            sandbox_root=sandbox_root,
            run_id=args.run_id,
            allow_dirty=args.allow_dirty,
            skip_smoke=args.skip_smoke,
        )

    all_checks = [path_check, boundary_check] + delegated_steps
    passed = all(check.get("passed") is True for check in all_checks)

    return {
        "schema_version": "1.0",
        "tool": "check_v1_release_readiness",
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "run_id": args.run_id,
        "repo_root": str(repo_root),
        "sandbox_root": str(sandbox_root),
        "release": {
            "target_version": "v1.0.0",
            "name": "Stable local-first dry-run runtime",
            "status": "release_readiness_check",
        },
        "passed": passed,
        "approval_status": APPROVAL_STATUS,
        "path_check": path_check,
        "boundary_check": boundary_check,
        "delegated_steps": delegated_steps,
        "summary": {
            "total_checks": len(all_checks),
            "passed_checks": sum(1 for check in all_checks if check.get("passed") is True),
            "failed_checks": sum(1 for check in all_checks if check.get("passed") is not True),
        },
        "non_authority_statement": (
            "This checker adds no runtime authority. It verifies public files, runs "
            "allowlisted tests/checks, and writes a sandbox report only."
        ),
    }


def print_text_report(report: Dict) -> None:
    if report["passed"]:
        print("V1 RELEASE READINESS PASSED")
    else:
        print("V1 RELEASE READINESS FAILED")

    print(f"Target release: {report['release']['target_version']} - {report['release']['name']}")
    print(f"Required public paths: {report['path_check']['present_count']} present, {report['path_check']['missing_count']} missing")
    print(f"Checks passed: {report['summary']['passed_checks']}/{report['summary']['total_checks']}")
    print("Execution: blocked")
    print("Filesystem mutation: sandbox reports and delegated sandbox outputs only")
    print("Repository apply: blocked")
    print("Git operations: read-only or blocked")
    print("Git write operations: blocked")
    print("Private context access: blocked")
    print("Adapter execution: mock only through adapter gate")
    print("Real adapter execution: blocked")
    print("Network access: blocked")

    blockers: List[str] = []
    if not report["path_check"]["passed"]:
        blockers.append("missing required public paths")
    if not report["boundary_check"]["passed"]:
        blockers.append("missing required boundary phrases")
    for step in report["delegated_steps"]:
        if not step["passed"]:
            blockers.append(f"{step['name']} failed with return code {step['returncode']}")

    for blocker in blockers:
        print(f"Blocker: {blocker}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Konoha v1.0 release readiness.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--sandbox-root", default="./sandbox", help="Sandbox root used for reports and delegated dry-run outputs.")
    parser.add_argument("--run-id", default="v1-release-readiness", help="Safe run identifier.")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow dirty Git status during pre-commit local checks.")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip integrated and dogfood smoke tests.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing readiness report.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    try:
        report = build_report(args)
        sandbox_root = Path(args.sandbox_root).resolve()
        report_path = resolve_under(sandbox_root, f"reports/{args.run_id}_v1_release_readiness_report.json")

        if report_path.exists() and not args.force:
            return fail(f"report already exists: {report_path}")

        write_json_lf(report_path, report)

        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_text_report(report)
            print(f"Report: {report_path}")

        return 0 if report["passed"] else 1

    except Exception as exc:
        return fail(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
