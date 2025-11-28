import logging

from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request
from typing import Optional

from medperf.commands.benchmark.submit import SubmitBenchmark
from medperf.commands.compatibility_test.run import CompatibilityTestExecution
from medperf.commands.execution.utils import filter_latest_executions
import medperf.config as config
from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.entities.cube import Cube
from medperf.account_management import get_medperf_user_data
from medperf.entities.execution import Execution
from medperf.web_ui.common import (
    check_user_api,
    initialize_state_task,
    reset_state_task,
    templates,
    sort_associations_display,
    check_user_ui,
)
from medperf.web_ui.utils import get_container_type

from medperf.commands.association.approval import Approval
from medperf.enums import Status
from medperf.commands.benchmark.update_associations_poilcy import (
    UpdateAssociationsPolicy,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ui", response_class=HTMLResponse)
def benchmarks_ui(
    request: Request,
    mine_only: bool = False,
    current_user: bool = Depends(check_user_ui),
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
    current_user: bool = Depends(check_user_ui),
):
    benchmark = Benchmark.get(benchmark_id)
    data_preparation_container = Cube.get(cube_uid=benchmark.data_preparation_mlcube)
    reference_model_container = Cube.get(cube_uid=benchmark.reference_model_mlcube)
    metrics_container = Cube.get(cube_uid=benchmark.data_evaluator_mlcube)
    datasets_associations = []
    models_associations = []
    datasets = {}
    models = {}
    results = []
    dataset_assoc_pending = False
    model_assoc_pending = False
    current_user_is_benchmark_owner = benchmark.owner == get_medperf_user_data()["id"]
    if current_user_is_benchmark_owner:
        datasets_associations = Benchmark.get_datasets_associations(
            benchmark_uid=benchmark_id
        )
        dataset_assoc_pending = any(
            [i["approval_status"] == "PENDING" for i in datasets_associations]
        )
        models_associations = Benchmark.get_models_associations(
            benchmark_uid=benchmark_id
        )
        model_assoc_pending = any(
            [i["approval_status"] == "PENDING" for i in models_associations]
        )
        datasets_associations = sort_associations_display(datasets_associations)
        models_associations = sort_associations_display(models_associations)

        datasets = {
            assoc["dataset"]: Dataset.get(assoc["dataset"])
            for assoc in datasets_associations
            if assoc["dataset"]
        }
        models = {
            assoc["model_mlcube"]: Cube.get(assoc["model_mlcube"])
            for assoc in models_associations
            if assoc["model_mlcube"]
        }

        # Results
        results = Execution.all(filters={"benchmark": benchmark_id})
        results = filter_latest_executions(results)
        datasets_with_users = Benchmark.get_datasets_with_users(benchmark_id)
        id_to_email_mapping = {}
        for dataset in datasets_with_users:
            id_to_email_mapping[dataset["id"]] = dataset["owner"]["email"]

        for result in results:
            result.data_owner_email = id_to_email_mapping.get(result.dataset, "Hidden")

    return templates.TemplateResponse(
        "benchmark/benchmark_detail.html",
        {
            "request": request,
            "entity": benchmark,
            "entity_name": benchmark.name,
            "data_preparation_container": data_preparation_container,
            "reference_model_container": reference_model_container,
            "metrics_container": metrics_container,
            "datasets_associations": datasets_associations,  #
            "models_associations": models_associations,  #
            "datasets": datasets,
            "models": models,
            "current_user_is_benchmark_owner": current_user_is_benchmark_owner,
            "results": results,
            "dataset_assoc_pending": dataset_assoc_pending,
            "model_assoc_pending": model_assoc_pending,
        },
    )


@router.get("/register/ui", response_class=HTMLResponse)
def create_benchmark_ui(
    request: Request,
    current_user: bool = Depends(check_user_ui),
):

    my_user_id = get_medperf_user_data()["id"]
    filters = {"owner": my_user_id}

    my_containers = Cube.all(
        filters=filters,
    )

    containers = []

    for container in my_containers:
        container_obj = {
            "id": container.id,
            "name": container.name,
            "type": get_container_type(container),
        }
        containers.append(container_obj)
    data_prep_containers = [i for i in containers if i["type"] == "data-prep-container"]
    reference_containers = [i for i in containers if i["type"] == "reference-container"]
    metrics_containers = [i for i in containers if i["type"] == "metrics-container"]
    return templates.TemplateResponse(
        "benchmark/register_benchmark.html",
        {
            "request": request,
            "data_prep_containers": data_prep_containers,
            "reference_containers": reference_containers,
            "metrics_containers": metrics_containers,
        },
    )


@router.get("/register/workflow_test", response_class=HTMLResponse)
def workflow_test_ui(
    request: Request,
    current_user: bool = Depends(check_user_ui),
):

    return templates.TemplateResponse(
        "benchmark/workflow_test.html", {"request": request}
    )


@router.post("/run_workflow_test", response_class=JSONResponse)
def test_benchmark(
    request: Request,
    data_preparation: str = Form(...),
    model_path: str = Form(...),
    evaluator_path: str = Form(...),
    data_path: str = Form(...),
    labels_path: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="benchmark_workflow_test")
    return_response = {"status": "", "error": "", "results": None}
    try:
        _, results = CompatibilityTestExecution.run(
            data_prep=data_preparation,
            model=model_path,
            evaluator=evaluator_path,
            data_path=data_path,
            labels_path=labels_path,
        )
        return_response["status"] = "success"
        return_response["results"] = results
        notification_message = "Benchmark workflow test succeeded"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Benchmark workflow test failed"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url="/benchmarks/register/ui",
    )
    return return_response


@router.post("/register", response_class=JSONResponse)
def register_benchmark(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    reference_dataset_tarball_url: str = Form(...),
    data_preparation_container: str = Form(...),
    reference_model_container: str = Form(...),
    evaluator_container: str = Form(...),
    skip_data_preparation_step: bool = Form(...),
    current_user: bool = Depends(check_user_api),
):

    benchmark_info = {
        "name": name,
        "description": description,
        "docs_url": "",
        "demo_dataset_tarball_url": reference_dataset_tarball_url,
        "demo_dataset_tarball_hash": "",
        "data_preparation_mlcube": data_preparation_container,
        "reference_model_mlcube": reference_model_container,
        "data_evaluator_mlcube": evaluator_container,
        "state": "OPERATION",
    }
    initialize_state_task(request, task_name="benchmark_registration")
    return_response = {"status": "", "error": "", "benchmark_id": None}
    benchmark_id = None
    try:
        benchmark_id = SubmitBenchmark.run(
            benchmark_info, skip_data_preparation_step=skip_data_preparation_step
        )
        return_response["status"] = "success"
        return_response["benchmark_id"] = benchmark_id
        notification_message = "Benchmark successfully registered!"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to register benchmark"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/benchmarks/ui/display/{benchmark_id}" if benchmark_id else "",
    )
    return return_response


@router.post("/approve", response_class=JSONResponse)
def approve(
    request: Request,
    benchmark_id: int = Form(...),
    container_id: Optional[int] = Form(None),
    dataset_id: Optional[int] = Form(None),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="approve_association")
    return_response = {"status": "", "error": ""}
    try:
        Approval.run(
            benchmark_uid=benchmark_id,
            approval_status=Status.APPROVED,
            dataset_uid=dataset_id,
            mlcube_uid=container_id,
        )
        return_response["status"] = "success"
        notification_message = "Association successfully approved"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to approve association"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/benchmarks/ui/display/{benchmark_id}",
    )
    return return_response


@router.post("/reject", response_class=JSONResponse)
def reject(
    request: Request,
    benchmark_id: int = Form(...),
    container_id: Optional[int] = Form(None),
    dataset_id: Optional[int] = Form(None),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="reject_association")
    return_response = {"status": "", "error": ""}
    try:
        Approval.run(
            benchmark_uid=benchmark_id,
            approval_status=Status.REJECTED,
            dataset_uid=dataset_id,
            mlcube_uid=container_id,
        )
        return_response["status"] = "success"
        notification_message = "Association successfully rejected"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to reject association"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/benchmarks/ui/display/{benchmark_id}",
    )
    return return_response


@router.post("/update_associations_policy", response_class=JSONResponse)
def update_associations_policy(
    request: Request,
    benchmark_id: int = Form(...),
    dataset_mode: Optional[str] = Form(None),
    dataset_emails: Optional[str] = Form(None),
    model_mode: Optional[str] = Form(None),
    model_emails: Optional[str] = Form(None),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="update_associations_policy")
    return_response = {"status": "", "error": ""}
    try:
        UpdateAssociationsPolicy.run(
            benchmark_uid=benchmark_id,
            dataset_mode=dataset_mode,
            dataset_emails=dataset_emails,
            model_mode=model_mode,
            model_emails=model_emails,
        )
        return_response["status"] = "success"
        notification_message = "Associations policy updated"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to update associations policy"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/benchmarks/ui/display/{benchmark_id}",
    )
    return return_response
