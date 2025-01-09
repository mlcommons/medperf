import logging
from pathlib import Path

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

templates_folder_path = Path(resources.files("medperf.web_ui")) / "templates"  # noqa
templates = Jinja2Templates(directory=templates_folder_path)

logger = logging.getLogger(__name__)


def custom_exception_handler(request: Request, exc: Exception):
    # Log the exception details
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Prepare the context for the error page
    context = {"request": request, "exception": exc}

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
        login_url = f"/login?redirect_url={request.url.path}"
        raise NotAuthenticatedException(redirect_url=login_url)


def get_current_user_api(
    token: str = Security(api_key_cookie),
):
    if token == security_token:
        return True
    else:
        raise HTTPException(status_code=401, detail="Not authorized")
