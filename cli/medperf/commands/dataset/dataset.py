import typer
from typing import Optional

import medperf.config as config
from medperf.decorators import clean_except
from medperf.entities.dataset import Dataset
from medperf.commands.list import EntityList
from medperf.commands.view import EntityView
from medperf.commands.dataset.submit import DataCreation
from medperf.commands.dataset.prepare import DataPreparation
from medperf.commands.dataset.set_operational import DatasetSetOperational
from medperf.commands.dataset.associate import AssociateDataset
from medperf.commands.dataset.train import TrainingExecution

app = typer.Typer()


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help="Get unregistered datasets"
    ),
    mine: bool = typer.Option(False, "--mine", help="Get current-user datasets"),
    mlcube: int = typer.Option(
        None, "--mlcube", "-m", help="Get datasets for a given data prep mlcube"
    ),
):
    """List datasets"""
    EntityList.run(
        Dataset,
        fields=["UID", "Name", "Data Preparation Cube UID", "State", "Status", "Owner"],
        unregistered=unregistered,
        mine_only=mine,
        mlcube=mlcube,
    )


@app.command("submit")
@clean_except
def submit(
    benchmark_uid: int = typer.Option(
        None, "--benchmark", "-b", help="UID of the desired benchmark"
    ),
    data_prep_uid: int = typer.Option(
        None, "--data_prep", "-p", help="UID of the desired preparation cube"
    ),
    data_path: str = typer.Option(..., "--data_path", "-d", help="Path to the data"),
    labels_path: str = typer.Option(
        ..., "--labels_path", "-l", help="Path to the labels"
    ),
    metadata_path: str = typer.Option(
        None,
        "--metadata_path",
        "-m",
        help="Metadata folder location (Might be required if the dataset is already prepared)",
    ),
    name: str = typer.Option(
        ..., "--name", help="A human-readable name of the dataset"
    ),
    description: str = typer.Option(
        None, "--description", help="A description of the dataset"
    ),
    location: str = typer.Option(
        None, "--location", help="Location or Institution the data belongs to"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
    submit_as_prepared: bool = typer.Option(
        False,
        "--submit-as-prepared",
        help="Use this flag if the dataset is already prepared",
    ),
):
    """Submits a Dataset instance to the backend"""
    ui = config.ui
    DataCreation.run(
        benchmark_uid,
        data_prep_uid,
        data_path,
        labels_path,
        metadata_path,
        name=name,
        description=description,
        location=location,
        approved=approval,
        submit_as_prepared=submit_as_prepared,
    )
    ui.print("✅ Done!")


@app.command("prepare")
@clean_except
def prepare(
    data_uid: str = typer.Option(..., "--data_uid", "-d", help="Dataset UID"),
    approval: bool = typer.Option(
        False,
        "-y",
        help="Skip report submission approval step (In this case, it is assumed to be approved)",
    ),
):
    """Runs the Data preparation step for a raw dataset"""
    ui = config.ui
    DataPreparation.run(data_uid, approve_sending_reports=approval)
    ui.print("✅ Done!")


@app.command("set_operational")
@clean_except
def set_operational(
    data_uid: str = typer.Option(..., "--data_uid", "-d", help="Dataset UID"),
    approval: bool = typer.Option(
        False, "-y", help="Skip confirmation and statistics submission approval step"
    ),
):
    """Marks a dataset as Operational"""
    ui = config.ui
    DatasetSetOperational.run(data_uid, approved=approval)
    ui.print("✅ Done!")


@app.command("associate")
@clean_except
def associate(
    data_uid: int = typer.Option(
        ..., "--data_uid", "-d", help="Registered Dataset UID"
    ),
    benchmark_uid: int = typer.Option(
        None, "--benchmark_uid", "-b", help="Benchmark UID"
    ),
    training_exp_uid: int = typer.Option(
        None, "--training_exp_uid", "-t", help="Training experiment UID"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Execute the benchmark association test even if results already exist",
    ),
):
    """Associate a registered dataset with a specific benchmark or experiment."""
    ui = config.ui
    AssociateDataset.run(
        data_uid, benchmark_uid, training_exp_uid, approved=approval, no_cache=no_cache
    )
    ui.print("✅ Done!")


@app.command("train")
@clean_except
def train(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of the desired benchmark"
    ),
    data_uid: int = typer.Option(
        ..., "--data_uid", "-d", help="Registered Dataset UID"
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite outputs if present"
    ),
    restart_on_failure: bool = typer.Option(
        False,
        "--restart_on_failure",
        help="Keep restarting failing training processes until Keyboard interrupt",
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
    skip_restart_on_failure_prompt: bool = typer.Option(
        False, "--skip_restart_on_failure_prompt", help="Skip restart on failure prompt"
    ),
):
    """Runs training"""
    TrainingExecution.run(
        training_exp_id,
        data_uid,
        overwrite,
        approval,
        restart_on_failure,
        skip_restart_on_failure_prompt,
    )
    config.ui.print("✅ Done!")


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
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help="Display unregistered datasets if dataset ID is not provided",
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
    """Displays the information of one or more datasets"""
    EntityView.run(entity_id, Dataset, format, unregistered, mine, output)
