from typing import Optional
from medperf.entities.training_exp import TrainingExp
from medperf.enums import Status
import typer

import medperf.config as config
from medperf.decorators import clean_except

from medperf.commands.training.submit import SubmitTrainingExp
from medperf.commands.training.run import TrainingExecution
from medperf.commands.training.lock import LockTrainingExp
from medperf.commands.training.associate import DatasetTrainingAssociation
from medperf.commands.training.approve import TrainingAssociationApproval
from medperf.commands.training.list_assocs import ListTrainingAssociations
from medperf.commands.list import EntityList
from medperf.commands.view import EntityView

app = typer.Typer()


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help="Name of the benchmark"),
    description: str = typer.Option(
        ..., "--description", "-d", help="Description of the benchmark"
    ),
    docs_url: str = typer.Option("", "--docs-url", "-u", help="URL to documentation"),
    prep_mlcube: int = typer.Option(
        ..., "--prep-mlcube", "-p", help="prep MLCube UID"
    ),
    fl_mlcube: int = typer.Option(
        ..., "--fl-mlcube", "-m", help="Reference Model MLCube UID"
    ),
):
    """Submits a new benchmark to the platform"""
    training_exp_info = {
        "name": name,
        "description": description,
        "docs_url": docs_url,
        "fl_mlcube": fl_mlcube,
        "demo_dataset_tarball_url": "link", # TODO later
        "demo_dataset_tarball_hash": "hash",
        "demo_dataset_generated_uid": "uid",
        "data_preparation_mlcube": prep_mlcube,
    }
    SubmitTrainingExp.run(training_exp_info)
    config.ui.print("✅ Done!")


@app.command("lock")
@clean_except
def lock(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of the desired benchmark"
    ),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    LockTrainingExp.run(training_exp_id)
    config.ui.print("✅ Done!")


@app.command("run")
@clean_except
def run(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of the desired benchmark"
    ),
    data_uid: int = typer.Option(
        ..., "--data_uid", "-d", help="Registered Dataset UID"
    ),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    TrainingExecution.run(training_exp_id, data_uid)
    config.ui.print("✅ Done!")


@app.command("associate_dataset")
@clean_except
def associate(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of the desired benchmark"
    ),
    data_uid: int = typer.Option(
        ..., "--data_uid", "-d", help="Registered Dataset UID"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    DatasetTrainingAssociation.run(training_exp_id, data_uid, approved=approval)
    config.ui.print("✅ Done!")


@app.command("approve_association")
@clean_except
def approve(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of the desired benchmark"
    ),
    data_uid: int = typer.Option(
        None, "--data_uid", "-d", help="Registered Dataset UID"
    ),
    aggregator: int = typer.Option(
        None, "--aggregator", "-a", help="Registered Dataset UID"
    ),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    TrainingAssociationApproval.run(
        training_exp_id, Status.APPROVED, data_uid, aggregator
    )
    config.ui.print("✅ Done!")


@app.command("list_associations")
@clean_except
def list(filter: Optional[str] = typer.Argument(None)):
    """Display all training associations related to the current user.

    Args:
        filter (str, optional): Filter training associations by approval status.
            Defaults to displaying all user training associations.
    """
    ListTrainingAssociations.run(filter)


@app.command("ls")
@clean_except
def list(
    local: bool = typer.Option(False, "--local", help="Get local exps"),
    mine: bool = typer.Option(False, "--mine", help="Get current-user exps"),
):
    """List experiments stored locally and remotely from the user"""
    EntityList.run(
        TrainingExp,
        fields=["UID", "Name", "State", "Approval Status", "Registered"],
        local_only=local,
        mine_only=mine,
    )


@app.command("view")
@clean_except
def view(
    entity_id: Optional[int] = typer.Argument(None, help="Benchmark ID"),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help="Format to display contents. Available formats: [yaml, json]",
    ),
    local: bool = typer.Option(
        False,
        "--local",
        help="Display local benchmarks if benchmark ID is not provided",
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help="Display current-user benchmarks if benchmark ID is not provided",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file to store contents. If not provided, the output will be displayed",
    ),
):
    """Displays the information of one or more benchmarks"""
    EntityView.run(entity_id, TrainingExp, format, local, mine, output)
