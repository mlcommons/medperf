import logging
import uuid
from dataclasses import dataclass
from typing import Dict

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse
from fastapi import Request
from starlette.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from medperf.account_management import get_medperf_user_data
from medperf.commands.dataset.submit import DataCreation
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
from medperf.web_ui.common import templates, sort_associations_display

router = APIRouter()
logger = logging.getLogger(__name__)


@dataclass
class _DatasetDraft:
    preparation: DataCreation
    submission_dict: dict
    draft_id: str


# stores some draft data for the dataset creation form
_drafts: Dict[str, _DatasetDraft] = {}


@router.get("/ui", response_class=HTMLResponse)
def datasets_ui(request: Request, mine_only: bool = False):
    filters = {}
    my_user_id = get_medperf_user_data()["id"]
    if mine_only:
        filters["owner"] = my_user_id
    datasets = Dataset.all(
        filters=filters,
    )

    datasets = sorted(datasets, key=lambda x: x.created_at, reverse=True)
    # sort by (mine recent) (mine oldish), (other recent), (other oldish)
    mine_datasets = [d for d in datasets if d.owner == my_user_id]
    other_datasets = [d for d in datasets if d.owner != my_user_id]
    datasets = mine_datasets + other_datasets
    return templates.TemplateResponse("datasets.html", {"request": request, "datasets": datasets})


@router.get("/ui/display/{dataset_id}", response_class=HTMLResponse)
def dataset_detail_ui(request: Request, dataset_id: int):
    dataset = Dataset.get(dataset_id)

    prep_cube = Cube.get(cube_uid=dataset.data_preparation_mlcube)

    benchmark_associations = Dataset.get_benchmarks_associations(dataset_uid=dataset_id)
    benchmark_associations = sort_associations_display(benchmark_associations)

    benchmarks = {assoc.benchmark: Benchmark.get(assoc.benchmark) for assoc in benchmark_associations if
                  assoc.benchmark}

    return templates.TemplateResponse("dataset_detail.html",
                                      {
                                          "request": request,
                                          "entity": dataset,
                                          "entity_name": dataset.name,
                                          "prep_cube": prep_cube,
                                          "benchmark_associations": benchmark_associations,
                                          "benchmarks": benchmarks
                                      })


@router.get("/ui/create", response_class=HTMLResponse)
def create_dataset_ui(request: Request):
    # Fetch the list of benchmarks to populate the benchmark dropdown
    benchmarks = Benchmark.all()
    # Render the dataset creation form with the list of benchmarks
    return templates.TemplateResponse("create_dataset.html", {"request": request, "benchmarks": benchmarks})


@router.post("/draft/generate", response_class=JSONResponse)
async def generate_draft(
        benchmark: int = Form(...),
        name: str = Form(...),
        description: str = Form(...),
        location: str = Form(...),
        data_path: str = Form(...),
        labels_path: str = Form(...)
):
    draft_id = str(uuid.uuid4())
    # Run the dataset creation logic using the CLI method
    preparation = DataCreation(
        benchmark_uid=benchmark,
        prep_cube_uid=None,
        data_path=data_path,
        labels_path=labels_path,
        metadata_path=None,  # metadata_path,
        name=name,
        description=description,
        location=location,
        approved=False,
        submit_as_prepared=False,
        for_test=False,
    )
    submission_dict = preparation.prepare_dict(False)
    draft = _DatasetDraft(
        preparation=preparation,
        submission_dict=submission_dict,
        draft_id=draft_id
    )
    _drafts[draft_id] = draft

    return {"data": draft.submission_dict, "draft_id": draft.draft_id}


@router.get("/draft/submit", response_class=RedirectResponse)
async def submit_draft(
        draft_id: str,
):
    draft = _drafts[draft_id]
    preparation = draft.preparation
    preparation.approved = True

    updated_dataset_dict = preparation.upload()
    preparation.to_permanent_path(updated_dataset_dict)
    preparation.write(updated_dataset_dict)
    dataset_id = updated_dataset_dict["id"]
    return RedirectResponse(f"/datasets/ui/display/{dataset_id}")


@router.get("/draft/decline", response_class=RedirectResponse)
async def decline_draft(draft_id: str):
    del _drafts[draft_id]
    return RedirectResponse("/datasets/ui")
