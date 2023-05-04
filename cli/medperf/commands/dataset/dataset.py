import typer
from typing import Optional

import medperf.config as config
from medperf.decorators import clean_except
from medperf.entities.dataset import Dataset
from medperf.commands.list import EntityList
from medperf.commands.view import EntityView
from medperf.commands.edit import EntityEdit
from medperf.commands.dataset.create import DataPreparation
from medperf.commands.dataset.submit import DatasetRegistration
from medperf.commands.dataset.associate import AssociateDataset

NAME_OPTION = typer.Option(..., "--name", help="Name of the dataset")
DESC_OPTION = typer.Option(
    ..., "--description", help="Description of the dataset"
)
LOC_OPTION = typer.Option(
    ..., "--location", help="Location or Institution the data belongs to"
)

app = typer.Typer()


@app.command("ls")
@clean_except
def list(
    local: bool = typer.Option(False, "--local", help="Get local datasets"),
    mine: bool = typer.Option(False, "--mine", help="Get current-user datasets"),
):
    """List datasets stored locally and remotely from the user"""
    EntityList.run(
        Dataset,
        fields=["UID", "Name", "Data Preparation Cube UID", "Registered"],
        local_only=local,
        mine_only=mine,
    )


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
    name: str = NAME_OPTION,
    description: str = DESC_OPTION,
    location: str = LOC_OPTION
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
    uid = DatasetRegistration.run(data_uid, approved=approval)
    ui.print("✅ Done!")
    ui.print(
        f"Next step: associate the dataset with 'medperf dataset associate -b <BENCHMARK_UID> -d {uid}'"
    )


@app.command("edit")
@clean_except
def edit(
    entity_id: int = typer.Argument(..., help="Dataset ID"),
    name: str = NAME_OPTION,
    description: str = DESC_OPTION,
    location: str = LOC_OPTION
):
    """Edits a Dataset"""
    dset_info = {
        "name": name,
        "description": description,
        "location": location,
    }
    EntityEdit.run(Dataset, entity_id, dset_info)
    config.ui.print("✅ Done!")


@app.command("associate")
@clean_except
def associate(
    data_uid: int = typer.Option(
        ..., "--data_uid", "-d", help="Registered Dataset UID"
    ),
    benchmark_uid: int = typer.Option(
        ..., "--benchmark_uid", "-b", help="Benchmark UID"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Execute the test even if results already exist",
    ),
):
    """Associate a registered dataset with a specific benchmark.
    The dataset and benchmark must share the same data preparation cube.
    """
    ui = config.ui
    AssociateDataset.run(data_uid, benchmark_uid, approved=approval, no_cache=no_cache)
    ui.print("✅ Done!")
    ui.print(
        f"Next step: Once approved, run the benchmark with 'medperf run -b {benchmark_uid} -d {data_uid}'"
    )


@app.command("view")
@clean_except
def view(
    entity_id: Optional[str] = typer.Argument(None, help="Dataset ID"),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help="Format to display contents. Available formats: [yaml, json]",
    ),
    local: bool = typer.Option(
        False, "--local", help="Display local datasets if dataset ID is not provided"
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help="Display current-user datasets if dataset ID is not provided",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file to store contents. If not provided, the output will be displayed",
    ),
):
    """Displays the information of one or more datasets
    """
    EntityView.run(entity_id, Dataset, format, local, mine, output)
