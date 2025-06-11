import sys
import typer
import logging
import logging.handlers

from medperf import __version__
import medperf.config as config
from medperf.decorators import clean_except, add_inline_parameters
from medperf.commands.execution import execution
from medperf.commands.execution.create import BenchmarkExecution
from medperf.commands.execution.submit import ResultSubmission
import medperf.commands.mlcube.mlcube as mlcube
import medperf.commands.dataset.dataset as dataset
import medperf.commands.auth.auth as auth
import medperf.commands.benchmark.benchmark as benchmark
import medperf.commands.profile as profile
import medperf.commands.association.association as association
import medperf.commands.compatibility_test.compatibility_test as compatibility_test
import medperf.commands.training.training as training
import medperf.commands.aggregator.aggregator as aggregator
import medperf.commands.ca.ca as ca
import medperf.commands.certificate.certificate as certificate
import medperf.commands.storage as storage

from medperf.utils import check_for_updates
from medperf.logging.utils import log_machine_details

app = typer.Typer()
app.add_typer(mlcube.app, name="mlcube", help="Manage mlcubes")
app.add_typer(mlcube.app, name="container", help="Manage containers")
app.add_typer(execution.app, name="result", help="Manage results")
app.add_typer(dataset.app, name="dataset", help="Manage datasets")
app.add_typer(benchmark.app, name="benchmark", help="Manage benchmarks")
app.add_typer(association.app, name="association", help="Manage associations")
app.add_typer(profile.app, name="profile", help="Manage profiles")
app.add_typer(compatibility_test.app, name="test", help="Manage compatibility tests")
app.add_typer(auth.app, name="auth", help="Authentication")
app.add_typer(storage.app, name="storage", help="Storage management")
app.add_typer(training.app, name="training", help="Manage training experiments")
app.add_typer(aggregator.app, name="aggregator", help="Manage aggregators")
app.add_typer(ca.app, name="ca", help="Manage CAs")
app.add_typer(certificate.app, name="certificate", help="Manage certificates")


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
        help="Ignore failing models, allowing for possibly submitting partial results",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Ignore existing results. The experiment then will be rerun",
    ),
    new_result: bool = typer.Option(
        False,
        "--new-result",
        help=(
            "Works if the result of the execution was already uploaded."
            "This will rerun and create a new record."
        ),
    ),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    BenchmarkExecution.run(
        benchmark_uid,
        data_uid,
        [model_uid],
        ignore_model_errors=ignore_model_errors,
        no_cache=no_cache,
        rerun_finalized_executions=new_result,
    )
    ResultSubmission.run(benchmark_uid, data_uid, model_uid, approved=approval)
    config.ui.print("✅ Done!")


def version_callback(value: bool):
    if value:
        print(f"MedPerf version {__version__}")
        raise typer.Exit()


@app.callback()
@add_inline_parameters
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
):
    # Set inline parameters
    inline_args = ctx.params
    for param in inline_args:
        setattr(config, param, inline_args[param])

    # Update logging level according to the passed inline params
    loglevel = config.loglevel.upper()
    logging.getLogger().setLevel(loglevel)
    logging.getLogger("requests").setLevel(loglevel)

    logging.info(f"Running MedPerf v{__version__} on {loglevel} logging level")
    logging.info(f"Executed command: {' '.join(sys.argv[1:])}")
    log_machine_details()
    check_for_updates()

    config.ui.print(f"MedPerf {__version__}")
