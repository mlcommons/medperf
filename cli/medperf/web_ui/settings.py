from fastapi import Form, APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse

from medperf import config
from medperf.config_management.config_management import read_config, write_config
from medperf.exceptions import InvalidArgumentError
from medperf.utils import make_pretty_dict
from medperf.web_ui.common import check_user_api, check_user_ui, templates
from medperf.init import initialize
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def profiles_ui(request: Request, current_user: bool = Depends(check_user_ui)):

    profiles = read_config()
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "profiles": profiles,
            "default_gpus": config.gpus if config.gpus else "0",
            "default_platform": config.platform,
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
    config_p = read_config()
    config_p.active_profile.update({"gpus": gpus, "platform": platform})
    write_config(config_p)
    initialize(for_webui=True)
    return {"status": "success", "error": ""}


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
