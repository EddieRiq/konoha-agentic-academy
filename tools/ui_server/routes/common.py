"""Shared UI route helpers."""

from __future__ import annotations

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates


UI_ROOT = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(UI_ROOT / "templates"))


def roots_from_request(request: Request) -> dict:
    return {
        "repo_root": request.app.state.repo_root,
        "workspace_root": request.app.state.workspace_root,
        "sandbox_root": request.app.state.sandbox_root,
    }
