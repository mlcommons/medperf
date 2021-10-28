import os
import stat
import typer
import logging
import getpass
from tabulate import tabulate

from medperf.commands import (
    DataPreparation,
    BenchmarkExecution,
    DatasetBenchmarkAssociation,
)
from medperf.config import config
from medperf.decorators import clean_except
from medperf.entities import Server, Dataset


app = typer.Typer()


@clean_except
@app.command("login")
def login():
    """Login to the medperf server. Must be done only once.
    """
    cred_path = config["credentials_path"]
    user = input("username: ")
    pwd = getpass.getpass("password: ")
    server = Server(config["server"])
    server.login(user, pwd)
    token = server.token

    if os.path.exists(cred_path):
        os.remove(cred_path)
    with open(cred_path, "w") as f:
        f.write(token)

    os.chmod(cred_path, stat.S_IREAD)


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

    Args:
        benchmark_uid (int): UID of the desired benchmark.
        data_path (str): Location of the data to be prepared.
        labels_path (str): Labels file location.
    """
    data_uid = DataPreparation.run(benchmark_uid, data_path, labels_path)
    DatasetBenchmarkAssociation.run(data_uid, benchmark_uid)
    typer.echo("✅ Done!")


@clean_except
@app.command("execute")
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
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model

    Args:
        benchmark_uid (int): UID of the desired benchmark.
        data_uid (int): Registered Dataset UID.
        model_uid (int): UID of model to execute.
    """
    BenchmarkExecution.run(benchmark_uid, data_uid, model_uid)
    typer.echo("✅ Done!")


@clean_except
@app.command("associate")
def associate(
    data_uid: int = typer.Option(
        ..., "--data_uid", "-d", help="Registered Dataset UID"
    ),
    benchmark_uid: int = typer.Option(
        ..., "-benchmark_uid", "-b", help="Benchmark UID"
    ),
):
    """Associate a registered dataset with a specific benchmark. The dataset and benchmark must share the same data preparation cube.
    """
    DatasetBenchmarkAssociation.run(data_uid, benchmark_uid)
    typer.echo("✅ Done!")


@app.callback()
def main(log: str = "INFO", log_file: str = config["log_file"]):
    log = log.upper()
    log_lvl = getattr(logging, log)
    log_fmt = "%(asctime)s | %(levelname)s: %(message)s"
    logging.basicConfig(filename=log_file, level=log_lvl, format=log_fmt)
    logging.info(f"Running MedPerf v{config['version']} on {log} logging level")
    typer.echo(f"MedPerf {config['version']}")


@clean_except
@app.command("datasets")
def datasets():
    """Lists all local datasets
	"""
    dsets = Dataset.all()
    headers = ["UID", "Name", "Data Preparation Cube UID"]
    dsets_data = [
        [dset.data_uid, dset.name, dset.preparation_cube_uid] for dset in dsets
    ]
    tab = tabulate(dsets_data, headers=headers)
    typer.echo(tab)


if __name__ == "__main__":
    app()
