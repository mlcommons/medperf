import logging

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

from medperf.account_management import get_medperf_user_data
from medperf.entities.model import Model
from medperf.entities.benchmark import Benchmark
from medperf.commands.model.associate import AssociateModel
from medperf.commands.mlcube.utils import check_access_to_container
from medperf.commands.cc.model_configure_for_cc import ModelConfigureForCC
from medperf.commands.cc.model_update_cc_policy import ModelUpdateCCPolicy
import medperf.config as config
from medperf.web_ui.common import (
    check_user_api,
    initialize_state_task,
    reset_state_task,
    templates,
    check_user_ui,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ui", response_class=HTMLResponse)
def models_ui(
    request: Request,
    mine_only: bool = False,
    current_user: bool = Depends(check_user_ui),
):
    filters = {}
    my_user_id = get_medperf_user_data()["id"]
    if mine_only:
        filters["owner"] = my_user_id

    models = Model.all(filters=filters)
    models = sorted(models, key=lambda x: x.created_at, reverse=True)
    # sort by (mine recent) (mine oldish), (other recent), (other oldish)
    my_models = [c for c in models if c.owner == my_user_id]
    other_models = [c for c in models if c.owner != my_user_id]
    models = my_models + other_models
    return templates.TemplateResponse(
        "model/models.html",
        {"request": request, "models": models, "mine_only": mine_only},
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
    cc_configured = model.is_cc_configured()
    cc_initialized = model.is_cc_initialized()
    cc_last_synced = model.get_last_synced()
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
            "cc_config_defaults": cc_config_defaults,
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


@router.post("/edit_cc_config", response_class=JSONResponse)
def edit_cc_config(
    request: Request,
    entity_id: int = Form(...),
    configure_cc: bool = Form(False),
    project_id: str = Form(""),
    project_number: str = Form(""),
    bucket: str = Form(""),
    keyring_name: str = Form(""),
    key_name: str = Form(""),
    key_location: str = Form(""),
    wip: str = Form(""),
    wip_provider: str = Form(""),
    current_user: bool = Depends(check_user_api),
):
    args = {
        "project_id": project_id,
        "project_number": project_number,
        "bucket": bucket,
        "keyring_name": keyring_name,
        "key_name": key_name,
        "key_location": key_location,
        "wip": wip,
        "wip_provider": wip_provider,
    }
    if not configure_cc:
        args = {}

    initialize_state_task(request, task_name="model_update_cc_config")
    return_response = {"status": "", "error": ""}
    try:
        ModelConfigureForCC.run(entity_id, args, {})
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
