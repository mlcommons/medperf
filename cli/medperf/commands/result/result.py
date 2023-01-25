import typer
from typing import Optional, Union

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.view import EntityView
from medperf.entities.result import Result
from medperf.commands.result.list import ResultsList
from medperf.commands.result.create import BenchmarkExecution
from medperf.commands.result.submit import ResultSubmission

app = typer.Typer()


@app.command("create")
@clean_except
def create(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help="UID of the desired benchmark"
    ),
    data_uid: str = typer.Option(
        ..., "--data_uid", "-d", help="Registered Dataset UID"
    ),
    model_uid: int = typer.Option(
        ..., "--model_uid", "-m", help="UID of model to execute"
    ),
    ignore_errors: bool = typer.Option(
        False,
        "--ignore-errors",
        help="Ignore failing cubes, allowing for submitting partial results",
    ),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model
    """
    BenchmarkExecution.run(
        benchmark_uid, data_uid, model_uid, ignore_errors=ignore_errors
    )
    config.ui.print("✅ Done!")


@app.command("submit")
@clean_except
def submit(
    result_uid: str = typer.Option(
        ..., "--result", "-r", help="Unregistered result UID"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """Submits already obtained results to the server"""
    ResultSubmission.run(result_uid, approved=approval)
    config.ui.print("✅ Done!")


@app.command("ls")
@clean_except
def list(
    local: bool = typer.Option(False, "--local", help="Get local results"),
    mine: bool = typer.Option(False, "--mine", help="Get current-user results"),
):
    """List results stored locally and remotely from the user"""
    ResultsList.run(local, mine)


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
    EntityView.run(entity_id, Result, format, local, mine, output)
