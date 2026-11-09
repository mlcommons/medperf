from fastapi import Form, APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse

from medperf import config
from medperf.commands.certificate.client_certificate import GetUserCertificate
from medperf.commands.certificate.delete_client_certificate import DeleteCertificate
from medperf.commands.certificate.submit import SubmitCertificate
from medperf.commands.certificate.utils import current_user_certificate_status
from medperf.account_management.account_management import get_medperf_user_object
from medperf.commands.utils import set_profile_args
from medperf.config_management.config_management import read_config, write_config
from medperf.commands.cc.setup_cc_operator import SetupCCOperator
from medperf.entities.ca import CA
from medperf.exceptions import InvalidArgumentError
from medperf.utils import make_pretty_dict
from medperf.init import initialize
from medperf.enums import CryptoKeyType
from medperf.web_ui.common import (
    check_user_api,
    check_user_ui,
    UITask,
    is_logged_in,
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
    signing_certificate_status = None

    cc_config_defaults = {}
    cc_configured = False
    cc_initialized = False

    if is_logged_in():
        cas = CA.all()
        cas = {c.id: c.name for c in cas}
        certificate_status = current_user_certificate_status(key_type=CryptoKeyType.RSA)
        signing_certificate_status = current_user_certificate_status(
            key_type=CryptoKeyType.EC
        )

        user = get_medperf_user_object()
        cc_config_defaults = user.get_cc_config()
        cc_configured = user.is_cc_configured()
        cc_initialized = user.is_cc_initialized()

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
            "signing_certificate_status": signing_certificate_status,
            "CryptoKeyType": CryptoKeyType,
            "cc_config_defaults": cc_config_defaults,
            "cc_configured": cc_configured,
            "cc_initialized": cc_initialized,
        },
    )


@router.post("/activate_profile", response_class=JSONResponse)
def activate_profile(
    request: Request,
    profile: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    # The automatic grant access workers act as the current user; switching the
    # profile (and thus possibly the user or server) under them is not allowed.
    if request.app.state.model_auto_give_access:
        return {
            "status": "failed",
            "error": "Automatic grant access is currently running. Stop it before switching profiles.",
        }

    config_p = read_config()

    if profile not in config_p:
        return {"status": "failed", "error": "The provided profile does not exists"}

    config_p.activate(profile)
    write_config(config_p)
    initialize(for_webui=True)
    config.ui.load_history()
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
    key_type: CryptoKeyType = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "get_client_certificate") as task:
        GetUserCertificate.run(key_type=key_type)
    task.notify(
        success_message="Certificate retrieved",
        failure_message="Failed to get certificate",
    )
    return task.response


@router.post("/delete_certificate", response_class=JSONResponse)
def delete_certificate(
    request: Request,
    key_type: CryptoKeyType = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "delete_client_certificate") as task:
        DeleteCertificate.run(key_type=key_type)
    task.notify(
        success_message="Certificate deleted",
        failure_message="Failed to delete certificate",
    )
    return task.response


@router.post("/submit_certificate", response_class=JSONResponse)
def submit_certificate(
    request: Request,
    key_type: CryptoKeyType = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "submit_client_certificate") as task:
        SubmitCertificate.run(key_type=key_type)
    task.notify(
        success_message="Certificate submitted",
        failure_message="Failed to submit certificate",
    )
    return task.response


@router.post("/edit_cc_operator", response_class=JSONResponse)
def edit_cc_operator(
    configure_cc: bool = Form(False),
    project_id: str = Form(""),
    service_account_name: str = Form(""),
    bucket: str = Form(""),
    vm_zone: str = Form(""),
    vm_name: str = Form(""),
    current_user: bool = Depends(check_user_api),
):
    args = {
        "project_id": project_id,
        "service_account_name": service_account_name,
        "bucket": bucket,
        "vm_zone": vm_zone,
        "vm_name": vm_name,
    }
    if not configure_cc:
        args = {}

    try:
        SetupCCOperator.run(args)
        return {"status": "success", "error": ""}
    except Exception as exp:
        logger.exception(exp)
        return {"status": "failed", "error": str(exp)}
