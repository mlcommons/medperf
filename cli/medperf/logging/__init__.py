import re
import os
import logging
from logging import handlers
from .filters.redacting_filter import RedactingFilter
from medperf import config


def setup_logging(log_file: str, loglevel: str):
    # Ensure root folder exists
    log_folder = os.path.dirname(log_file)
    os.makedirs(log_folder, exist_ok=True)

    log_fmt = "%(asctime)s | %(module)s.%(funcName)s | %(levelname)s: %(message)s"
    handler = handlers.RotatingFileHandler(log_file, backupCount=config.logs_backup_count)
    handler.setFormatter(logging.Formatter(log_fmt))
    logging.basicConfig(
        level=loglevel.upper(),
        handlers=[handler],
        format=log_fmt,
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )

    sensitive_pattern = re.compile(
        r"""(["']?(password|pwd|token)["']?[:=] ?)["'][^\n\[\]{}"']*["']"""
    )

    redacting_filter = RedactingFilter(patterns=[sensitive_pattern])
    requests_logger = logging.getLogger("requests")
    requests_logger.addHandler(handler)
    requests_logger.setLevel(loglevel.upper())
    logger = logging.getLogger()
    logger.addFilter(redacting_filter)

    # Force the creation of a new log file for each execution
    handler.doRollover()
