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
    DatasetsList.run(comms, ui, all)


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
    name: str = typer.Option(..., "--name", help="Name of the dataset"),
    description: str = typer.Option(
        ..., "--description", help="Description of the dataset"
    ),
    location: str = typer.Option(
        ..., "--location", help="Location or Institution the data belongs to"
    ),
):
    """Runs the Data preparation step for a specified benchmark and raw dataset
    """
    comms = config.comms
    ui = config.ui
    data_uid = DataPreparation.run(
        benchmark_uid,
        data_path,
        labels_path,
        comms,
        ui,
        name=name,
        description=description,
        location=location,
    )
    ui.print("✅ Done!")
    ui.print(
        f"Next step: register the dataset with 'medperf dataset register -d {data_uid}'"
    )


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
    DatasetRegistration.run(data_uid, comms, ui)
    ui.print("✅ Done!")
    ui.print(
        f"Next step: associate the dataset with 'medperf dataset associate -b <BENCHMARK_UID> -d {data_uid}'"
    )


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
    AssociateDataset.run(data_uid, benchmark_uid, comms, ui)
    ui.print("✅ Done!")
    ui.print(
        f"Next step: Once approved, run the benchmark with 'medperf run -b {benchmark_uid} -d {data_uid}'"
    )
