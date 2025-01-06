import medperf.config as config
from dataclasses import dataclass

from typing import Dict

from fastapi import Form, APIRouter, Depends
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, HTMLResponse

from medperf.commands.dataset.submit import DataCreation
from medperf.entities.benchmark import Benchmark
from medperf.web_ui.common import templates, get_current_user_ui, get_current_user_api

import asyncio  # noqa


@dataclass
class _DatasetDraft:
    preparation: DataCreation
    submission_dict: dict
    draft_id: str


router = APIRouter()

_drafts: Dict[str, _DatasetDraft] = {}


@router.post("/submit/generate", response_class=JSONResponse)
async def generate_draft(
    benchmark: int = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    data_path: str = Form(...),
    labels_path: str = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    import threading

    def p():
        DataCreation.run(
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

    threading.Thread(target=p).start()


@router.get("/event", response_class=JSONResponse)
async def get_prompt(
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
async def prompt(
    request: Request,
    is_approved: bool = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    config.ui.set_response({"value": is_approved})


@router.get("/submit/submit", response_class=RedirectResponse)
async def submit_draft(
    draft_id: str,
    current_user: bool = Depends(get_current_user_api),
):
    draft = _drafts[draft_id]
    preparation = draft.preparation
    preparation.approved = True

    updated_dataset_dict = preparation.upload()
    preparation.to_permanent_path(updated_dataset_dict)
    preparation.write(updated_dataset_dict)
    dataset_id = updated_dataset_dict["id"]
    return RedirectResponse(f"/datasets/ui/display/{dataset_id}")


@router.get("/submit/decline", response_class=RedirectResponse)
async def decline_draft(
    draft_id: str,
    current_user: bool = Depends(get_current_user_api),
):
    del _drafts[draft_id]
    return RedirectResponse("/datasets/ui")


@router.get("/submit/ui", response_class=HTMLResponse)
async def create_dataset_ui(
    request: Request,
    current_user: bool = Depends(get_current_user_ui),
):
    # Fetch the list of benchmarks to populate the benchmark dropdown
    benchmarks = Benchmark.all()
    # Render the dataset creation form with the list of benchmarks
    return templates.TemplateResponse(
        "dataset/dataset_submit.html", {"request": request, "benchmarks": benchmarks}
    )
