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
from medperf.commands.dataset.import_dataset import ImportDataset
from medperf.commands.dataset.export_dataset import ExportDataset
from medperf.commands.dataset.check import DataCheck
import medperf.help_texts as help_texts

app = typer.Typer()


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help=help_texts.Dataset.ls_unregistered
    ),
    mine: bool = typer.Option(False, "--mine", help=help_texts.Dataset.ls_mine),
    mlcube: int = typer.Option(
        None,
        "--data-preparation-container",
        "-m",
        help=help_texts.Dataset.data_preparation_container_filter,
    ),
    name: str = typer.Option(None, "--name", help=help_texts.Common.name_filter),
    owner: int = typer.Option(None, "--owner", help=help_texts.Common.owner_filter),
    state: str = typer.Option(None, "--state", help=help_texts.Common.state_filter),
    is_valid: bool = typer.Option(
        None, "--valid/--invalid", help=help_texts.Common.valid_filter
    ),
):
    """List datasets"""
    EntityList.run(
        Dataset,
        fields=[
            "UID",
            "Name",
            "Data Preparation Container UID",
            "State",
            "Status",
            "Owner",
        ],
        unregistered=unregistered,
        mine_only=mine,
        mlcube=mlcube,
        name=name,
        owner=owner,
        state=state,
        is_valid=is_valid,
    )


@app.command("submit")
@clean_except
def submit(
    benchmark_uid: int = typer.Option(
        None, "--benchmark", "-b", help=help_texts.Dataset.benchmark_uid
    ),
    data_prep_uid: int = typer.Option(
        None, "--data_prep", "-p", help=help_texts.Dataset.data_preparation_container
    ),
    data_path: str = typer.Option(
        ..., "--data_path", "-d", help=help_texts.Dataset.data_path
    ),
    labels_path: str = typer.Option(
        ..., "--labels_path", "-l", help=help_texts.Dataset.labels_path
    ),
    metadata_path: str = typer.Option(
        None,
        "--metadata_path",
        "-m",
        help=help_texts.Dataset.metadata_path,
    ),
    name: str = typer.Option(..., "--name", help=help_texts.Dataset.name),
    description: str = typer.Option(
        None, "--description", help=help_texts.Dataset.description
    ),
    location: str = typer.Option(None, "--location", help=help_texts.Dataset.location),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
    submit_as_prepared: bool = typer.Option(
        False,
        "--submit-as-prepared",
        help=help_texts.Dataset.submit_as_prepared,
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
    data_uid: str = typer.Option(..., "--data_uid", "-d", help=help_texts.Dataset.uid),
    approval: bool = typer.Option(
        False,
        "-y",
        help=help_texts.Dataset.prepare_approval,
    ),
):
    """Runs the Data preparation step for a raw dataset"""
    ui = config.ui
    DataPreparation.run(data_uid, approve_sending_reports=approval)
    ui.print("✅ Done!")


@app.command("check")
@clean_except
def check(
    data_uid: str = typer.Option(..., "--data_uid", "-d", help=help_texts.Dataset.uid),
):
    """Checks if the hash of the dataset matches the one registered on the server"""
    ui = config.ui
    DataCheck.run(data_uid)
    ui.print("✅ Done!")


@app.command("set_operational")
@clean_except
def set_operational(
    data_uid: str = typer.Option(..., "--data_uid", "-d", help=help_texts.Dataset.uid),
    approval: bool = typer.Option(
        False, "-y", help=help_texts.Dataset.set_operational_approval
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
        ..., "--data_uid", "-d", help=help_texts.Dataset.registered_uid
    ),
    benchmark_uid: int = typer.Option(
        None, "--benchmark_uid", "-b", help=help_texts.Benchmark.uid
    ),
    training_exp_uid: int = typer.Option(
        None, "--training_exp_uid", "-t", help=help_texts.Training.uid
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help=help_texts.Dataset.associate_no_cache,
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
        ..., "--training_exp_id", "-t", help=help_texts.Training.uid
    ),
    data_uid: int = typer.Option(
        ..., "--data_uid", "-d", help=help_texts.Dataset.registered_uid
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help=help_texts.Common.overwrite
    ),
    restart_on_failure: bool = typer.Option(
        False,
        "--restart_on_failure",
        help=help_texts.Dataset.restart_on_failure,
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
    skip_restart_on_failure_prompt: bool = typer.Option(
        False,
        "--skip_restart_on_failure_prompt",
        help=help_texts.Dataset.skip_restart_on_failure_prompt,
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
    entity_id: Optional[str] = typer.Argument(None, help=help_texts.Dataset.id),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help=help_texts.Common.format,
    ),
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help=help_texts.Dataset.view_unregistered,
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help=help_texts.Dataset.view_mine,
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help=help_texts.Common.output,
    ),
):
    """Displays the information of one or more datasets"""
    EntityView.run(entity_id, Dataset, format, unregistered, mine, output)


@app.command("import")
@clean_except
def import_dataset(
    data_uid: str = typer.Option(
        ..., "--data_uid", "-d", help=help_texts.Dataset.import_uid
    ),
    input_path: str = typer.Option(
        ...,
        "--input",
        "-i",
        help=help_texts.Dataset.import_input_path,
    ),
    raw_path: str = typer.Option(
        None,
        "--raw_dataset_path",
        help=help_texts.Dataset.import_raw_path,
    ),
):
    """Imports dataset files from specified tar.gz file."""
    ImportDataset.run(data_uid, input_path, raw_path)
    config.ui.print("✅ Done!")


@app.command("export")
@clean_except
def export_dataset(
    data_uid: str = typer.Option(
        ..., "--data_uid", "-d", help=help_texts.Dataset.export_uid
    ),
    output: str = typer.Option(
        ...,
        "--output",
        "-o",
        help=help_texts.Dataset.export_output_path,
    ),
):
    """Exports dataset files to a tar.gz file in the specified output folder."""
    ExportDataset.run(data_uid, output)
    config.ui.print("✅ Done!")
