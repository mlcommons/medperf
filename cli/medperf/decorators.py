import sys
import typer
import logging
import functools
from merge_args import merge_args
from collections.abc import Callable
from medperf.utils import pretty_error, cleanup
from medperf.logging.utils import package_logs
from medperf.exceptions import MedperfException, CleanExit
import medperf.config as config
import medperf.help_texts as help_texts


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
            sys.exit(e.medperf_status_code)
        except MedperfException as e:
            logging.exception(e)
            pretty_error(str(e))
            sys.exit(1)
        except Exception as e:
            logging.error("An unexpected error occured. Terminating.")
            logging.exception(e)
            raise e
        finally:
            package_logs()
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
            config.server, "--server", help=help_texts.GlobalOptions.server
        ),
        auth_class: str = typer.Option(
            config.auth_class,
            "--auth_class",
            help=help_texts.GlobalOptions.auth_class,
        ),
        auth_domain: str = typer.Option(
            config.auth_domain,
            "--auth_domain",
            help=help_texts.GlobalOptions.auth_domain,
        ),
        auth_jwks_url: str = typer.Option(
            config.auth_jwks_url,
            "--auth_jwks_url",
            help=help_texts.GlobalOptions.auth_jwks_url,
        ),
        auth_idtoken_issuer: str = typer.Option(
            config.auth_idtoken_issuer,
            "--auth_idtoken_issuer",
            help=help_texts.GlobalOptions.auth_idtoken_issuer,
        ),
        auth_client_id: str = typer.Option(
            config.auth_client_id,
            "--auth_client_id",
            help=help_texts.GlobalOptions.auth_client_id,
        ),
        auth_audience: str = typer.Option(
            config.auth_audience,
            "--auth_audience",
            help=help_texts.GlobalOptions.auth_audience,
        ),
        certificate: str = typer.Option(
            config.certificate,
            "--certificate",
            help=help_texts.GlobalOptions.certificate,
        ),
        loglevel: str = typer.Option(
            config.loglevel,
            "--loglevel",
            help=help_texts.GlobalOptions.loglevel,
        ),
        prepare_timeout: int = typer.Option(
            config.prepare_timeout,
            "--prepare_timeout",
            help=help_texts.GlobalOptions.prepare_timeout,
        ),
        sanity_check_timeout: int = typer.Option(
            config.sanity_check_timeout,
            "--sanity_check_timeout",
            help=help_texts.GlobalOptions.sanity_check_timeout,
        ),
        statistics_timeout: int = typer.Option(
            config.statistics_timeout,
            "--statistics_timeout",
            help=help_texts.GlobalOptions.statistics_timeout,
        ),
        infer_timeout: int = typer.Option(
            config.infer_timeout,
            "--infer_timeout",
            help=help_texts.GlobalOptions.infer_timeout,
        ),
        evaluate_timeout: int = typer.Option(
            config.evaluate_timeout,
            "--evaluate_timeout",
            help=help_texts.GlobalOptions.evaluate_timeout,
        ),
        container_loglevel: str = typer.Option(
            config.container_loglevel,
            "--container-loglevel",
            help=help_texts.GlobalOptions.container_loglevel,
        ),
        platform: str = typer.Option(
            config.platform,
            "--platform",
            help=help_texts.GlobalOptions.platform,
        ),
        gpus: str = typer.Option(
            config.gpus,
            "--gpus",
            help=help_texts.GlobalOptions.gpus,
        ),
        cleanup: bool = typer.Option(
            config.cleanup,
            "--cleanup/--no-cleanup",
            help=help_texts.GlobalOptions.cleanup,
        ),
        certificate_authority_id: int = typer.Option(
            config.certificate_authority_id,
            "--certificate_authority_id",
            help=help_texts.GlobalOptions.certificate_authority_id,
        ),
        certificate_authority_fingerprint: str = typer.Option(
            config.certificate_authority_fingerprint,
            "--certificate_authority_fingerprint",
            help=help_texts.GlobalOptions.certificate_authority_fingerprint,
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
            help=help_texts.GlobalOptions.loglevel,
        ),
        prepare_timeout: int = typer.Option(
            config.prepare_timeout,
            "--prepare_timeout",
            help=help_texts.GlobalOptions.prepare_timeout,
        ),
        sanity_check_timeout: int = typer.Option(
            config.sanity_check_timeout,
            "--sanity_check_timeout",
            help=help_texts.GlobalOptions.sanity_check_timeout,
        ),
        statistics_timeout: int = typer.Option(
            config.statistics_timeout,
            "--statistics_timeout",
            help=help_texts.GlobalOptions.statistics_timeout,
        ),
        infer_timeout: int = typer.Option(
            config.infer_timeout,
            "--infer_timeout",
            help=help_texts.GlobalOptions.infer_timeout,
        ),
        evaluate_timeout: int = typer.Option(
            config.evaluate_timeout,
            "--evaluate_timeout",
            help=help_texts.GlobalOptions.evaluate_timeout,
        ),
        container_loglevel: str = typer.Option(
            config.container_loglevel,
            "--container-loglevel",
            help=help_texts.GlobalOptions.container_loglevel,
        ),
        platform: str = typer.Option(
            config.platform,
            "--platform",
            help=help_texts.GlobalOptions.platform,
        ),
        gpus: str = typer.Option(
            config.gpus,
            "--gpus",
            help=help_texts.GlobalOptions.gpus_inline,
        ),
        shm_size: str = typer.Option(
            config.shm_size,
            "--shm-size",
            help=help_texts.GlobalOptions.shm_size,
        ),
        cleanup: bool = typer.Option(
            config.cleanup,
            "--cleanup/--no-cleanup",
            help=help_texts.GlobalOptions.cleanup,
        ),
        **kwargs,
    ):
        return func(*args, **kwargs)

    return wrapper
