#!/usr/bin/env python3
"""Unified CLI entrypoint for Konoha Agentic Academy.

The CLI delegates to allowlisted internal tools. It does not execute arbitrary
scripts and does not add authority beyond the delegated tool boundaries.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable


VERSION = "0.23.0"


TOOL_SCRIPTS = {
    ("mission", "dry-run"): "tools/mission_workflow/run_dry_run_mission.py",
    ("runtime", "dry-run"): "tools/runtime_runner/run_dry_run_runtime.py",
    ("package", "validate"): "tools/runtime_validator/validate_runtime_package.py",
    ("package", "inspect"): "tools/runtime_inspector/inspect_runtime_package.py",
    ("runs", "list"): "tools/runtime_registry/list_runtime_runs.py",
    ("repo", "inspect"): "tools/repo_inspector/inspect_public_repo.py",
    ("git", "readiness"): "tools/git_readiness/inspect_git_readiness.py",
    ("git", "stage"): "tools/git_staging/stage_allowlisted_files.py",
    ("sandbox", "prepare"): "tools/sandbox_boundary/prepare_sandbox_run.py",
    ("artifact", "write"): "tools/artifact_writer/write_sandbox_artifact.py",
    ("apply", "preview"): "tools/apply_plan/apply_sandbox_plan.py",
    ("apply", "confirm"): "tools/apply_plan/apply_sandbox_plan.py",
    ("config", "validate"): "tools/config_validator/validate_konoha_config.py",
}


ALIASES = {
    "--target-repo-root": "--repo-root",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def print_help() -> None:
    commands = "\n".join(
        f"  {group} {command}" for group, command in sorted(TOOL_SCRIPTS)
    )
    print(
        f"""Konoha Agentic Academy CLI {VERSION}

Usage:
  python tools/konoha_cli.py <group> <command> [arguments]
  python tools/konoha_cli.py --version

Commands:
{commands}

Examples:
  python tools/konoha_cli.py mission dry-run --title "Docs update" --scope "Prepare dry-run package" --run-id "demo" --sandbox-root ".\\sandbox" --force
  python tools/konoha_cli.py package validate .\\sandbox\\runs\\demo\\runtime_package.json
  python tools/konoha_cli.py runs list --sandbox-root ".\\sandbox"

Safety:
  The CLI dispatches only to allowlisted internal tools.
  It does not bypass approval tokens, path allowlists, or delegated safety gates.
"""
    )


def normalize_args(args: list[str]) -> list[str]:
    normalized: list[str] = []
    for arg in args:
        normalized.append(ALIASES.get(arg, arg))
    return normalized


def dispatch(group: str, command: str, args: list[str]) -> int:
    key = (group, command)
    if key not in TOOL_SCRIPTS:
        print(f"Unknown Konoha command: {group} {command}", file=sys.stderr)
        print("Run `python tools/konoha_cli.py --help` for available commands.", file=sys.stderr)
        return 2

    script = (repo_root() / TOOL_SCRIPTS[key]).resolve()
    if not script.exists():
        print(f"Delegated tool not found: {script}", file=sys.stderr)
        return 1

    delegated_args = normalize_args(args)

    if key == ("apply", "confirm") and "--confirm-apply" not in delegated_args:
        delegated_args = ["--confirm-apply", *delegated_args]

    completed = subprocess.run(  # noqa: S603 - dispatch is restricted to allowlisted internal tools.
        [sys.executable, str(script), *delegated_args],
        text=True,
        shell=False,
        check=False,
    )
    return completed.returncode


def main(argv: Iterable[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if not args or args[0] in {"-h", "--help", "help"}:
        print_help()
        return 0

    if args[0] == "--version":
        print(VERSION)
        return 0

    if len(args) < 2:
        print("Expected <group> <command>.", file=sys.stderr)
        print_help()
        return 2

    return dispatch(args[0], args[1], args[2:])


if __name__ == "__main__":
    raise SystemExit(main())
