import logging
from pathlib import Path

import anyio
from fastapi import HTTPException, Security
from fastapi.security import APIKeyCookie, APIKeyHeader
from fastapi.templating import Jinja2Templates
from importlib import resources

from fastapi.requests import Request
from starlette.responses import RedirectResponse

from medperf.entities.association import Association
from medperf.enums import Status
from medperf.web_ui.auth import (
    security_token,
    AUTH_COOKIE_NAME,
    API_KEY_NAME,
    NotAuthenticatedException,
)
import uuid
import time

templates_folder_path = Path(resources.files("medperf.web_ui")) / "templates"
templates = Jinja2Templates(directory=templates_folder_path)

logger = logging.getLogger(__name__)


def generate_uuid():
    return str(uuid.uuid4())


def initialize_state_task(request: Request, task_name: str) -> str:
    form_data = dict(anyio.run(lambda: request.form()))
    new_task_id = generate_uuid()
    request.app.state.task = {
        "id": new_task_id,
        "name": task_name,
        "running": True,
        "logs": [],
        "formData": form_data,
    }
    request.app.state.task_running = True

    return new_task_id


def reset_state_task(request: Request):
    current_task = request.app.state.task
    current_task["running"] = False
    if len(request.app.state.old_tasks) == 10:
        request.app.state.old_tasks.pop(0)
    request.app.state.old_tasks.append(current_task)
    request.app.state.task = {
        "id": "",
        "name": "",
        "running": False,
        "logs": [],
        "formData": {},
    }
    request.app.state.task_running = False


def add_notification(request: Request, message: str, type: str, url: str = ""):
    request.app.state.new_notifications.append(
        {
            "id": generate_uuid(),
            "message": message,
            "type": type,
            "read": False,
            "timestamp": time.time(),
            "url": url,
        }
    )


def custom_exception_handler(request: Request, exc: Exception):
    # Log the exception details
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Prepare the context for the error page
    context = {"request": request, "exception": exc}

    if "You are not logged in" in str(exc):
        return RedirectResponse("/medperf_login?redirect=true")

    # Return a detailed error page
    return templates.TemplateResponse("error.html", context, status_code=500)


def sort_associations_display(associations: list[Association]) -> list[Association]:
    """
    Sorts associations:
    - by approval status (pending, approved, rejected)
    - by date (recent first)
    Args:
        associations: associations to sort
    Returns: sorted list
    """

    approval_status_order = {
        Status.PENDING: 0,
        Status.APPROVED: 1,
        Status.REJECTED: 2,
    }

    def assoc_sorting_key(assoc):
        # lower status - first
        status_order = approval_status_order.get(assoc.approval_status, -1)
        # recent associations - first
        date_order = -(assoc.approved_at or assoc.created_at).timestamp()
        return status_order, date_order

    return sorted(associations, key=assoc_sorting_key)


api_key_cookie = APIKeyCookie(name=AUTH_COOKIE_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_current_user_ui(
    request: Request,
    token: str = Security(api_key_cookie),
):
    if token == security_token:
        return True
    else:
        login_url = f"/security_check?redirect_url={request.url.path}"
        raise NotAuthenticatedException(redirect_url=login_url)


def get_current_user_api(
    token: str = Security(api_key_cookie),
):
    if token == security_token:
        return True
    else:
        raise HTTPException(status_code=401, detail="Not authorized")
