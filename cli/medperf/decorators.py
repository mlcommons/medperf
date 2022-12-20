import typer
import logging
import functools
from merge_args import merge_args
from collections.abc import Callable
from medperf.utils import (
    pretty_error,
    cleanup,
    init_config,
    read_config,
    set_custom_config,
)
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


def configurable(func: Callable) -> Callable:
    """Decorator that adds common configuration options to a typer command

    Args:
        func (Callable): function to be decorated

    Returns:
        Callable: decorated function
    """
    # initialize config if it is not yet initialized
    init_config()
    # Set profile parameters
    config_p = read_config()
    set_custom_config(config_p.active_profile)

    @merge_args(func)
    def wrapper(
        *args,
        server: str = typer.Option(
            config.server, "--server", help="URL of a hosted MedPerf API instance",
        ),
        certificate: str = typer.Option(
            config.certificate, "--certificate", help="path to a valid SSL certificate",
        ),
        comms: str = typer.Option(
            config.comms, "--comms", help="communications interface to use. [REST]",
        ),
        ui: str = typer.Option(config.ui, "--ui", help="UI interface to use. [CLI]"),
        loglevel: str = typer.Option(
            config.loglevel,
            "--loglevel",
            help="Logging level [debug | info | warning | error]",
        ),
        prepare_timeout: int = typer.Option(
            config.prepare_timeout,
            "--prepare_timeout",
            help="Maximum time in seconds before interrupting prepare task",
        ),
        sanity_check_timeout: int = typer.Option(
            config.sanity_check_timeout,
            "--sanity_check_timeout",
            help="Maximum time in seconds before interrupting sanity_check task",
        ),
        statistics_timeout: int = typer.Option(
            config.statistics_timeout,
            "--statistics_timeout",
            help="Maximum time in seconds before interrupting statistics task",
        ),
        infer_timeout: int = typer.Option(
            config.infer_timeout,
            "--infer_timeout",
            help="Maximum time in seconds before interrupting infer task",
        ),
        evaluate_timeout: int = typer.Option(
            config.evaluate_timeout,
            "--evaluate_timeout",
            help="Maximum time in seconds before interrupting evaluate task",
        ),
        platform: str = typer.Option(
            config.platform,
            "--platform",
            help="Platform to use for MLCube. [docker | singularity]",
        ),
        cleanup: bool = typer.Option(
            config.cleanup,
            "--cleanup/--no-cleanup",
            help="Wether to clean up temporary medperf storage after execution",
        ),
        **kwargs,
    ):
        return func(*args, **kwargs)

    return wrapper
