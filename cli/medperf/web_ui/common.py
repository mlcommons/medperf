import logging
from pathlib import Path

import anyio
from fastapi import HTTPException, Security
from fastapi.security import APIKeyCookie, APIKeyHeader
from fastapi.templating import Jinja2Templates
from importlib import resources
from urllib.parse import urlparse

from fastapi.requests import Request
from medperf import config
from starlette.responses import RedirectResponse
from pydantic.datetime_parse import parse_datetime

from medperf.enums import Status
from medperf.exceptions import CleanExit
from medperf.web_ui.auth import (
    security_token,
    AUTH_COOKIE_NAME,
    API_KEY_NAME,
    NotAuthenticatedException,
)

from medperf.account_management.account_management import (
    get_medperf_user_data,
    read_user_account,
)
from medperf.web_ui.schemas import WebUITask
from medperf.web_ui.utils import generate_uuid
import medperf.help_texts as help_texts

templates_folder_path = Path(resources.files("medperf.web_ui")) / "templates"
templates = Jinja2Templates(directory=templates_folder_path)
templates.env.globals["help_texts"] = help_texts

logger = logging.getLogger(__name__)

ALLOWED_PATHS = [
    "/events",
    "/notifications",
    "/current_task",
    "/api/running_tasks",
    "/api/task_history",
    "/api/stop_task",
    "/api/support",
    "/containers/auto_access_logs",
]


def initialize_state_task(request: Request, task_name: str) -> str:
    form_data = dict(anyio.from_thread.run(lambda: request.form()))
    new_task_id = generate_uuid()
    config.ui.start_task(new_task_id, task_name)
    request.app.state.task = WebUITask(
        id=new_task_id, name=task_name, running=True, formData=form_data
    )
    request.app.state.task_running = True

    return new_task_id


def reset_state_task(request: Request):
    current_task = request.app.state.task
    current_task.set_running(False)
    if len(request.app.state.old_tasks) == 10:
        request.app.state.old_tasks.pop(0)
    request.app.state.old_tasks.append(current_task)
    request.app.state.task = WebUITask()
    request.app.state.task_running = False


class UITask:
    """Run the body of a `with` block as a web UI task.

    Replaces the boilerplate shared by the routes that run a MedPerf command:
    it starts the task (so its logs are streamed to the page), catches and logs
    any exception raised by the block, sets the task status and ends it. The
    exception is not propagated: the route then sends the notification and
    returns the task response, whatever the outcome.

    The task status is one of:
        "success": the block finished.
        "info": the block stopped with a CleanExit, which, as in the CLI
            (see decorators.clean_except), is not an error: e.g. the user
            declined a prompt, or there was nothing to do.
        "failed": the block raised any other exception.

    Example:
        with UITask(request, "register_container", response={"entity_id": None}) as task:
            container_id = SubmitCube.run(...)
            task.response["entity_id"] = container_id
        task.notify(
            success_message="Container successfully registered",
            failure_message="Failed to register container",
        )
        return task.response

    Attributes:
        response (dict): the task response ("status", "error" and any extra field),
            returned to the page and passed to the notification. "error" holds
            the error, or the reason the task stopped.
    """

    def __init__(self, request: Request, task_name: str, response: dict = None):
        self.request = request
        self.task_name = task_name
        self.response = {"status": "", "error": "", **(response or {})}

    @property
    def succeeded(self) -> bool:
        return self.response["status"] == "success"

    def __enter__(self):
        initialize_state_task(self.request, task_name=self.task_name)
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc is None:
            self.response["status"] = "success"
        elif isinstance(exc, CleanExit) and exc.medperf_status_code == 0:
            self.response["status"] = "info"
            self.response["error"] = str(exc)
            logger.info(str(exc))
        else:
            self.response["status"] = "failed"
            self.response["error"] = str(exc)
            if isinstance(exc, Exception):
                logger.exception(exc, exc_info=(exc_type, exc, traceback))
        self._end()
        # Exceptions are reported in the response instead of being raised;
        # anything else (e.g. KeyboardInterrupt) still propagates
        return exc is None or isinstance(exc, Exception)

    def _end(self):
        config.ui.end_task(self.response)
        reset_state_task(self.request)

    def notify(self, success_message: str, failure_message: str, url: str = ""):
        """Notify the user of the task outcome: a failure also shows its error,
        and a task stopped with a CleanExit shows the reason it stopped.

        Args:
            success_message (str): message shown if the task succeeded.
            failure_message (str): message shown if the task failed.
            url (str, optional): page opened from the notification.
        """
        if self.response["status"] == "info":
            message = self.response["error"]
        elif self.succeeded:
            message = success_message
        else:
            message = failure_message
        config.ui.add_notification(
            message=message, return_response=self.response, url=url
        )


def custom_exception_handler(request: Request, exc: Exception):
    # Log the exception details
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Prepare the context for the error page
    context = {"request": request, "exception": exc}

    if "You are not logged in" in str(exc):
        return RedirectResponse("/medperf_login?redirected=true")

    # Return a detailed error page
    return templates.TemplateResponse("error.html", context, status_code=500)


def sort_associations_display(associations: list[dict]) -> list[dict]:
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
        status_order = approval_status_order.get(assoc["approval_status"], -1)
        # recent associations - first
        date_order = -parse_datetime(
            assoc.get("approved_at") or assoc["created_at"]
        ).timestamp()
        return status_order, date_order

    return sorted(associations, key=assoc_sorting_key)


api_key_cookie = APIKeyCookie(name=AUTH_COOKIE_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def is_logged_in():
    return read_user_account() is not None


def process_notifications(request: Request):
    request.app.state.notifications = config.ui.get_all_notifications()
    request.app.state.unread_count = config.ui.get_unread_notifications_count()


def check_user_ui(
    request: Request,
    token: str = Security(api_key_cookie),
):
    logged_in = is_logged_in()
    request.app.state.logged_in = logged_in
    request.app.state.user_email = (
        get_medperf_user_data().get("email") if logged_in else None
    )
    process_notifications(request)
    if not request.app.state.task_running:
        request.app.state.global_events = config.ui.get_all_global_events()

    if token == security_token:
        return True

    login_url = f"/security_check?redirect_url={request.url.path}"
    raise NotAuthenticatedException(redirect_url=login_url)


def check_user_api(
    request: Request,
    token: str = Security(api_key_cookie),
):
    request_path = request.url.path

    request.app.state.logged_in = is_logged_in()
    if request.app.state.task_running:
        if not any(request_path.startswith(path) for path in ALLOWED_PATHS):
            raise HTTPException(
                status_code=400,
                detail="A task is currently running, please wait until it is finished",
            )
    if token == security_token:
        return True

    raise HTTPException(status_code=401, detail="Not authorized")


def sanitize_redirect_url(url: str, fallback: str = "/") -> bool:
    """Validate that the URL is a relative path or matches allowed hosts."""
    normalized_url = url.replace("\\", "")  # Normalize backslashes
    parsed = urlparse(normalized_url)
    if not parsed.netloc and not parsed.scheme:
        return normalized_url
    return fallback
