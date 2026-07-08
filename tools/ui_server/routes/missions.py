from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from tools.ui_server.routes.common import roots_from_request, templates
from tools.ui_server.services import command_service, workspace_service

router = APIRouter(prefix="/missions")


@router.get("")
def missions_index(request: Request):
    roots = roots_from_request(request)
    missions = workspace_service.list_missions(roots["workspace_root"])
    return templates.TemplateResponse(
        request,
        "missions.html",
        {"request": request, "roots": roots, "missions": missions},
    )


@router.post("/new")
def mission_new(
    request: Request,
    mission_id: str = Form(...),
    title: str = Form(...),
    scope: str = Form(...),
):
    roots = roots_from_request(request)
    workspace_service.create_mission_workspace(
        workspace_root=roots["workspace_root"],
        mission_id=mission_id,
        title=title,
        scope=scope,
        force=False,
    )
    return RedirectResponse(url=f"/missions/{mission_id}", status_code=303)


@router.get("/{mission_id}")
def mission_detail(request: Request, mission_id: str):
    roots = roots_from_request(request)
    detail = workspace_service.inspect_mission(roots["workspace_root"], mission_id)
    commands = command_service.suggest_commands(
        repo_root=roots["repo_root"],
        workspace_root=roots["workspace_root"],
        sandbox_root=roots["sandbox_root"],
        mission_id=mission_id,
    )
    return templates.TemplateResponse(
        request,
        "mission_detail.html",
        {
            "request": request,
            "roots": roots,
            "mission": detail,
            "commands": commands,
        },
    )
