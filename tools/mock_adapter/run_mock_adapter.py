#!/usr/bin/env python3
"""Konoha Mock Adapter / Clerk Interface.

This tool is a deterministic, local-only mock adapter for dry-run workflows.

It may:
- read an existing sandbox run manifest;
- create adapter output under sandbox/runs/<run_id>/adapter_outputs/;
- write a mock adapter invocation report inside the same sandbox run;
- print text or JSON status.

It may not:
- execute shell commands;
- call external APIs;
- use the network;
- invoke real adapters;
- access private Village context;
- modify repository files outside the configured sandbox run;
- perform Git operations;
- authorize runtime actions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "0.27.0"
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,96}$")
APPROVED_MODES = {"draft_summary", "checklist", "template_note"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fail(message: str, as_json: bool = False) -> int:
    if as_json:
        print(json.dumps({
            "status": "failed",
            "error": message,
            "execution": "blocked",
            "git_operations": "blocked",
            "private_context_access": "blocked",
            "adapter_execution": "mock_only",
            "network_access": "blocked",
        }, indent=2))
    else:
        print("MOCK ADAPTER FAILED")
        print(message)
    return 1


def assert_safe_run_id(run_id: str) -> None:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_id must be a simple slug; path traversal and separators are not allowed.")
    if "/" in run_id or "\\" in run_id or ".." in run_id:
        raise ValueError("run_id must not contain path separators or traversal.")


def resolve_under(root: Path, candidate: Path) -> Path:
    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve()
    if candidate_resolved != root_resolved and root_resolved not in candidate_resolved.parents:
        raise ValueError(f"Resolved path escapes allowed root: {candidate}")
    return candidate_resolved


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return data


def build_mock_content(mode: str, task: str, input_context: str) -> str:
    safe_context = input_context.strip()
    if len(safe_context) > 1200:
        safe_context = safe_context[:1200] + "\n\n[truncated for deterministic mock output]"

    if mode == "checklist":
        body = "\n".join([
            "# Mock Adapter Checklist",
            "",
            f"Task: {task}",
            "",
            "- [ ] Confirm Mission Charter exists.",
            "- [ ] Confirm sandbox run manifest exists.",
            "- [ ] Confirm output remains inside sandbox.",
            "- [ ] Confirm no private context was requested.",
            "- [ ] Confirm no Git operation was requested.",
            "- [ ] Confirm human review is still required.",
        ])
    elif mode == "template_note":
        body = "\n".join([
            "# Mock Adapter Template Note",
            "",
            "## Purpose",
            "",
            task,
            "",
            "## Draft",
            "",
            "This is deterministic mock output for review inside the sandbox.",
            "",
            "## Review reminders",
            "",
            "- This output is not authoritative.",
            "- This output does not authorize repository changes.",
            "- This output must be reviewed before any apply or Git gate.",
        ])
    else:
        body = "\n".join([
            "# Mock Adapter Draft Summary",
            "",
            f"Task: {task}",
            "",
            "## Summary",
            "",
            "This mock adapter produced a deterministic dry-run draft.",
            "",
            "## Input context excerpt",
            "",
            safe_context if safe_context else "_No input context provided._",
            "",
            "## Boundary",
            "",
            "This is mock-only output. It does not invoke real adapters or authorize actions.",
        ])

    return body + "\n"


def write_report(
    run_id: str,
    sandbox_root: Path,
    run_dir: Path,
    output_path: Path,
    mode: str,
    task: str,
    status: str,
) -> Dict[str, Any]:
    report = {
        "schema_version": "0.27.0",
        "tool": "mock_adapter",
        "status": status,
        "created_at": utc_now(),
        "run_id": run_id,
        "mode": mode,
        "task": task,
        "sandbox_root": str(sandbox_root),
        "run_dir": str(run_dir),
        "output_path": str(output_path),
        "boundaries": {
            "execution": "blocked",
            "filesystem_mutation": "sandbox_adapter_outputs_only",
            "repository_apply": "blocked",
            "git_operations": "blocked",
            "private_context_access": "blocked",
            "adapter_execution": "mock_only",
            "network_access": "blocked",
            "runtime_authorization": "blocked",
        },
        "review_required": True,
    }
    report_path = run_dir / "mock_adapter_invocation_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def run(args: argparse.Namespace) -> int:
    try:
        assert_safe_run_id(args.run_id)

        if args.mode not in APPROVED_MODES:
            raise ValueError(f"Unsupported mode: {args.mode}")

        sandbox_root = Path(args.sandbox_root)
        sandbox_runs_root = resolve_under(sandbox_root, sandbox_root / "runs")
        run_dir = resolve_under(sandbox_runs_root, sandbox_runs_root / args.run_id)

        manifest_path = run_dir / "sandbox_run_manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Sandbox run manifest not found: {manifest_path}. "
                "Prepare a sandbox run before invoking the mock adapter."
            )

        manifest = load_json(manifest_path)
        if manifest.get("boundaries", {}).get("adapter_execution") not in {"blocked", "mock_only", None}:
            raise ValueError("Sandbox run manifest does not preserve adapter execution boundary.")

        output_dir = resolve_under(run_dir, run_dir / "adapter_outputs")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_name = args.output_name
        if "/" in output_name or "\\" in output_name or ".." in output_name:
            raise ValueError("output_name must be a simple file name.")
        if not output_name.endswith(".md"):
            raise ValueError("output_name must end with .md for this mock adapter baseline.")

        output_path = resolve_under(output_dir, output_dir / output_name)
        if output_path.exists() and not args.force:
            raise FileExistsError(f"Output already exists: {output_path}. Use --force to overwrite.")

        content = build_mock_content(args.mode, args.task, args.input_context or "")
        output_path.write_text(content, encoding="utf-8")

        report = write_report(
            run_id=args.run_id,
            sandbox_root=sandbox_root,
            run_dir=run_dir,
            output_path=output_path,
            mode=args.mode,
            task=args.task,
            status="passed",
        )

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("MOCK ADAPTER PASSED")
            print(f"Mode: {args.mode}")
            print(f"Output: {output_path}")
            print("Execution: blocked")
            print("Filesystem mutation: sandbox adapter outputs only")
            print("Repository apply: blocked")
            print("Git operations: blocked")
            print("Private context access: blocked")
            print("Adapter execution: mock only")
            print("Network access: blocked")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary reports all failures.
        return fail(str(exc), args.json)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run deterministic mock adapter output inside an existing sandbox run."
    )
    parser.add_argument("--sandbox-root", required=True, help="Sandbox root, usually ./sandbox")
    parser.add_argument("--run-id", required=True, help="Existing sandbox run ID")
    parser.add_argument("--task", required=True, help="Task for the mock adapter")
    parser.add_argument(
        "--mode",
        default="draft_summary",
        choices=sorted(APPROVED_MODES),
        help="Mock output mode",
    )
    parser.add_argument("--input-context", default="", help="Optional public context text")
    parser.add_argument("--output-name", default="mock_adapter_output.md", help="Output markdown file name")
    parser.add_argument("--force", action="store_true", help="Overwrite existing mock output")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    parser.add_argument("--version", action="version", version=VERSION)
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
