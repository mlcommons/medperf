import logging

from fastapi.templating import Jinja2Templates
from importlib import resources

from fastapi.requests import Request

templates = Jinja2Templates(directory=str(resources.path("medperf.web_ui", "templates")))

logger = logging.getLogger(__name__)


async def custom_exception_handler(request: Request, exc: Exception):
    # Log the exception details
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Prepare the context for the error page
    context = {"request": request, "exception": exc}

    # Return a detailed error page
    return templates.TemplateResponse("error.html", context, status_code=500)