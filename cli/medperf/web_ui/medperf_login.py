from fastapi import Request, Form, APIRouter, Depends
from fastapi.responses import HTMLResponse, JSONResponse

from medperf.web_ui.common import (
    UITask,
    check_user_api,
    check_user_ui,
    templates,
)
from medperf.account_management import read_user_account
from medperf.exceptions import InvalidArgumentError
from email_validator import validate_email
import medperf.config as config

router = APIRouter()


@router.get("/medperf_login", response_class=HTMLResponse)
def login_form(
    request: Request,
    redirected: str = "false",
    current_user: bool = Depends(check_user_ui),
):
    account_info = read_user_account()
    msg = ""
    if account_info is not None:
        msg = (
            f"You are already logged in as {account_info['email']}."
            " Logout before logging in again"
        )
    redirected = redirected.lower() == "true"
    return templates.TemplateResponse(
        "medperf_login.html",
        {
            "request": request,
            "redirected": redirected,
            "already_logged_in_msg": msg if account_info else None,
        },
    )


@router.post("/medperf_login", response_class=JSONResponse)
def login(
    request: Request,
    email: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    with UITask(request, "medperf_login") as task:
        account_info = read_user_account()
        if account_info is not None:
            raise InvalidArgumentError(
                f"You are already logged in as {account_info['email']}."
                " Logout before logging in again"
            )
        validate_email(email, check_deliverability=False)
        config.auth.login(email)
        config.ui.load_history()
    task.notify(
        success_message="Successfully Logged In",
        failure_message="Error Logging In",
        url="" if task.succeeded else "/medperf_login",
    )
    return task.response


@router.post("/logout", response_class=JSONResponse)
def logout(
    request: Request,
    current_user: bool = Depends(check_user_api),
):
    if request.app.state.model_auto_give_access:
        return {
            "status": "failed",
            "error": "Automatic grant access is currently running. Stop it before logging out.",
        }

    with UITask(request, "medperf_logout") as task:
        config.auth.logout()
        config.ui.load_history()
    task.notify(
        success_message="Successfully Logged Out",
        failure_message="Error Logging Out",
    )
    return task.response
