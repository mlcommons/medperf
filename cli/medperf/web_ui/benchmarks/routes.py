import logging

import anyio

from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request
from typing import Optional

from medperf.commands.benchmark.submit import SubmitBenchmark
from medperf.commands.execution.utils import filter_latest_executions
from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.entities.cube import Cube
from medperf.entities.model import Model
from medperf.account_management import get_medperf_user_data
from medperf.entities.execution import Execution
from medperf.web_ui.common import (
    check_user_api,
    UITask,
    templates,
    sort_associations_display,
    check_user_ui,
)
from medperf.web_ui.listing import fetch_listing_page

from medperf.commands.association.approval import Approval
from medperf.enums import Status
from medperf.commands.benchmark.update_associations_poilcy import (
    UpdateAssociationsPolicy,
)
from medperf.commands.benchmark.update_committee_members import UpdateCommitteeMembers

from medperf.web_ui.utils import mount_dashboard

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ui", response_class=HTMLResponse)
def benchmarks_ui(
    request: Request,
    mine_only: bool = False,
    page: int = 1,
    page_size: int = 9,
    ordering: str = "created_at_desc",
    search: Optional[str] = None,
    current_user: bool = Depends(check_user_ui),
):
    my_user_id = get_medperf_user_data()["id"]
    benchmarks, search_query, pagination_context = fetch_listing_page(
        Benchmark,
        page=page,
        page_size=page_size,
        ordering=ordering,
        mine_only=mine_only,
        my_user_id=my_user_id,
        search=search,
    )

    return templates.TemplateResponse(
        "benchmark/benchmarks.html",
        {
            "request": request,
            "benchmarks": benchmarks,
            "mine_only": mine_only,
            "search_query": search_query,
            **pagination_context,
        },
    )


def _results_with_data_owners(benchmark_id: int) -> list:
    """Latest results of the benchmark, each with the email of its data owner
    (or "Hidden" when the owner didn't share it)."""
    results = filter_latest_executions(
        Execution.all(filters={"benchmark": benchmark_id})
    )
    owners_emails = {
        dataset["id"]: dataset["owner"]["email"]
        for dataset in Benchmark.get_datasets_with_users(benchmark_id)
    }
    for result in results:
        result.data_owner_email = owners_emails.get(result.dataset, "Hidden")
    return results


def _benchmark_management_context(benchmark_id: int) -> dict:
    """What the benchmark managers see: the dataset and model associations
    (sorted for display, with the associated entities) and the results."""
    datasets_associations = Benchmark.get_datasets_associations(
        benchmark_uid=benchmark_id
    )
    models_associations = Benchmark.get_models_associations(benchmark_uid=benchmark_id)
    datasets_associations = sort_associations_display(datasets_associations)
    models_associations = sort_associations_display(models_associations)
    return {
        "datasets_associations": datasets_associations,
        "models_associations": models_associations,
        "dataset_assoc_pending": any(
            assoc["approval_status"] == "PENDING" for assoc in datasets_associations
        ),
        "model_assoc_pending": any(
            assoc["approval_status"] == "PENDING" for assoc in models_associations
        ),
        "datasets": {
            assoc["dataset"]: Dataset.get(assoc["dataset"])
            for assoc in datasets_associations
            if assoc["dataset"]
        },
        "models": {
            assoc["model"]: Model.get(assoc["model"])
            for assoc in models_associations
            if assoc["model"]
        },
        "results": _results_with_data_owners(benchmark_id),
    }


@router.get("/ui/display/{benchmark_id}", response_class=HTMLResponse)
def benchmark_detail_ui(
    request: Request,
    benchmark_id: int,
    current_user: bool = Depends(check_user_ui),
):
    benchmark = Benchmark.get(benchmark_id)
    can_manage = benchmark.user_can_manage()

    context = {
        "request": request,
        "entity": benchmark,
        "entity_name": benchmark.name,
        "data_preparation_container": Cube.get(
            cube_uid=benchmark.data_preparation_mlcube
        ),
        "reference_model": Model.get(benchmark.reference_model),
        "metrics_container": Cube.get(cube_uid=benchmark.data_evaluator_mlcube),
        "current_user_is_benchmark_owner": benchmark.owner
        == get_medperf_user_data()["id"],
        "current_user_can_manage_benchmark": can_manage,
        # Only benchmark managers see the associations and results
        "datasets_associations": [],
        "models_associations": [],
        "dataset_assoc_pending": False,
        "model_assoc_pending": False,
        "datasets": {},
        "models": {},
        "results": [],
    }
    if can_manage:
        context.update(_benchmark_management_context(benchmark_id))

    return templates.TemplateResponse("benchmark/benchmark_detail.html", context)


@router.get("/register/ui", response_class=HTMLResponse)
def create_benchmark_ui(
    request: Request,
    current_user: bool = Depends(check_user_ui),
):
    return templates.TemplateResponse(
        "benchmark/register_benchmark.html",
        {"request": request},
    )


@router.post("/register", response_class=JSONResponse)
def register_benchmark(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    reference_dataset_tarball_url: str = Form(""),
    data_preparation_container: str = Form(...),
    reference_model: str = Form(...),
    evaluator_container: str = Form(...),
    skip_data_preparation_step: bool = Form(...),
    skip_compatibility_tests: bool = Form(...),
    current_user: bool = Depends(check_user_api),
):

    benchmark_info = {
        "name": name,
        "description": description,
        "docs_url": "",
        "demo_dataset_tarball_url": reference_dataset_tarball_url,
        "demo_dataset_tarball_hash": "",
        "data_preparation_mlcube": data_preparation_container,
        "reference_model": reference_model,
        "data_evaluator_mlcube": evaluator_container,
        "state": "OPERATION",
    }
    benchmark_id = None
    with UITask(request, "register_benchmark", response={"entity_id": None}) as task:
        benchmark_id = SubmitBenchmark.run(
            benchmark_info,
            skip_data_preparation_step=skip_data_preparation_step,
            skip_compatibility_tests=skip_compatibility_tests,
        )
        task.response["entity_id"] = benchmark_id
    task.notify(
        success_message="Benchmark successfully registered!",
        failure_message="Failed to register benchmark",
        url=f"/benchmarks/ui/display/{benchmark_id}" if benchmark_id else "",
    )
    return task.response


@router.post("/approve", response_class=JSONResponse)
def approve(
    request: Request,
    benchmark_id: int = Form(...),
    model_id: Optional[int] = Form(None),
    dataset_id: Optional[int] = Form(None),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "approve_association") as task:
        Approval.run(
            benchmark_uid=benchmark_id,
            approval_status=Status.APPROVED,
            dataset_uid=dataset_id,
            model_uid=model_id,
        )
    task.notify(
        success_message="Association successfully approved",
        failure_message="Failed to approve association",
        url=f"/benchmarks/ui/display/{benchmark_id}",
    )
    return task.response


@router.post("/reject", response_class=JSONResponse)
def reject(
    request: Request,
    benchmark_id: int = Form(...),
    model_id: Optional[int] = Form(None),
    dataset_id: Optional[int] = Form(None),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "reject_association") as task:
        Approval.run(
            benchmark_uid=benchmark_id,
            approval_status=Status.REJECTED,
            dataset_uid=dataset_id,
            model_uid=model_id,
        )
    task.notify(
        success_message="Association successfully rejected",
        failure_message="Failed to reject association",
        url=f"/benchmarks/ui/display/{benchmark_id}",
    )
    return task.response


@router.post("/update_associations_policy", response_class=JSONResponse)
def update_associations_policy(
    request: Request,
    benchmark_id: int = Form(...),
    dataset_mode: Optional[str] = Form(None),
    model_mode: Optional[str] = Form(None),
    current_user: bool = Depends(check_user_api),
):
    # dataset_emails/model_emails are read from the raw form instead of via
    # FastAPI's Form(None): an empty-string value there is indistinguishable
    # from the field being absent, which breaks "explicitly clear the allow
    # list" (as opposed to "the field wasn't part of this submission at all").
    form_data = anyio.from_thread.run(lambda: request.form())
    dataset_emails = form_data.get("dataset_emails")
    model_emails = form_data.get("model_emails")

    with UITask(request, "update_associations_policy") as task:
        UpdateAssociationsPolicy.run(
            benchmark_uid=benchmark_id,
            dataset_mode=dataset_mode,
            dataset_emails=dataset_emails,
            model_mode=model_mode,
            model_emails=model_emails,
        )
    task.notify(
        success_message="Associations policy updated",
        failure_message="Failed to update associations policy",
        url=f"/benchmarks/ui/display/{benchmark_id}",
    )
    return task.response


@router.post("/update_committee_members", response_class=JSONResponse)
def update_committee_members(
    request: Request,
    benchmark_id: int = Form(...),
    committee_emails: str = Form(""),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "update_committee_members") as task:
        UpdateCommitteeMembers.run(
            benchmark_uid=benchmark_id,
            committee_emails=committee_emails,
        )
    task.notify(
        success_message="Committee members updated",
        failure_message="Failed to update committee members",
        url=f"/benchmarks/ui/display/{benchmark_id}",
    )
    return task.response


@router.post("/ui/dashboard", response_class=HTMLResponse)
def preparation_dashboard(
    request: Request,
    benchmark_id: int = Form(...),
    benchmark_name: str = Form(...),
    stages: str = Form(...),
    institutions: str = Form(...),
    force_update: bool = Form(False),
    current_user: bool = Depends(check_user_ui),
):
    errors = False
    error_message = "Failed to load dashboard: "

    benchmark = Benchmark.get(benchmark_id)
    can_manage = benchmark.user_can_manage()
    if not can_manage:
        errors = True
        error_message += (
            "Only the benchmark owner or committee members can access the dashboard."
        )

    try:
        if not errors:
            mount_dashboard(request, benchmark_id, stages, institutions, force_update)
    except Exception as exp:
        logger.exception(exp)
        errors = True
        error_message += str(exp)

    if errors:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "exception": error_message,
            },
        )

    return templates.TemplateResponse(
        "dashboard_wrapper.html",
        {
            "request": request,
            "mount_point": f"/ui/display/{benchmark_id}/dashboard/app",
            "benchmark_id": benchmark_id,
            "prev_url": f"/benchmarks/ui/display/{benchmark_id}/",
            "benchmark_name": benchmark_name,
        },
    )
