from typing import Optional
from medperf.entities.training_exp import TrainingExp
import typer

import medperf.config as config
from medperf.decorators import clean_except

from medperf.commands.training.submit import SubmitTrainingExp
from medperf.commands.training.set_plan import SetPlan
from medperf.commands.training.start_event import StartEvent
from medperf.commands.training.close_event import CloseEvent
from medperf.commands.list import EntityList
from medperf.commands.view import EntityView
from medperf.commands.training.get_experiment_status import GetExperimentStatus
from medperf.commands.training.update_plan import UpdatePlan
from medperf.commands.training.set_aggregator import SetAggregator
import medperf.help_texts as help_texts

app = typer.Typer()


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help=help_texts.Training.name),
    description: str = typer.Option(
        ..., "--description", "-d", help=help_texts.Training.description
    ),
    docs_url: str = typer.Option(
        "", "--docs-url", "-u", help=help_texts.Common.docs_url
    ),
    prep_mlcube: int = typer.Option(
        ...,
        "--prep-container",
        "-p",
        help=help_texts.Training.data_preparation_container,
    ),
    fl_mlcube: int = typer.Option(
        ..., "--fl-container", "-m", help=help_texts.Training.fl_container
    ),
    fl_admin_mlcube: int = typer.Option(
        None, "--fl-admin-container", "-a", help=help_texts.Training.fl_admin_container
    ),
    operational: bool = typer.Option(
        False,
        "--operational",
        help=help_texts.Training.operational,
    ),
    aggregator: int = typer.Option(
        None, "--aggregator", "-g", help=help_texts.Training.aggregator
    ),
):
    """Submits a new training experiment to the platform"""
    training_exp_info = {
        "name": name,
        "description": description,
        "docs_url": docs_url,
        "fl_mlcube": fl_mlcube,
        "fl_admin_mlcube": fl_admin_mlcube,
        "aggregator": aggregator,
        "demo_dataset_tarball_url": "link",
        "demo_dataset_tarball_hash": "hash",
        "demo_dataset_generated_uid": "uid",
        "data_preparation_mlcube": prep_mlcube,
        "state": "OPERATION" if operational else "DEVELOPMENT",
    }
    SubmitTrainingExp.run(training_exp_info)
    config.ui.print("✅ Done!")


@app.command("set_plan")
@clean_except
def set_plan(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help=help_texts.Training.uid
    ),
    training_config_path: str = typer.Option(
        ..., "--config-path", "-c", help=help_texts.Training.config_path
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
):
    """Sets the training plan of a training experiment"""
    SetPlan.run(training_exp_id, training_config_path, approval)
    config.ui.print("✅ Done!")


@app.command("start_event")
@clean_except
def start_event(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help=help_texts.Training.uid
    ),
    name: str = typer.Option(..., "--name", "-n", help=help_texts.Training.event_name),
    participants_list_file: str = typer.Option(
        None,
        "--participants_list_file",
        "-p",
        help=help_texts.Training.participants_list_file,
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
):
    """Starts a new training event for a training experiment"""
    StartEvent.run(training_exp_id, name, participants_list_file, approval)
    config.ui.print("✅ Done!")


@app.command("get_experiment_status")
@clean_except
def get_experiment_status(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help=help_texts.Training.uid
    ),
    silent: bool = typer.Option(False, "--silent", help=help_texts.Training.silent),
):
    """Gets the current status of a training experiment"""
    GetExperimentStatus.run(training_exp_id, silent)
    config.ui.print("✅ Done!")


@app.command("update_plan")
@clean_except
def update_plan(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help=help_texts.Training.uid
    ),
    field_name: str = typer.Option(
        ..., "--field_name", "-f", help=help_texts.Training.field_name
    ),
    value: str = typer.Option(..., "--value", "-v", help=help_texts.Training.value),
):
    """Runtime-update of a scalar field of the training plan"""
    UpdatePlan.run(training_exp_id, field_name, value)
    config.ui.print("✅ Done!")


@app.command("set_aggregator")
@clean_except
def set_aggregator(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help=help_texts.Training.uid
    ),
    aggregator_id: int = typer.Option(
        ..., "--aggregator_id", "-a", help=help_texts.Training.aggregator
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
):
    """Set the aggregator for a training experiment."""
    SetAggregator.run(training_exp_id, aggregator_id, approved=approval)
    config.ui.print("✅ Done!")


@app.command("close_event")
@clean_except
def close_event(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help=help_texts.Training.uid
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
):
    """Closes the current training event of a training experiment"""
    CloseEvent.run(training_exp_id, approval=approval)
    config.ui.print("✅ Done!")


@app.command("cancel_event")
@clean_except
def cancel_event(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help=help_texts.Training.uid
    ),
    report_path: str = typer.Option(
        ..., "--report-path", "-r", help=help_texts.Training.report_path
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
):
    """Cancels the current training event of a training experiment using the given report"""
    CloseEvent.run(training_exp_id, report_path=report_path, approval=approval)
    config.ui.print("✅ Done!")


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help=help_texts.Training.ls_unregistered
    ),
    mine: bool = typer.Option(False, "--mine", help=help_texts.Training.ls_mine),
):
    """List training experiments"""
    EntityList.run(
        TrainingExp,
        fields=["UID", "Name", "State", "Approval Status", "Registered"],
        unregistered=unregistered,
        mine_only=mine,
    )


@app.command("view")
@clean_except
def view(
    entity_id: Optional[int] = typer.Argument(None, help=help_texts.Training.id),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help=help_texts.Common.format,
    ),
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help=help_texts.Training.view_unregistered,
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help=help_texts.Training.view_mine,
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help=help_texts.Common.output,
    ),
):
    """Displays the information of one or more training experiments"""
    EntityView.run(entity_id, TrainingExp, format, unregistered, mine, output)
