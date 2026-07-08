#!/usr/bin/env python3
"""Local Village Bootstrap and Hardware Profile.

This tool is local-first and evidence-only. It can inspect basic hardware and
create a private Local Village skeleton only after explicit human approval.

It does not read private project files, .env files, credentials, emails, user
documents, or arbitrary directories. It does not execute commands, use network
access, invoke models, invoke adapters, apply repository changes, or perform
Git operations.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


PROFILE_TOKEN = "INSPECT_LOCAL_HARDWARE"
BOOTSTRAP_TOKEN = "BOOTSTRAP_LOCAL_VILLAGE"

VAULT_DIRS = [
    "00-inbox",
    "10-requests",
    "20-decisions",
    "30-missions",
    "40-communications",
    "50-context-packs",
    "90-archive",
]

VILLAGE_DIRS = [
    "config",
    "memory/vault",
    "assets",
    "style",
    "missions",
    "context",
    "local_kage",
    "reports",
    ".konoha.local",
]

BOUNDARIES = {
    "execution": "blocked",
    "repository_apply": "blocked",
    "git_operations": "blocked",
    "network_access": "blocked",
    "model_invocation": "blocked",
    "adapter_invocation": "blocked",
    "private_context_read": "blocked_by_default",
    "secret_read": "blocked",
    "background_agents": "blocked",
}

AUTHORITY = {
    "hardware_profile_is_evidence_only": True,
    "bootstrap_report_is_evidence_only": True,
    "local_config_does_not_authorize_execution": True,
    "local_village_does_not_authorize_private_context_access": True,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def to_posix(path: Path) -> str:
    return path.as_posix()


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Dict[str, Any], force: bool = False) -> None:
    if path.exists() and not force:
        raise RuntimeError(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str, force: bool = False) -> None:
    if path.exists() and not force:
        raise RuntimeError(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def validate_slug(value: str, label: str) -> str:
    if not value:
        raise ValueError(f"{label} is required")
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    if any(ch not in allowed for ch in value):
        raise ValueError(f"{label} must contain only letters, numbers, hyphen, or underscore")
    if value in {".", ".."}:
        raise ValueError(f"{label} cannot be a relative traversal token")
    return value


def safe_resolve(path: str) -> Path:
    raw = Path(path).expanduser()
    return raw.resolve()


def detect_ram_bytes() -> Optional[int]:
    if hasattr(os, "sysconf"):
        try:
            page_size = os.sysconf("SC_PAGE_SIZE")
            pages = os.sysconf("SC_PHYS_PAGES")
            if isinstance(page_size, int) and isinstance(pages, int) and page_size > 0 and pages > 0:
                return page_size * pages
        except Exception:
            return None
    return None


def bytes_to_gib(value: Optional[int]) -> Optional[float]:
    if value is None:
        return None
    return round(value / (1024 ** 3), 2)


def detect_tool_presence() -> Dict[str, Dict[str, Any]]:
    tools = {}
    for name in ["python", "git", "node", "npm", "ollama", "lmstudio"]:
        found = shutil.which(name)
        tools[name] = {
            "available": bool(found),
            "path_recorded": bool(found),
            "path": found if found else None,
        }
    return tools


def build_hardware_profile(village_name: str, profile_id: str, repo_root: Path, village_root: Path) -> Dict[str, Any]:
    disk_target = village_root if village_root.exists() else repo_root
    try:
        disk = shutil.disk_usage(str(disk_target))
        disk_payload = {
            "target": str(disk_target),
            "total_gib": bytes_to_gib(disk.total),
            "used_gib": bytes_to_gib(disk.used),
            "free_gib": bytes_to_gib(disk.free),
        }
    except Exception as exc:
        disk_payload = {"target": str(disk_target), "error": str(exc)}

    ram_bytes = detect_ram_bytes()

    return {
        "schema_version": "1.0.0",
        "profile_id": profile_id,
        "village_name": village_name,
        "generated_at": utc_now(),
        "profile_type": "local_hardware_profile",
        "inspection_mode": "stdlib_read_only",
        "system": {
            "os": platform.system(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "ram_gib": bytes_to_gib(ram_bytes),
            "gpu": {
                "status": "not_inspected",
                "reason": "GPU and VRAM detection is intentionally not performed by this stdlib-only safe profile.",
            },
            "disk": disk_payload,
            "tools": detect_tool_presence(),
        },
        "recommended_local_profile": {
            "machine_tier": infer_machine_tier(ram_bytes, os.cpu_count()),
            "recommended_workers": infer_workers(ram_bytes, os.cpu_count()),
            "local_models": {
                "clerk": "use local/free small model if available",
                "summarizer": "use local/free small model if available",
                "classifier": "use local/free small model if available",
                "reasoning_fallback": "use gated remote model only for high-impact reasoning",
            },
            "remote_escalation": {
                "enabled": "user_configured",
                "use_for": [
                    "architecture",
                    "high-impact debugging",
                    "security-sensitive review",
                    "complex planning",
                ],
            },
        },
        "privacy": {
            "project_files_read": False,
            "env_files_read": False,
            "credentials_read": False,
            "emails_read": False,
            "user_documents_read": False,
            "arbitrary_directory_scan": False,
        },
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
    }


def infer_machine_tier(ram_bytes: Optional[int], cpu_count: Optional[int]) -> str:
    ram_gib = bytes_to_gib(ram_bytes) or 0
    cpus = cpu_count or 0
    if ram_gib >= 64 and cpus >= 12:
        return "high"
    if ram_gib >= 32 and cpus >= 8:
        return "medium_high"
    if ram_gib >= 16 and cpus >= 4:
        return "medium"
    if ram_gib > 0:
        return "light"
    return "unknown"


def infer_workers(ram_bytes: Optional[int], cpu_count: Optional[int]) -> int:
    tier = infer_machine_tier(ram_bytes, cpu_count)
    return {
        "high": 6,
        "medium_high": 4,
        "medium": 2,
        "light": 1,
        "unknown": 1,
    }[tier]


def build_local_config(village_name: str, village_root: Path, hardware_profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    profile = hardware_profile.get("recommended_local_profile", {}) if hardware_profile else {}
    return {
        "schema_version": "1.0.0",
        "village_name": village_name,
        "village_type": "local_private_village",
        "generated_at": utc_now(),
        "village_root": str(village_root),
        "language_policy": {
            "public_core_language": "English",
            "local_village_language": "local_team_language",
        },
        "memory": {
            "format": "markdown_yaml_frontmatter",
            "obsidian_compatible": True,
            "root": "memory/vault",
            "private_by_default": True,
        },
        "assets": {
            "root": "assets",
            "private_by_default": True,
            "public_assets_must_be_generic_original_license_safe": True,
        },
        "local_profile": profile or {
            "machine_tier": "unknown",
            "recommended_workers": 1,
            "local_models": {},
            "remote_escalation": {"enabled": "user_configured", "use_for": []},
        },
        "permissions": {
            "private_context_access": "requires_explicit_human_approval",
            "email_access": "blocked_by_default",
            "secret_access": "blocked",
            "doctrine_rewrite": "blocked",
            "git_operations": "blocked",
            "network_access": "blocked_by_default",
            "background_agents": "blocked",
        },
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
    }


def render_readme(village_name: str) -> str:
    return f"""# {village_name} Local Village

This is a private Local Village workspace for Konoha.

It may contain private context, local memory, local assets, local style guides, mission records, and local configuration.

## Safety boundary

- Private context stays local.
- Local memory supports action but does not authorize action.
- Local assets are display evidence only.
- Local configuration does not authorize execution.
- Access to sensitive files requires explicit human approval.
- This folder should not be committed to the public repository unless it is a public template.

## Suggested folders

```text
config/
memory/vault/
assets/
style/
missions/
context/
local_kage/
reports/
.konoha.local/
```
"""


def render_memory_readme(village_name: str) -> str:
    return f"""# {village_name} Yamanaka Vault

Obsidian-compatible local memory.

Private by default.

Canonical sections:

```text
00-inbox/
10-requests/
20-decisions/
30-missions/
40-communications/
50-context-packs/
90-archive/
```

Memory supports action but does not authorize action.
Summaries are not truth.
Context packs are not permission.
"""


def render_style_template(village_name: str) -> str:
    return f"""# {village_name} Corporate Language Template

Use this file for local/private communication tone rules.

Do not commit private team language to a public repository.

## Audiences

### Managers

- Preferred tone:
- Words to avoid:
- Escalation format:

### Peers

- Preferred tone:
- Words to avoid:
- Collaboration format:

### Business users

- Preferred tone:
- Words to avoid:
- Status update format:
"""


def create_village_skeleton(
    village_name: str,
    village_root: Path,
    hardware_profile: Optional[Dict[str, Any]],
    force: bool = False,
) -> List[str]:
    created: List[str] = []
    for rel in VILLAGE_DIRS:
        path = village_root / rel
        path.mkdir(parents=True, exist_ok=True)
        created.append(to_posix(path))

    for rel in VAULT_DIRS:
        path = village_root / "memory" / "vault" / rel
        path.mkdir(parents=True, exist_ok=True)
        created.append(to_posix(path))

    write_text(village_root / "README.md", render_readme(village_name), force=force)
    write_text(village_root / "memory" / "vault" / "README.md", render_memory_readme(village_name), force=force)
    write_text(village_root / "style" / "corporate_language.template.md", render_style_template(village_name), force=force)
    config = build_local_config(village_name, village_root, hardware_profile)
    write_json(village_root / "config" / "local_village_config.json", config, force=force)

    created.extend([
        to_posix(village_root / "README.md"),
        to_posix(village_root / "memory" / "vault" / "README.md"),
        to_posix(village_root / "style" / "corporate_language.template.md"),
        to_posix(village_root / "config" / "local_village_config.json"),
    ])
    return created


def build_bootstrap_report(
    village_name: str,
    bootstrap_id: str,
    repo_root: Path,
    village_root: Path,
    invocation: str,
    status: str,
    created_paths: Optional[List[str]] = None,
    hardware_profile: Optional[Dict[str, Any]] = None,
    blockers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "report_type": "local_village_bootstrap_report",
        "bootstrap_id": bootstrap_id,
        "village_name": village_name,
        "generated_at": utc_now(),
        "status": status,
        "invocation": invocation,
        "repo_root": str(repo_root),
        "village_root": str(village_root),
        "created_paths": created_paths or [],
        "hardware_profile_embedded": bool(hardware_profile),
        "hardware_profile": hardware_profile,
        "blockers": blockers or [],
        "privacy": {
            "project_files_read": False,
            "env_files_read": False,
            "credentials_read": False,
            "emails_read": False,
            "user_documents_read": False,
            "arbitrary_directory_scan": False,
        },
        "authority": AUTHORITY,
        "boundaries": BOUNDARIES,
    }


def command_profile(args: argparse.Namespace) -> int:
    try:
        village_name = validate_slug(args.village_name, "village_name")
        repo_root = safe_resolve(args.repo_root)
        village_root = safe_resolve(args.village_root)
        if not args.confirm_profile:
            profile = build_hardware_profile(village_name, args.profile_id, repo_root, village_root)
            profile["invocation"] = "preview_only"
            profile["status"] = "preview"
            print("LOCAL HARDWARE PROFILE PREVIEW")
            print("Profile: preview_only")
            print("Repository apply: blocked")
            print("Git operations: blocked")
            print("Private context access: blocked")
            print("Secret read: blocked")
            if args.json:
                print(json.dumps(profile, indent=2, sort_keys=True))
            return 0
        if args.approval_token != PROFILE_TOKEN:
            raise RuntimeError("invalid approval token for hardware profile")
        profile = build_hardware_profile(village_name, args.profile_id, repo_root, village_root)
        profile["invocation"] = "confirmed_profile"
        profile["status"] = "passed"
        if args.output:
            output = safe_resolve(args.output)
            write_json(output, profile, force=args.force)
        print("LOCAL HARDWARE PROFILE PASSED")
        print("Profile: stdlib_read_only")
        print("Repository apply: blocked")
        print("Git operations: blocked")
        print("Private context access: blocked")
        print("Secret read: blocked")
        if args.json:
            print(json.dumps(profile, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print("LOCAL HARDWARE PROFILE FAILED")
        print("Blocker:", exc)
        return 1


def command_bootstrap(args: argparse.Namespace) -> int:
    try:
        village_name = validate_slug(args.village_name, "village_name")
        bootstrap_id = validate_slug(args.bootstrap_id, "bootstrap_id")
        repo_root = safe_resolve(args.repo_root)
        village_root = safe_resolve(args.village_root)

        hardware_profile = None
        if args.hardware_profile:
            hardware_profile = read_json(safe_resolve(args.hardware_profile))

        if not args.confirm_bootstrap:
            report = build_bootstrap_report(
                village_name=village_name,
                bootstrap_id=bootstrap_id,
                repo_root=repo_root,
                village_root=village_root,
                invocation="preview_only",
                status="preview",
                created_paths=[],
                hardware_profile=hardware_profile,
            )
            print("LOCAL VILLAGE BOOTSTRAP PREVIEW")
            print("Bootstrap: preview_only")
            print("Filesystem mutation: blocked")
            print("Repository apply: blocked")
            print("Git operations: blocked")
            print("Private context access: blocked")
            print("Secret read: blocked")
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            return 0

        if args.approval_token != BOOTSTRAP_TOKEN:
            raise RuntimeError("invalid approval token for local village bootstrap")

        created_paths = create_village_skeleton(village_name, village_root, hardware_profile, force=args.force)
        report = build_bootstrap_report(
            village_name=village_name,
            bootstrap_id=bootstrap_id,
            repo_root=repo_root,
            village_root=village_root,
            invocation="confirmed_bootstrap",
            status="passed",
            created_paths=created_paths,
            hardware_profile=hardware_profile,
        )
        report_path = village_root / "reports" / f"{bootstrap_id}_local_village_bootstrap_report.json"
        write_json(report_path, report, force=args.force)

        print("LOCAL VILLAGE BOOTSTRAP PASSED")
        print("Village:", village_name)
        print("Village root:", village_root)
        print("Private context access: blocked by default")
        print("Repository apply: blocked")
        print("Git operations: blocked")
        print("Secret read: blocked")
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print("LOCAL VILLAGE BOOTSTRAP FAILED")
        print("Blocker:", exc)
        return 1


def command_doctor(args: argparse.Namespace) -> int:
    try:
        village_root = safe_resolve(args.village_root)
        config_path = village_root / "config" / "local_village_config.json"
        report_path = None
        reports_dir = village_root / "reports"
        if reports_dir.exists():
            matches = sorted(reports_dir.glob("*_local_village_bootstrap_report.json"))
            report_path = matches[-1] if matches else None
        status = "passed" if config_path.exists() else "failed"
        blockers = [] if config_path.exists() else ["local_village_config.json does not exist"]
        report = {
            "schema_version": "1.0.0",
            "report_type": "local_village_doctor_report",
            "generated_at": utc_now(),
            "status": status,
            "village_root": str(village_root),
            "required_paths": {
                rel: (village_root / rel).exists() for rel in VILLAGE_DIRS
            },
            "config_path": str(config_path),
            "bootstrap_report_path": str(report_path) if report_path else None,
            "blockers": blockers,
            "authority": AUTHORITY,
            "boundaries": BOUNDARIES,
        }
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("LOCAL VILLAGE DOCTOR", status.upper())
            for item, exists in report["required_paths"].items():
                print(f"{item}: {'ok' if exists else 'missing'}")
            if blockers:
                print("Blockers:")
                for blocker in blockers:
                    print("-", blocker)
        return 0 if status == "passed" else 1
    except Exception as exc:
        print("LOCAL VILLAGE DOCTOR FAILED")
        print("Blocker:", exc)
        return 1


def command_init_dirs(args: argparse.Namespace) -> int:
    print("Local Village canonical directories:")
    for rel in VILLAGE_DIRS:
        print("-", rel)
    print("Yamanaka vault directories:")
    for rel in VAULT_DIRS:
        print("-", f"memory/vault/{rel}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap a private Local Village and record a safe hardware profile."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    profile = sub.add_parser("profile", help="Build a read-only hardware profile.")
    profile.add_argument("--repo-root", required=True)
    profile.add_argument("--village-root", required=True)
    profile.add_argument("--village-name", required=True)
    profile.add_argument("--profile-id", default="local-hardware-profile")
    profile.add_argument("--confirm-profile", action="store_true")
    profile.add_argument("--approval-token", default="")
    profile.add_argument("--output")
    profile.add_argument("--force", action="store_true")
    profile.add_argument("--json", action="store_true")
    profile.set_defaults(func=command_profile)

    bootstrap = sub.add_parser("bootstrap", help="Create a private Local Village skeleton.")
    bootstrap.add_argument("--repo-root", required=True)
    bootstrap.add_argument("--village-root", required=True)
    bootstrap.add_argument("--village-name", required=True)
    bootstrap.add_argument("--bootstrap-id", default="local-village-bootstrap")
    bootstrap.add_argument("--hardware-profile")
    bootstrap.add_argument("--confirm-bootstrap", action="store_true")
    bootstrap.add_argument("--approval-token", default="")
    bootstrap.add_argument("--force", action="store_true")
    bootstrap.add_argument("--json", action="store_true")
    bootstrap.set_defaults(func=command_bootstrap)

    doctor = sub.add_parser("doctor", help="Inspect a Local Village skeleton.")
    doctor.add_argument("--village-root", required=True)
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=command_doctor)

    dirs = sub.add_parser("dirs", help="List canonical Local Village directories.")
    dirs.set_defaults(func=command_init_dirs)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
