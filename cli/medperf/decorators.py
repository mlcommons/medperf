import sys
import typer
import logging
import functools
from merge_args import merge_args
from collections.abc import Callable
from medperf.utils import pretty_error, cleanup
from medperf.exceptions import MedperfException, CleanExit
import medperf.config as config


def clean_except(func: Callable) -> Callable:
    """Decorator for handling errors. It allows logging
    and cleaning the project's directory before throwing the error.

    Args:
        func (Callable): Function to handle for errors

    Returns:
        Callable: Decorated function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logging.info(f"Running function '{func.__name__}'")
            func(*args, **kwargs)
        except CleanExit as e:
            logging.info(str(e))
            config.ui.print(str(e))
        except MedperfException as e:
            logging.exception(e)
            pretty_error(str(e))
            sys.exit(1)
        except Exception as e:
            logging.error("An unexpected error occured. Terminating.")
            logging.exception(e)
            raise e
        finally:
            cleanup()

    return wrapper


def configurable(func: Callable) -> Callable:
    """Decorator that adds common configuration options to a typer command

    Args:
        func (Callable): function to be decorated

    Returns:
        Callable: decorated function
    """

    # NOTE: changing parameters here should be accompanied
    #       by changing configurable_parameters
    @merge_args(func)
    def wrapper(
        *args,
        server: str = typer.Option(
            config.server, "--server", help="URL of a hosted MedPerf API instance"
        ),
        auth_class: str = typer.Option(
            config.auth_class,
            "--auth_class",
            help="Authentication interface to use [Auth0]",
        ),
        auth_domain: str = typer.Option(
            config.auth_domain, "--auth_domain", help="Auth0 domain name"
        ),
        auth_jwks_url: str = typer.Option(
            config.auth_jwks_url, "--auth_jwks_url", help="Auth0 Json Web Key set URL"
        ),
        auth_idtoken_issuer: str = typer.Option(
            config.auth_idtoken_issuer,
            "--auth_idtoken_issuer",
            help="Auth0 ID token issuer",
        ),
        auth_client_id: str = typer.Option(
            config.auth_client_id, "--auth_client_id", help="Auth0 client ID"
        ),
        auth_audience: str = typer.Option(
            config.auth_audience,
            "--auth_audience",
            help="Server's Auth0 API identifier",
        ),
        certificate: str = typer.Option(
            config.certificate, "--certificate", help="path to a valid SSL certificate"
        ),
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
        container_loglevel: str = typer.Option(
            config.container_loglevel,
            "--container-loglevel",
            help="Logging level for containers to be run [debug | info | warning | error]",
        ),
        platform: str = typer.Option(
            config.platform,
            "--platform",
            help="Platform to use for MLCube. [docker | singularity]",
        ),
        gpus: str = typer.Option(
            config.gpus,
            "--gpus",
            help="""
            What GPUs to expose to MLCube.
            Accepted Values are comma separated GPU IDs (e.g "1,2"), or \"all\".
            MLCubes that aren't configured to use GPUs won't be affected by this.
            Defaults to all available GPUs""",
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


def add_inline_parameters(func: Callable) -> Callable:
    """Decorator that adds common configuration options to a typer command

    Args:
        func (Callable): function to be decorated

    Returns:
        Callable: decorated function
    """

    # NOTE: changing parameters here should be accompanied
    #       by changing config.inline_parameters
    @merge_args(func)
    def wrapper(
        *args,
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
        container_loglevel: str = typer.Option(
            config.container_loglevel,
            "--container-loglevel",
            help="Logging level for containers to be run [debug | info | warning | error]",
        ),
        platform: str = typer.Option(
            config.platform,
            "--platform",
            help="Platform to use for MLCube. [docker | singularity]",
        ),
        gpus: str = typer.Option(
            config.gpus,
            "--gpus",
            help="""
            What GPUs to expose to MLCube.
            Accepted Values are:\n
            - "" or 0: to expose no GPUs (e.g.: --gpus="")\n
            - "all": to expose all GPUs. (e.g.: --gpus=all)\n
            - an integer: to expose a certain number of GPUs. ONLY AVAILABLE FOR DOCKER
            (e.g., --gpus=2 to expose 2 GPUs)\n
            - Form "device=<id1>,<id2>": to expose specific GPUs.
            (e.g., --gpus="device=0,2")\n""",
        ),
        cleanup: bool = typer.Option(
            config.cleanup,
            "--cleanup/--no-cleanup",
            help="Whether to clean up temporary medperf storage after execution",
        ),
        **kwargs,
    ):
        return func(*args, **kwargs)

    return wrapper
