from fastapi import Form, APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse

from medperf.entities.ca import CA
from medperf import config
from medperf.config_management.config_management import read_config, write_config
from medperf.commands.utils import set_profile_args
from medperf.exceptions import InvalidArgumentError
from medperf.utils import make_pretty_dict
from medperf.web_ui.common import check_user_api, check_user_ui, templates
from medperf.init import initialize
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def profiles_ui(request: Request, current_user: bool = Depends(check_user_ui)):

    config_p = read_config()
    cas = CA.all()
    cas = {c.id: c.name for c in cas}
    default_ca = config_p.active_profile["certificate_authority_id"]
    default_fingerprint = config_p.active_profile["certificate_authority_fingerprint"]

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "profiles": config_p,
            "default_gpus": config.gpus if config.gpus else "0",
            "default_platform": config.platform,
            "cas": cas,
            "default_ca": default_ca,
            "default_fingerprint": default_fingerprint,
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
    current_user: bool = Depends(check_user_api),
):
    if platform is None:
        platform = config.platform
    if gpus is None:
        gpus = config.gpus

    try:
        config_p = read_config()
        profile_config = config_p.active_profile.copy()
        profile_config.update({"gpus": gpus, "platform": platform})
        set_profile_args(profile_config)
        initialize(for_webui=True)
        return {"status": "success", "error": ""}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


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


@router.post("/edit_certificate", response_class=JSONResponse)
def edit_certificate(
    ca: int = Form(None),
    fingerprint: str = Form(None),
    current_user: bool = Depends(check_user_api),
):
    if ca is None:
        ca = config.certificate_authority_id
    if fingerprint is None:
        fingerprint = config.certificate_authority_fingerprint

    try:
        config_p = read_config()
        profile_config = config_p.active_profile.copy()
        profile_config.update(
            {
                "certificate_authority_id": ca,
                "certificate_authority_fingerprint": fingerprint,
            }
        )
        initialize(for_webui=True)
        set_profile_args(profile_config)
        return {"status": "success", "error": ""}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
