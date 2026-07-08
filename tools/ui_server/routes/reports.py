from __future__ import annotations

from fastapi import APIRouter, Request

from tools.ui_server.routes.common import roots_from_request, templates
from tools.ui_server.services import report_service

router = APIRouter(prefix="/reports")


@router.get("")
def reports_index(request: Request):
    roots = roots_from_request(request)
    reports = report_service.list_reports(roots["sandbox_root"])
    return templates.TemplateResponse(
        request,
        "reports.html",
        {"request": request, "roots": roots, "reports": reports},
    )
