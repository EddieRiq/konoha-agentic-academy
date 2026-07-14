#!/usr/bin/env python3
"""Canonical terminal entrypoint for Konoha Agentic Academy.

The CLI delegates only to the canonical command registry. It does not add
approval tokens, enable network, infer consent, or bypass delegated gates.
"""

from __future__ import annotations

import difflib
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

MAINTAINER_PREFIXES = {"package", "release"}
START_COMMANDS = {
    ("welcome",),
    ("quickstart",),
    ("next",),
    ("doctor",),
    ("status",),
    ("shell",),
    ("mission", "start"),
    ("mission", "review"),
    ("mission", "teachback"),
    ("mission", "close"),
}

# Compatibility view for historical callers/tests.
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
    registry = ALL_COMMANDS if include_deprecated else COMMAND_REGISTRY
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
            errors.append(f"{command_label(key)} has no script")
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

        if "--allow-network" in (fixed_args or []):
            errors.append(
                f"{command_label(key)} injects --allow-network"
            )
        if "--approval-token" in (fixed_args or []):
            errors.append(
                f"{command_label(key)} injects approval token"
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


def is_maintainer_command(key: CommandKey) -> bool:
    return bool(key) and key[0] in MAINTAINER_PREFIXES


def format_command_lines(
    registry,
    *,
    include_maintainer: bool,
) -> List[str]:
    lines: List[str] = []
    for key, entry in sorted(registry.items()):
        if not include_maintainer and is_maintainer_command(key):
            continue
        lines.append(
            f"  konoha {command_label(key):27} "
            f"{entry['description']}"
        )
    return lines


def print_help(*, show_all: bool = False) -> None:
    user_lines = format_command_lines(
        COMMAND_REGISTRY,
        include_maintainer=show_all,
    )

    sections = [
        f"Konoha Agentic Academy {VERSION}",
        "",
        "Local-first supervised missions from one terminal command.",
        "",
        "Start here:",
        "  konoha quickstart --confirm-quickstart \\",
        "    --approval-token START_KONOHA_QUICKSTART",
        "  konoha next",
        "  konoha mission start --help",
        "  konoha shell",
        "",
        "Core commands:",
        *user_lines,
        "",
        "Help:",
        "  konoha help",
        "  konoha help mission",
        "  konoha help maintainer",
        "  konoha help --all",
        "  konoha <command> --help",
    ]

    if show_all:
        sections.extend(
            [
                "",
                "Deprecated compatibility commands:",
                *[
                    "  konoha "
                    + f"{command_label(key):27} "
                    + "deprecated"
                    + (
                        f" → {entry['replacement']}"
                        if entry.get("replacement")
                        else ""
                    )
                    for key, entry in sorted(LEGACY_COMMANDS.items())
                ],
            ]
        )

    sections.extend(
        [
            "",
            "Safety:",
            "  Commands never receive approval tokens automatically.",
            "  Network access remains blocked unless explicitly enabled.",
            "  Status, model output, memory and suggestions are evidence only.",
        ]
    )
    print("\n".join(sections))


def print_mission_help() -> None:
    print(
        """Konoha supervised mission flow

  1. konoha mission start --help
  2. konoha mission plan --help
  3. execute only through an explicitly approved gate
  4. konoha mission review --help
  5. konoha mission teachback-prepare --help
  6. konoha mission teachback --help
  7. konoha mission close --help

Use `konoha next` to inspect the local workspace and receive one
evidence-based next command. The recommendation is not permission.
"""
    )


def print_maintainer_help() -> None:
    lines = format_command_lines(
        {
            key: value
            for key, value in COMMAND_REGISTRY.items()
            if is_maintainer_command(key)
        },
        include_maintainer=True,
    )
    print(
        "\n".join(
            [
                "Konoha maintainer commands",
                "",
                *lines,
                "",
                "These commands retain explicit package, Git, network,",
                "tag and release approval gates.",
            ]
        )
    )


def print_help_topic(args: Sequence[str]) -> int:
    if not args:
        print_help()
        return 0
    topic = args[0]
    if topic == "--all":
        print_help(show_all=True)
        return 0
    if topic == "mission":
        print_mission_help()
        return 0
    if topic == "maintainer":
        print_maintainer_help()
        return 0

    key, delegated = resolve_command(args)
    if key is None:
        print_unknown(args)
        return 2
    return dispatch_key(key, [*delegated, "--help"])


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


def command_suggestions(args: Sequence[str]) -> List[str]:
    attempted = " ".join(args[:2]).strip()
    labels = [command_label(key) for key in ALL_COMMANDS]
    return difflib.get_close_matches(
        attempted,
        labels,
        n=3,
        cutoff=0.45,
    )


def print_unknown(args: Sequence[str]) -> None:
    attempted = " ".join(args[:2]).strip() or "(empty)"
    print(
        f"Unknown Konoha command: {attempted}",
        file=sys.stderr,
    )
    suggestions = command_suggestions(args)
    if suggestions:
        print("Closest commands:", file=sys.stderr)
        for suggestion in suggestions:
            print(f"  konoha {suggestion}", file=sys.stderr)
    print(
        "Run `konoha help` for the product workflow.",
        file=sys.stderr,
    )


def dispatch_key(
    key: CommandKey,
    args: Sequence[str],
) -> int:
    entry = ALL_COMMANDS.get(key)
    if entry is None:
        print_unknown(list(key))
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
        print_unknown([group, command])
        return 2
    return dispatch_key(key, args)


def main(argv: Iterable[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if not args:
        return dispatch_key(("shell",), [])

    if args[0] in {"-h", "--help"}:
        print_help()
        return 0

    if args[0] == "help":
        return print_help_topic(args[1:])

    if args[0] == "mission" and (len(args) == 1 or args[1] in {"-h", "--help"}):
        print_mission_help()
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
        print_unknown(args)
        return 2

    return dispatch_key(key, delegated)


if __name__ == "__main__":
    raise SystemExit(main())
