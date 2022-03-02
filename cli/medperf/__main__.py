import typer
import logging
from os.path import abspath, expanduser

from medperf.commands import Login
from medperf.commands.benchmark import CompatibilityTestExecution
from medperf.commands.result import result
import medperf.config as config
from medperf.utils import init_storage, storage_path, cleanup
from medperf.decorators import clean_except
from medperf.comms import CommsFactory
from medperf.ui import UIFactory
from medperf.utils import init_storage
from medperf.commands.dataset import dataset
from medperf.commands.benchmark import benchmark


app = typer.Typer()
app.add_typer(result.app, name="result", help="Manage results")
app.add_typer(dataset.app, name="dataset", help="Manage datasets")
app.add_typer(benchmark.app, name="benchmark", help="Manage benchmarks")


@clean_except
@app.command("login")
def login():
    """Login to the medperf server. Must be done only once.
    """
    Login.run(config.comms, config.ui)


@clean_except
@app.command("run")
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
    result.run_benchmark(
        benchmark_uid=benchmark_uid, data_uid=data_uid, model_uid=model_uid
    )


@clean_except
@app.command("test")
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
        help="Registered Dataset UID. Used for dataset testing. Optional. Defaults to benchmark demo dataset.",
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
        "--evaluator",
        "-e",
        help="UID or local path to the evaluator mlcube. Optional. Defaults to benchmark evaluator mlcube",
    ),
):
    """Executes a compatibility test for a determined benchmark. Can test prepared datasets, remote and local models independently."""
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    CompatibilityTestExecution.run(
        benchmark_uid, comms, ui, data_uid, data_prep, model, evaluator
    )
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
