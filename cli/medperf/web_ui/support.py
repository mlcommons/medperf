"""Support helpers of the web UI.

Gathers what a user needs to ask for support: the latest lines of the web UI
log, some environment details, and the full logs package to attach to an email.
"""

import logging
import os
import platform
from collections import deque
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from medperf import config
from medperf._version import __version__
from medperf.logging.utils import package_logs
from medperf.web_ui.common import check_user_api
from medperf.web_ui.utils import strip_ansi

logger = logging.getLogger(__name__)

router = APIRouter()


def read_last_lines(path: str, max_lines: int) -> List[str]:
    """Return the last lines of a text file (an empty list if it doesn't exist).

    Args:
        path (str): path of the file.
        max_lines (int): maximum number of lines to return.
    """
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8", errors="replace") as f:
        return [line.rstrip("\n") for line in deque(f, maxlen=max_lines)]


def get_environment_details() -> dict:
    """Return details about the MedPerf installation that help troubleshooting."""
    return {
        "MedPerf version": __version__,
        "Server": config.server,
        "Container platform": config.platform,
        "Operating system": f"{platform.system()} {platform.release()}",
        "Python version": platform.python_version(),
    }


@router.get("/info", response_class=JSONResponse)
def support_info(current_user: bool = Depends(check_user_api)):
    """Return the support email, environment details and the latest web UI log lines."""
    log_file = os.path.join(config.logs_storage, config.webui_log_file)
    try:
        log_lines = read_last_lines(log_file, config.webui_max_log_messages)
    except OSError as e:
        logger.exception(e)
        log_lines = []
    return {
        "emails": config.webui_support_emails,
        "environment": get_environment_details(),
        "log_file": log_file,
        "log_lines": [strip_ansi(line) for line in log_lines],
    }


@router.get("/logs")
def download_logs(current_user: bool = Depends(check_user_api)):
    """Package all MedPerf log files and download them as a tarball."""
    package_logs()
    package_file = os.path.join(config.logs_storage, config.log_package_file)
    if not os.path.isfile(package_file):
        raise HTTPException(status_code=404, detail="No log files were found")
    return FileResponse(
        package_file,
        media_type="application/gzip",
        filename=config.log_package_file,
    )
