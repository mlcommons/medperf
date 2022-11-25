import logging
import functools
from collections.abc import Callable

from medperf.utils import pretty_error, cleanup
from medperf.exceptions import MedperfException, CleanExit
import medperf.config as config


def clean_except(func: Callable) -> Callable:
    """Decorator for handling unexpected errors. It allows logging
    and cleaning the project's directory before throwing the error.

    Args:
        func (Callable): Function to handle for unexpected errors

    Returns:
        Callable: Decorated function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logging.info(f"Running function '{func.__name__}'")
            func(*args, **kwargs)
        except CleanExit as e:
            logging.exception(e)
            config.ui.print(str(e))
            if e.clean:
                cleanup()
        except MedperfException as e:
            logging.exception(e)
            pretty_error(str(e), clean=e.clean)
        except Exception as e:
            logging.error("An unexpected error occured. Terminating.")
            logging.exception(e)
            pretty_error(str(e))

    return wrapper
