# medperf/web-ui/benchmarks/routes.py
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.templating import Jinja2Templates

from medperf.entities.benchmark import Benchmark
from medperf.entities.cube import Cube
from medperf.account_management import get_medperf_user_data

router = APIRouter()
templates = Jinja2Templates(directory="medperf/web_ui/templates")
logger = logging.getLogger(__name__)


@router.get("/ui", response_class=HTMLResponse)
def benchmarks_ui(request: Request, local_only: bool = False, mine_only: bool = False):
    filters = {}
    if mine_only:
        filters["owner"] = get_medperf_user_data()["id"]

    benchmarks = Benchmark.all(
        local_only=local_only,
        filters=filters,
    )
    return templates.TemplateResponse("benchmarks.html", {"request": request, "benchmarks": benchmarks})


@router.get("/ui/{benchmark_id}", response_class=HTMLResponse)
def benchmark_detail_ui(request: Request, benchmark_id: int):
    benchmark = Benchmark.get(benchmark_id)
    data_preparation_mlcube = Cube.get(cube_uid=benchmark.data_preparation_mlcube)
    reference_model_mlcube = Cube.get(cube_uid=benchmark.reference_model_mlcube)
    metrics_mlcube = Cube.get(cube_uid=benchmark.data_evaluator_mlcube)

    return templates.TemplateResponse(
        "benchmark_detail.html",
        {
            "request": request,
            "benchmark": benchmark,
            "data_preparation_mlcube": data_preparation_mlcube,
            "reference_model_mlcube": reference_model_mlcube,
            "metrics_mlcube": metrics_mlcube
        }
    )
