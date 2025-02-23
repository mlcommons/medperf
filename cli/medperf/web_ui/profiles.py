from fastapi import Form, APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse

from medperf import config
from medperf.config_management.config_management import read_config, write_config
from medperf.exceptions import MedperfException
from medperf.utils import dict_pretty_print
from medperf.web_ui.common import get_current_user_api, get_current_user_ui, templates

router = APIRouter()


@router.get("/profiles", response_class=HTMLResponse)
def profiles_ui(request: Request, current_user: bool = Depends(get_current_user_ui)):

    profiles = read_config()
    return templates.TemplateResponse(
        "profiles.html",
        {"request": request, "profiles": profiles},
    )


@router.post("/activate_profile", response_class=JSONResponse)
def activate_profile(
    profile: str = Form(...), current_user: bool = Depends(get_current_user_api)
):
    config_p = read_config()

    if profile not in config_p:
        return {"status": "failed", "error": "The provided profile does not exists"}

    config_p.activate(profile)
    write_config(config_p)
    return {"status": "success", "error": ""}


@router.post("/view_profile", response_class=JSONResponse)
def view_profile(
    profile: str = Form(...), current_user: bool = Depends(get_current_user_api)
):
    try:
        config_p = read_config()
        profile_config = config_p.active_profile
        if profile:
            profile_config = config_p[profile]

        profile_config.pop(config.credentials_keyword, None)
        dict_pretty_print(profile_config, skip_none_values=False)
        config.ui.set_success()
        return {"status": "success", "error": ""}
    except MedperfException as e:
        config.ui.set_error()
        return {"status": "failed", "error": str(e)}
