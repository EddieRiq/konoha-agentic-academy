#!/usr/bin/env python3
"""Unified CLI entrypoint for Konoha Agentic Academy.

This CLI is an orchestration entrypoint over existing Konoha tools.

Safety boundary:
- It only dispatches to allowlisted internal Python tools.
- It does not run arbitrary shell commands.
- It does not use shell=True.
- It does not execute missions by itself.
- It does not authorize Git writes, adapter calls, private context access, or repo mutation.

Individual subcommands keep their own approval gates and safety checks.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Sequence


VERSION = "0.21.0"


TOOL_SCRIPTS = {
    "runtime_runner": Path("tools/runtime_runner/run_dry_run_runtime.py"),
    "runtime_registry": Path("tools/runtime_registry/list_runtime_runs.py"),
    "runtime_validator": Path("tools/runtime_validator/validate_runtime_package.py"),
    "runtime_inspector": Path("tools/runtime_inspector/inspect_runtime_package.py"),
    "sandbox_prepare": Path("tools/sandbox_boundary/prepare_sandbox_run.py"),
    "artifact_writer": Path("tools/artifact_writer/write_sandbox_artifact.py"),
    "apply_plan": Path("tools/apply_plan/apply_sandbox_plan.py"),
    "git_readiness": Path("tools/git_readiness/inspect_git_readiness.py"),
    "git_staging": Path("tools/git_staging/stage_allowlisted_files.py"),
    "repo_inspector": Path("tools/repo_inspector/inspect_public_repo.py"),
}


def normalize_repo_root(repo_root: str | Path) -> Path:
    """Return a resolved repository root path."""
    return Path(repo_root).expanduser().resolve()


def resolve_tool_script(repo_root: Path, command_key: str) -> Path:
    """Resolve an allowlisted internal tool script inside the repository."""
    if command_key not in TOOL_SCRIPTS:
        raise ValueError(f"Unknown command key: {command_key}")

    script_path = (repo_root / TOOL_SCRIPTS[command_key]).resolve()

    try:
        script_path.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"Resolved script escapes repository root: {script_path}") from exc

    if "tools" not in script_path.parts:
        raise ValueError(f"Resolved script is not under tools/: {script_path}")

    return script_path


def run_internal_tool(repo_root: Path, command_key: str, tool_args: Sequence[str]) -> int:
    """Run an allowlisted internal Python tool without shell execution."""
    script_path = resolve_tool_script(repo_root, command_key)

    if not script_path.exists():
        print(f"KONOHA CLI FAILED: missing tool script: {script_path}", file=sys.stderr)
        return 2

    command = [sys.executable, str(script_path), *tool_args]
    completed = subprocess.run(command, cwd=str(repo_root), check=False)
    return int(completed.returncode)


def append_flag(args: List[str], flag: str, enabled: bool) -> None:
    if enabled:
        args.append(flag)


def append_option(args: List[str], option: str, value: str | None) -> None:
    if value is not None:
        args.extend([option, value])


def build_tool_args(ns: argparse.Namespace) -> List[str]:
    """Translate unified CLI arguments to the selected internal tool arguments."""
    key = getattr(ns, "command_key", None)

    if key == "runtime_runner":
        tool_args: List[str] = [
            "--title", ns.title,
            "--scope", ns.scope,
            "--run-id", ns.run_id,
            "--sandbox-root", ns.sandbox_root,
        ]
        append_flag(tool_args, "--force", ns.force)
        append_flag(tool_args, "--json", ns.json)
        return tool_args

    if key == "runtime_registry":
        tool_args = ["--sandbox-root", ns.sandbox_root]
        append_flag(tool_args, "--passed-only", ns.passed_only)
        append_flag(tool_args, "--json", ns.json)
        return tool_args

    if key == "runtime_validator":
        return [ns.package_path]

    if key == "runtime_inspector":
        tool_args = [ns.package_path]
        append_flag(tool_args, "--json", ns.json)
        return tool_args

    if key == "sandbox_prepare":
        tool_args = [
            "--sandbox-root", ns.sandbox_root,
            "--run-id", ns.run_id,
            "--mission-title", ns.mission_title,
        ]
        append_flag(tool_args, "--force", ns.force)
        return tool_args

    if key == "artifact_writer":
        tool_args = [
            "--sandbox-root", ns.sandbox_root,
            "--run-id", ns.run_id,
            "--artifact-path", ns.artifact_path,
            "--content", ns.content,
            "--artifact-kind", ns.artifact_kind,
        ]
        append_option(tool_args, "--intended-repo-path", ns.intended_repo_path)
        append_flag(tool_args, "--force", ns.force)
        return tool_args

    if key == "apply_plan":
        tool_args = [
            "--sandbox-root", ns.sandbox_root,
            "--run-id", ns.run_id,
            "--repo-root", ns.target_repo_root,
        ]
        append_flag(tool_args, "--confirm-apply", ns.confirm_apply)
        append_option(tool_args, "--approval-token", ns.approval_token)
        return tool_args

    if key == "git_readiness":
        tool_args = ["--repo-root", ns.target_repo_root]
        append_flag(tool_args, "--allow-dirty", ns.allow_dirty)
        append_flag(tool_args, "--json", ns.json)
        return tool_args

    if key == "git_staging":
        tool_args = ["--repo-root", ns.target_repo_root]
        for path in ns.path:
            tool_args.extend(["--path", path])
        append_flag(tool_args, "--confirm-stage", ns.confirm_stage)
        append_option(tool_args, "--approval-token", ns.approval_token)
        append_flag(tool_args, "--json", ns.json)
        return tool_args

    if key == "repo_inspector":
        tool_args = ["--repo-root", ns.target_repo_root]
        append_flag(tool_args, "--json", ns.json)
        return tool_args

    raise ValueError("No internal command selected.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="konoha",
        description="Unified CLI entrypoint for Konoha safe local-first tooling.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing Konoha tools. Default: current directory.",
    )
    parser.add_argument("--version", action="version", version=f"konoha {VERSION}")

    subparsers = parser.add_subparsers(dest="area", required=True)

    runtime = subparsers.add_parser("runtime", help="Dry-run runtime orchestration commands.")
    runtime_sub = runtime.add_subparsers(dest="runtime_command", required=True)

    runtime_dry = runtime_sub.add_parser("dry-run", help="Run the dry-run runtime runner.")
    runtime_dry.add_argument("--title", required=True)
    runtime_dry.add_argument("--scope", required=True)
    runtime_dry.add_argument("--run-id", required=True)
    runtime_dry.add_argument("--sandbox-root", default="sandbox")
    runtime_dry.add_argument("--force", action="store_true")
    runtime_dry.add_argument("--json", action="store_true")
    runtime_dry.set_defaults(command_key="runtime_runner")

    runs = subparsers.add_parser("runs", help="Runtime run registry commands.")
    runs_sub = runs.add_subparsers(dest="runs_command", required=True)

    runs_list = runs_sub.add_parser("list", help="List sandbox runtime runs.")
    runs_list.add_argument("--sandbox-root", default="sandbox")
    runs_list.add_argument("--passed-only", action="store_true")
    runs_list.add_argument("--json", action="store_true")
    runs_list.set_defaults(command_key="runtime_registry")

    package = subparsers.add_parser("package", help="Dry-run package commands.")
    package_sub = package.add_subparsers(dest="package_command", required=True)

    package_validate = package_sub.add_parser("validate", help="Validate a runtime package.")
    package_validate.add_argument("package_path")
    package_validate.set_defaults(command_key="runtime_validator")

    package_inspect = package_sub.add_parser("inspect", help="Inspect a runtime package.")
    package_inspect.add_argument("package_path")
    package_inspect.add_argument("--json", action="store_true")
    package_inspect.set_defaults(command_key="runtime_inspector")

    sandbox = subparsers.add_parser("sandbox", help="Sandbox boundary commands.")
    sandbox_sub = sandbox.add_subparsers(dest="sandbox_command", required=True)

    sandbox_prepare = sandbox_sub.add_parser("prepare", help="Prepare a sandbox run.")
    sandbox_prepare.add_argument("--sandbox-root", default="sandbox")
    sandbox_prepare.add_argument("--run-id", required=True)
    sandbox_prepare.add_argument("--mission-title", required=True)
    sandbox_prepare.add_argument("--force", action="store_true")
    sandbox_prepare.set_defaults(command_key="sandbox_prepare")

    artifact = subparsers.add_parser("artifact", help="Sandbox artifact proposal commands.")
    artifact_sub = artifact.add_subparsers(dest="artifact_command", required=True)

    artifact_write = artifact_sub.add_parser("write", help="Write a proposed artifact inside sandbox.")
    artifact_write.add_argument("--sandbox-root", default="sandbox")
    artifact_write.add_argument("--run-id", required=True)
    artifact_write.add_argument("--artifact-path", required=True)
    artifact_write.add_argument("--content", required=True)
    artifact_write.add_argument("--artifact-kind", required=True)
    artifact_write.add_argument("--intended-repo-path")
    artifact_write.add_argument("--force", action="store_true")
    artifact_write.set_defaults(command_key="artifact_writer")

    apply = subparsers.add_parser("apply", help="Human-approved apply plan commands.")
    apply_sub = apply.add_subparsers(dest="apply_command", required=True)

    apply_preview = apply_sub.add_parser("preview", help="Preview a sandbox apply plan.")
    apply_preview.add_argument("--sandbox-root", default="sandbox")
    apply_preview.add_argument("--run-id", required=True)
    apply_preview.add_argument("--target-repo-root", default=".")
    apply_preview.set_defaults(command_key="apply_plan", confirm_apply=False, approval_token=None)

    apply_confirm = apply_sub.add_parser("confirm", help="Apply a sandbox plan with explicit approval.")
    apply_confirm.add_argument("--sandbox-root", default="sandbox")
    apply_confirm.add_argument("--run-id", required=True)
    apply_confirm.add_argument("--target-repo-root", default=".")
    apply_confirm.add_argument("--approval-token", required=True)
    apply_confirm.set_defaults(command_key="apply_plan", confirm_apply=True)

    git = subparsers.add_parser("git", help="Git gate commands.")
    git_sub = git.add_subparsers(dest="git_command", required=True)

    git_readiness = git_sub.add_parser("readiness", help="Inspect Git readiness.")
    git_readiness.add_argument("--target-repo-root", default=".")
    git_readiness.add_argument("--allow-dirty", action="store_true")
    git_readiness.add_argument("--json", action="store_true")
    git_readiness.set_defaults(command_key="git_readiness")

    git_stage = git_sub.add_parser("stage", help="Preview or stage explicit allowlisted files.")
    git_stage.add_argument("--target-repo-root", default=".")
    git_stage.add_argument("--path", action="append", required=True)
    git_stage.add_argument("--confirm-stage", action="store_true")
    git_stage.add_argument("--approval-token")
    git_stage.add_argument("--json", action="store_true")
    git_stage.set_defaults(command_key="git_staging")

    repo = subparsers.add_parser("repo", help="Repository inspection commands.")
    repo_sub = repo.add_subparsers(dest="repo_command", required=True)

    repo_inspect = repo_sub.add_parser("inspect", help="Inspect public repository coherence.")
    repo_inspect.add_argument("--target-repo-root", default=".")
    repo_inspect.add_argument("--json", action="store_true")
    repo_inspect.set_defaults(command_key="repo_inspector")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)

    repo_root = normalize_repo_root(ns.repo_root)
    try:
        tool_args = build_tool_args(ns)
        return run_internal_tool(repo_root, ns.command_key, tool_args)
    except ValueError as exc:
        print(f"KONOHA CLI FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
