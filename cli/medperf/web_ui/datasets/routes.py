import logging

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse
from fastapi import Request

from medperf.account_management import get_medperf_user_data
from medperf.commands.dataset.submit import DataCreation
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
from medperf.web_ui.common import templates, sort_associations_display

router = APIRouter()
logger = logging.getLogger(__name__)


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


@router.post("/create", response_class=HTMLResponse)
async def create_dataset(
        request: Request,
        benchmark: int = Form(...),
        name: str = Form(...),
        description: str = Form(...),
        location: str = Form(...),
        data_path: str = Form(...),
        labels_path: str = Form(...)
):
    # Run the dataset creation logic using the CLI method
    DataCreation.run(
        benchmark_uid=benchmark,
        prep_cube_uid=None,
        data_path=data_path,
        labels_path=labels_path,
        name=name,
        description=description,
        location=location
    )
    return templates.TemplateResponse("success.html", {"request": request})
