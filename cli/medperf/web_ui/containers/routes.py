import logging
import threading
from collections import deque
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from medperf.account_management import get_medperf_user_data
from medperf.entities.certificate import Certificate
from medperf.entities.cube import Cube
from medperf.entities.model import Model
from medperf.entities.benchmark import Benchmark
from medperf.commands.mlcube.delete_keys import DeleteKeys
from medperf.commands.mlcube.grant_access import GrantAccess
from medperf.commands.mlcube.revoke_user_access import RevokeUserAccess
from medperf.commands.mlcube.submit import SubmitCube
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
from medperf.web_ui.listing import fetch_listing_page

router = APIRouter()
logger = logging.getLogger(__name__)


def _auto_access_key(model_id: int, benchmark_id: int) -> str:
    return f"{model_id}-{benchmark_id}"


def _format_auto_access_log_line(message: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}] {message}"


def _running_auto_access_for_container(
    model_auto_give_access: dict, container_id: int
) -> dict:
    running = {}
    for key, state in model_auto_give_access.items():
        try:
            model_id_str, benchmark_id_str = key.split("-", 1)
            if int(model_id_str) == container_id:
                running[int(benchmark_id_str)] = {
                    "name": state["name"],
                    "emails": state["emails"],
                    "interval": state["interval"],
                }
        except (ValueError, IndexError):
            continue
    return running


@router.get("/ui", response_class=HTMLResponse)
def containers_ui(
    request: Request,
    mine_only: bool = False,
    page: int = 1,
    page_size: int = 9,
    ordering: str = "created_at_desc",
    search: Optional[str] = None,
    current_user: bool = Depends(check_user_ui),
):
    my_user_id = get_medperf_user_data()["id"]
    containers, search_query, pagination_context = fetch_listing_page(
        Cube,
        page=page,
        page_size=page_size,
        ordering=ordering,
        mine_only=mine_only,
        my_user_id=my_user_id,
        search=search,
    )

    return templates.TemplateResponse(
        "container/containers.html",
        {
            "request": request,
            "containers": containers,
            "mine_only": mine_only,
            "search_query": search_query,
            **pagination_context,
        },
    )


@router.get("/ui/display/{container_id}", response_class=HTMLResponse)
def container_detail_ui(
    request: Request,
    container_id: int,
    current_user: bool = Depends(check_user_ui),
):
    container = Cube.get(cube_uid=container_id, valid_only=False)

    # If this container is used by a model, redirect to the model dashboard

    if container.is_model():
        model = Model.get_by_container(container_id)
        redirect_url = sanitize_redirect_url(f"/models/ui/display/{model.id}")
        return RedirectResponse(url=redirect_url)

    is_owner = container.owner == get_medperf_user_data()["id"]

    if not is_owner:
        container._encrypted = container.is_encrypted()

        if container._encrypted:
            container.access_status = check_access_to_container(container.id)

    return templates.TemplateResponse(
        "container/container_detail.html",
        {
            "request": request,
            "entity": container,
            "entity_name": container.name,
            "is_owner": is_owner,
        },
    )


@router.get("/register/ui", response_class=HTMLResponse)
def create_container_ui(
    request: Request,
    current_user: bool = Depends(check_user_ui),
):
    # Fetch the list of benchmarks to populate the benchmark dropdown
    benchmarks = Benchmark.all()
    # Render the dataset creation form with the list of benchmarks
    return templates.TemplateResponse(
        "container/register_container.html",
        {"request": request, "benchmarks": benchmarks},
    )


@router.post("/register", response_class=JSONResponse)
def register_container(
    request: Request,
    name: str = Form(...),
    container_file: str = Form(...),
    parameters_file: str = Form(None),
    additional_file: str = Form(""),
    model_encrypted: bool = Form(...),
    decryption_file: str = Form(None),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="register_container")

    return_response = {"status": "", "error": "", "entity_id": None}
    container_info = {
        "name": name,
        "additional_files_tarball_url": additional_file,
        "additional_files_tarball_hash": "",
        "state": "OPERATION",
    }
    container_id = None
    try:
        container_id = SubmitCube.run(
            container_info,
            container_config=container_file,
            parameters_config=parameters_file,
            decryption_key=decryption_file,
        )
        return_response["status"] = "success"
        return_response["entity_id"] = container_id
        notification_message = "Container successfully registered"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to register container"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
        url=f"/containers/ui/display/{container_id}" if container_id else "",
    )
    return return_response


@router.get("/ui/display/{container_id}/access", response_class=HTMLResponse)
def container_access_ui(
    request: Request,
    container_id: int,
    current_user: bool = Depends(check_user_ui),
):
    container = Cube.get(cube_uid=container_id, valid_only=False)

    is_owner = container.owner == get_medperf_user_data()["id"]

    if not is_owner:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "exception": "You don't have access to this page, non-owner",
            },
        )

    if not container.is_encrypted():
        redirect_url = sanitize_redirect_url(f"/containers/ui/display/{container_id}")
        return RedirectResponse(url=redirect_url)

    container_model = Model.get_by_container(container_id)
    benchmark_assocs = Model.get_benchmarks_associations(model_uid=container_model.id)

    benchmark_associations = {}
    for assoc in benchmark_assocs:
        benchmark_associations[assoc["benchmark"]] = assoc

    benchmark_allowed_ids = ",".join(
        str(benchmark_id)
        for benchmark_id, assoc in benchmark_associations.items()
        if assoc["approval_status"] == "APPROVED"
    )

    existing_keys = {
        i.id: i.certificate for i in EncryptedKey.get_container_keys(container_id)
    }

    approved_benchmark_ids = [
        int(benchmark_id)
        for benchmark_id, assoc in benchmark_associations.items()
        if assoc["approval_status"] == "APPROVED"
    ]

    if existing_keys:
        certs_mapping = {}
        for benchmark_id in approved_benchmark_ids:
            _, cert_user_info = Certificate.get_benchmark_datasets_certificates(
                benchmark_id
            )
            for cert_id in cert_user_info:
                certs_mapping[cert_id] = cert_user_info[cert_id]

        for key_id in existing_keys:
            cert_id = existing_keys[key_id]
            if cert_id in certs_mapping:
                existing_keys[key_id] = certs_mapping[cert_id]

    running_auto_access = _running_auto_access_for_container(
        request.app.state.model_auto_give_access, container_id
    )
    running_benchmarks = [
        {"id": benchmark_id, "name": state["name"]}
        for benchmark_id, state in running_auto_access.items()
    ]

    return templates.TemplateResponse(
        "container/container_access.html",
        {
            "request": request,
            "entity": container,
            "entity_name": container.name,
            "is_owner": is_owner,
            "benchmark_allowed_ids": benchmark_allowed_ids,
            "keys": existing_keys,
            "running_auto_access": running_auto_access,
            "running_benchmarks": running_benchmarks,
        },
    )


@router.post("/grant_access", response_class=JSONResponse)
def grant_access(
    request: Request,
    benchmark_id: int = Form(...),
    model_id: int = Form(...),
    emails: str = Form(""),
    current_user: bool = Depends(check_user_api),
):

    initialize_state_task(request, task_name="container_grant_access")
    return_response = {"status": "", "error": ""}
    try:
        GrantAccess.run(
            benchmark_id=benchmark_id, model_id=model_id, allowed_emails=emails
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
        url=f"/containers/ui/display/{model_id}/access",
    )
    return return_response


def grant_access_worker(
    benchmark_id, model_id, emails, interval, stop_event: threading.Event, logs: deque
):
    interval_in_seconds = interval * 60
    while not stop_event.is_set():
        try:
            with config.ui.capture() as messages:
                GrantAccess.run(
                    benchmark_id=benchmark_id,
                    model_id=model_id,
                    approved=True,
                    allowed_emails=emails,
                )
        except Exception as exp:
            messages.append(f"Error: {exp}")
            logger.exception(exp)
        for message in messages:
            logs.append(_format_auto_access_log_line(message))
        if stop_event.wait(interval_in_seconds):
            break


@router.post("/start_auto_access", response_class=JSONResponse)
def start_auto_access(
    request: Request,
    benchmark_id: int = Form(...),
    model_id: int = Form(...),
    interval: int = Form(...),
    emails: str = Form(""),
    current_user: bool = Depends(check_user_api),
):
    model_auto_give_access = request.app.state.model_auto_give_access
    key = _auto_access_key(model_id, benchmark_id)
    if key in model_auto_give_access:
        return {
            "status": "failed",
            "error": "Auto give access is already running for the selected container and benchmark.",
        }

    return_response = {"status": "", "error": ""}
    try:
        benchmark_name = Benchmark.get(benchmark_id).name
        event = threading.Event()
        logs = deque(maxlen=config.webui_max_log_messages)
        auto_access_worker = threading.Thread(
            target=grant_access_worker,
            args=(benchmark_id, model_id, emails, interval, event, logs),
            daemon=True,
        )
        auto_access_worker.start()
        model_auto_give_access[key] = {
            "worker": auto_access_worker,
            "event": event,
            "name": benchmark_name,
            "emails": emails,
            "interval": interval,
            "logs": logs,
        }
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
        url=f"/containers/ui/display/{model_id}/access",
    )
    return return_response


@router.post("/stop_auto_access", response_class=JSONResponse)
def stop_auto_access(
    request: Request,
    model_id: int = Form(...),
    benchmark_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    model_auto_give_access = request.app.state.model_auto_give_access
    key = _auto_access_key(model_id, benchmark_id)
    if key not in model_auto_give_access:
        return {
            "status": "failed",
            "error": "Auto give access is not started, nothing to stop.",
        }

    return_response = {"status": "", "error": ""}
    try:
        model_auto_give_access[key]["event"].set()
        model_auto_give_access[key]["worker"].join()
        del model_auto_give_access[key]
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
        url=f"/containers/ui/display/{model_id}/access",
    )
    return return_response


@router.get("/auto_access_logs", response_class=JSONResponse)
def auto_access_logs(
    request: Request,
    model_id: int,
    benchmark_id: int,
    current_user: bool = Depends(check_user_api),
):
    model_auto_give_access = request.app.state.model_auto_give_access
    key = _auto_access_key(model_id, benchmark_id)
    if key not in model_auto_give_access:
        return {
            "status": "failed",
            "error": "Auto give access is not running for the selected container and benchmark.",
            "logs": [],
        }

    return {"status": "success", "error": "", "logs": list(model_auto_give_access[key]["logs"])}


@router.post("/revoke_user_access", response_class=JSONResponse)
def revoke_user_access(
    request: Request,
    model_id: int = Form(...),
    key_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):

    initialize_state_task(request, task_name="container_revoke_key")
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
        url=f"/containers/ui/display/{model_id}/access",
    )
    return return_response


@router.post("/delete_keys", response_class=JSONResponse)
def delete_keys(
    request: Request,
    model_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):

    initialize_state_task(request, task_name="container_delete_keys")
    return_response = {"status": "", "error": ""}
    try:
        DeleteKeys.run(model_id)
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
        url=f"/containers/ui/display/{model_id}/access",
    )
    return return_response
