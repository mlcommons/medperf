import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.templating import Jinja2Templates

from medperf.entities.cube import Cube
from medperf.account_management import get_medperf_user_data

router = APIRouter()
templates = Jinja2Templates(directory="medperf/web_ui/templates")
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
