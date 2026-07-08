from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from tools.ui_server.routes.common import roots_from_request, templates
from tools.ui_server.services import approval_service, workspace_service

router = APIRouter(prefix="/approvals")


@router.get("/{mission_id}")
def approvals_page(request: Request, mission_id: str):
    roots = roots_from_request(request)
    mission = workspace_service.inspect_mission(roots["workspace_root"], mission_id)
    events = approval_service.list_approval_events(roots["workspace_root"], mission_id)
    return templates.TemplateResponse(
        request,
        "approvals.html",
        {
            "request": request,
            "roots": roots,
            "mission": mission,
            "events": events,
        },
    )


@router.post("/{mission_id}")
def record_approval(
    request: Request,
    mission_id: str,
    transition: str = Form(...),
    decision: str = Form(...),
    reason: str = Form(...),
    approval_token: str = Form(...),
):
    roots = roots_from_request(request)
    approval_service.record_decision(
        workspace_root=roots["workspace_root"],
        mission_id=mission_id,
        transition=transition,
        decision=decision,
        reason=reason,
        approval_token=approval_token,
    )
    return RedirectResponse(url=f"/approvals/{mission_id}", status_code=303)
