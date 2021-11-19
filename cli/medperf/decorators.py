from typing import Type
from collections.abc import Callable
import logging
import os

from medperf.utils import cleanup, pretty_error
from medperf.entities import Server
from medperf.config import config


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


def authenticate(func: Callable) -> Callable:
    """Decorator for exeuting a command as an authenticated user. For this, the
    decorator initializes and authenticates a server instance with the already
    saved credentials token in ~/.medperf/credentials

    Decorated command MUST have a parameter named server

    CLI must have been setup before with:
        medperf login

    Args:
        func (Callable): command to run as an authenticated user

    Returns:
        Callable: command wrapped with the authentication layer
    """

    def wrapper(*args, **kwargs):
        cred_path = config["credentials_path"]
        if os.path.exists(cred_path):
            with open(cred_path) as f:
                token = f.readline()
        else:
            pretty_error(
                "Couldn't find credentials file. Did you run 'medperf login' before?"
            )

        server = Server(config["server"], token)

        kwargs["server"] = server
        return func(*args, **kwargs)

    return wrapper
