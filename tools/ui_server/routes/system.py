from __future__ import annotations

import platform
import sys

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from tools.ui_server.routes.common import roots_from_request, templates
from tools.ui_server.services import report_service, safety_service, workspace_service

router = APIRouter(prefix="/system")


@router.get("")
def system_page(request: Request):
    roots = roots_from_request(request)
    checks = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "repo_root_exists": roots["repo_root"].exists(),
        "workspace_root_exists": roots["workspace_root"].exists(),
        "sandbox_root_exists": roots["sandbox_root"].exists(),
        "missions_dir_exists": (roots["workspace_root"] / "missions").exists(),
    }
    return templates.TemplateResponse(
        request,
        "system.html",
        {
            "request": request,
            "roots": roots,
            "checks": checks,
            "boundaries": safety_service.boundaries(),
        },
    )


@router.get("/healthz")
def healthz(request: Request):
    roots = roots_from_request(request)
    return JSONResponse(
        {
            "status": "ok",
            "ui": "local_web_ui_alpha",
            "repo_root_exists": roots["repo_root"].exists(),
            "workspace_root_exists": roots["workspace_root"].exists(),
            "sandbox_root_exists": roots["sandbox_root"].exists(),
            "execution": "blocked",
            "repository_apply": "blocked",
            "git_operations": "blocked",
            "private_context_access": "blocked",
            "real_model_invocation": "blocked",
            "network_access": "localhost_ui_only",
        }
    )


@router.post("/session-report")
def session_report(request: Request):
    roots = roots_from_request(request)
    payload = report_service.write_ui_session_report(
        sandbox_root=roots["sandbox_root"],
        workspace_root=roots["workspace_root"],
        mission_count=len(workspace_service.list_missions(roots["workspace_root"])),
    )
    return JSONResponse(payload)
