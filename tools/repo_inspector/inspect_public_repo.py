#!/usr/bin/env python3
"""Read-only public repository inspector for Konoha Agentic Academy.

This tool inspects public repository artifacts for structural coherence,
non-execution boundaries, risky code patterns, and public/private leakage
signals.

It is read-only:
- no shell execution;
- no Git operations;
- no network access;
- no file mutation;
- no adapter invocation;
- no private Village access.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PUBLIC_FILE_ALLOWLIST = {
    "README.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "AGENTS.md",
}

PUBLIC_DIR_ALLOWLIST = {
    "docs",
    "scrolls",
    "runtime",
    "tools",
    "tests",
    "schemas",
    "examples",
    "adapters",
    "evals",
    "protocols",
    "missions",
    "council",
    "memory",
    "clans",
    "ui",
    "core",
    "telemetry",
    "shikamaru",
    "sandbox",
    "shinobi",
    "kagebunshin",
    "marketplace",
    "hokage",
    "jounin",
}

# Local/private areas must never be traversed by this public inspector.
BLOCKED_PATH_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "private-library",
    "vault",
    "local-memory",
    "local_context",
    "local-context",
    "kirigakure",
}

PRIVATE_LEAKAGE_PATTERNS = [
    "private-library",
    "kirigakure",
    "credential",
    "password=",
    "secret=",
    "token=",
    "api_key",
    "connection string",
    "dsn=",
]

DANGEROUS_PYTHON_PATTERNS = {
    "subprocess import/call": re.compile(r"\bsubprocess\b"),
    "os.system call": re.compile(r"\bos\.system\s*\("),
    "Popen call": re.compile(r"\bPopen\s*\("),
    "network requests": re.compile(r"\brequests\b"),
    "socket usage": re.compile(r"\bsocket\b"),
    "recursive delete": re.compile(r"\bshutil\.rmtree\s*\("),
    "unlink call": re.compile(r"\.unlink\s*\("),
    "remove call": re.compile(r"\.remove\s*\("),
}

EXECUTABLE_EXAMPLE_EXTENSIONS = {
    ".py",
    ".sh",
    ".ps1",
    ".js",
    ".ts",
    ".go",
    ".rs",
    ".bat",
    ".cmd",
}


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "level": self.level,
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


def is_blocked_path(path: Path) -> bool:
    lower_parts = {part.lower() for part in path.parts}
    return bool(lower_parts & BLOCKED_PATH_PARTS)


def relative_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def iter_public_files(repo_root: Path) -> Iterable[Path]:
    """Yield public files from allowlisted roots only, skipping private paths."""
    for file_name in sorted(PUBLIC_FILE_ALLOWLIST):
        candidate = repo_root / file_name
        if candidate.is_file() and not is_blocked_path(candidate):
            yield candidate

    for dir_name in sorted(PUBLIC_DIR_ALLOWLIST):
        root = repo_root / dir_name
        if not root.exists() or not root.is_dir() or is_blocked_path(root):
            continue

        # The sandbox root is public only for tracked placeholders/docs. Runtime
        # run contents are local outputs, so skip sandbox/runs and sandbox/tmp.
        if dir_name == "sandbox":
            allowed = [root / "README.md", root / ".gitkeep"]
            for candidate in allowed:
                if candidate.is_file() and not is_blocked_path(candidate):
                    yield candidate
            continue

        for path in sorted(root.rglob("*")):
            if path.is_file() and not is_blocked_path(path):
                yield path


def read_text_safely(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def check_required_files(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    required = [
        "README.md",
        "CHANGELOG.md",
        "docs/guides/README.md",
        "scrolls/README.md",
        "tools/runtime_runner/run_dry_run_runtime.py",
        "tools/runtime_validator/validate_runtime_package.py",
        "tools/runtime_builder/create_dry_run_package.py",
        "tools/runtime_inspector/inspect_runtime_package.py",
        "tools/runtime_registry/list_runtime_runs.py",
        "tools/sandbox_boundary/prepare_sandbox_run.py",
    ]
    for rel in required:
        if not (repo_root / rel).is_file():
            findings.append(
                Finding(
                    "error",
                    "missing_required_file",
                    rel,
                    "Required public artifact is missing.",
                )
            )
    return findings


def check_private_leakage(repo_root: Path, files: Iterable[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        if path.suffix.lower() not in {".md", ".py", ".json", ".txt", ".yml", ".yaml"}:
            continue
        rel = relative_posix(path, repo_root)
        text = read_text_safely(path).lower()
        for pattern in PRIVATE_LEAKAGE_PATTERNS:
            if pattern in text:
                findings.append(
                    Finding(
                        "warning",
                        "private_leakage_signal",
                        rel,
                        f"Public file contains private-boundary signal: {pattern}",
                    )
                )
    return findings


def check_python_safety(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    tools_root = repo_root / "tools"
    if not tools_root.is_dir():
        return findings

    for path in sorted(tools_root.rglob("*.py")):
        if is_blocked_path(path):
            continue
        rel = relative_posix(path, repo_root)
        text = read_text_safely(path)
        for label, pattern in DANGEROUS_PYTHON_PATTERNS.items():
            if pattern.search(text):
                findings.append(
                    Finding(
                        "warning",
                        "dangerous_python_pattern",
                        rel,
                        f"Review possible unsafe pattern: {label}",
                    )
                )
    return findings


def check_example_boundaries(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    examples_root = repo_root / "examples"
    if not examples_root.is_dir():
        return findings

    for path in sorted(examples_root.rglob("*")):
        if not path.is_file() or is_blocked_path(path):
            continue
        rel = relative_posix(path, repo_root)
        if path.suffix.lower() in EXECUTABLE_EXAMPLE_EXTENSIONS:
            findings.append(
                Finding(
                    "error",
                    "executable_example",
                    rel,
                    "Examples must remain documentation/data fixtures, not executable files.",
                )
            )

    return findings


def check_boundary_language(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    root_readme = repo_root / "README.md"
    if not root_readme.is_file():
        return findings

    text = read_text_safely(root_readme).lower()
    required_phrases = [
        "does not execute",
        "git operations",
        "private context",
    ]

    for phrase in required_phrases:
        if phrase not in text:
            findings.append(
                Finding(
                    "warning",
                    "missing_boundary_language",
                    "README.md",
                    f"README may be missing safety boundary phrase: {phrase}",
                )
            )
    return findings


def inspect_repo(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    public_files = list(iter_public_files(repo_root))

    findings: list[Finding] = []
    findings.extend(check_required_files(repo_root))
    findings.extend(check_private_leakage(repo_root, public_files))
    findings.extend(check_python_safety(repo_root))
    findings.extend(check_example_boundaries(repo_root))
    findings.extend(check_boundary_language(repo_root))

    errors = [finding for finding in findings if finding.level == "error"]
    warnings = [finding for finding in findings if finding.level == "warning"]

    return {
        "schema_version": "0.16.0",
        "tool": "read_only_repo_inspector",
        "repo_root": str(repo_root),
        "mode": "read_only",
        "status": "failed" if errors else "passed",
        "public_files_scanned": len(public_files),
        "summary": {
            "errors": len(errors),
            "warnings": len(warnings),
            "findings": len(findings),
        },
        "boundaries": {
            "execution": "blocked",
            "filesystem_mutation": "blocked",
            "git_operations": "blocked",
            "adapter_execution": "blocked",
            "private_context_access": "blocked",
            "network_access": "blocked",
        },
        "findings": [finding.as_dict() for finding in findings],
    }


def print_text_report(report: dict) -> None:
    if report["status"] == "passed":
        print("REPO INSPECTION PASSED")
    else:
        print("REPO INSPECTION FAILED")

    print(f"Public files scanned: {report['public_files_scanned']}")
    print(f"Errors: {report['summary']['errors']}")
    print(f"Warnings: {report['summary']['warnings']}")
    print("Execution: blocked")
    print("Filesystem mutation: blocked")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Adapter execution: blocked")
    print("Network access: blocked")

    for finding in report["findings"]:
        print(
            f"[{finding['level'].upper()}] "
            f"{finding['code']} :: {finding['path']} :: {finding['message']}"
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect public Konoha repo artifacts without mutation."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to inspect. Defaults to current directory.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the inspection report as JSON.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero on warnings as well as errors.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = Path(args.repo_root)

    if not repo_root.exists() or not repo_root.is_dir():
        report = {
            "schema_version": "0.16.0",
            "tool": "read_only_repo_inspector",
            "repo_root": str(repo_root),
            "mode": "read_only",
            "status": "failed",
            "summary": {"errors": 1, "warnings": 0, "findings": 1},
            "boundaries": {
                "execution": "blocked",
                "filesystem_mutation": "blocked",
                "git_operations": "blocked",
                "adapter_execution": "blocked",
                "private_context_access": "blocked",
                "network_access": "blocked",
            },
            "findings": [
                {
                    "level": "error",
                    "code": "repo_root_missing",
                    "path": str(repo_root),
                    "message": "Repository root does not exist or is not a directory.",
                }
            ],
        }
    else:
        report = inspect_repo(repo_root)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    if report["summary"]["errors"] > 0:
        return 1
    if args.strict and report["summary"]["warnings"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
