import sys
import typer
import logging
import logging.handlers
from os.path import expanduser, abspath

from medperf import __version__
import medperf.config as config
from medperf.ui.factory import UIFactory
from medperf.decorators import clean_except, configurable
from medperf.comms.factory import CommsFactory
from medperf.comms.auth.auth0 import Auth
import medperf.commands.result.result as result
from medperf.commands.result.create import BenchmarkExecution
from medperf.commands.result.submit import ResultSubmission
import medperf.commands.mlcube.mlcube as mlcube
import medperf.commands.dataset.dataset as dataset
import medperf.commands.auth.auth as auth
import medperf.commands.benchmark.benchmark as benchmark
import medperf.commands.profile as profile
from medperf.utils import (
    set_custom_config,
    set_unique_tmp_config,
    init_storage,
    setup_logging,
)
import medperf.commands.association.association as association
import medperf.commands.compatibility_test.compatibility_test as compatibility_test


app = typer.Typer()
app.add_typer(mlcube.app, name="mlcube", help="Manage mlcubes")
app.add_typer(result.app, name="result", help="Manage results")
app.add_typer(dataset.app, name="dataset", help="Manage datasets")
app.add_typer(benchmark.app, name="benchmark", help="Manage benchmarks")
app.add_typer(mlcube.app, name="mlcube", help="Manage mlcubes")
app.add_typer(result.app, name="result", help="Manage results")
app.add_typer(association.app, name="association", help="Manage associations")
app.add_typer(profile.app, name="profile", help="Manage profiles")
app.add_typer(compatibility_test.app, name="test", help="Manage compatibility tests")
app.add_typer(auth.app, name="auth", help="Authentication")


@app.command("run")
@clean_except
def execute(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help="UID of the desired benchmark"
    ),
    data_uid: int = typer.Option(
        ..., "--data_uid", "-d", help="Registered Dataset UID"
    ),
    model_uid: int = typer.Option(
        ..., "--model_uid", "-m", help="UID of model to execute"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
    ignore_model_errors: bool = typer.Option(
        False,
        "--ignore-model-errors",
        help="Ignore failing model cubes, allowing for possibly submitting partial results",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Ignore existing results. The experiment then will be rerun",
    ),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    result = BenchmarkExecution.run(
        benchmark_uid,
        data_uid,
        [model_uid],
        ignore_model_errors=ignore_model_errors,
        no_cache=no_cache,
    )[0]
    if result.id:  # TODO: use result.is_registered once PR #338 is merged
        config.ui.print(  # TODO: msg should be colored yellow
            """An existing registered result for the requested execution has been\n
            found. If you wish to submit a new result for the same execution,\n
            please run the command again with the --no-cache option.\n"""
        )
    else:
        ResultSubmission.run(result.generated_uid, approved=approval)
    config.ui.print("✅ Done!")


def version_callback(value: bool):
    if value:
        print(f"MedPerf version {__version__}")
        raise typer.Exit()


@app.callback()
@configurable
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
):
    # Set inline parameters
    inline_args = ctx.params
    set_custom_config(inline_args)

    if config.certificate is not None:
        config.certificate = abspath(expanduser(config.certificate))

    set_unique_tmp_config()

    init_storage()
    log = config.loglevel.upper()
    log_lvl = getattr(logging, log)
    setup_logging(log_lvl)
    logging.info(f"Running MedPerf v{__version__} on {log_lvl} logging level")
    logging.info(f"Executed command: {' '.join(sys.argv[1:])}")

    config.ui = UIFactory.create_ui(config.ui)
    config.comms = CommsFactory.create_comms(config.comms, config.server)
    config.auth = Auth(**config.auth_settings)
    config.ui.print(f"MedPerf {__version__}")


if __name__ == "__main__":
    app()
