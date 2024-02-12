import re
import logging
from logging import handlers
from .filters.redacting_filter import RedactingFilter


def setup_logging(log_file: str, loglevel: str):
    log_fmt = "%(asctime)s | %(module)s.%(funcName)s | %(levelname)s: %(message)s"
    handler = handlers.RotatingFileHandler(log_file, backupCount=20)
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
