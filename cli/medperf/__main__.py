import typer
import logging

from medperf.commands import (
    DataPreparation,
    DatasetRegistration,
    BenchmarkExecution,
    DatasetBenchmarkAssociation,
    ResultSubmission,
    Login,
    Datasets,
)
from medperf.config import config
from medperf.utils import init_storage
from medperf.decorators import clean_except
from medperf.comms import CommsFactory
from medperf.ui import UIFactory
from medperf.utils import init_storage


app = typer.Typer()
state = {"comms": None, "ui": None}


@clean_except
@app.command("login")
def login():
    """Login to the medperf server. Must be done only once.
    """
    Login.run(state["comms"], state["ui"])


@clean_except
@app.command("prepare")
def prepare(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help="UID of the desired benchmark"
    ),
    data_path: str = typer.Option(
        ..., "--data_path", "-d", help="Location of the data to be prepared"
    ),
    labels_path: str = typer.Option(
        ..., "--labels_path", "-l", help="Labels file location"
    ),
):
    """Runs the Data preparation step for a specified benchmark and raw dataset
    """
    comms = state["comms"]
    ui = state["ui"]
    comms.authenticate()
    data_uid = DataPreparation.run(benchmark_uid, data_path, labels_path, comms, ui)
    DatasetRegistration.run(data_uid, comms, ui)
    DatasetBenchmarkAssociation.run(data_uid, benchmark_uid, comms, ui)
    ui.print("✅ Done!")


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
    comms = state["comms"]
    ui = state["ui"]
    comms.authenticate()
    BenchmarkExecution.run(benchmark_uid, data_uid, model_uid, comms, ui)
    ResultSubmission.run(benchmark_uid, data_uid, model_uid, comms, ui)
    ui.print("✅ Done!")


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
    comms = state["comms"]
    ui = state["ui"]
    comms.authenticate()
    ResultSubmission.run(benchmark_uid, data_uid, model_uid, comms, ui)
    ui.print("✅ Done!")


@clean_except
@app.command("associate")
def associate(
    data_uid: str = typer.Option(
        ..., "--data_uid", "-d", help="Registered Dataset UID"
    ),
    benchmark_uid: int = typer.Option(
        ..., "-benchmark_uid", "-b", help="Benchmark UID"
    ),
):
    """Associate a registered dataset with a specific benchmark. The dataset and benchmark must share the same data preparation cube.
    """
    comms = state["comms"]
    ui = state["ui"]
    comms.authenticate()
    DatasetBenchmarkAssociation.run(data_uid, benchmark_uid, comms, ui)
    ui.print("✅ Done!")


@clean_except
@app.command("register")
def register(
    data_uid: str = typer.Option(
        ..., "--data_uid", "-d", help="Unregistered Dataset UID"
    )
):
    """Registers an unregistered Dataset instance to the backend
    """
    comms = state["comms"]
    ui = state["ui"]
    comms.authenticate()
    DatasetRegistration.run(data_uid, comms, ui)
    ui.print("✅ Done!")


@clean_except
@app.command("datasets")
def datasets():
    """Lists all local datasets
	"""
    ui = state["ui"]
    Datasets.run(ui)


@app.callback()
def main(
    log: str = "INFO",
    log_file: str = config["log_file"],
    comms: str = config["default_comms"],
    ui: str = config["default_ui"],
):
    init_storage()
    log = log.upper()
    log_lvl = getattr(logging, log)
    log_fmt = "%(asctime)s | %(levelname)s: %(message)s"
    logging.basicConfig(filename=log_file, level=log_lvl, format=log_fmt)
    logging.info(f"Running MedPerf v{config['version']} on {log} logging level")

    state["ui"] = UIFactory.create_ui(ui)
    state["comms"] = CommsFactory.create_comms(comms, state["ui"])

    state["ui"].print(f"MedPerf {config['version']}")


if __name__ == "__main__":
    app()
