import logging
from typing import List

from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request, APIRouter, Depends, Form

from medperf import config
from medperf.account_management import get_medperf_user_data
from medperf.commands.dataset.associate import AssociateDataset
from medperf.commands.dataset.prepare import DataPreparation
from medperf.commands.dataset.set_operational import DatasetSetOperational
from medperf.commands.dataset.submit import DataCreation
from medperf.commands.result.create import BenchmarkExecution
from medperf.commands.result.submit import ResultSubmission
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
from medperf.entities.result import Result
from medperf.exceptions import MedperfException
from medperf.web_ui.common import (
    templates,
    get_current_user_ui,
    get_current_user_api,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/ui", response_class=HTMLResponse)
def datasets_ui(
    request: Request,
    mine_only: bool = False,
    current_user: bool = Depends(get_current_user_ui),
):
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
    return templates.TemplateResponse(
        "dataset/datasets.html",
        {"request": request, "datasets": datasets, "mine_only": mine_only},
    )


@router.get("/ui/display/{dataset_id}", response_class=HTMLResponse)
def dataset_detail_ui(
    request: Request,
    dataset_id: int,
    current_user: bool = Depends(get_current_user_ui),
):
    dataset = Dataset.get(dataset_id)
    dataset.read_report()
    dataset.read_statistics()
    prep_cube = Cube.get(cube_uid=dataset.data_preparation_mlcube)

    benchmark_assocs = Dataset.get_benchmarks_associations(dataset_uid=dataset_id)
    benchmark_associations = {}
    for assoc in benchmark_assocs:
        benchmark_associations[assoc.benchmark] = assoc
    # benchmark_associations = sort_associations_display(benchmark_associations)

    # Get all results
    if benchmark_assocs:
        user_id = get_medperf_user_data()["id"]
        results = Result.all(filters={"owner": user_id})
        results += Result.all(unregistered=True)

    # Fetch models associated with each benchmark
    benchmark_models = {}
    for assoc in benchmark_assocs:
        if assoc.approval_status != "APPROVED":
            continue  # if association is not approved we cannot list its models
        models_uids = Benchmark.get_models_uids(benchmark_uid=assoc.benchmark)
        models = [Cube.get(cube_uid=model_uid) for model_uid in models_uids]
        benchmark_models[assoc.benchmark] = models
        for model in models:
            if results:
                model.result = [
                    (
                        result.todict()
                        if result.benchmark == assoc.id
                        and result.dataset == assoc.dataset
                        and result.model == model.id
                        else None
                    )
                    for result in results
                ][0]
                # [0] just to be able to use list comprehension
            else:
                model.result = None

    # Get all relevant benchmarks for making an association
    benchmarks = Benchmark.all()
    valid_benchmarks = {
        b.id: b
        for b in benchmarks
        if b.data_preparation_mlcube == dataset.data_preparation_mlcube
    }
    for benchmark in valid_benchmarks:
        reference_model_mlcube = valid_benchmarks[benchmark].reference_model_mlcube
        valid_benchmarks[benchmark].reference_model_mlcube = Cube.get(
            cube_uid=reference_model_mlcube
        )

    dataset_is_operational = dataset.state == "OPERATION"
    dataset_is_prepared = dataset.submitted_as_prepared or dataset.is_ready()
    approved_benchmarks = [
        i
        for i in benchmark_associations
        if benchmark_associations[i].approval_status == "APPROVED"
    ]
    return templates.TemplateResponse(
        "dataset/dataset_detail.html",
        {
            "request": request,
            "dataset": dataset,
            "prep_cube": prep_cube,
            "dataset_is_prepared": dataset_is_prepared,
            "dataset_is_operational": dataset_is_operational,
            "benchmark_associations": benchmark_associations,
            "benchmarks": valid_benchmarks,  # Benchmarks that can be associated
            "benchmark_models": benchmark_models,  # Pass associated models without status
            "approved_benchmarks": approved_benchmarks,
        },
    )


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


@router.post("/submit/", response_class=JSONResponse)
def submit_dataset(
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
        config.ui.set_success()
        return {"status": "success", "dataset_id": dataset_id, "error": ""}
    except MedperfException as exp:
        config.ui.set_error()
        return {"status": "failed", "dataset_id": None, "error": str(exp)}


@router.post("/prepare", response_class=JSONResponse)
def prepare(
    dataset_id: int = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        dataset_id = DataPreparation.run(dataset_id)
        config.ui.set_success()
        return {"status": "success", "dataset_id": dataset_id, "error": ""}
    except MedperfException as exp:
        config.ui.set_error()
        return {"status": "failed", "dataset_id": None, "error": str(exp)}


@router.post("/set_operational", response_class=JSONResponse)
def set_operational(
    dataset_id: int = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        dataset_id = DatasetSetOperational.run(dataset_id)
        config.ui.set_success()
        return {"status": "success", "dataset_id": dataset_id, "error": ""}
    except MedperfException as exp:
        config.ui.set_error()
        return {"status": "failed", "dataset_id": None, "error": str(exp)}


@router.post("/associate", response_class=JSONResponse)
def associate(
    dataset_id: int = Form(...),
    benchmark_id: int = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        AssociateDataset.run(data_uid=dataset_id, benchmark_uid=benchmark_id)
        config.ui.set_success()
        return {"status": "success", "error": ""}
    except MedperfException as exp:
        config.ui.set_error()
        return {"status": "failed", "error": str(exp)}


@router.post("/run", response_class=JSONResponse)
def run(
    dataset_id: int = Form(...),
    benchmark_id: int = Form(...),
    model_ids: List[int] = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        BenchmarkExecution.run(benchmark_id, dataset_id, model_ids)
        config.ui.set_success()
        return {"status": "success", "error": ""}
    except MedperfException as exp:
        config.ui.set_error()
        return {"status": "failed", "error": str(exp)}


@router.post("/result_submit", response_class=JSONResponse)
def submit_result(
    result_id: str = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    try:
        ResultSubmission.run(result_id)
        config.ui.set_success()
        return {"status": "success", "error": ""}
    except MedperfException as exp:
        config.ui.set_error()
        return {"status": "failed", "error": str(exp)}
