"""FastAPI app factory for the Konoha Local Web UI Alpha."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from tools.ui_server.routes import approvals, dashboard, missions, reports, system


def create_app(repo_root: Path, workspace_root: Path, sandbox_root: Path) -> FastAPI:
    app = FastAPI(
        title="Konoha Local Web UI Alpha",
        version="1.7.0",
        description="Local-only Konoha UI. Adds no new runtime authority.",
    )

    app.state.repo_root = repo_root
    app.state.workspace_root = workspace_root
    app.state.sandbox_root = sandbox_root

    ui_root = Path(__file__).resolve().parent
    app.mount("/static", StaticFiles(directory=str(ui_root / "static")), name="static")

    app.include_router(dashboard.router)
    app.include_router(missions.router)
    app.include_router(approvals.router)
    app.include_router(reports.router)
    app.include_router(system.router)

    return app
