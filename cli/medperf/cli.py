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
import medperf.commands.asset.asset as asset
import medperf.commands.model.model as model_cmds
import medperf.commands.cc.cc as cc_cmds
import medperf.commands.storage as storage
import medperf.web_ui.app as web_ui
from medperf.utils import check_for_updates, get_webui_properties
from medperf.logging.utils import log_machine_details
import medperf.help_texts as help_texts

app = typer.Typer()
app.add_typer(mlcube.app, name="mlcube", help=help_texts.Groups.mlcube)
app.add_typer(mlcube.app, name="container", help=help_texts.Groups.container)
app.add_typer(execution.app, name="result", help=help_texts.Groups.result)
app.add_typer(dataset.app, name="dataset", help=help_texts.Groups.dataset)
app.add_typer(benchmark.app, name="benchmark", help=help_texts.Groups.benchmark)
app.add_typer(association.app, name="association", help=help_texts.Groups.association)
app.add_typer(profile.app, name="profile", help=help_texts.Groups.profile)
app.add_typer(compatibility_test.app, name="test", help=help_texts.Groups.test)
app.add_typer(auth.app, name="auth", help=help_texts.Groups.auth)
app.add_typer(storage.app, name="storage", help=help_texts.Groups.storage)
app.add_typer(training.app, name="training", help=help_texts.Groups.training)
app.add_typer(aggregator.app, name="aggregator", help=help_texts.Groups.aggregator)
app.add_typer(ca.app, name="ca", help=help_texts.Groups.ca)
app.add_typer(certificate.app, name="certificate", help=help_texts.Groups.certificate)
app.add_typer(asset.app, name="asset", help=help_texts.Groups.asset)
app.add_typer(model_cmds.app, name="model", help=help_texts.Groups.model)
app.add_typer(cc_cmds.app, name="confidential", help=help_texts.Groups.confidential)
app.add_typer(web_ui.app, name="web-ui", help=help_texts.Groups.web_ui)


@app.command("run")
@clean_except
def execute(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help=help_texts.Benchmark.uid
    ),
    data_uid: int = typer.Option(
        ..., "--data_uid", "-d", help=help_texts.Dataset.registered_uid
    ),
    model_uid: int = typer.Option(
        ..., "--model_uid", "-m", help=help_texts.Result.model_uid
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
    ignore_model_errors: bool = typer.Option(
        False,
        "--ignore-model-errors",
        help=help_texts.Common.ignore_model_errors,
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help=help_texts.Common.no_cache,
    ),
    new_result: bool = typer.Option(
        False,
        "--new-result",
        help=help_texts.Result.new_result,
    ),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    execution = BenchmarkExecution.run(
        benchmark_uid,
        data_uid,
        [model_uid],
        ignore_model_errors=ignore_model_errors,
        no_cache=no_cache,
        rerun_finalized_executions=new_result,
    )[0]
    ResultSubmission.run(execution.id, approved=approval)
    config.ui.print("✅ Done!")


@app.command("get_webui_properties")
@clean_except
def get_webui_props():
    """Prints necessary information to access an already-running medperf webui"""
    get_webui_properties()


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
