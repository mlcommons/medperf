import typer
import logging
import logging.handlers
from os.path import abspath, expanduser

import medperf.config as config
from medperf.ui.factory import UIFactory
from medperf.decorators import clean_except
from medperf.comms.factory import CommsFactory
import medperf.commands.result.result as result
import medperf.commands.mlcube.mlcube as mlcube
import medperf.commands.dataset.dataset as dataset
from medperf.commands.auth import Login, PasswordChange
import medperf.commands.benchmark.benchmark as benchmark
from medperf.utils import init_storage, storage_path, cleanup
from medperf.commands.compatibility_test import CompatibilityTestExecution


app = typer.Typer()
app.add_typer(mlcube.app, name="mlcube", help="Manage mlcubes")
app.add_typer(result.app, name="result", help="Manage results")
app.add_typer(dataset.app, name="dataset", help="Manage datasets")
app.add_typer(benchmark.app, name="benchmark", help="Manage benchmarks")
app.add_typer(mlcube.app, name="mlcube", help="Manage mlcubes")
app.add_typer(result.app, name="result", help="Manage results")


@app.command("login")
@clean_except
def login():
    """Login to the medperf server. Must be done only once.
    """
    Login.run(config.comms, config.ui)


@app.command("passwd")
@clean_except
def passwd():
    """Set a new password. Must be logged in.
    """
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    PasswordChange.run(comms, ui)
    ui.print("✅ Done!")


@app.command("run")
@clean_except
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
        None,
        "--evaluator",
        "-e",
        help="UID or local path to the evaluator mlcube. Optional. Defaults to benchmark evaluator mlcube",
    ),
):
    """
    Executes a compatibility test for a determined benchmark.
    Can test prepared datasets, remote and local models independently.
    """
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
    certificate: str = config.certificate,
    local: bool = typer.Option(
        False, help="Run the CLI with local server configuration"
    ),
):
    # Set configuration variables
    config.storage = abspath(expanduser(storage))
    if log_file is None:
        log_file = storage_path(config.log_file)
    else:
        log_file = abspath(expanduser(log_file))
    if local:
        config.server = config.local_server
        config.certificate = abspath(expanduser(config.local_certificate))
    else:
        config.server = host
        config.certificate = certificate
    config.log_file = log_file

    init_storage()
    log = log.upper()
    log_lvl = getattr(logging, log)
    log_fmt = "%(asctime)s | %(levelname)s: %(message)s"
    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10000000, backupCount=5
    )
    handler.setFormatter(logging.Formatter(log_fmt))
    logging.basicConfig(
        level=log_lvl, handlers=[handler], format=log_fmt, datefmt="%Y-%m-%d %H:%M:%S"
    )
    logging.info(f"Running MedPerf v{config.version} on {log} logging level")

    config.ui = UIFactory.create_ui(ui)
    config.comms = CommsFactory.create_comms(comms, config.ui, config.server)

    config.ui.print(f"MedPerf {config.version}")


if __name__ == "__main__":
    app()
