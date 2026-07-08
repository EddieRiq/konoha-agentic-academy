#!/usr/bin/env python3
"""Adapter Invocation Gate for Konoha Agentic Academy.

v0.28.0 boundary:
- real adapter execution is disabled by default and remains blocked in this MVP;
- mock adapter invocation is allowed only with explicit flags and approval token;
- all outputs stay inside an existing sandbox run;
- no shell commands, Git operations, network access, or private context access.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

APPROVAL_TOKEN = "INVOKE_ADAPTER_GATE"
SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")
MOCK_MODES = {"draft_summary", "checklist", "template_note"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_under(root: Path, *parts: str) -> Path:
    root_resolved = root.resolve()
    candidate = root_resolved.joinpath(*parts).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"path escapes root: {candidate}") from exc
    return candidate


def validate_run_id(run_id: str) -> None:
    if not SAFE_RUN_ID.match(run_id):
        raise ValueError("run_id must be alphanumeric plus '.', '_' or '-' and may not contain path separators")
    if run_id in {".", ".."} or "/" in run_id or "\\" in run_id:
        raise ValueError("run_id may not contain path traversal or path separators")


def load_sandbox_manifest(sandbox_root: Path, run_id: str) -> Dict[str, Any]:
    validate_run_id(run_id)
    run_dir = resolve_under(sandbox_root, "runs", run_id)
    manifest_path = resolve_under(run_dir, "sandbox_run_manifest.json")
    if not manifest_path.exists():
        raise FileNotFoundError(f"sandbox run manifest not found: {manifest_path}")
    with manifest_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def render_mock_output(task: str, mode: str) -> str:
    safe_task = task.strip()
    if mode == "checklist":
        return "\n".join(
            [
                "# Mock Adapter Checklist",
                "",
                f"Task: {safe_task}",
                "",
                "- Confirm Mission Charter exists.",
                "- Confirm sandbox run manifest exists.",
                "- Confirm outputs are review-required.",
                "- Confirm real adapter execution remains blocked.",
                "- Confirm no Git operations are requested.",
            ]
        )
    if mode == "template_note":
        return "\n".join(
            [
                "# Mock Adapter Template Note",
                "",
                f"Requested task: {safe_task}",
                "",
                "## Draft",
                "",
                "This is a deterministic mock output for review. It is not model-generated authority.",
            ]
        )
    return "\n".join(
        [
            "# Mock Adapter Draft Summary",
            "",
            f"Task: {safe_task}",
            "",
            "This deterministic mock summary exists only to exercise adapter-shaped workflows.",
            "It must be reviewed before any downstream use.",
        ]
    )


def build_report(
    *,
    status: str,
    run_id: str,
    adapter_requested: str,
    mode: str,
    task: str,
    invocation_state: str,
    approval_present: bool,
    output_path: Optional[str],
    findings: List[Dict[str, str]],
) -> Dict[str, Any]:
    blocked = {
        "execution": "blocked",
        "real_adapter_execution": "blocked",
        "repository_apply": "blocked",
        "git_operations": "blocked",
        "private_context_access": "blocked",
        "network_access": "blocked",
        "runtime_authorization": "blocked",
    }
    if invocation_state == "mock_invoked":
        filesystem = "sandbox_adapter_outputs_only"
    elif invocation_state == "preview_only":
        filesystem = "blocked"
    else:
        filesystem = "blocked"
    blocked["filesystem_mutation"] = filesystem

    return {
        "schema_version": "0.28.0",
        "report_type": "adapter_invocation_gate_report",
        "generated_at": utc_now(),
        "status": status,
        "run_id": run_id,
        "adapter_requested": adapter_requested,
        "adapter_effective": "mock" if invocation_state == "mock_invoked" else "none",
        "mode": mode,
        "task": task,
        "invocation_state": invocation_state,
        "approval": {
            "required_for_invocation": True,
            "provided": approval_present,
            "token_name": "INVOKE_ADAPTER_GATE",
        },
        "output_path": output_path,
        "boundaries": blocked,
        "findings": findings,
    }


def write_json(path: Path, payload: Dict[str, Any], force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing file without --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def run_gate(args: argparse.Namespace) -> Dict[str, Any]:
    sandbox_root = Path(args.sandbox_root)
    load_sandbox_manifest(sandbox_root, args.run_id)
    run_dir = resolve_under(sandbox_root, "runs", args.run_id)

    findings: List[Dict[str, str]] = []
    adapter = args.adapter
    mode = args.mode

    if adapter == "real":
        findings.append(
            {
                "severity": "blocker",
                "code": "real_adapter_disabled_by_default",
                "message": "Real adapter invocation is disabled in v0.28.0.",
            }
        )
        return build_report(
            status="blocked",
            run_id=args.run_id,
            adapter_requested=adapter,
            mode=mode,
            task=args.task,
            invocation_state="blocked",
            approval_present=bool(args.approval_token),
            output_path=None,
            findings=findings,
        )

    if mode not in MOCK_MODES:
        findings.append(
            {
                "severity": "blocker",
                "code": "unsupported_mock_mode",
                "message": f"Unsupported mock mode: {mode}",
            }
        )
        return build_report(
            status="blocked",
            run_id=args.run_id,
            adapter_requested=adapter,
            mode=mode,
            task=args.task,
            invocation_state="blocked",
            approval_present=bool(args.approval_token),
            output_path=None,
            findings=findings,
        )

    if not args.confirm_invocation:
        findings.append(
            {
                "severity": "info",
                "code": "preview_only",
                "message": "No adapter invocation performed. Use explicit confirmation to invoke the mock adapter.",
            }
        )
        return build_report(
            status="preview",
            run_id=args.run_id,
            adapter_requested=adapter,
            mode=mode,
            task=args.task,
            invocation_state="preview_only",
            approval_present=False,
            output_path=None,
            findings=findings,
        )

    if args.approval_token != APPROVAL_TOKEN:
        findings.append(
            {
                "severity": "blocker",
                "code": "approval_token_invalid",
                "message": "Confirmed adapter invocation requires exact approval token.",
            }
        )
        return build_report(
            status="blocked",
            run_id=args.run_id,
            adapter_requested=adapter,
            mode=mode,
            task=args.task,
            invocation_state="blocked",
            approval_present=bool(args.approval_token),
            output_path=None,
            findings=findings,
        )

    if not args.enable_mock_adapter:
        findings.append(
            {
                "severity": "blocker",
                "code": "mock_adapter_not_enabled",
                "message": "Mock adapter invocation requires --enable-mock-adapter.",
            }
        )
        return build_report(
            status="blocked",
            run_id=args.run_id,
            adapter_requested=adapter,
            mode=mode,
            task=args.task,
            invocation_state="blocked",
            approval_present=True,
            output_path=None,
            findings=findings,
        )

    output_dir = resolve_under(run_dir, "adapter_outputs")
    output_path = resolve_under(output_dir, "adapter_gate_mock_output.md")
    report_path = resolve_under(run_dir, "adapter_invocation_gate_report.json")

    if output_path.exists() and not args.force:
        raise FileExistsError(f"refusing to overwrite existing adapter output without --force: {output_path}")
    if report_path.exists() and not args.force:
        raise FileExistsError(f"refusing to overwrite existing adapter gate report without --force: {report_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_mock_output(args.task, mode) + "\n", encoding="utf-8", newline="\n")

    findings.append(
        {
            "severity": "info",
            "code": "mock_adapter_invoked",
            "message": "Deterministic mock adapter output written inside sandbox run.",
        }
    )

    report = build_report(
        status="passed",
        run_id=args.run_id,
        adapter_requested=adapter,
        mode=mode,
        task=args.task,
        invocation_state="mock_invoked",
        approval_present=True,
        output_path=str(output_path),
        findings=findings,
    )
    write_json(report_path, report, force=args.force)
    return report


def print_text(report: Dict[str, Any]) -> None:
    status = report["status"]
    if status == "passed":
        print("ADAPTER INVOCATION GATE PASSED")
    elif status == "preview":
        print("ADAPTER INVOCATION GATE PREVIEW")
    else:
        print("ADAPTER INVOCATION GATE FAILED")
    print(f"Adapter requested: {report['adapter_requested']}")
    print(f"Invocation: {report['invocation_state']}")
    print(f"Execution: {report['boundaries']['execution']}")
    print(f"Filesystem mutation: {report['boundaries']['filesystem_mutation']}")
    print(f"Repository apply: {report['boundaries']['repository_apply']}")
    print(f"Git operations: {report['boundaries']['git_operations']}")
    print(f"Private context access: {report['boundaries']['private_context_access']}")
    print(f"Real adapter execution: {report['boundaries']['real_adapter_execution']}")
    print(f"Network access: {report['boundaries']['network_access']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adapter invocation gate disabled by default.")
    parser.add_argument("--sandbox-root", default="sandbox", help="Sandbox root containing runs/<run_id>.")
    parser.add_argument("--run-id", required=True, help="Existing sandbox run id.")
    parser.add_argument("--adapter", choices=["mock", "real"], default="mock", help="Adapter request type.")
    parser.add_argument("--task", required=True, help="Task text to pass to the mock adapter.")
    parser.add_argument("--mode", default="draft_summary", help="Mock mode: draft_summary, checklist, or template_note.")
    parser.add_argument("--confirm-invocation", action="store_true", help="Confirm a gated mock invocation.")
    parser.add_argument("--approval-token", default="", help="Exact approval token required for invocation.")
    parser.add_argument("--enable-mock-adapter", action="store_true", help="Enable deterministic mock adapter invocation.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing sandbox adapter outputs/reports.")
    parser.add_argument("--json", action="store_true", help="Print JSON report to stdout.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = run_gate(args)
    except Exception as exc:  # explicit CLI failure boundary
        report = build_report(
            status="blocked",
            run_id=getattr(args, "run_id", ""),
            adapter_requested=getattr(args, "adapter", "unknown"),
            mode=getattr(args, "mode", "unknown"),
            task=getattr(args, "task", ""),
            invocation_state="blocked",
            approval_present=bool(getattr(args, "approval_token", "")),
            output_path=None,
            findings=[{"severity": "blocker", "code": "exception", "message": str(exc)}],
        )
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_text(report)
            print(f"Blocker: {exc}")
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    return 0 if report["status"] in {"passed", "preview"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
