import logging

import anyio
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

from medperf.account_management import get_medperf_user_data, get_medperf_user_object
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.entities.model import Model
from medperf.entities.benchmark import Benchmark
from medperf.entities.user import User
from medperf.commands.model.associate import AssociateModel
from medperf.commands.mlcube.utils import check_access_to_container
from medperf.commands.cc.download_cc_results import DownloadCCResults
from medperf.commands.cc.model_configure_for_cc import ModelConfigureForCC
from medperf.commands.cc.model_update_cc_policy import ModelUpdateCCPolicy
from medperf.commands.execution.model_benchmark_run import ModelBenchmarkRun
from medperf.commands.execution.submit import ResultSubmission
from medperf.commands.execution.utils import filter_latest_executions
from medperf.cc.collector import collects_results
import medperf.config as config
from medperf.web_ui.common import (
    check_user_api,
    initialize_state_task,
    reset_state_task,
    templates,
    check_user_ui,
)
from typing import List, Optional

from medperf.web_ui.cc_forms import (
    backend_settings_from_form,
    service_settings,
    field_label,
    selected_backend,
)
from medperf.web_ui.listing import fetch_listing_page
from medperf_cc import asset_backends

router = APIRouter()
logger = logging.getLogger(__name__)


def cc_run_status(model: Model, dataset: Dataset, operator: User) -> dict:
    """Whether this model owner can run their model against this dataset.

    Three things have to be in place, and all three belong to somebody: the
    model's confidential settings and the machine to run on are this user's,
    the dataset's are the data owner's and nothing here can hurry them along.
    So an unmet one is named rather than left as a greyed-out button.
    """
    if not model.is_cc_configured():
        return {
            "can_run": False,
            "reason": "Your model is not configured for confidential computing yet",
        }
    if not dataset.is_cc_configured():
        return {
            "can_run": False,
            "reason": "Wait for the data owner to configure their dataset for CC",
        }
    if not operator.cc_operator.configured:
        return {
            "can_run": False,
            "reason": "You haven't configured your workload run settings for CC yet",
        }
    return {"can_run": True, "reason": ""}


def datasets_to_run(
    model: Model, benchmarks: dict, benchmark_uids: List[int], operator: User
) -> dict:
    """The datasets of each benchmark this model can be run against.

    The mirror of the dataset dashboard's list of models to run. Only reachable
    for a model that runs confidentially: for anything else the model owner has
    no business pointing their model at somebody else's data, and the server
    would not show them the datasets either.
    """
    user_executions = filter_latest_executions(
        Execution.all(filters={"owner": operator.id})
    )

    per_benchmark = {}
    for benchmark_uid in benchmark_uids:
        benchmark = benchmarks.get(benchmark_uid)
        datasets = [
            Dataset.get(data_uid)
            for data_uid in Benchmark.get_datasets_uids(benchmark_uid)
        ]
        for dataset in datasets:
            dataset.cc_run_status = cc_run_status(model, dataset, operator)
            # Whether a run of this pair would seal its results for this user.
            dataset.cc_can_collect = benchmark is not None and collects_results(
                operator.id, benchmark, dataset, model
            )
            dataset.result = __result_of(
                user_executions, benchmark_uid, model.id, dataset.id
            )
        per_benchmark[benchmark_uid] = datasets

    return per_benchmark


def __result_of(executions, benchmark_uid: int, model_uid: int, data_uid: int):
    """What this user holds for one (benchmark, model, dataset) triplet.

    A confidential run whose results were released to the data owner leaves the
    model owner an execution with nothing in it, so "there are results" means
    results they can actually read, not merely a finished run.
    """
    for execution in executions:
        if (
            execution.benchmark != benchmark_uid
            or execution.model != model_uid
            or execution.dataset != data_uid
        ):
            continue
        result = execution.todict()
        result["ran"] = execution.is_executed() or execution.finalized
        try:
            result["results"] = execution.read_results() if result["ran"] else {}
        except OSError:
            result["results"] = {}
        result["results_exist"] = bool(result["results"])
        return result
    return None


@router.get("/ui", response_class=HTMLResponse)
def models_ui(
    request: Request,
    mine_only: bool = False,
    page: int = 1,
    page_size: int = 9,
    ordering: str = "created_at_desc",
    search: Optional[str] = None,
    current_user: bool = Depends(check_user_ui),
):
    my_user_id = get_medperf_user_data()["id"]
    models, search_query, pagination_context = fetch_listing_page(
        Model,
        page=page,
        page_size=page_size,
        ordering=ordering,
        mine_only=mine_only,
        my_user_id=my_user_id,
        search=search,
    )

    return templates.TemplateResponse(
        "model/models.html",
        {
            "request": request,
            "models": models,
            "mine_only": mine_only,
            "search_query": search_query,
            **pagination_context,
        },
    )


@router.get("/ui/display/{model_id}", response_class=HTMLResponse)
def model_detail_ui(
    request: Request,
    model_id: int,
    current_user: bool = Depends(check_user_ui),
):
    model = Model.get(model_id, valid_only=False)

    benchmark_assocs = Model.get_benchmarks_associations(model_uid=model_id)

    benchmark_associations = {}
    for assoc in benchmark_assocs:
        benchmark_associations[assoc["benchmark"]] = assoc

    benchmarks = Benchmark.all()
    benchmarks = {b.id: b for b in benchmarks}
    # benchmarks_associations = sort_associations_display(benchmarks_associations)
    is_owner = model.owner == get_medperf_user_data()["id"]
    model._encrypted = model.is_encrypted()
    if model._encrypted:
        model.access_status = check_access_to_container(model.container.id)

    asset_object = None
    container_object = None
    if model.is_asset():
        asset_object = model.asset_obj
        asset_object._is_local = asset_object.is_local()
    else:
        container_object = model.container_obj

    cc_config_defaults = model.get_cc_config()
    cc_policy = model.get_cc_policy()
    cc_configured = model.is_cc_configured()
    cc_initialized = model.is_cc_initialized()
    cc_last_synced = model.get_last_synced()

    # Only a confidential model gives its owner somebody else's dataset to run.
    model._requires_cc = model.requires_cc()
    approved_benchmarks = [
        benchmark_uid
        for benchmark_uid, assoc in benchmark_associations.items()
        if assoc["approval_status"] == "APPROVED"
    ]
    benchmark_datasets = {}
    evaluating = request.app.state.ui_mode == request.app.state.EVALUATION_MODE
    if is_owner and model._requires_cc and evaluating:
        benchmark_datasets = datasets_to_run(
            model, benchmarks, approved_benchmarks, get_medperf_user_object()
        )

    return templates.TemplateResponse(
        "model/model_detail.html",
        {
            "request": request,
            "entity": model,
            "entity_is_container": model.is_container(),
            "container_object": container_object,
            "asset_object": asset_object,
            "entity_name": model.name,
            "is_owner": is_owner,
            "benchmarks_associations": benchmark_associations,  #
            "benchmarks": benchmarks,
            "approved_benchmarks": approved_benchmarks,
            "benchmark_datasets": benchmark_datasets,
            "cc_config_defaults": cc_config_defaults,
            "cc_policy": cc_policy,
            "cc_backends": asset_backends(),
            "cc_backend": {
                service: selected_backend(cc_config_defaults, service)
                for service in ("storage", "vault")
            },
            "cc_settings": {
                service: service_settings(cc_config_defaults, service)
                for service in ("storage", "vault")
            },
            "cc_field_label": field_label,
            "cc_configured": cc_configured,
            "cc_initialized": cc_initialized,
            "cc_last_synced": cc_last_synced,
        },
    )


@router.post("/associate", response_class=JSONResponse)
def associate(
    request: Request,
    model_id: int = Form(...),
    benchmark_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="model_association")
    return_response = {"status": "", "error": "", "entity_id": model_id}
    try:
        AssociateModel.run(model_uid=model_id, benchmark_uid=benchmark_id)
        return_response["status"] = "success"
        notification_message = "Successfully requested model association!"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to request model association"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/models/ui/display/{model_id}",
    )
    return return_response


@router.post("/run", response_class=JSONResponse)
def run(
    request: Request,
    entity_id: int = Form(...),
    benchmark_id: int = Form(...),
    data_ids: List[int] = Form(...),
    run_all: bool = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="run_benchmark")
    return_response = {"status": "", "error": "", "entity_id": entity_id}

    try:
        ModelBenchmarkRun.run(
            benchmark_id,
            entity_id,
            data_ids,
            no_cache=not run_all,
            rerun_finalized_executions=not run_all,
        )
        return_response["status"] = "success"
        notification_message = "Execution ran successfully"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Error during execution"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/models/ui/display/{entity_id}",
    )
    return return_response


@router.post("/download_cc_results", response_class=JSONResponse)
def download_cc_results(
    request: Request,
    entity_id: int = Form(...),
    execution_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="download_cc_results")
    return_response = {"status": "", "error": "", "entity_id": entity_id}

    try:
        DownloadCCResults.run(execution_id)
        return_response["status"] = "success"
        notification_message = "Results successfully collected"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to collect results"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/models/ui/display/{entity_id}",
    )
    return return_response


@router.post("/submit_result", response_class=JSONResponse)
def submit_result(
    request: Request,
    result_id: str = Form(...),
    model_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="submit_result")
    return_response = {"status": "", "error": "", "entity_id": model_id}

    try:
        ResultSubmission.run(result_id)
        return_response["status"] = "success"
        notification_message = "Result successfully submitted"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to submit results"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/models/ui/display/{model_id}",
    )
    return return_response


@router.post("/edit_cc_config", response_class=JSONResponse)
def edit_cc_config(
    request: Request,
    entity_id: int = Form(...),
    configure_cc: bool = Form(False),
    bind_peer_asset: bool = Form(False),
    allowed_result_collectors: List[str] = Form([]),
    current_user: bool = Depends(check_user_api),
):
    # Read as posted rather than declared field by field: which settings there
    # are depends on the backends chosen, and only medperf_cc knows them.
    form = anyio.from_thread.run(lambda: request.form())
    backends = asset_backends()
    args = {
        "storage": backend_settings_from_form(form, backends["storage"], "storage_"),
        "vault": backend_settings_from_form(form, backends["vault"], "vault_"),
    }
    # An unchecked box is simply absent from the form, so both choices are read
    # as stated rather than left to the asset kind's default.
    policy = {
        "bind_peer_asset": bind_peer_asset,
        "allowed_result_collectors": allowed_result_collectors,
    }
    if not configure_cc:
        args = {}
        policy = {}

    initialize_state_task(request, task_name="model_update_cc_config")
    return_response = {"status": "", "error": ""}
    try:
        ModelConfigureForCC.run(entity_id, args, policy)
        return_response["status"] = "success"
        notification_message = "Successfully updated model CC config!"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to update model CC config"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/models/ui/display/{entity_id}",
    )
    return return_response


@router.post("/sync_cc_policy", response_class=JSONResponse)
def sync_cc_policy(
    request: Request,
    entity_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="model_update_cc_policy")
    return_response = {"status": "", "error": ""}
    try:
        ModelUpdateCCPolicy.run(entity_id)
        return_response["status"] = "success"
        notification_message = "Successfully updated model CC policy!"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to update model CC policy"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/models/ui/display/{entity_id}",
    )
    return return_response
