import logging
import threading

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from medperf.account_management import get_medperf_user_data
from medperf.entities.certificate import Certificate
from medperf.entities.cube import Cube
from medperf.entities.model import Model
from medperf.entities.asset import Asset
from medperf.entities.benchmark import Benchmark
from medperf.commands.model.associate import AssociateModel
from medperf.commands.model.submit import SubmitModel
from medperf.commands.mlcube.delete_keys import DeleteKeys
from medperf.commands.mlcube.grant_access import GrantAccess
from medperf.commands.mlcube.revoke_user_access import RevokeUserAccess
from medperf.commands.mlcube.utils import check_access_to_container
import medperf.config as config
from medperf.entities.encrypted_key import EncryptedKey
from medperf.web_ui.common import (
    check_user_api,
    initialize_state_task,
    reset_state_task,
    templates,
    check_user_ui,
    sanitize_redirect_url,
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
    my_models = [m for m in models if m.owner == my_user_id]
    other_models = [m for m in models if m.owner != my_user_id]
    models = my_models + other_models
    return templates.TemplateResponse(
        "model/models.html",
        {"request": request, "models": models, "mine_only": mine_only},
    )


@router.get("/by-container/{container_id}", response_class=JSONResponse)
def model_by_container(
    request: Request,
    container_id: int,
    current_user: bool = Depends(check_user_api),
):
    model = Model.get_by_container(container_id)
    if model is None:
        return JSONResponse(content={"model": None}, status_code=404)
    return JSONResponse(
        content={"model": {"id": model.id, "name": model.name, "type": model.type}}
    )


@router.get("/ui/display/{model_id}", response_class=HTMLResponse)
def model_detail_ui(
    request: Request,
    model_id: int,
    current_user: bool = Depends(check_user_ui),
):
    model = Model.get(model_id)

    container = None
    asset = None
    if model.type == "CONTAINER" and model.container:
        container = Cube.get(cube_uid=model.container, valid_only=False)
    elif model.type == "ASSET" and model.asset:
        asset = Asset.get(model.asset)

    benchmark_assocs = Model.get_benchmarks_associations(model_uid=model_id)
    benchmark_associations = {}
    for assoc in benchmark_assocs:
        benchmark_associations[assoc["benchmark"]] = assoc

    benchmarks = Benchmark.all()
    benchmarks = {b.id: b for b in benchmarks}

    is_owner = model.owner == get_medperf_user_data()["id"]

    if container and not is_owner:
        container._encrypted = container.is_encrypted()
        if container._encrypted:
            container.access_status = check_access_to_container(container.id)

    return templates.TemplateResponse(
        "model/model_detail.html",
        {
            "request": request,
            "entity": model,
            "entity_name": model.name,
            "container": container,
            "asset": asset,
            "is_owner": is_owner,
            "benchmarks_associations": benchmark_associations,
            "benchmarks": benchmarks,
        },
    )


@router.get("/register/ui", response_class=HTMLResponse)
def create_model_ui(
    request: Request,
    current_user: bool = Depends(check_user_ui),
):
    return templates.TemplateResponse(
        "model/register_model.html",
        {"request": request},
    )


@router.post("/register", response_class=JSONResponse)
def register_model(
    request: Request,
    name: str = Form(...),
    model_type: str = Form(...),
    # Container fields
    container_file: str = Form(None),
    parameters_file: str = Form(None),
    additional_file: str = Form(""),
    model_encrypted: bool = Form(False),
    decryption_file: str = Form(None),
    # Asset fields
    asset_path: str = Form(None),
    asset_url: str = Form(None),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="model_registration")
    return_response = {"status": "", "error": "", "model_id": None}
    model_id = None
    try:
        if model_type == "container":
            model_id = SubmitModel.run(
                name=name,
                container_config_file=container_file,
                parameters_config_file=parameters_file,
                additional_file=additional_file or None,
                decryption_key=decryption_file,
                operational=True,
            )
        else:
            model_id = SubmitModel.run(
                name=name,
                asset_path=asset_path or None,
                asset_url=asset_url or None,
                operational=True,
            )
        return_response["status"] = "success"
        return_response["model_id"] = model_id
        notification_message = "Model successfully registered"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to register model"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/models/ui/display/{model_id}" if model_id else "",
    )
    return return_response


@router.post("/associate", response_class=JSONResponse)
def associate(
    request: Request,
    model_id: int = Form(...),
    benchmark_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="model_association")
    return_response = {"status": "", "error": ""}
    try:
        AssociateModel.run(
            model_uid=model_id, benchmark_uid=benchmark_id, approved=True
        )
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


@router.get("/ui/display/{model_id}/access", response_class=HTMLResponse)
def model_access_ui(
    request: Request,
    model_id: int,
    current_user: bool = Depends(check_user_ui),
):
    model = Model.get(model_id)

    if model.type != "CONTAINER" or not model.container:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "exception": "Access management is only available for container-backed models",
            },
        )

    container = Cube.get(cube_uid=model.container, valid_only=False)
    is_owner = model.owner == get_medperf_user_data()["id"]

    if not is_owner:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "exception": "You don't have access to this page, non-owner",
            },
        )

    if not container.is_encrypted():
        redirect_url = sanitize_redirect_url(f"/models/ui/display/{model_id}")
        return RedirectResponse(url=redirect_url)

    benchmark_assocs = Model.get_benchmarks_associations(model_uid=model_id)
    benchmark_associations = {}
    for assoc in benchmark_assocs:
        benchmark_associations[assoc["benchmark"]] = assoc

    benchmarks = Benchmark.all()
    benchmarks = {
        b.id: b.name
        for b in benchmarks
        if b.id in benchmark_associations
        and benchmark_associations[b.id]["approval_status"] == "APPROVED"
    }

    existing_keys = {
        i.id: i.certificate for i in EncryptedKey.get_container_keys(container.id)
    }

    if existing_keys:
        certs_mapping = {}
        for benchmark_id in benchmarks:
            _, cert_user_info = Certificate.get_benchmark_datasets_certificates(
                benchmark_id
            )
            for cert_id in cert_user_info:
                certs_mapping[cert_id] = cert_user_info[cert_id]

        for key_id in existing_keys:
            cert_id = existing_keys[key_id]
            if cert_id in certs_mapping:
                existing_keys[key_id] = certs_mapping[cert_id]

    return templates.TemplateResponse(
        "model/model_access.html",
        {
            "request": request,
            "entity": model,
            "entity_name": model.name,
            "container": container,
            "is_owner": is_owner,
            "benchmarks": benchmarks,
            "keys": existing_keys,
        },
    )


@router.post("/grant_access", response_class=JSONResponse)
def grant_access(
    request: Request,
    benchmark_id: int = Form(...),
    model_id: int = Form(...),
    emails: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="model_grant_access")
    return_response = {"status": "", "error": ""}

    model_obj = Model.get(model_id)
    container_id = model_obj.container

    try:
        GrantAccess.run(
            benchmark_id=benchmark_id, model_id=container_id, allowed_emails=emails
        )
        return_response["status"] = "success"
        notification_message = "Successfully granted access to the selected users."
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to grant access"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/models/ui/display/{model_id}/access",
    )
    return return_response


def grant_access_worker(
    benchmark_id, model_id, container_id, emails, interval, stop_event: threading.Event
):
    interval_in_seconds = interval * 60
    while not stop_event.is_set():
        try:
            GrantAccess.run(
                benchmark_id=benchmark_id,
                model_id=container_id,
                emails=emails,
                approved=True,
            )
        except Exception:
            pass
        if stop_event.wait(interval_in_seconds):
            break


@router.post("/start_auto_access", response_class=JSONResponse)
def start_auto_access(
    request: Request,
    benchmark_id: int = Form(...),
    model_id: int = Form(...),
    interval: int = Form(...),
    emails: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    if request.app.state.model_auto_give_access["running"]:
        bmk = request.app.state.model_auto_give_access["benchmark"]
        m = request.app.state.model_auto_give_access["model"]
        return {
            "status": "failed",
            "error": f"Auto give access is already running for benchmark: {bmk}, model: {m}",
        }

    model_obj = Model.get(model_id)
    container_id = model_obj.container

    return_response = {"status": "", "error": ""}
    try:
        event = threading.Event()
        auto_access_worker = threading.Thread(
            target=grant_access_worker,
            args=(benchmark_id, model_id, container_id, emails, interval, event),
            daemon=True,
        )
        auto_access_worker.start()
        return_response["status"] = "success"
        notification_message = "Successfully started automatic grant access."
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to start automatic grant access."
        logger.exception(exp)

    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/models/ui/display/{model_id}/access",
    )

    request.app.state.model_auto_give_access = {
        "running": True,
        "worker": auto_access_worker,
        "event": event,
        "benchmark": benchmark_id,
        "model": model_id,
        "emails": emails,
        "interval": interval,
    }
    return return_response


@router.post("/stop_auto_access", response_class=JSONResponse)
def stop_auto_access(
    request: Request,
    model_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    if not request.app.state.model_auto_give_access["running"]:
        return {
            "status": "failed",
            "error": "Auto give access is not started, nothing to stop.",
        }

    return_response = {"status": "", "error": ""}
    try:
        request.app.state.model_auto_give_access["event"].set()
        request.app.state.model_auto_give_access["worker"].join()
        return_response["status"] = "success"
        notification_message = "Successfully stopped automatic grant access."
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to stop automatic grant access."
        logger.exception(exp)

    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/models/ui/display/{model_id}/access",
    )

    request.app.state.model_auto_give_access = {
        "running": False,
        "worker": None,
        "event": None,
        "benchmark": 0,
        "model": 0,
        "emails": "",
        "interval": 0,
    }

    return return_response


@router.post("/revoke_user_access", response_class=JSONResponse)
def revoke_user_access(
    request: Request,
    model_id: int = Form(...),
    key_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="model_revoke_key")
    return_response = {"status": "", "error": ""}
    try:
        RevokeUserAccess.run(key_id)
        return_response["status"] = "success"
        notification_message = "Successfully revoked key"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to revoke key"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/models/ui/display/{model_id}/access",
    )
    return return_response


@router.post("/delete_keys", response_class=JSONResponse)
def delete_keys(
    request: Request,
    model_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="model_delete_keys")
    return_response = {"status": "", "error": ""}

    model_obj = Model.get(model_id)
    container_id = model_obj.container

    try:
        DeleteKeys.run(container_id)
        return_response["status"] = "success"
        notification_message = "Successfully deleted keys."
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to delete keys"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/models/ui/display/{model_id}/access",
    )
    return return_response
