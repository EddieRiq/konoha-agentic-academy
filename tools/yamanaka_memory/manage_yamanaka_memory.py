#!/usr/bin/env python3
"""Yamanaka advanced memory and context pack manager.

This tool manages Obsidian-compatible local memory notes and context packs
from explicit Mission Workspace evidence.

It does not execute missions, invoke models, invoke adapters, apply repository
changes, perform Git operations, access private context by default, or close
missions.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"

CAPTURE_APPROVAL_TOKEN = "RECORD_YAMANAKA_MEMORY"
CONTEXT_PACK_APPROVAL_TOKEN = "BUILD_CONTEXT_PACK"

VAULT_DIRS = [
    "00-inbox",
    "10-missions",
    "20-decisions",
    "30-tactics",
    "40-failures",
    "50-scroll-proposals",
    "60-context-packs",
    "90-archive",
    "_reports",
    "_index",
]

MISSION_SUBDIRS = [
    "plans",
    "reports",
    "approvals",
    "evidence",
    "outputs",
    "context",
]

BOUNDARIES = {
    "execution": "blocked",
    "repository_apply": "blocked",
    "git_operations": "blocked",
    "private_context_access": "blocked_by_default",
    "real_model_invocation": "blocked",
    "adapter_invocation": "blocked",
    "network_access": "blocked",
    "background_agents": "blocked",
}

AUTHORITY = {
    "memory_supports_action_but_does_not_authorize_action": True,
    "context_packs_are_not_permission": True,
    "summaries_are_not_truth": True,
    "mission_closure_is_not_performed_by_this_tool": True,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def json_dumps(data: Dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def slugify(value: str) -> str:
    safe = []
    for ch in value.strip():
        if ch.isalnum() or ch in ("-", "_"):
            safe.append(ch)
        elif ch in (" ", ".", "/"):
            safe.append("-")
    result = "".join(safe).strip("-_")
    return result or "unnamed"


def reject_unsafe_id(label: str, value: str) -> None:
    if not value:
        raise ValueError(f"{label} is required")
    if ".." in value or "/" in value or "\\" in value or value.startswith("."):
        raise ValueError(f"unsafe {label}: path traversal is not allowed")


def resolve_path(path: str) -> Path:
    return Path(path).expanduser().resolve()


def assert_within(root: Path, child: Path, label: str) -> None:
    root = root.resolve()
    child = child.resolve()
    if child == root:
        return
    if root not in child.parents:
        raise ValueError(f"{label} must stay inside {root}")


def write_text(path: Path, text: str, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing file without --force: {path}")
    path.write_text(text, encoding="utf-8")


def read_text_optional(path: Path, limit: int = 24000) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > limit:
        return text[:limit] + "\n\n<!-- truncated by Yamanaka memory manager -->\n"
    return text


def read_json_optional(path: Path) -> Optional[Dict[str, Any]]:
    text = read_text_optional(path)
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):
        return data
    return None


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def yaml_frontmatter(data: Dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {yaml_scalar(item)}")
        else:
            lines.append(f"{key}: {yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def print_boundaries() -> None:
    print("Execution: blocked")
    print("Repository apply: blocked")
    print("Git operations: blocked")
    print("Private context access: blocked by default")
    print("Real model invocation: blocked")
    print("Adapter invocation: blocked")
    print("Network access: blocked")
    print("Background agents: blocked")


def ensure_vault(memory_root: Path, force: bool = False) -> Dict[str, Any]:
    memory_root.mkdir(parents=True, exist_ok=True)
    for item in VAULT_DIRS:
        (memory_root / item).mkdir(parents=True, exist_ok=True)

    readme = memory_root / "README.md"
    if force or not readme.exists():
        write_text(
            readme,
            "# Yamanaka Memory Vault\n\n"
            "This vault stores Obsidian-compatible Markdown memory notes, context packs, "
            "indexes, and reports for Konoha missions.\n\n"
            "Memory supports action but does not authorize action.\n"
            "Context packs are not permission.\n"
            "Summaries are not truth.\n",
            force=True,
        )

    return {
        "memory_root": str(memory_root),
        "created_directories": VAULT_DIRS,
        "status": "ok",
    }


def mission_path(workspace_root: Path, mission_id: str) -> Path:
    reject_unsafe_id("mission_id", mission_id)
    path = workspace_root / "missions" / mission_id
    assert_within(workspace_root, path, "mission path")
    if not path.exists():
        raise FileNotFoundError(f"mission workspace not found: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"mission path is not a directory: {path}")
    return path


def list_files(base: Path, rel_dir: str) -> List[str]:
    directory = base / rel_dir
    if not directory.exists():
        return []
    files: List[str] = []
    for item in sorted(directory.rglob("*")):
        if item.is_file():
            files.append(item.relative_to(base).as_posix())
    return files


def collect_mission_evidence(mission_dir: Path) -> Dict[str, Any]:
    manifest = read_json_optional(mission_dir / "mission_manifest.json")
    status = read_json_optional(mission_dir / "mission_status.json")
    notification_state = read_json_optional(mission_dir / "mission_notification_state.json")
    charter = read_text_optional(mission_dir / "charter.md", limit=8000)
    readme = read_text_optional(mission_dir / "README.md", limit=8000)

    files_by_type = {rel_dir: list_files(mission_dir, rel_dir) for rel_dir in MISSION_SUBDIRS}

    return {
        "manifest": manifest,
        "status": status,
        "notification_state": notification_state,
        "charter_present": charter is not None,
        "readme_present": readme is not None,
        "files_by_type": files_by_type,
        "evidence_file_count": sum(len(values) for values in files_by_type.values()),
    }


def mission_title(mission_id: str, evidence: Dict[str, Any]) -> str:
    manifest = evidence.get("manifest") or {}
    for key in ("title", "mission_title", "goal"):
        value = manifest.get(key)
        if value:
            return str(value)
    return mission_id


def build_mission_note(
    mission_id: str,
    capture_id: str,
    evidence: Dict[str, Any],
    human_actor: str,
    generated_at: str,
) -> str:
    manifest = evidence.get("manifest") or {}
    status = evidence.get("status") or {}
    notification_state = evidence.get("notification_state") or {}
    title = mission_title(mission_id, evidence)

    frontmatter = yaml_frontmatter(
        {
            "type": "mission_memory_note",
            "schema_version": SCHEMA_VERSION,
            "mission_id": mission_id,
            "capture_id": capture_id,
            "title": title,
            "generated_at": generated_at,
            "human_actor": human_actor,
            "source": "mission_workspace",
            "authority": "evidence_only",
            "memory_supports_action_but_does_not_authorize_action": True,
        }
    )

    lines = [
        frontmatter,
        f"# Mission Memory Note: {mission_id}",
        "",
        "## Summary",
        "",
        manifest.get("scope") or manifest.get("goal") or "Mission scope was not available in the manifest.",
        "",
        "## Status",
        "",
        f"- Mission status: `{status.get('status', 'unknown')}`",
        f"- Notification state: `{notification_state.get('state', 'unknown')}`",
        f"- Evidence file count: `{evidence.get('evidence_file_count', 0)}`",
        "",
        "## Evidence references",
        "",
    ]

    files_by_type = evidence.get("files_by_type") or {}
    for section, files in files_by_type.items():
        lines.append(f"### {section}")
        lines.append("")
        if not files:
            lines.append("- None recorded.")
        else:
            for rel_path in files:
                lines.append(f"- `{rel_path}`")
        lines.append("")

    lines.extend(
        [
            "## Non-authority boundary",
            "",
            "- This memory note is evidence only.",
            "- Memory supports action but does not authorize action.",
            "- Summaries are not truth.",
            "- This note does not close a mission.",
            "- This note does not authorize execution, model calls, adapter calls, repository apply, Git operations, or private context access.",
            "",
        ]
    )

    return "\n".join(lines)


def build_context_pack_markdown(
    mission_id: str,
    context_pack_id: str,
    note_paths: List[str],
    source_report_paths: List[str],
    generated_at: str,
    purpose: str,
) -> str:
    frontmatter = yaml_frontmatter(
        {
            "type": "yamanaka_context_pack",
            "schema_version": SCHEMA_VERSION,
            "mission_id": mission_id,
            "context_pack_id": context_pack_id,
            "generated_at": generated_at,
            "purpose": purpose,
            "authority": "evidence_only",
            "context_pack_is_not_permission": True,
            "summaries_are_not_truth": True,
        }
    )

    lines = [
        frontmatter,
        f"# Yamanaka Context Pack: {context_pack_id}",
        "",
        "## Purpose",
        "",
        purpose,
        "",
        "## Memory notes included",
        "",
    ]

    if note_paths:
        for item in note_paths:
            lines.append(f"- `{item}`")
    else:
        lines.append("- None found.")

    lines.extend(["", "## Source reports", ""])
    if source_report_paths:
        for item in source_report_paths:
            lines.append(f"- `{item}`")
    else:
        lines.append("- None found.")

    lines.extend(
        [
            "",
            "## Operating boundary",
            "",
            "- Context packs are not permission.",
            "- Context packs are not ground truth.",
            "- They are a compact pointer set for human and agent review.",
            "- They do not authorize execution, model calls, adapter calls, repository apply, Git operations, private context access, doctrine rewrite, or mission closure.",
            "",
        ]
    )

    return "\n".join(lines)


def report_base(
    command: str,
    status: str,
    generated_at: str,
    blockers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": f"yamanaka_{command}_report",
        "generated_at": generated_at,
        "command": command,
        "status": status,
        "blockers": blockers or [],
        "boundaries": BOUNDARIES,
        "authority": AUTHORITY,
    }


def command_init(args: argparse.Namespace) -> int:
    memory_root = resolve_path(args.memory_root)
    try:
        result = ensure_vault(memory_root, force=args.force)
    except Exception as exc:
        print("YAMANAKA MEMORY INIT FAILED")
        print("Blocker:", exc)
        return 1

    report = report_base("init", "passed", utc_now())
    report.update(result)
    if args.json:
        print(json_dumps(report), end="")
    else:
        print("YAMANAKA MEMORY INIT PASSED")
        print(f"Memory root: {memory_root}")
        print_boundaries()
    return 0


def command_capture_mission(args: argparse.Namespace) -> int:
    generated_at = utc_now()
    workspace_root = resolve_path(args.workspace_root)
    memory_root = resolve_path(args.memory_root)
    capture_id = slugify(args.capture_id or f"{args.mission_id}-capture")
    reject_unsafe_id("capture_id", capture_id)

    try:
        mission_dir = mission_path(workspace_root, args.mission_id)
        evidence = collect_mission_evidence(mission_dir)
    except Exception as exc:
        report = report_base("capture_mission", "failed", generated_at, [str(exc)])
        print("YAMANAKA MEMORY CAPTURE FAILED")
        print(json_dumps(report), end="" if args.json else "\n")
        return 1

    if not args.confirm_capture:
        if args.json:
            report = report_base("capture_mission", "preview", generated_at)
            report.update(
                {
                    "invocation": "preview_only",
                    "mission_id": args.mission_id,
                    "capture_id": capture_id,
                    "would_write": [
                        f"10-missions/{args.mission_id}_{capture_id}.md",
                        f"_reports/{capture_id}_yamanaka_memory_capture_report.json",
                    ],
                    "evidence": evidence,
                }
            )
            print(json_dumps(report), end="")
        else:
            print("YAMANAKA MEMORY CAPTURE PREVIEW")
            print("Invocation: preview_only")
            print("Filesystem mutation: blocked")
            print_boundaries()
        return 0

    if args.approval_token != CAPTURE_APPROVAL_TOKEN:
        report = report_base(
            "capture_mission",
            "failed",
            generated_at,
            [f"approval token must be {CAPTURE_APPROVAL_TOKEN}"],
        )
        print("YAMANAKA MEMORY CAPTURE FAILED")
        print(json_dumps(report), end="" if args.json else "\n")
        return 1

    try:
        ensure_vault(memory_root, force=False)
        note_rel = Path("10-missions") / f"{args.mission_id}_{capture_id}.md"
        report_rel = Path("_reports") / f"{capture_id}_yamanaka_memory_capture_report.json"
        note_path = memory_root / note_rel
        report_path = memory_root / report_rel
        assert_within(memory_root, note_path, "memory note path")
        assert_within(memory_root, report_path, "capture report path")

        note_text = build_mission_note(
            args.mission_id,
            capture_id,
            evidence,
            args.human_actor,
            generated_at,
        )
        write_text(note_path, note_text, force=args.force)

        report = report_base("capture_mission", "passed", generated_at)
        report.update(
            {
                "mission_id": args.mission_id,
                "capture_id": capture_id,
                "memory_root": str(memory_root),
                "mission_memory_note": note_rel.as_posix(),
                "capture_report": report_rel.as_posix(),
                "evidence": evidence,
            }
        )
        write_text(report_path, json_dumps(report), force=True)
    except Exception as exc:
        report = report_base("capture_mission", "failed", generated_at, [str(exc)])
        print("YAMANAKA MEMORY CAPTURE FAILED")
        print(json_dumps(report), end="" if args.json else "\n")
        return 1

    if args.json:
        print(json_dumps(report), end="")
    else:
        print("YAMANAKA MEMORY CAPTURE PASSED")
        print(f"Mission: {args.mission_id}")
        print(f"Memory note: {note_rel.as_posix()}")
        print(f"Capture report: {report_rel.as_posix()}")
        print_boundaries()
    return 0


def command_build_context_pack(args: argparse.Namespace) -> int:
    generated_at = utc_now()
    memory_root = resolve_path(args.memory_root)
    context_pack_id = slugify(args.context_pack_id or f"{args.mission_id}-context-pack")
    reject_unsafe_id("context_pack_id", context_pack_id)

    if not memory_root.exists():
        print("YAMANAKA CONTEXT PACK FAILED")
        print("Blocker: memory root does not exist")
        return 1

    note_paths = [
        path.relative_to(memory_root).as_posix()
        for path in sorted((memory_root / "10-missions").glob(f"{args.mission_id}_*.md"))
        if path.is_file()
    ]
    source_report_paths = [
        path.relative_to(memory_root).as_posix()
        for path in sorted((memory_root / "_reports").glob("*yamanaka_memory_capture_report.json"))
        if path.is_file()
    ]

    if not args.confirm_build:
        if args.json:
            report = report_base("build_context_pack", "preview", generated_at)
            report.update(
                {
                    "invocation": "preview_only",
                    "mission_id": args.mission_id,
                    "context_pack_id": context_pack_id,
                    "notes_found": note_paths,
                    "would_write": [
                        f"60-context-packs/{context_pack_id}.md",
                        f"60-context-packs/{context_pack_id}.manifest.json",
                    ],
                }
            )
            print(json_dumps(report), end="")
        else:
            print("YAMANAKA CONTEXT PACK PREVIEW")
            print("Invocation: preview_only")
            print("Filesystem mutation: blocked")
            print_boundaries()
        return 0

    if args.approval_token != CONTEXT_PACK_APPROVAL_TOKEN:
        print("YAMANAKA CONTEXT PACK FAILED")
        print(f"Blocker: approval token must be {CONTEXT_PACK_APPROVAL_TOKEN}")
        return 1

    try:
        ensure_vault(memory_root, force=False)
        pack_rel = Path("60-context-packs") / f"{context_pack_id}.md"
        manifest_rel = Path("60-context-packs") / f"{context_pack_id}.manifest.json"
        pack_path = memory_root / pack_rel
        manifest_path = memory_root / manifest_rel
        assert_within(memory_root, pack_path, "context pack path")
        assert_within(memory_root, manifest_path, "context pack manifest path")

        pack_text = build_context_pack_markdown(
            args.mission_id,
            context_pack_id,
            note_paths,
            source_report_paths,
            generated_at,
            args.purpose,
        )
        write_text(pack_path, pack_text, force=args.force)

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "manifest_type": "yamanaka_context_pack_manifest",
            "generated_at": generated_at,
            "mission_id": args.mission_id,
            "context_pack_id": context_pack_id,
            "context_pack_path": pack_rel.as_posix(),
            "notes_included": note_paths,
            "source_reports": source_report_paths,
            "purpose": args.purpose,
            "authority": AUTHORITY,
            "boundaries": BOUNDARIES,
        }
        write_text(manifest_path, json_dumps(manifest), force=True)
    except Exception as exc:
        print("YAMANAKA CONTEXT PACK FAILED")
        print("Blocker:", exc)
        return 1

    if args.json:
        print(json_dumps(manifest), end="")
    else:
        print("YAMANAKA CONTEXT PACK BUILT")
        print(f"Mission: {args.mission_id}")
        print(f"Context pack: {pack_rel.as_posix()}")
        print(f"Manifest: {manifest_rel.as_posix()}")
        print_boundaries()
    return 0


def scan_memory_root(memory_root: Path) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    files: List[str] = []

    for directory in VAULT_DIRS:
        dir_path = memory_root / directory
        if not dir_path.exists():
            counts[directory] = 0
            continue
        dir_files = [p for p in sorted(dir_path.rglob("*")) if p.is_file()]
        counts[directory] = len(dir_files)
        files.extend([p.relative_to(memory_root).as_posix() for p in dir_files])

    return {"counts": counts, "files": files}


def command_index(args: argparse.Namespace) -> int:
    generated_at = utc_now()
    memory_root = resolve_path(args.memory_root)

    if not memory_root.exists():
        print("YAMANAKA MEMORY INDEX FAILED")
        print("Blocker: memory root does not exist")
        return 1

    try:
        ensure_vault(memory_root, force=False)
        scan = scan_memory_root(memory_root)
        index = {
            "schema_version": SCHEMA_VERSION,
            "index_type": "yamanaka_memory_index",
            "generated_at": generated_at,
            "memory_root": str(memory_root),
            "counts": scan["counts"],
            "files": scan["files"],
            "authority": AUTHORITY,
            "boundaries": BOUNDARIES,
        }
        index_path = memory_root / "_index" / "yamanaka_memory_index.json"
        write_text(index_path, json_dumps(index), force=True)
    except Exception as exc:
        print("YAMANAKA MEMORY INDEX FAILED")
        print("Blocker:", exc)
        return 1

    if args.json:
        print(json_dumps(index), end="")
    else:
        print("YAMANAKA MEMORY INDEX PASSED")
        print(f"Index: {(Path('_index') / 'yamanaka_memory_index.json').as_posix()}")
        print_boundaries()
    return 0


def command_inspect(args: argparse.Namespace) -> int:
    generated_at = utc_now()
    memory_root = resolve_path(args.memory_root)

    if not memory_root.exists():
        report = report_base("inspect", "failed", generated_at, ["memory root does not exist"])
    else:
        scan = scan_memory_root(memory_root)
        report = report_base("inspect", "passed", generated_at)
        report.update(
            {
                "memory_root": str(memory_root),
                "counts": scan["counts"],
                "files": scan["files"][:200],
                "truncated": len(scan["files"]) > 200,
            }
        )

    if args.json:
        print(json_dumps(report), end="")
    else:
        if report["status"] == "passed":
            print("YAMANAKA MEMORY INSPECT PASSED")
            print(f"Memory root: {memory_root}")
            for key, count in report["counts"].items():
                print(f"{key}: {count}")
            print_boundaries()
        else:
            print("YAMANAKA MEMORY INSPECT FAILED")
            for blocker in report["blockers"]:
                print("Blocker:", blocker)
    return 0 if report["status"] == "passed" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage Yamanaka advanced memory and context packs."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Initialize a Yamanaka memory vault.")
    init.add_argument("--memory-root", required=True)
    init.add_argument("--force", action="store_true")
    init.add_argument("--json", action="store_true")
    init.set_defaults(func=command_init)

    capture = subparsers.add_parser("capture-mission", help="Capture Mission Workspace evidence into memory.")
    capture.add_argument("--workspace-root", required=True)
    capture.add_argument("--memory-root", required=True)
    capture.add_argument("--mission-id", required=True)
    capture.add_argument("--capture-id", required=True)
    capture.add_argument("--human-actor", default="human")
    capture.add_argument("--confirm-capture", action="store_true")
    capture.add_argument("--approval-token", default="")
    capture.add_argument("--force", action="store_true")
    capture.add_argument("--json", action="store_true")
    capture.set_defaults(func=command_capture_mission)

    build = subparsers.add_parser("build-context-pack", help="Build a context pack from memory notes.")
    build.add_argument("--memory-root", required=True)
    build.add_argument("--mission-id", required=True)
    build.add_argument("--context-pack-id", required=True)
    build.add_argument("--purpose", default="Compact mission context for future review.")
    build.add_argument("--confirm-build", action="store_true")
    build.add_argument("--approval-token", default="")
    build.add_argument("--force", action="store_true")
    build.add_argument("--json", action="store_true")
    build.set_defaults(func=command_build_context_pack)

    index = subparsers.add_parser("index", help="Build a memory index.")
    index.add_argument("--memory-root", required=True)
    index.add_argument("--json", action="store_true")
    index.set_defaults(func=command_index)

    inspect = subparsers.add_parser("inspect", help="Inspect a Yamanaka memory vault.")
    inspect.add_argument("--memory-root", required=True)
    inspect.add_argument("--json", action="store_true")
    inspect.set_defaults(func=command_inspect)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("YAMANAKA MEMORY INTERRUPTED")
        return 130
    except Exception as exc:
        print("YAMANAKA MEMORY FAILED")
        print("Blocker:", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
