"""Resolve Konoha logical UI assets without granting runtime authority.

The resolver is read-only except when explicitly asked to write a resolution
report under the sandbox reports directory. It does not fetch remote assets,
execute commands, inspect private context, or authorize UI/runtime actions.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


LOGICAL_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,120}$")
ALLOWED_EXTENSIONS = {
    ".txt",
    ".md",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".wav",
    ".mp3",
}
REPORT_SUFFIX = "_asset_resolution_report.json"

FALLBACK_TEXT = {
    "status.waiting_user_input": "[?] Waiting for user input.",
    "status.waiting_approval": "[!] Waiting for human approval.",
    "status.blocked": "[X] Blocked.",
    "status.ready_for_review": "[R] Ready for review.",
    "status.ready_for_teachback": "[T] Ready for teachback.",
    "status.closed": "[OK] Closed.",
    "avatar.kagebunshin.coding": "[worker:coding]",
    "background.cubicles_active": "[cubicles:active]",
}


@dataclass(frozen=True)
class AssetRoot:
    tier: str
    root: Path


@dataclass(frozen=True)
class Resolution:
    status: str
    logical_name: str
    source_tier: str
    asset_type: str
    resolved_path: Optional[Path]
    display_path: Optional[str]
    content_preview: Optional[str]
    blockers: Tuple[str, ...]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_logical_name(logical_name: str) -> None:
    if not LOGICAL_NAME_PATTERN.match(logical_name):
        raise ValueError(
            "logical asset name must use lowercase letters, numbers, dots, "
            "underscores, or hyphens only"
        )
    if ".." in logical_name or logical_name.startswith(".") or logical_name.endswith("."):
        raise ValueError("logical asset name cannot contain path traversal patterns")


def safe_join(root: Path, relative_path: str) -> Path:
    rel = Path(relative_path)
    if rel.is_absolute():
        raise ValueError("asset registry path must be relative")
    if any(part in {"..", ""} for part in rel.parts):
        raise ValueError("asset registry path must not contain traversal")
    candidate = (root / rel).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("asset path escapes configured asset root") from exc
    if candidate.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(f"asset extension is not allowed: {candidate.suffix}")
    return candidate


def load_registry(root: Path) -> Dict[str, Dict[str, str]]:
    registry_path = root / "asset_registry.json"
    if not registry_path.exists():
        return {}
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    assets = data.get("assets", {})
    if not isinstance(assets, dict):
        raise ValueError(f"invalid asset registry at {registry_path}: assets must be an object")
    normalized: Dict[str, Dict[str, str]] = {}
    for logical_name, spec in assets.items():
        validate_logical_name(logical_name)
        if not isinstance(spec, dict):
            raise ValueError(f"invalid asset registry entry for {logical_name}")
        path = spec.get("path")
        asset_type = spec.get("type", "unknown")
        description = spec.get("description", "")
        if not isinstance(path, str) or not path:
            raise ValueError(f"asset registry entry for {logical_name} requires path")
        if not isinstance(asset_type, str) or not asset_type:
            raise ValueError(f"asset registry entry for {logical_name} requires type")
        normalized[logical_name] = {
            "path": path,
            "type": asset_type,
            "description": str(description),
        }
    return normalized


def redact_path(path: Path, root: Path, tier: str, show_private_paths: bool = False) -> str:
    if show_private_paths or tier == "public_generic":
        return str(path)
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError:
        relative = Path(path.name)
    if tier == "local_village":
        prefix = "$VILLAGE_ASSETS"
    elif tier == "user":
        prefix = "$USER_ASSETS"
    else:
        prefix = "$ASSET_ROOT"
    return str(Path(prefix) / relative)


def read_content_preview(path: Path) -> Optional[str]:
    if path.suffix.lower() not in {".txt", ".md", ".svg"}:
        return None
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if len(text) > 500:
        return text[:500] + "\n..."
    return text


def default_asset_roots(
    repo_root: Path,
    village_assets_root: Optional[Path],
    user_assets_root: Optional[Path],
    public_assets_root: Optional[Path],
) -> List[AssetRoot]:
    roots: List[AssetRoot] = []
    if village_assets_root is not None:
        roots.append(AssetRoot("local_village", village_assets_root))
    if user_assets_root is not None:
        roots.append(AssetRoot("user", user_assets_root))
    roots.append(AssetRoot("public_generic", public_assets_root or repo_root / "shinobi" / "assets" / "generic"))
    return roots


def resolve_asset(
    logical_name: str,
    roots: Iterable[AssetRoot],
    show_private_paths: bool = False,
) -> Resolution:
    validate_logical_name(logical_name)
    blockers: List[str] = []

    for asset_root in roots:
        root = asset_root.root.expanduser()
        if not root.exists():
            continue
        registry = load_registry(root)
        spec = registry.get(logical_name)
        if spec is None:
            continue
        try:
            candidate = safe_join(root, spec["path"])
        except ValueError as exc:
            raise ValueError(f"unsafe asset registry entry for {logical_name}: {exc}") from exc
        if not candidate.exists() or not candidate.is_file():
            blockers.append(f"{asset_root.tier} asset is registered but file is missing")
            continue
        return Resolution(
            status="resolved",
            logical_name=logical_name,
            source_tier=asset_root.tier,
            asset_type=spec.get("type", "unknown"),
            resolved_path=candidate,
            display_path=redact_path(candidate, root, asset_root.tier, show_private_paths),
            content_preview=read_content_preview(candidate),
            blockers=tuple(blockers),
        )

    fallback = FALLBACK_TEXT.get(logical_name, f"[missing asset: {logical_name}]")
    return Resolution(
        status="fallback",
        logical_name=logical_name,
        source_tier="text_fallback",
        asset_type="text",
        resolved_path=None,
        display_path=None,
        content_preview=fallback,
        blockers=tuple(blockers + ["no matching asset found in configured roots"]),
    )


def build_report(
    resolution: Resolution,
    repo_root: Path,
    sandbox_root: Path,
    write_report: bool,
) -> Dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "report_type": "asset_resolution_report",
        "generated_at": utc_now(),
        "status": resolution.status,
        "logical_name": resolution.logical_name,
        "source_tier": resolution.source_tier,
        "asset_type": resolution.asset_type,
        "display_path": resolution.display_path,
        "content_preview": resolution.content_preview,
        "blockers": list(resolution.blockers),
        "write_report": write_report,
        "roots": {
            "repo_root": str(repo_root.resolve()),
            "sandbox_root": str(sandbox_root.resolve()),
        },
        "boundaries": {
            "execution": "blocked",
            "repository_apply": "blocked",
            "git_operations": "blocked",
            "private_context_access": "blocked",
            "real_model_invocation": "blocked",
            "adapter_invocation": "blocked",
            "network_access": "blocked",
            "background_agents": "blocked",
        },
        "authority": {
            "asset_resolution_is_evidence_only": True,
            "asset_resolution_does_not_authorize_execution": True,
            "asset_resolution_does_not_close_mission": True,
        },
    }


def report_path_for(sandbox_root: Path, logical_name: str) -> Path:
    safe_name = logical_name.replace(".", "_").replace("-", "_")
    return sandbox_root / "reports" / f"{safe_name}{REPORT_SUFFIX}"


def write_report_file(report: Dict[str, object], sandbox_root: Path, logical_name: str, force: bool) -> Path:
    reports_dir = sandbox_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = report_path_for(sandbox_root, logical_name)
    if path.exists() and not force:
        raise FileExistsError(f"report already exists: {path}")
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve Konoha logical UI assets through local, user, public, and text fallback tiers."
    )
    parser.add_argument("--logical-name", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--sandbox-root", default="sandbox")
    parser.add_argument("--village-assets-root")
    parser.add_argument("--user-assets-root")
    parser.add_argument("--public-assets-root")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--show-private-paths", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    sandbox_root = Path(args.sandbox_root)
    village_root = Path(args.village_assets_root) if args.village_assets_root else None
    user_root = Path(args.user_assets_root) if args.user_assets_root else None
    public_root = Path(args.public_assets_root) if args.public_assets_root else None

    try:
        roots = default_asset_roots(repo_root, village_root, user_root, public_root)
        resolution = resolve_asset(args.logical_name, roots, args.show_private_paths)
        report = build_report(resolution, repo_root, sandbox_root, args.write_report)

        if args.write_report:
            path = write_report_file(report, sandbox_root, args.logical_name, args.force)
            report["report_path"] = str(path)

        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            if resolution.status == "resolved":
                print("ASSET RESOLUTION PASSED")
            else:
                print("ASSET RESOLUTION FALLBACK")
            print(f"Logical name: {resolution.logical_name}")
            print(f"Source tier: {resolution.source_tier}")
            print(f"Asset type: {resolution.asset_type}")
            if resolution.display_path:
                print(f"Display path: {resolution.display_path}")
            if resolution.content_preview:
                print("Preview:")
                print(resolution.content_preview)
            print("Execution: blocked")
            print("Repository apply: blocked")
            print("Git operations: blocked")
            print("Private context access: blocked")
            print("Real model invocation: blocked")
            print("Adapter invocation: blocked")
            print("Network access: blocked")
        return 0
    except Exception as exc:
        error_report = {
            "schema_version": "1.0.0",
            "report_type": "asset_resolution_report",
            "generated_at": utc_now(),
            "status": "failed",
            "logical_name": args.logical_name,
            "blockers": [str(exc)],
            "boundaries": {
                "execution": "blocked",
                "repository_apply": "blocked",
                "git_operations": "blocked",
                "private_context_access": "blocked",
                "real_model_invocation": "blocked",
                "adapter_invocation": "blocked",
                "network_access": "blocked",
                "background_agents": "blocked",
            },
        }
        if args.json:
            print(json.dumps(error_report, indent=2, sort_keys=True))
        else:
            print("ASSET RESOLUTION FAILED")
            print("Blocker:", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
