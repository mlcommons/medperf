# ./cli/medperf/web-ui/datasets/routes.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import List
from fastapi import Request
from fastapi.templating import Jinja2Templates

from medperf.account_management import get_medperf_user_data
from medperf.entities.dataset import Dataset

router = APIRouter()

templates = Jinja2Templates(directory="medperf/web_ui/templates")


@router.get("/", response_model=List[Dataset])
def get_datasets(local_only: bool = False, mine_only: bool = False):
    # try:
    filters = {}
    if mine_only:
        filters["owner"] = get_medperf_user_data()["id"]

    return Dataset.all(
        local_only=local_only,
        filters=filters,
    )
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))


@router.get("/ui", response_class=HTMLResponse)
def datasets_ui(request: Request):
    return templates.TemplateResponse("datasets.html", {"request": request})
