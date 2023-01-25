import typer
from typing import Optional

import medperf.config as config
from medperf.decorators import clean_except
from medperf.entities.dataset import Dataset
from medperf.commands.view import EntityView
from medperf.commands.dataset.list import DatasetsList
from medperf.commands.dataset.create import DataPreparation
from medperf.commands.dataset.submit import DatasetRegistration
from medperf.commands.dataset.associate import AssociateDataset

app = typer.Typer()


@app.command("ls")
@clean_except
def datasets(
    local: bool = typer.Option(False, "--local", help="Get local datasets"),
    mine: bool = typer.Option(False, "--mine", help="Get current-user datasets"),
):
    """Lists all datasets from the user by default.
    Use all to get all datasets in the platform
    """
    DatasetsList.run(local, mine)


@app.command("create")
@clean_except
def create(
    benchmark_uid: int = typer.Option(
        None, "--benchmark", "-b", help="UID of the desired benchmark"
    ),
    data_prep_uid: int = typer.Option(
        None, "--data_prep", "-p", help="UID of the desired preparation cube"
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
    ui = config.ui
    data_uid = DataPreparation.run(
        benchmark_uid,
        data_prep_uid,
        data_path,
        labels_path,
        name=name,
        description=description,
        location=location,
    )
    ui.print("✅ Done!")
    ui.print(
        f"Next step: register the dataset with 'medperf dataset submit -d {data_uid}'"
    )


@app.command("submit")
@clean_except
def register(
    data_uid: str = typer.Option(
        ..., "--data_uid", "-d", help="Unregistered Dataset UID"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """Submits an unregistered Dataset instance to the backend
    """
    ui = config.ui
    DatasetRegistration.run(data_uid, approved=approval)
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
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
    force_test: bool = typer.Option(
        False, "--force-test", help="Execute the test even if results already exist",
    ),
):
    """Associate a registered dataset with a specific benchmark.
    The dataset and benchmark must share the same data preparation cube.
    """
    ui = config.ui
    AssociateDataset.run(
        data_uid, benchmark_uid, approved=approval, force_test=force_test
    )
    ui.print("✅ Done!")
    ui.print(
        f"Next step: Once approved, run the benchmark with 'medperf run -b {benchmark_uid} -d {data_uid}'"
    )


@app.command("view")
@clean_except
def view(
    entity_id: Optional[int] = typer.Argument(None, help="Result ID"),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help="Format to display contents. Available formats: [yaml, json]",
    ),
    local: bool = typer.Option(False, "--local", help="Get local results"),
    mine: bool = typer.Option(False, "--mine", help="Get current-user results"),
    output: str = typer.Option(
        None, "--output", "-o", help="Output file to store contents"
    ),
):
    """Displays the information of one or more results
    """
    EntityView.run(entity_id, Dataset, format, local, mine, output)
