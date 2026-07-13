#!/usr/bin/env python3
"""Canonical terminal entrypoint for Konoha Agentic Academy.

The CLI delegates only to the canonical command registry. It does not add
approval tokens, enable network, infer consent, or bypass delegated gates.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.command_registry import (  # noqa: E402
    ALL_COMMANDS,
    COMMAND_REGISTRY,
    LEGACY_COMMANDS,
    CommandKey,
    command_label,
)
from tools.version import VERSION  # noqa: E402

ALIASES = {
    "--target-repo-root": "--repo-root",
}

# Compatibility view for existing callers/tests. New code should use registry.
TOOL_SCRIPTS = {
    key: entry["script"]
    for key, entry in ALL_COMMANDS.items()
    if len(key) == 2
}


def repo_root() -> Path:
    return REPO_ROOT


def normalize_args(args: Sequence[str]) -> List[str]:
    return [ALIASES.get(arg, arg) for arg in args]


def validate_registry(
    root: Optional[Path] = None,
    *,
    include_deprecated: bool = False,
) -> List[str]:
    base = (root or repo_root()).resolve()
    registry = (
        ALL_COMMANDS
        if include_deprecated
        else COMMAND_REGISTRY
    )
    errors: List[str] = []

    for key, entry in registry.items():
        if not key or not all(
            isinstance(part, str) and part
            for part in key
        ):
            errors.append(f"invalid command key: {key!r}")
            continue

        script = entry.get("script")
        if not isinstance(script, str) or not script:
            errors.append(
                f"{command_label(key)} has no script"
            )
            continue

        candidate = (base / script).resolve()
        try:
            candidate.relative_to(base)
        except ValueError:
            errors.append(
                f"{command_label(key)} script escapes repo"
            )
            continue

        if not candidate.is_file():
            errors.append(
                f"{command_label(key)} missing script: {script}"
            )

        fixed_args = entry.get("fixed_args")
        if not isinstance(fixed_args, list) or not all(
            isinstance(item, str)
            for item in fixed_args
        ):
            errors.append(
                f"{command_label(key)} fixed_args invalid"
            )

        if entry.get("status") not in {
            "active",
            "deprecated",
        }:
            errors.append(
                f"{command_label(key)} status invalid"
            )

    return errors


def registry_payload() -> dict:
    def serialize(registry):
        return {
            command_label(key): dict(value)
            for key, value in sorted(registry.items())
        }

    return {
        "schema_version": "1.0.0",
        "report_type": "konoha_command_registry",
        "version": VERSION,
        "active": serialize(COMMAND_REGISTRY),
        "deprecated": serialize(LEGACY_COMMANDS),
        "authority": {
            "registry_is_not_permission": True,
            "cli_does_not_inject_approval_tokens": True,
            "cli_does_not_enable_network": True,
            "delegated_tool_retains_authority": True,
        },
    }


def print_help() -> None:
    active_lines = []
    for key, entry in sorted(COMMAND_REGISTRY.items()):
        active_lines.append(
            f"  {command_label(key):30} "
            f"{entry['description']}"
        )

    deprecated_lines = []
    for key, entry in sorted(LEGACY_COMMANDS.items()):
        replacement = entry.get("replacement")
        suffix = (
            f" → {replacement}"
            if replacement
            else ""
        )
        deprecated_lines.append(
            f"  {command_label(key):30} deprecated{suffix}"
        )

    print(
        f"""Konoha Agentic Academy CLI {VERSION}

Usage:
  python tools/konoha_cli.py <command> [arguments]
  python tools/konoha_cli.py <group> <command> [arguments]
  python tools/konoha_cli.py --version
  python tools/konoha_cli.py --registry-json

Active commands:
{chr(10).join(active_lines)}

Deprecated compatibility commands:
{chr(10).join(deprecated_lines)}

Examples:
  python tools/konoha_cli.py doctor --repo-root .
  python tools/konoha_cli.py status --repo-root .
  python tools/konoha_cli.py shell --repo-root .
  python tools/konoha_cli.py mission start --help
  python tools/konoha_cli.py mission teachback --help
  python tools/konoha_cli.py mission close --help
  python tools/konoha_cli.py package status --help
  python tools/konoha_cli.py release status --help
  python tools/konoha_cli.py release deliver --help
  python tools/konoha_cli.py install-status
  python tools/konoha_cli.py upgrade --help
  python tools/konoha_cli.py uninstall --help

Install:
  curl -fsSL https://raw.githubusercontent.com/EddieRiq/konoha-agentic-academy/v3.3.0/scripts/install.sh | \
    bash -s -- --version v3.3.0 --confirm-install \
    --approval-token INSTALL_KONOHA_CLI

Safety:
  The CLI dispatches only to registered internal tools.
  It never supplies approval tokens or --allow-network.
  Registry metadata is evidence only.
  Delegated tools retain every safety and approval gate.
"""
    )


def resolve_command(
    args: Sequence[str],
) -> Tuple[Optional[CommandKey], List[str]]:
    if not args:
        return None, []

    one = (args[0],)
    if one in ALL_COMMANDS:
        return one, list(args[1:])

    if len(args) >= 2:
        two = (args[0], args[1])
        if two in ALL_COMMANDS:
            return two, list(args[2:])

    return None, list(args)


def dispatch_key(
    key: CommandKey,
    args: Sequence[str],
) -> int:
    entry = ALL_COMMANDS.get(key)
    if entry is None:
        print(
            f"Unknown Konoha command: {command_label(key)}",
            file=sys.stderr,
        )
        return 2

    root = repo_root().resolve()
    script = (root / entry["script"]).resolve()
    try:
        script.relative_to(root)
    except ValueError:
        print(
            "Delegated tool escapes repository root.",
            file=sys.stderr,
        )
        return 1

    if not script.is_file():
        print(
            f"Delegated tool not found: {script}",
            file=sys.stderr,
        )
        return 1

    delegated_args = [
        *entry.get("fixed_args", []),
        *normalize_args(args),
    ]
    completed = subprocess.run(
        [sys.executable, str(script), *delegated_args],
        text=True,
        shell=False,
        check=False,
    )
    return int(completed.returncode)


def dispatch(
    group: str,
    command: str,
    args: Sequence[str],
) -> int:
    """Compatibility dispatch for historical two-part callers."""
    key = (group, command)
    if key not in ALL_COMMANDS:
        print(
            f"Unknown Konoha command: {group} {command}",
            file=sys.stderr,
        )
        print(
            "Run `python tools/konoha_cli.py --help` "
            "for available commands.",
            file=sys.stderr,
        )
        return 2
    return dispatch_key(key, args)


def main(argv: Iterable[str] | None = None) -> int:
    args = list(
        sys.argv[1:]
        if argv is None
        else argv
    )

    if not args or args[0] in {
        "-h",
        "--help",
        "help",
    }:
        print_help()
        return 0

    if args[0] == "--version":
        print(VERSION)
        return 0

    if args[0] == "--registry-json":
        print(
            json.dumps(
                registry_payload(),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args[0] == "--validate-registry":
        errors = validate_registry()
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("KONOHA COMMAND REGISTRY PASSED")
        return 0

    key, delegated = resolve_command(args)
    if key is None:
        print(
            f"Unknown Konoha command: {' '.join(args[:2])}",
            file=sys.stderr,
        )
        print(
            "Run `python tools/konoha_cli.py --help` "
            "for available commands.",
            file=sys.stderr,
        )
        return 2

    return dispatch_key(key, delegated)


if __name__ == "__main__":
    raise SystemExit(main())
