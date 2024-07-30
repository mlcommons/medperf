import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request

from medperf.entities.cube import Cube
from medperf.account_management import get_medperf_user_data
from medperf.web_ui.common import templates

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ui", response_class=HTMLResponse)
def mlcubes_ui(request: Request, local_only: bool = False, mine_only: bool = False):
    filters = {}
    if mine_only:
        filters["owner"] = get_medperf_user_data()["id"]

    mlcubes = Cube.all(
        local_only=local_only,
        filters=filters,
    )
    return templates.TemplateResponse("mlcubes.html", {"request": request, "mlcubes": mlcubes})


@router.get("/ui/{mlcube_id}", response_class=HTMLResponse)
def mlcube_detail_ui(request: Request, mlcube_id: int):
    mlcube = Cube.get(cube_uid=mlcube_id, valid_only=False)
    return templates.TemplateResponse("mlcube_detail.html", {"request": request, "mlcube": mlcube})
