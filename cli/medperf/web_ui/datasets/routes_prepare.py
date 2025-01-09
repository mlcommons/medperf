from fastapi import APIRouter, Depends, Form
from medperf.exceptions import CleanExit
from starlette.responses import JSONResponse

from medperf.commands.dataset.prepare import DataPreparation
from medperf.web_ui.common import get_current_user_api
import medperf.config as config

router = APIRouter()


@router.post("/prepare/prepare", response_class=JSONResponse)
def prepare(
    dataset_id: int = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        dataset_id = DataPreparation.run(dataset_id)
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
