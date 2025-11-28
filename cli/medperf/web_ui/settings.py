from fastapi import Form, APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse

from medperf import config
from medperf.commands.certificate.client_certificate import GetUserCertificate
from medperf.commands.certificate.delete_client_certificate import DeleteCertificate
from medperf.commands.certificate.submit import SubmitCertificate
from medperf.commands.certificate.utils import current_user_certificate_status
from medperf.commands.utils import set_profile_args
from medperf.config_management.config_management import read_config, write_config
from medperf.entities.ca import CA
from medperf.exceptions import InvalidArgumentError
from medperf.utils import make_pretty_dict
from medperf.init import initialize
from medperf.web_ui.common import (
    check_user_api,
    check_user_ui,
    initialize_state_task,
    is_logged_in,
    reset_state_task,
    templates,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def settings_ui(request: Request, current_user: bool = Depends(check_user_ui)):
    config_p = read_config()
    cas = None
    certificate_status = None

    if is_logged_in():
        cas = CA.all()
        cas = {c.id: c.name for c in cas}
        certificate_status = current_user_certificate_status()

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "profiles": config_p,
            "default_gpus": config.gpus if config.gpus else "0",
            "default_platform": config.platform,
            "cas": cas,
            "default_ca": config.certificate_authority_id,
            "default_fingerprint": config.certificate_authority_fingerprint,
            "certificate_status": certificate_status,
        },
    )


@router.post("/activate_profile", response_class=JSONResponse)
def activate_profile(
    profile: str = Form(...), current_user: bool = Depends(check_user_api)
):
    config_p = read_config()

    if profile not in config_p:
        return {"status": "failed", "error": "The provided profile does not exists"}

    config_p.activate(profile)
    write_config(config_p)
    initialize(for_webui=True)
    return {"status": "success", "error": ""}


@router.post("/edit_profile", response_class=JSONResponse)
def edit_profile(
    gpus: str = Form(None),
    platform: str = Form(None),
    ca: int = Form(None),
    fingerprint: str = Form(None),
    current_user: bool = Depends(check_user_api),
):
    if platform is None:
        platform = config.platform
    if gpus is None:
        gpus = config.gpus
    if ca is None:
        ca = config.certificate_authority_id
    if fingerprint is None:
        fingerprint = config.certificate_authority_fingerprint

    args = {
        "gpus": gpus,
        "platform": platform,
        "certificate_authority_id": ca,
        "certificate_authority_fingerprint": fingerprint,
    }
    try:
        set_profile_args(args)
        initialize(for_webui=True)
        return {"status": "success", "error": ""}
    except Exception as exp:
        logger.exception(exp)
        return {"status": "failed", "error": str(exp)}


@router.post("/view_profile", response_class=JSONResponse)
def view_profile(
    profile: str = Form(...), current_user: bool = Depends(check_user_api)
):
    return_response = {"status": "", "error": "", "profile": "", "profile_dict": ""}
    try:
        config_p = read_config()
        profile_config = config_p.active_profile
        if profile:
            if profile not in config_p:
                raise InvalidArgumentError("The provided profile does not exist")
            profile_config = config_p[profile]

        profile_config.pop(config.credentials_keyword, None)
        profile_dict = make_pretty_dict(profile_config, skip_none_values=False)

        return_response["status"] = "success"
        return_response["profile_dict"] = profile_dict
        return_response["profile"] = profile
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        logger.exception(exp)

    return return_response


@router.post("/get_certificate", response_class=JSONResponse)
def get_certificate(
    request: Request,
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="get_client_certificate")
    return_response = {"status": "", "error": ""}

    try:
        GetUserCertificate.run()
        return_response["status"] = "success"
        notification_message = "Certificate retrieved"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to get certificate"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
    )
    return return_response


@router.post("/delete_certificate", response_class=JSONResponse)
def delete_certificate(
    request: Request,
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="delete_client_certificate")
    return_response = {"status": "", "error": ""}

    try:
        DeleteCertificate.run()
        return_response["status"] = "success"
        notification_message = "Certificate deleted"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to delete certificate"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
    )
    return return_response


@router.post("/submit_certificate", response_class=JSONResponse)
def submit_certificate(
    request: Request,
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="submit_client_certificate")
    return_response = {"status": "", "error": ""}

    try:
        SubmitCertificate.run()
        return_response["status"] = "success"
        notification_message = "Certificate submitted"
    except Exception as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)
        notification_message = "Failed to submit certificate"
        logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    config.ui.add_notification(
        message=notification_message,
        return_response=return_response,
    )
    return return_response
