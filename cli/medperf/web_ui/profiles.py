from fastapi import Form, APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse

from medperf import config
from medperf.config_management.config_management import read_config, write_config
from medperf.exceptions import InvalidArgumentError, MedperfException
from medperf.utils import make_pretty_dict
from medperf.web_ui.common import check_user_api, check_user_ui, templates
from medperf.init import initialize

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def profiles_ui(request: Request, current_user: bool = Depends(check_user_ui)):

    profiles = read_config()
    return templates.TemplateResponse(
        "profiles.html",
        {"request": request, "profiles": profiles},
    )


@router.post("/activate", response_class=JSONResponse)
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


@router.post("/view", response_class=JSONResponse)
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
    except MedperfException as exp:
        return_response["status"] = "failed"
        return_response["error"] = str(exp)

    return return_response
