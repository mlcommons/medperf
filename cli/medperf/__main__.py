import typer
import logging
import logging.handlers
from os.path import expanduser, abspath

from medperf import __version__
import medperf.config as config
from medperf.ui.factory import UIFactory
from medperf.decorators import clean_except, configurable
from medperf.comms.factory import CommsFactory
import medperf.commands.result.result as result
from medperf.commands.result.create import BenchmarkExecution
from medperf.commands.result.submit import ResultSubmission
import medperf.commands.mlcube.mlcube as mlcube
import medperf.commands.dataset.dataset as dataset
from medperf.commands.auth import Login, PasswordChange, SynapseLogin
import medperf.commands.benchmark.benchmark as benchmark
import medperf.commands.profile as profile
from medperf.utils import (
    set_custom_config,
    set_unique_tmp_config,
    init_storage,
    setup_logging,
    cleanup,
)
import medperf.commands.association.association as association
from medperf.commands.compatibility_test import CompatibilityTestExecution


app = typer.Typer()
app.add_typer(mlcube.app, name="mlcube", help="Manage mlcubes")
app.add_typer(result.app, name="result", help="Manage results")
app.add_typer(dataset.app, name="dataset", help="Manage datasets")
app.add_typer(benchmark.app, name="benchmark", help="Manage benchmarks")
app.add_typer(mlcube.app, name="mlcube", help="Manage mlcubes")
app.add_typer(result.app, name="result", help="Manage results")
app.add_typer(association.app, name="association", help="Manage associations")
app.add_typer(profile.app, name="profile", help="Manage profiles")


@app.command("synapse_login")
@clean_except
def synapse_login(
    username: str = typer.Option(
        None, "--username", "-u", help="Username to login with"
    ),
    password: str = typer.Option(
        None, "--password", "-p", help="Password to login with"
    ),
    token: str = typer.Option(
        None, "--token", "-t", help="Personal Access Token to login with"
    ),
):
    """Login to the synapse server. Must be done only once.
    Provide either a username and a password, or a token
    """
    SynapseLogin.run(username=username, password=password, token=token)
    config.ui.print("✅ Done!")


@app.command("login")
@clean_except
def login(
    username: str = typer.Option(
        None, "--username", "-u", help="Username to login with"
    ),
    password: str = typer.Option(
        None, "--password", "-p", help="Password to login with"
    ),
):
    """Login to the medperf server. Must be done only once.
    """
    Login.run(username=username, password=password)
    config.ui.print("✅ Done!")


@app.command("passwd")
@clean_except
def passwd():
    """Set a new password. Must be logged in.
    """
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    PasswordChange.run()
    ui.print("✅ Done!")


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
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model
    """
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


@app.command("test")
@clean_except
def test(
    benchmark_uid: int = typer.Option(
        None,
        "--benchmark",
        "-b",
        help="UID of the benchmark to test. If not passed, a temporary benchmark is created.",
    ),
    data_uid: str = typer.Option(
        None,
        "--data_uid",
        "-d",
        help="Prepared Dataset UID. Used for dataset testing. Optional. Defaults to benchmark demo dataset.",
    ),
    data_prep: str = typer.Option(
        None,
        "--data_preparation",
        "-p",
        help="UID or local path to the data preparation mlcube. Optional. Defaults to benchmark data preparation mlcube.",
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help="UID or local path to the model mlcube. Optional. Defaults to benchmark reference mlcube.",
    ),
    evaluator: str = typer.Option(
        None,
        "--evaluator",
        "-e",
        help="UID or local path to the evaluator mlcube. Optional. Defaults to benchmark evaluator mlcube",
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Execute the test even if results already exist",
    ),
):
    """
    Executes a compatibility test for a determined benchmark.
    Can test prepared datasets, remote and local models independently.
    """
    CompatibilityTestExecution.run(
        benchmark_uid, data_uid, data_prep, model, evaluator, no_cache=no_cache,
    )
    config.ui.print("✅ Done!")
    cleanup()


@app.callback()
@configurable
def main(ctx: typer.Context):
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

    config.ui = UIFactory.create_ui(config.ui)
    config.comms = CommsFactory.create_comms(config.comms, config.server)

    config.ui.print(f"MedPerf {__version__}")


if __name__ == "__main__":
    app()
