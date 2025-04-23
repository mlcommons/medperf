from fastapi import Request, Form, APIRouter, Depends
from fastapi.responses import HTMLResponse, JSONResponse

from medperf.exceptions import MedperfException
from medperf.web_ui.common import (
    add_notification,
    initialize_state_task,
    reset_state_task,
    templates,
)
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
    task_id = initialize_state_task(request, task_name="medperf_login")
    config.ui.set_task_id(task_id)
    return_response = {"status": "", "error": ""}
    success = True

    account_info = read_user_account()
    if account_info is not None:
        msg = (
            f"You are already logged in as {account_info['email']}."
            " Logout before logging in again"
        )
        return_response["status"] = "failed"
        return_response["error"] = msg
        success = False
        notification_message = "Error Logging In"

    if success:
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as exp:
            return_response["status"] = "failed"
            return_response["error"] = str(exp)
            success = False
            notification_message = "Error Logging In"

    if success:
        try:
            config.auth.login(email)
            templates.env.globals["logged_in"] = True
            return_response["status"] = "success"
            notification_message = "Successfully Logged In"
        except MedperfException as exp:
            return_response["status"] = "failed"
            return_response["error"] = str(exp)
            notification_message = "Error Logging In"

    config.ui.end_task(return_response)
    reset_state_task(request)
    add_notification(
        request,
        message=notification_message,
        type=return_response["status"],
        url="/" if success else "/medperf_login",
    )
    return return_response


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
