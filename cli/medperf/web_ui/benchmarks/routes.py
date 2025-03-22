import logging

from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request
from typing import Optional

from medperf.commands.benchmark.submit import SubmitBenchmark
from medperf.commands.compatibility_test.run import CompatibilityTestExecution
import medperf.config as config
from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.entities.cube import Cube
from medperf.account_management import get_medperf_user_data
from medperf.exceptions import MedperfException
from medperf.web_ui.common import (
    get_current_user_api,
    templates,
    sort_associations_display,
    get_current_user_ui,
)

from medperf.commands.association.approval import Approval
from medperf.enums import Status

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ui", response_class=HTMLResponse)
def benchmarks_ui(
    request: Request,
    mine_only: bool = False,
    current_user: bool = Depends(get_current_user_ui),
):
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
    return templates.TemplateResponse(
        "benchmark/benchmarks.html",
        {"request": request, "benchmarks": benchmarks, "mine_only": mine_only},
    )


@router.get("/ui/display/{benchmark_id}", response_class=HTMLResponse)
def benchmark_detail_ui(
    request: Request,
    benchmark_id: int,
    current_user: bool = Depends(get_current_user_ui),
):
    benchmark = Benchmark.get(benchmark_id)
    data_preparation_mlcube = Cube.get(cube_uid=benchmark.data_preparation_mlcube)
    reference_model_mlcube = Cube.get(cube_uid=benchmark.reference_model_mlcube)
    metrics_mlcube = Cube.get(cube_uid=benchmark.data_evaluator_mlcube)
    datasets_associations = []
    models_associations = []
    datasets = {}
    models = {}
    current_user_is_benchmark_owner = benchmark.owner == get_medperf_user_data()["id"]
    if current_user_is_benchmark_owner:
        datasets_associations = Benchmark.get_datasets_associations(
            benchmark_uid=benchmark_id
        )
        models_associations = Benchmark.get_models_associations(
            benchmark_uid=benchmark_id
        )

        datasets_associations = sort_associations_display(datasets_associations)
        models_associations = sort_associations_display(models_associations)

        datasets = {
            assoc.dataset: Dataset.get(assoc.dataset)
            for assoc in datasets_associations
            if assoc.dataset
        }
        models = {
            assoc.model_mlcube: Cube.get(assoc.model_mlcube)
            for assoc in models_associations
            if assoc.model_mlcube
        }

    return templates.TemplateResponse(
        "benchmark/benchmark_detail.html",
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
            "current_user_is_benchmark_owner": current_user_is_benchmark_owner,
        },
    )


@router.get("/submit/ui", response_class=HTMLResponse)
def create_benchmark_ui(
    request: Request,
    current_user: bool = Depends(get_current_user_ui),
):

    return templates.TemplateResponse(
        "benchmark/benchmark_submit.html", {"request": request}
    )


@router.get("/submit/workflow_test", response_class=HTMLResponse)
def workflow_test_ui(
    request: Request,
    current_user: bool = Depends(get_current_user_ui),
):

    return templates.TemplateResponse(
        "benchmark/workflow_test.html", {"request": request}
    )


@router.post("/test", response_class=JSONResponse)
def test_benchmark(
    data_preparation: str = Form(...),
    model_path: str = Form(...),
    evaluator_path: str = Form(...),
    data_path: str = Form(...),
    labels_path: str = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        _, results = CompatibilityTestExecution.run(
            data_prep=data_preparation,
            model=model_path,
            evaluator=evaluator_path,
            data_path=data_path,
            labels_path=labels_path,
        )
        config.ui.set_success()
        return {"status": "success", "error": "", "results": results}
    except MedperfException as exp:
        config.ui.set_error()
        return {"status": "failed", "error": str(exp), "results": ""}


@router.post("/submit", response_class=JSONResponse)
def submit_benchmark(
    name: str = Form(...),
    description: str = Form(...),
    demo_url: str = Form(...),
    data_preparation_mlcube: str = Form(...),
    reference_model_mlcube: str = Form(...),
    evaluator_mlcube: str = Form(...),
    current_user: bool = Depends(get_current_user_api),
):

    benchmark_info = {
        "name": name,
        "description": description,
        "docs_url": "",
        "demo_dataset_tarball_url": demo_url,
        "demo_dataset_tarball_hash": "",
        "data_preparation_mlcube": data_preparation_mlcube,
        "reference_model_mlcube": reference_model_mlcube,
        "data_evaluator_mlcube": evaluator_mlcube,
        "state": "OPERATION",
    }
    try:
        benchmark_id = SubmitBenchmark.run(benchmark_info)
        config.ui.set_success()
        return {"status": "success", "benchmark_id": benchmark_id, "error": ""}
    except MedperfException as exp:
        config.ui.set_error()
        return {"status": "failed", "benchmark_id": None, "error": str(exp)}


@router.post("/approve", response_class=JSONResponse)
def approve(
    request: Request,
    benchmark_id: int = Form(...),
    mlcube_id: Optional[int] = Form(None),
    dataset_id: Optional[int] = Form(None),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        Approval.run(
            benchmark_uid=benchmark_id,
            approval_status=Status.APPROVED,
            dataset_uid=dataset_id,
            mlcube_uid=mlcube_id,
        )
        return {"status": "success", "error": ""}
    except MedperfException as exp:
        return {"status": "failed", "error": str(exp)}


@router.post("/reject", response_class=JSONResponse)
def reject(
    request: Request,
    benchmark_id: int = Form(...),
    mlcube_id: Optional[int] = Form(None),
    dataset_id: Optional[int] = Form(None),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        Approval.run(
            benchmark_uid=benchmark_id,
            approval_status=Status.REJECTED,
            dataset_uid=dataset_id,
            mlcube_uid=mlcube_id,
        )
        return {"status": "success", "error": ""}
    except MedperfException as exp:
        return {"status": "failed", "error": str(exp)}
