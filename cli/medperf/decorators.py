from collections.abc import Callable
import logging

from medperf.utils import cleanup


def clean_except(func: Callable) -> Callable:
    """Decorator for handling unexpected errors. It allows logging
    and cleaning the project's directory before throwing the error.

    Args:
        func (Callable): Function to handle for unexpected errors

    Returns:
        Callable: Decorated function
    """

    def wrapper():
        try:
            logging.info(f"Running function '{func.__name__}'")
            func()
        except Exception as e:
            logging.error("An unexpected error occured. Terminating.")
            logging.error(e)
            cleanup()
            raise e

    return wrapper
