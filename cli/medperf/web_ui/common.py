import logging

from fastapi.templating import Jinja2Templates
from importlib import resources

from fastapi.requests import Request

from medperf.entities.association import Association
from medperf.enums import Status

templates = Jinja2Templates(directory=str(resources.path("medperf.web_ui", "templates")))

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
