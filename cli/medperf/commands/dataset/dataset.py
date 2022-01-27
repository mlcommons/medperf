import typer
from medperf.commands.dataset import (
    DatasetsList,
    DatasetRegistration,
    DataPreparation,
    DatasetBenchmarkAssociation,
)
from medperf.decorators import clean_except
import medperf.config as config

app = typer.Typer()


@clean_except
@app.command("ls")
def datasets():
    """Lists all local datasets
	"""
    ui = config.ui
    comms = config.comms
    comms.authenticate()
    DatasetsList.run(comms, ui)


@clean_except
@app.command("create")
def create(
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
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    data_uid = DataPreparation.run(benchmark_uid, data_path, labels_path, comms, ui)
    DatasetRegistration.run(data_uid, comms, ui)
    DatasetBenchmarkAssociation.run(data_uid, benchmark_uid, comms, ui)
    ui.print("✅ Done!")


@clean_except
@app.command("submit")
def register(
    data_uid: str = typer.Option(
        ..., "--data_uid", "-d", help="Unregistered Dataset UID"
    )
):
    """Submits an unregistered Dataset instance to the backend
    """
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    DatasetRegistration.run(data_uid, comms, ui)
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
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    DatasetBenchmarkAssociation.run(data_uid, benchmark_uid, comms, ui)
    ui.print("✅ Done!")

