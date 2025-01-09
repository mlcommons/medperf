from medperf.exceptions import CleanExit
from fastapi import APIRouter, Depends, Form
from starlette.responses import JSONResponse

from medperf import config
from medperf.commands.dataset.set_operational import DatasetSetOperational
from medperf.web_ui.common import get_current_user_api


router = APIRouter()


@router.post("/set_operational/", response_class=JSONResponse)
def set_operational(
    dataset_id: int = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        dataset_id = DatasetSetOperational.run(dataset_id)
        config.ui.set_success()
        return {"dataset_id": dataset_id}
    except CleanExit:
        config.ui.set_error()
        return {"dataset_id": None}


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
