import typer
import logging
from os.path import abspath, expanduser

from medperf.commands import (
    BenchmarkExecution,
    ResultSubmission,
    Login,
    CompatibilityTestExecution,
)
import medperf.config as config
from medperf.utils import init_storage, storage_path, cleanup
from medperf.decorators import clean_except
from medperf.comms import CommsFactory
from medperf.ui import UIFactory
from medperf.utils import init_storage
from medperf.commands.dataset import dataset


app = typer.Typer()
app.add_typer(dataset.app, name="dataset", help="Manage datasets")


@clean_except
@app.command("login")
def login():
    """Login to the medperf server. Must be done only once.
    """
    Login.run(config.comms, config.ui)


@clean_except
@app.command("execute")
def execute(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help="UID of the desired benchmark"
    ),
    data_uid: str = typer.Option(
        ..., "--data_uid", "-d", help="Registered Dataset UID"
    ),
    model_uid: int = typer.Option(
        ..., "--model_uid", "-m", help="UID of model to execute"
    ),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model
    """
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    BenchmarkExecution.run(benchmark_uid, data_uid, model_uid, comms, ui)
    ResultSubmission.run(benchmark_uid, data_uid, model_uid, comms, ui)
    ui.print("✅ Done!")
    cleanup()


@clean_except
@app.command("test")
def execute(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help="UID of the desired benchmark"
    ),
    data_uid: str = typer.Option(
        None,
        "--data_uid",
        "-d",
        help="Registered Dataset UID. Used for dataset testing. Optional. Defaults to benchmark demo dataset.",
    ),
    model_uid: int = typer.Option(
        None,
        "--model_uid",
        "-m",
        help="UID of model to execute. Used for model testing. Optional. defaults to benchmark reference cube.",
    ),
    cube_path: str = typer.Option(
        None,
        "--cube_path",
        "-c",
        help="Path to a local implementation of an mlcube. Used for local model testing. Optional. defaults to None.",
    ),
):
    """Executes a compatibility test for a determined benchmark. Can test prepared datasets, remote and local models independently."""
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    CompatibilityTestExecution.run(
        benchmark_uid, comms, ui, data_uid, model_uid, cube_path
    )
    ui.print("✅ Done!")
    cleanup()


@clean_except
@app.command("submit")
def submit(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help="UID of the executed benchmark"
    ),
    data_uid: int = typer.Option(
        ..., "--data_uid", "-d", help="UID of the dataset used for results"
    ),
    model_uid: int = typer.Option(
        ..., "--model_uid", "-m", help="UID of the executed model"
    ),
):
    """Submits already obtained results to the server"""
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    ResultSubmission.run(benchmark_uid, data_uid, model_uid, comms, ui)
    ui.print("✅ Done!")
    cleanup()


@app.callback()
def main(
    log: str = "INFO",
    log_file: str = None,
    comms: str = config.default_comms,
    ui: str = config.default_ui,
    host: str = config.server,
    storage: str = config.storage,
):
    # Set configuration variables
    config.storage = abspath(expanduser(storage))
    if log_file is None:
        log_file = storage_path(config.log_file)
    else:
        log_file = abspath(expanduser(log_file))

    init_storage()
    log = log.upper()
    log_lvl = getattr(logging, log)
    log_fmt = "%(asctime)s | %(levelname)s: %(message)s"
    logging.basicConfig(filename=log_file, level=log_lvl, format=log_fmt)
    logging.info(f"Running MedPerf v{config.version} on {log} logging level")

    config.ui = UIFactory.create_ui(ui)
    config.comms = CommsFactory.create_comms(comms, config.ui, host)

    config.ui.print(f"MedPerf {config.version}")


if __name__ == "__main__":
    app()
