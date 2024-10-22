import logging

from fastapi.responses import HTMLResponse
from fastapi import Request, APIRouter

from medperf.account_management import get_medperf_user_data
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
from medperf.web_ui.common import templates, sort_associations_display

logger = logging.getLogger(__name__)

router = APIRouter()


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
    dataset.read_report()
    dataset.read_statistics()
    prep_cube = Cube.get(cube_uid=dataset.data_preparation_mlcube)

    benchmark_associations = Dataset.get_benchmarks_associations(dataset_uid=dataset_id)
    benchmark_associations = sort_associations_display(benchmark_associations)

    # Fetch models associated with each benchmark
    benchmark_models = {}
    for assoc in benchmark_associations:
        if assoc.approval_status != "APPROVED":
            continue  # if association is not approved we cannot list its models
        models_uids = Benchmark.get_models_uids(benchmark_uid=assoc.benchmark)
        models = [Cube.get(cube_uid=model_uid) for model_uid in models_uids]
        benchmark_models[assoc.benchmark] = models

    # Get all relevant benchmarks for association
    benchmarks = Benchmark.all()
    valid_benchmarks = {b.id: b for b in benchmarks if b.data_preparation_mlcube == dataset.data_preparation_mlcube}

    return templates.TemplateResponse(
        "dataset_detail.html",
        {
            "request": request,
            "entity": dataset,
            "entity_name": dataset.name,
            "prep_cube": prep_cube,
            "benchmark_associations": benchmark_associations,
            "benchmarks": valid_benchmarks,
            "benchmark_models": benchmark_models,  # Pass associated models without status
        }
    )

