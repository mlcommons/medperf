import logging
import threading

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from medperf.account_management import get_medperf_user_data
from medperf.entities.certificate import Certificate
from medperf.entities.cube import Cube
from medperf.entities.benchmark import Benchmark
from medperf.commands.compatibility_test.run import CompatibilityTestExecution
from medperf.commands.mlcube.associate import AssociateCube
from medperf.commands.mlcube.delete_keys import DeleteKeys
from medperf.commands.mlcube.grant_access import GrantAccess
from medperf.commands.mlcube.revoke_user_access import RevokeUserAccess
from medperf.commands.mlcube.submit import SubmitCube
import medperf.config as config
from medperf.entities.encrypted_key import EncryptedKey
from medperf.web_ui.common import (
    add_notification,
    check_user_api,
    initialize_state_task,
    reset_state_task,
    templates,
    check_user_ui,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ui", response_class=HTMLResponse)
def containers_ui(
    request: Request,
    mine_only: bool = False,
    current_user: bool = Depends(check_user_ui),
):
    filters = {}
    my_user_id = get_medperf_user_data()["id"]
    if mine_only:
        filters["owner"] = my_user_id

    containers = Cube.all(
        filters=filters,
    )
    containers = sorted(containers, key=lambda x: x.created_at, reverse=True)
    # sort by (mine recent) (mine oldish), (other recent), (other oldish)
    my_containers = [c for c in containers if c.owner == my_user_id]
    other_containers = [c for c in containers if c.owner != my_user_id]
    containers = my_containers + other_containers
    return templates.TemplateResponse(
        "container/containers.html",
        {"request": request, "containers": containers, "mine_only": mine_only},
    )


@router.get("/ui/display/{container_id}", response_class=HTMLResponse)
def container_detail_ui(
    request: Request,
    container_id: int,
    current_user: bool = Depends(check_user_ui),
):
    container = Cube.get(cube_uid=container_id, valid_only=False)

    benchmark_assocs = Cube.get_benchmarks_associations(mlcube_uid=container_id)

    benchmark_associations = {}
    for assoc in benchmark_assocs:
        benchmark_associations[assoc["benchmark"]] = assoc

    benchmarks = Benchmark.all()
    benchmarks = {b.id: b for b in benchmarks}
    # benchmarks_associations = sort_associations_display(benchmarks_associations)
    is_owner = container.owner == get_medperf_user_data()["id"]

    return templates.TemplateResponse(
        "container/container_detail.html",
        {
            "request": request,
            "entity": container,
            "entity_name": container.name,
            "is_owner": is_owner,
            "benchmarks_associations": benchmark_associations,  #
            "benchmarks": benchmarks,
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


@router.get("/register/compatibility_test", response_class=HTMLResponse)
def compatibilty_test_ui(
    request: Request,
    current_user: bool = Depends(check_user_ui),
):
    # Fetch the list of benchmarks to populate the benchmark dropdown
    benchmarks = Benchmark.all()
    # Render the dataset creation form with the list of benchmarks
    return templates.TemplateResponse(
        "container/compatibility_test.html",
        {"request": request, "benchmarks": benchmarks},
    )


@router.post("/register", response_class=JSONResponse)
def register_container(
    request: Request,
    name: str = Form(...),
    container_file: str = Form(...),
    parameters_file: str = Form(""),
    additional_file: str = Form(""),
    model_encrypted: bool = Form(...),
    decryption_file: str = Form(None),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="container_registration")
    return_response = {"status": "", "error": "", "container_id": None}
    container_info = {
        "name": name,
        "git_mlcube_url": container_file,
        "git_mlcube_hash": "",
        "git_parameters_url": parameters_file,
        "parameters_hash": "",
        "image_tarball_url": "",
        "image_tarball_hash": "",
        "additional_files_tarball_url": additional_file,
        "additional_files_tarball_hash": "",
        "state": "OPERATION",
    }
    container_id = None
    try:
        container_id = SubmitCube.run(container_info, decryption_key=decryption_file)
        return_response["status"] = "success"
        return_response["container_id"] = container_id
        notification_message = "Container successfully registered"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to register container"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    add_notification(
        request,
        message=notification_message,
        return_response=return_response,
        url=f"/containers/ui/display/{container_id}" if container_id else "",
    )
    return return_response


@router.post("/run_compatibility_test", response_class=JSONResponse)
def test_container(
    request: Request,
    benchmark: int = Form(...),
    container_path: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="container_compatibility_test")
    return_response = {"status": "", "error": "", "results": None}
    try:
        _, results = CompatibilityTestExecution.run(
            benchmark=benchmark, model=container_path
        )
        return_response["status"] = "success"
        return_response["results"] = results
        notification_message = "Container compatibility test succeeded!"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Container compatibility test failed"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    add_notification(
        request,
        message=notification_message,
        return_response=return_response,
        url="/containers/register/ui",
    )
    return return_response


@router.post("/associate", response_class=JSONResponse)
def associate(
    request: Request,
    container_id: int = Form(...),
    benchmark_id: int = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="container_association")
    return_response = {"status": "", "error": ""}
    try:
        AssociateCube.run(cube_uid=container_id, benchmark_uid=benchmark_id)
        return_response["status"] = "success"
        notification_message = "Successfully requested container association!"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to request container association"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    add_notification(
        request,
        message=notification_message,
        return_response=return_response,
        url=f"/containers/ui/display/{container_id}",
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
        return RedirectResponse(url=f"/containers/ui/display/{container_id}")

    benchmark_assocs = Cube.get_benchmarks_associations(mlcube_uid=container_id)

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
        i.id: i.certificate for i in EncryptedKey.get_container_keys(container_id)
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
        "container/container_access.html",
        {
            "request": request,
            "entity": container,
            "entity_name": container.name,
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
    add_notification(
        request,
        message=notification_message,
        return_response=return_response,
        url=f"/containers/ui/display/{model_id}/access",
    )
    return return_response


def grant_access_worker(
    benchmark_id, model_id, emails, interval, stop_event: threading.Event
):
    interval_in_seconds = interval * 60
    while not stop_event.is_set():
        try:
            GrantAccess.run(
                benchmark_id=benchmark_id,
                model_id=model_id,
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
        model = request.app.state.model_auto_give_access["model"]
        return {
            "status": "failed",
            "error": f"Auto give access is already running for benchmark: {bmk}, model: {model}",
        }

    return_response = {"status": "", "error": ""}
    try:
        event = threading.Event()
        auto_access_worker = threading.Thread(
            target=grant_access_worker,
            args=(benchmark_id, model_id, emails, interval, event),
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

    add_notification(
        request,
        message=notification_message,
        return_response=return_response,
        url=f"/containers/ui/display/{model_id}/access",
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

    add_notification(
        request,
        message=notification_message,
        return_response=return_response,
        url=f"/containers/ui/display/{model_id}/access",
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
    add_notification(
        request,
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
    add_notification(
        request,
        message=notification_message,
        return_response=return_response,
        url=f"/containers/ui/display/{model_id}/access",
    )
    return return_response
