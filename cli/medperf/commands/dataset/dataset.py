import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.dataset.list import DatasetsList
from medperf.commands.dataset.create import DataPreparation
from medperf.commands.dataset.submit import DatasetRegistration
from medperf.commands.dataset.associate import AssociateDataset

app = typer.Typer()


@app.command("ls")
@clean_except
def datasets(
    all: bool = typer.Option(False, help="Get all datasets from the platform")
):
    """Lists all datasets from the user by default.
    Use all to get all datasets in the platform
    """
    ui = config.ui
    comms = config.comms
    comms.authenticate()
    DatasetsList.run(comms, ui)


@app.command("create")
@clean_except
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
    AssociateDataset.run(data_uid, benchmark_uid, comms, ui)
    ui.print("✅ Done!")


@app.command("submit")
@clean_except
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


@app.command("associate")
@clean_except
def associate(
    data_uid: str = typer.Option(
        ..., "--data_uid", "-d", help="Registered Dataset UID"
    ),
    benchmark_uid: int = typer.Option(
        ..., "-benchmark_uid", "-b", help="Benchmark UID"
    ),
):
    """Associate a registered dataset with a specific benchmark.
    The dataset and benchmark must share the same data preparation cube.
    """
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    AssociateDataset.run(data_uid, benchmark_uid, comms, ui)
    ui.print("✅ Done!")
