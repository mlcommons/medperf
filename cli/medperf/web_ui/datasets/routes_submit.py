import medperf.config as config

from fastapi import Form, APIRouter, Depends
from medperf.exceptions import CleanExit
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse

from medperf.commands.dataset.submit import DataCreation
from medperf.entities.benchmark import Benchmark
from medperf.web_ui.common import templates, get_current_user_ui, get_current_user_api


router = APIRouter()


@router.post("/submit/submit", response_class=JSONResponse)
def generate_draft(
    benchmark: int = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    data_path: str = Form(...),
    labels_path: str = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        dataset_id = DataCreation.run(
            benchmark_uid=benchmark,
            prep_cube_uid=None,
            data_path=data_path,
            labels_path=labels_path,
            metadata_path=None,
            name=name,
            description=description,
            location=location,
            approved=False,
            submit_as_prepared=False,
        )
        return {"dataset_id": dataset_id}
    except CleanExit:
        return {"dataset_id": None}


@router.get("/event", response_class=JSONResponse)
def get_prompt(
    request: Request,
    current_user: bool = Depends(get_current_user_api),
):
    events = []
    event = config.ui.get_event()
    while event is not None:
        events.append(event)
        event = config.ui.get_event()
    return events


@router.post("/event")
def prompt(
    request: Request,
    is_approved: bool = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    config.ui.set_response({"value": is_approved})


@router.get("/submit/ui", response_class=HTMLResponse)
def create_dataset_ui(
    request: Request,
    current_user: bool = Depends(get_current_user_ui),
):
    # Fetch the list of benchmarks to populate the benchmark dropdown
    benchmarks = Benchmark.all()
    # Render the dataset creation form with the list of benchmarks
    return templates.TemplateResponse(
        "dataset/dataset_submit.html", {"request": request, "benchmarks": benchmarks}
    )
