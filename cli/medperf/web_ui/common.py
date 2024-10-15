import logging
from pathlib import Path

from fastapi.templating import Jinja2Templates
from importlib import resources

from fastapi.requests import Request

from medperf.config_management import config
from medperf.entities.association import Association
from medperf.enums import Status

templates_folder_path = Path(resources.files("medperf.web_ui")) / "templates"  # noqa
templates = Jinja2Templates(directory=templates_folder_path)

logger = logging.getLogger(__name__)


async def custom_exception_handler(request: Request, exc: Exception):
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


def list_profiles() -> list[str]:
    return list(config.profiles)


def get_active_profile() -> str:
    return config.active_profile_name


def get_profiles_context():
    profiles = list_profiles()
    active_profile = get_active_profile()
    context = {
        "profiles": profiles,
        "active_profile": active_profile,
    }
    return context
