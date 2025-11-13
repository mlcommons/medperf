from fastapi import Request, Form, APIRouter, Depends
from fastapi.responses import HTMLResponse, JSONResponse

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
    check_user_api,
    check_user_ui,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/medperf_login", response_class=HTMLResponse)
def login_form(
    request: Request,
    redirected: str = "false",
    current_user: bool = Depends(check_user_ui),
):
    redirected = redirected.lower() == "true"
    return templates.TemplateResponse(
        "medperf_login.html", {"request": request, "redirected": redirected}
    )


@router.post("/medperf_login", response_class=JSONResponse)
def login(
    request: Request,
    email: str = Form(...),
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="medperf_login")
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
            logger.exception(exp)

    if success:
        try:
            config.auth.login(email)
            templates.env.globals["logged_in"] = True
            return_response["status"] = "success"
            notification_message = "Successfully Logged In"
        except Exception as exp:
            return_response["status"] = "failed"
            return_response["error"] = str(exp)
            notification_message = "Error Logging In"
            logger.exception(exp)

    config.ui.end_task(return_response)
    reset_state_task(request)
    add_notification(
        request,
        message=notification_message,
        return_response=return_response,
        url="" if success else "/medperf_login",
    )
    return return_response


@router.post("/logout", response_class=JSONResponse)
def logout(
    request: Request,
    current_user: bool = Depends(check_user_api),
):
    initialize_state_task(request, task_name="medperf_logout")
    return_response = {"status": "", "error": ""}

    try:
        config.auth.logout()
        templates.env.globals["logged_in"] = False
        return_response["status"] = "success"
        notification_message = "Successfully Logged Out"
        request.app.state.notifications.clear()
        request.app.state.new_notifications.clear()
    except Exception as e:
        return_response["status"] = "failed"
        return_response["error"] = str(e)
        notification_message = "Error Logging Out"
        logger.exception(e)

    config.ui.end_task(return_response)
    reset_state_task(request)
    add_notification(
        request,
        message=notification_message,
        return_response=return_response,
    )
    return return_response
