from fastapi import Form, APIRouter, Depends
from fastapi.responses import JSONResponse

import medperf.config as config
from medperf.web_ui.common import (
    get_current_user_api,
)

router = APIRouter()


@router.get("/events", response_class=JSONResponse)
def get_event(
    current_user: bool = Depends(get_current_user_api),
):
    return config.ui.get_event()


@router.post("/events")
def respond(
    is_approved: bool = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    config.ui.set_response({"value": is_approved})
