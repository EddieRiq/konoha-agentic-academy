#!/usr/bin/env python3
"""Canonical release test gate for Konoha Agentic Academy.

Discovers immediate suite directories below tests/, runs each suite independently,
continues after failures, and returns non-zero if any selected suite fails.

No models, network, Git operations, private context, or repository mutation.
Optional JSON reports are restricted to sandbox/.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

SCHEMA_VERSION = "1.0.0"
REPORT_TYPE = "canonical_release_test_gate_report"
DEFAULT_PATTERN = "test_*.py"
DEFAULT_TIMEOUT_SECONDS = 180

BOUNDARIES = {
    "arbitrary_shell": "blocked",
    "git_operations": "blocked",
    "model_invocation": "blocked",
    "network_access": "blocked",
    "private_context_access": "blocked",
    "repository_mutation": "blocked",
    "report_writes": "optional_sandbox_only",
}

RAN_RE = re.compile(r"Ran\s+(\d+)\s+tests?", re.IGNORECASE)
FAILED_DETAIL_RE = re.compile(r"FAILED\s*\(([^)]*)\)")
OK_DETAIL_RE = re.compile(r"OK\s*\(([^)]*)\)")
COUNT_RE = re.compile(r"([A-Za-z_]+)=(\d+)")


class ReleaseTestGateError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_under(root: Path, candidate: Path) -> Path:
    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve()
    if candidate_resolved != root_resolved and root_resolved not in candidate_resolved.parents:
        raise ReleaseTestGateError(f"path escapes root: {candidate}")
    return candidate_resolved


def truncate_text(value: str, limit: int = 12000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "\n...[truncated]..."


def discover_suite_directories(tests_root: Path, pattern: str = DEFAULT_PATTERN) -> list[Path]:
    if not tests_root.exists():
        raise ReleaseTestGateError(f"tests root does not exist: {tests_root}")
    if not tests_root.is_dir():
        raise ReleaseTestGateError(f"tests root is not a directory: {tests_root}")

    suites = []
    for child in sorted(tests_root.iterdir(), key=lambda path: path.name):
        if not child.is_dir():
            continue
        if child.name == "__pycache__" or child.name.startswith("."):
            continue
        if any(path.is_file() for path in child.rglob(pattern)):
            suites.append(child)
    return suites


def parse_unittest_counts(output: str) -> dict[str, int]:
    counts = {
        "tests": 0,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "expected_failures": 0,
        "unexpected_successes": 0,
    }
    ran_match = RAN_RE.search(output)
    if ran_match:
        counts["tests"] = int(ran_match.group(1))

    detail_match = FAILED_DETAIL_RE.search(output) or OK_DETAIL_RE.search(output)
    if detail_match:
        for key, value in COUNT_RE.findall(detail_match.group(1)):
            key = key.lower()
            if key in counts:
                counts[key] = int(value)
    return counts


def run_suite(repo_root: Path, suite_path: Path, pattern: str, timeout_seconds: int) -> dict[str, Any]:
    suite_relative = suite_path.relative_to(repo_root).as_posix()
    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        suite_relative,
        "-p",
        pattern,
    ]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            text=True,
            capture_output=True,
            shell=False,
            check=False,
            timeout=timeout_seconds,
        )
        duration = time.monotonic() - started
        combined = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
        counts = parse_unittest_counts(combined)
        return {
            "suite": suite_path.name,
            "path": suite_relative,
            "command": command,
            "status": "passed" if completed.returncode == 0 else "failed",
            "passed": completed.returncode == 0,
            "returncode": completed.returncode,
            "timed_out": False,
            "duration_seconds": round(duration, 3),
            **counts,
            "stdout": truncate_text(completed.stdout),
            "stderr": truncate_text(completed.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        combined = "\n".join(part for part in (stdout, stderr) if part)
        counts = parse_unittest_counts(combined)
        return {
            "suite": suite_path.name,
            "path": suite_relative,
            "command": command,
            "status": "timeout",
            "passed": False,
            "returncode": None,
            "timed_out": True,
            "duration_seconds": round(duration, 3),
            **counts,
            "stdout": truncate_text(stdout),
            "stderr": truncate_text(stderr),
        }


def select_suites(discovered: list[Path], requested_names: Sequence[str]) -> list[Path]:
    if not requested_names:
        return discovered
    requested = list(dict.fromkeys(requested_names))
    by_name = {path.name: path for path in discovered}
    missing = [name for name in requested if name not in by_name]
    if missing:
        raise ReleaseTestGateError(
            "requested suite directories were not discovered: " + ", ".join(sorted(missing))
        )
    return [by_name[name] for name in requested]


def build_report(
    repo_root: Path,
    tests_root: Path,
    pattern: str = DEFAULT_PATTERN,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    requested_suites: Sequence[str] = (),
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    tests_root = resolve_under(repo_root, tests_root)
    discovered = discover_suite_directories(tests_root, pattern)
    selected = select_suites(discovered, requested_suites)
    if not selected:
        raise ReleaseTestGateError("no test suite directories were discovered")

    started = time.monotonic()
    results = [
        run_suite(repo_root, suite, pattern, timeout_seconds)
        for suite in selected
    ]
    duration = time.monotonic() - started
    passed_suites = sum(1 for result in results if result["passed"])
    failed_suites = len(results) - passed_suites

    summary = {
        "discovered_suite_count": len(discovered),
        "selected_suite_count": len(selected),
        "passed_suite_count": passed_suites,
        "failed_suite_count": failed_suites,
        "test_count": sum(result["tests"] for result in results),
        "failure_count": sum(result["failures"] for result in results),
        "error_count": sum(result["errors"] for result in results),
        "skipped_count": sum(result["skipped"] for result in results),
        "timeout_count": sum(1 for result in results if result["timed_out"]),
        "duration_seconds": round(duration, 3),
    }
    passed = failed_suites == 0
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "generated_at": utc_now(),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "repo_root": str(repo_root),
        "tests_root": str(tests_root),
        "pattern": pattern,
        "python_executable": sys.executable,
        "timeout_seconds_per_suite": timeout_seconds,
        "requested_suites": list(requested_suites),
        "boundaries": BOUNDARIES,
        "summary": summary,
        "suites": results,
        "authority": {
            "test_report_is_evidence_only": True,
            "test_success_is_not_permission": True,
            "git_operations_require_separate_approval": True,
        },
    }


def validate_output_path(repo_root: Path, output: Path) -> Path:
    repo_root = repo_root.resolve()
    sandbox_root = (repo_root / "sandbox").resolve()
    resolved = output.resolve() if output.is_absolute() else (repo_root / output).resolve()
    return resolve_under(sandbox_root, resolved)


def write_json_report(path: Path, report: dict[str, Any], force: bool) -> None:
    if path.exists() and not force:
        raise ReleaseTestGateError(f"report already exists: {path}; use --force")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def print_text_report(report: dict[str, Any], verbose: bool) -> None:
    print("KONOHA CANONICAL RELEASE TEST GATE")
    print(f"status: {report['status']}")
    print(f"discovered suites: {report['summary']['discovered_suite_count']}")
    print(f"selected suites: {report['summary']['selected_suite_count']}")
    print()
    for index, result in enumerate(report["suites"], start=1):
        marker = "PASS" if result["passed"] else "FAIL"
        print(
            f"[{index:02d}/{report['summary']['selected_suite_count']:02d}] "
            f"{marker} {result['suite']} tests={result['tests']} "
            f"failures={result['failures']} errors={result['errors']} "
            f"duration={result['duration_seconds']:.3f}s"
        )
        if verbose or not result["passed"]:
            if result["stdout"].strip():
                print("--- stdout ---")
                print(result["stdout"].rstrip())
            if result["stderr"].strip():
                print("--- stderr ---")
                print(result["stderr"].rstrip())
    summary = report["summary"]
    print()
    print("SUMMARY")
    print(f"suites: {summary['selected_suite_count']}")
    print(f"passed suites: {summary['passed_suite_count']}")
    print(f"failed suites: {summary['failed_suite_count']}")
    print(f"tests: {summary['test_count']}")
    print(f"failures: {summary['failure_count']}")
    print(f"errors: {summary['error_count']}")
    print(f"skipped: {summary['skipped_count']}")
    print(f"timeouts: {summary['timeout_count']}")
    print(f"duration: {summary['duration_seconds']:.3f}s")
    print("Git operations: blocked")
    print("Network access: blocked")
    print("Model invocation: blocked")
    print("Private context access: blocked")
    print("Result is evidence only.")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run each immediate tests/* suite independently."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--tests-root", default="tests")
    parser.add_argument("--pattern", default=DEFAULT_PATTERN)
    parser.add_argument("--suite", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", help="Optional JSON report path below sandbox/.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    try:
        if args.timeout <= 0:
            raise ReleaseTestGateError("--timeout must be greater than zero")
        repo_root = Path(args.repo_root).resolve()
        if not repo_root.exists():
            raise ReleaseTestGateError(f"repository root does not exist: {repo_root}")
        tests_input = Path(args.tests_root)
        tests_root = tests_input if tests_input.is_absolute() else repo_root / tests_input
        tests_root = resolve_under(repo_root, tests_root)

        if args.list:
            discovered = discover_suite_directories(tests_root, args.pattern)
            selected = select_suites(discovered, args.suite)
            for suite in selected:
                print(suite.name)
            return 0

        report = build_report(
            repo_root,
            tests_root,
            args.pattern,
            args.timeout,
            args.suite,
        )
        if args.output:
            output_path = validate_output_path(repo_root, Path(args.output))
            write_json_report(output_path, report, args.force)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_text_report(report, args.verbose)
            if args.output:
                print(f"Report: {validate_output_path(repo_root, Path(args.output))}")
        return 0 if report["passed"] else 1
    except ReleaseTestGateError as exc:
        if args.json:
            print(json.dumps({
                "schema_version": SCHEMA_VERSION,
                "report_type": REPORT_TYPE,
                "status": "blocked",
                "passed": False,
                "blocker": str(exc),
                "boundaries": BOUNDARIES,
            }, indent=2, sort_keys=True))
        else:
            print("KONOHA CANONICAL RELEASE TEST GATE BLOCKED", file=sys.stderr)
            print(f"Blocker: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
