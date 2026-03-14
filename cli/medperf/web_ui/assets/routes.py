import logging

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from medperf.entities.asset import Asset
from medperf.commands.asset.submit import SubmitAsset
from medperf.entities.model import Model

import medperf.config as config
from medperf.web_ui.common import (
    check_user_api,
    initialize_state_task,
    reset_state_task,
    templates,
    check_user_ui,
    sanitize_redirect_url,
)

router = APIRouter()
logger = logging.getLogger(__name__)


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
    initialize_state_task(request, task_name="asset_registration")

    return_response = {"status": "", "error": "", "asset_id": None}
    asset_id = None
    try:
        asset_id = SubmitAsset.run(
            name,
            asset_path=asset_path,
            asset_url=asset_url,
            operational=True,
        )
        return_response["status"] = "success"
        return_response["asset_id"] = asset_id
        notification_message = "Asset successfully registered"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to register asset"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/assets/ui/display/{asset_id}" if asset_id else "",
    )
    return return_response
