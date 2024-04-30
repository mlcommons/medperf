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

app = typer.Typer()


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help="Name of the benchmark"),
    description: str = typer.Option(
        ..., "--description", "-d", help="Description of the benchmark"
    ),
    docs_url: str = typer.Option("", "--docs-url", "-u", help="URL to documentation"),
    prep_mlcube: int = typer.Option(..., "--prep-mlcube", "-p", help="prep MLCube UID"),
    fl_mlcube: int = typer.Option(
        ..., "--fl-mlcube", "-m", help="Reference Model MLCube UID"
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
        "demo_dataset_tarball_url": "link",  # TODO later
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
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    StartEvent.run(training_exp_id, name, approval)
    config.ui.print("✅ Done!")


@app.command("close_event")
@clean_except
def close_event(
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of the desired benchmark"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    CloseEvent.run(training_exp_id, approval=approval)
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
