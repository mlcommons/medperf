# docstring_parameter decorator taken from
# https://stackoverflow.com/questions/10307696/how-to-put-a-variable-into-python-docstring
import typer
import logging
import functools
from merge_args import merge_args
from collections.abc import Callable

from medperf.utils import pretty_error


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
        except Exception as e:
            logging.error("An unexpected error occured. Terminating.")
            logging.exception(e)
            pretty_error(str(e))

    return wrapper


def configurable(with_args: bool = True) -> Callable:
    """Decorator that adds common configuration options to a typer command

    Args:
        func (Callable): function to be decorated
        with_args (bool, optional): Wether to expect arguments or just flags. Defaults to True.

    Returns:
        Callable: decorated function
    """
    def decorator(func):
        atype = str # common argument type
        cleanup_opts = "--cleanup/--no-cleanup"
        default_val = None
        if not with_args:
            atype = bool
            cleanup_opts = "--cleanup"
        @merge_args(func)
        def wrapper(
            ctx: typer.Context,
            server: atype = typer.Option(default_val, "--server", help="URL of a hosted MedPerf API instance"),
            certificate: atype = typer.Option(default_val, "--certificate", help="path to a valid SSL certificate"),
            comms: atype = typer.Option(default_val, "--comms", help="communications interface to use. [REST]"),
            ui: atype = typer.Option(default_val, "--ui", help="UI interface to use. [CLI]"),
            loglevel: atype = typer.Option(default_val, "--loglevel", help="Logging level [debug | info | warning | error]"),
            prepare_timeout: atype = typer.Option(default_val, "--prepare_timeout", help="Maximum time in seconds before interrupting prepare task"),
            sanity_check_timeout: atype = typer.Option(default_val, "--sanity_check_timeout", help="Maximum time in seconds before interrupting sanity_check task"),
            statistics_timeout: atype = typer.Option(default_val, "--statistics_timeout", help="Maximum time in seconds before interrupting statistics task"),
            infer_timeout: atype = typer.Option(default_val, "--infer_timeout", help="Maximum time in seconds before interrupting infer task"),
            evaluate_timeout: atype = typer.Option(default_val, "--evaluate_timeout", help="Maximum time in seconds before interrupting evaluate task"),
            platform: atype = typer.Option(default_val, "--platform", help="Platform to use for MLCube. [docker | singularity]"),
            cleanup: bool = typer.Option(default_val, cleanup_opts, help="Wether to clean up temporary medperf storage after execution"),
            **kwargs):
            assigned_params = [k for k, v in ctx.params.items() if v is not None]
            config_assigned_params = set(assigned_params) - set(kwargs.keys())
            config_dict = {key: ctx.params[key] for key in config_assigned_params}
            ctx.config_dict = config_dict
            return func(ctx, **kwargs)
        return wrapper
    return decorator
