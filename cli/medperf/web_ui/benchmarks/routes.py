import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request

from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.entities.cube import Cube
from medperf.account_management import get_medperf_user_data
from medperf.web_ui.common import templates, sort_associations_display, get_profiles_context

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ui", response_class=HTMLResponse)
def benchmarks_ui(request: Request, mine_only: bool = False):
    filters = {}
    my_user_id = get_medperf_user_data()["id"]
    if mine_only:
        filters["owner"] = my_user_id

    benchmarks = Benchmark.all(
        filters=filters,
    )

    benchmarks = sorted(benchmarks, key=lambda x: x.created_at, reverse=True)
    # sort by (mine recent) (mine oldish), (other recent), (other oldish)
    mine_benchmarks = [d for d in benchmarks if d.owner == my_user_id]
    other_benchmarks = [d for d in benchmarks if d.owner != my_user_id]
    benchmarks = mine_benchmarks + other_benchmarks
    profile_context = get_profiles_context()
    return templates.TemplateResponse("benchmarks.html", {"request": request, "benchmarks": benchmarks, **profile_context})


@router.get("/ui/{benchmark_id}", response_class=HTMLResponse)
def benchmark_detail_ui(request: Request, benchmark_id: int):
    benchmark = Benchmark.get(benchmark_id)
    data_preparation_mlcube = Cube.get(cube_uid=benchmark.data_preparation_mlcube)
    reference_model_mlcube = Cube.get(cube_uid=benchmark.reference_model_mlcube)
    metrics_mlcube = Cube.get(cube_uid=benchmark.data_evaluator_mlcube)
    datasets_associations = Benchmark.get_datasets_associations(benchmark_uid=benchmark_id)
    models_associations = Benchmark.get_models_associations(benchmark_uid=benchmark_id)

    datasets_associations = sort_associations_display(datasets_associations)
    models_associations = sort_associations_display(models_associations)

    datasets = {assoc.dataset: Dataset.get(assoc.dataset) for assoc in datasets_associations if assoc.dataset}
    models = {assoc.model_mlcube: Cube.get(assoc.model_mlcube) for assoc in models_associations if assoc.model_mlcube}

    profile_context = get_profiles_context()

    return templates.TemplateResponse(
        "benchmark_detail.html",
        {
            "request": request,
            "entity": benchmark,
            "entity_name": benchmark.name,
            "data_preparation_mlcube": data_preparation_mlcube,
            "reference_model_mlcube": reference_model_mlcube,
            "metrics_mlcube": metrics_mlcube,
            "datasets_associations": datasets_associations,
            "models_associations": models_associations,
            "datasets": datasets,
            "models": models,
            **profile_context
        }
    )
