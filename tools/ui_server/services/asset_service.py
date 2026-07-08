"""UI-facing asset resolution helpers.

This module intentionally wraps the read-only asset resolver. It gives the local
web UI a stable service boundary without granting new authority.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from tools.assets.resolve_asset import AssetRoot, default_asset_roots, resolve_asset


def resolve_ui_asset(
    logical_name: str,
    repo_root: Path,
    village_assets_root: Optional[Path] = None,
    user_assets_root: Optional[Path] = None,
    public_assets_root: Optional[Path] = None,
) -> Dict[str, object]:
    roots = default_asset_roots(
        repo_root=repo_root,
        village_assets_root=village_assets_root,
        user_assets_root=user_assets_root,
        public_assets_root=public_assets_root,
    )
    resolution = resolve_asset(logical_name, roots)
    return {
        "status": resolution.status,
        "logical_name": resolution.logical_name,
        "source_tier": resolution.source_tier,
        "asset_type": resolution.asset_type,
        "display_path": resolution.display_path,
        "content_preview": resolution.content_preview,
        "authority": {
            "asset_resolution_is_evidence_only": True,
            "ui_display_does_not_authorize_execution": True,
        },
    }
