from typing import Optional
from medperf.entities.training_exp import TrainingExp
import typer

import medperf.config as config
from medperf.decorators import clean_except

from medperf.commands.training.submit import SubmitTrainingExp
from medperf.commands.training.set_plan import SetPlan
from medperf.commands.training.start_event import StartEvent
from medperf.commands.training.close_event import CloseEvent
from medperf.commands.training.submit_job import SubmitJob

from medperf.commands.list import EntityList
from medperf.commands.view import EntityView
from medperf.commands.training.get_experiment_status import GetExperimentStatus
from medperf.commands.training.update_plan import UpdatePlan

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
        ..., "--prep-container", "-p", help="prep container UID"
    ),
    fl_mlcube: int = typer.Option(..., "--fl-container", "-m", help="FL container UID"),
    fl_admin_mlcube: int = typer.Option(
        None, "--fl-admin-container", "-a", help="FL admin interface container"
    ),
    operational: bool = typer.Option(
        False,
        "--operational",
        help="Submit the experiment as OPERATIONAL",
    ),
):
    """Submits a new benchmark to the platform"""
    training_exp_info = {
        "name": name,
        "description": description,
        "docs_url": docs_url,
        "fl_mlcube": fl_mlcube,
        "fl_admin_mlcube": fl_admin_mlcube,
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
        ..., "--training_exp_id", "-t", help="UID of the desired benchmark"
    ),
    training_config_path: str = typer.Option(
        ..., "--config-path", "-c", help="config path"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    SetPlan.run(training_exp_id, training_config_path, approval)
    config.ui.print("✅ Done!")


@app.command("start_event")
@clean_except
def start_event(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of the desired benchmark"
    ),
    name: str = typer.Option(..., "--name", "-n", help="Name of the benchmark"),
    participants_list_file: str = typer.Option(
        None, "--participants_list_file", "-p", help="Name of the benchmark"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    StartEvent.run(training_exp_id, name, participants_list_file, approval)
    config.ui.print("✅ Done!")


@app.command("submit_job")
@clean_except
def submit_job(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of the desired benchmark"
    )
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    SubmitJob.run(training_exp_id)
    config.ui.print("✅ Done!")


@app.command("get_experiment_status")
@clean_except
def get_experiment_status(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of the desired benchmark"
    ),
    silent: bool = typer.Option(False, "--silent", help="don't print"),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    GetExperimentStatus.run(training_exp_id, silent)
    config.ui.print("✅ Done!")


@app.command("update_plan")
@clean_except
def update_plan(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of the desired benchmark"
    ),
    field_name: str = typer.Option(
        ..., "--field_name", "-f", help="UID of the desired benchmark"
    ),
    value: str = typer.Option(
        ..., "--value", "-v", help="UID of the desired benchmark"
    ),
):
    """Runtime-update of a scalar field of the training plan"""
    UpdatePlan.run(training_exp_id, field_name, value)
    config.ui.print("✅ Done!")


@app.command("close_event")
@clean_except
def close_event(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of the desired benchmark"
    ),
    report_file: str = typer.Option(None, "--report_file", "-r", help="Report file"),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    CloseEvent.run(training_exp_id, report_file, approval=approval)
    config.ui.print("✅ Done!")


@app.command("cancel_event")
@clean_except
def cancel_event(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of the desired benchmark"
    ),
    report_path: str = typer.Option(..., "--report-path", "-r", help="report path"),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    CloseEvent.run(training_exp_id, report_path=report_path, approval=approval)
    config.ui.print("✅ Done!")


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help="Get unregistered exps"
    ),
    mine: bool = typer.Option(False, "--mine", help="Get current-user exps"),
):
    """List experiments stored locally and remotely from the user"""
    EntityList.run(
        TrainingExp,
        fields=["UID", "Name", "State", "Approval Status", "Registered"],
        unregistered=unregistered,
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
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help="Display unregistered benchmarks if benchmark ID is not provided",
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
    EntityView.run(entity_id, TrainingExp, format, unregistered, mine, output)
