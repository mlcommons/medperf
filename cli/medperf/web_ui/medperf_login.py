from fastapi import Request, Form, APIRouter, Depends
from fastapi.responses import HTMLResponse, JSONResponse

from medperf.exceptions import MedperfException
from medperf.web_ui.common import templates
from medperf.account_management import read_user_account
from email_validator import validate_email, EmailNotValidError
import medperf.config as config
from medperf.web_ui.common import (
    get_current_user_api,
    get_current_user_ui,
)

router = APIRouter()


@router.get("/medperf_login", response_class=HTMLResponse)
def login_form(
    request: Request,
    redirect: str = "false",
    current_user: bool = Depends(get_current_user_ui),
):
    redirect = redirect.lower() == "true"
    return templates.TemplateResponse(
        "medperf_login.html", {"request": request, "redirect": redirect}
    )


@router.post("/medperf_login", response_class=JSONResponse)
def login(
    request: Request,
    email: str = Form(...),
    current_user: bool = Depends(get_current_user_api),
):
    account_info = read_user_account()
    if account_info is not None:
        msg = (
            f"You are already logged in as {account_info['email']}."
            " Logout before logging in again"
        )
        config.ui.set_error()
        return {"status": "failed", "error": msg}

    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError as e:
        config.ui.set_error()
        return {"status": "failed", "error": str(e)}

    try:
        config.auth.login(email)
        config.ui.set_success()
        templates.env.globals["logged_in"] = True
        return {"status": "success", "error": ""}
    except MedperfException as e:
        config.ui.set_error()
        return {"status": "failed", "error": str(e)}


@router.post("/logout", response_class=JSONResponse)
def logout(
    current_user: bool = Depends(get_current_user_api),
):
    try:
        config.auth.logout()
        templates.env.globals["logged_in"] = False
        return {"status": "success", "error": ""}
    except MedperfException as e:
        return {"status": "failed", "error": str(e)}
