from __future__ import annotations

from fastapi import APIRouter, Request

from tools.ui_server.routes.common import roots_from_request, templates
from tools.ui_server.services import report_service, safety_service, workspace_service

router = APIRouter()


@router.get("/")
def dashboard(request: Request):
    roots = roots_from_request(request)
    missions = workspace_service.list_missions(roots["workspace_root"])[:10]
    reports = report_service.list_reports(roots["sandbox_root"])[:10]
    boundaries = safety_service.boundaries()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "roots": roots,
            "missions": missions,
            "reports": reports,
            "boundaries": boundaries,
        },
    )
