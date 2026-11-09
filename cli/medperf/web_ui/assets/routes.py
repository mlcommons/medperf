from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from medperf.entities.asset import Asset
from medperf.commands.asset.submit import SubmitAsset
from medperf.entities.model import Model

from medperf.web_ui.common import (
    check_user_api,
    UITask,
    templates,
    check_user_ui,
    sanitize_redirect_url,
)

router = APIRouter()


@router.get("/ui/display/{asset_id}", response_class=HTMLResponse)
def asset_detail_ui(
    request: Request,
    asset_id: int,
    current_user: bool = Depends(check_user_ui),
):
    asset = Asset.get(asset_id)

    if asset.is_model():
        model = Model.get_by_asset(asset_id)
        redirect_url = sanitize_redirect_url(f"/models/ui/display/{model.id}")
        return RedirectResponse(url=redirect_url)


@router.get("/register/ui", response_class=HTMLResponse)
def create_asset_ui(
    request: Request,
    current_user: bool = Depends(check_user_ui),
):

    return templates.TemplateResponse(
        "asset/register_asset.html",
        {"request": request},
    )


@router.post("/register", response_class=JSONResponse)
def register_asset(
    request: Request,
    name: str = Form(...),
    asset_url: str = Form(None),
    asset_is_remote: bool = Form(...),
    asset_path: str = Form(None),
    current_user: bool = Depends(check_user_api),
):
    asset_id = None
    with UITask(
        request, "asset_registration", response={"asset_id": None, "entity_id": None}
    ) as task:
        asset_id = SubmitAsset.run(
            name,
            asset_path=asset_path,
            asset_url=asset_url,
            operational=True,
        )
        task.response["asset_id"] = asset_id
        task.response["entity_id"] = asset_id
    task.notify(
        success_message="Asset successfully registered",
        failure_message="Failed to register asset",
        url=f"/assets/ui/display/{asset_id}" if asset_id else "",
    )
    return task.response
