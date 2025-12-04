import typer
from typing import Optional

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.view import EntityView
from medperf.entities.execution import Execution
from medperf.commands.list import EntityList
from medperf.commands.execution.create import BenchmarkExecution
from medperf.commands.execution.submit import ResultSubmission
from medperf.commands.execution.show_local_results import ShowLocalResults

app = typer.Typer()


@app.command("create")
@clean_except
def create(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help="UID of the desired benchmark"
    ),
    data_uid: int = typer.Option(
        ..., "--data_uid", "-d", help="Registered Dataset UID"
    ),
    model_uid: int = typer.Option(
        ..., "--model_uid", "-m", help="UID of model to execute"
    ),
    ignore_model_errors: bool = typer.Option(
        False,
        "--ignore-model-errors",
        help="Ignore failing models, allowing for possibly submitting partial results",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Execute even if results already exist",
    ),
    new_result: bool = typer.Option(
        False,
        "--new-result",
        help=(
            "Works if the result of the execution was already uploaded."
            "This will rerun and create a new record."
        ),
    ),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    BenchmarkExecution.run(
        benchmark_uid,
        data_uid,
        [model_uid],
        no_cache=no_cache,
        ignore_model_errors=ignore_model_errors,
        rerun_finalized_executions=new_result,
    )
    config.ui.print("✅ Done!")


@app.command("submit")
@clean_except
def submit(
    result_uid: int = typer.Option(None, "--result", "-r", help="UID of the result"),
    benchmark_uid: int = typer.Option(
        None, "--benchmark", "-b", help="UID of the desired benchmark"
    ),
    data_uid: int = typer.Option(
        None, "--data_uid", "-d", help="Registered Dataset UID"
    ),
    model_uid: int = typer.Option(
        None, "--model_uid", "-m", help="UID of model to execute"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """Submits already obtained results to the server"""
    ResultSubmission.run(
        result_uid, benchmark_uid, data_uid, model_uid, approved=approval
    )
    config.ui.print("✅ Done!")


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help="Get unregistered results"
    ),
    mine: bool = typer.Option(False, "--mine", help="Get current-user results"),
    benchmark: int = typer.Option(
        None, "--benchmark", "-b", help="Get results for a given benchmark"
    ),
    model: int = typer.Option(
        None, "--model", "-m", help="Get results for a given model"
    ),
    dataset: int = typer.Option(
        None, "--dataset", "-d", help="Get reuslts for a given dataset"
    ),
):
    """List results"""
    EntityList.run(
        Execution,
        fields=[
            "UID",
            "Name",
            "Benchmark",
            "Model",
            "Dataset",
            "Executed",
            "Finalized",
        ],
        unregistered=unregistered,
        mine_only=mine,
        benchmark=benchmark,
        model=model,
        dataset=dataset,
    )


@app.command("view")
@clean_except
def view(
    entity_id: Optional[str] = typer.Argument(None, help="Result ID"),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help="Format to display contents. Available formats: [yaml, json]",
    ),
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help="Display unregistered results if result ID is not provided",
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help="Display current-user results if result ID is not provided",
    ),
    benchmark: int = typer.Option(
        None, "--benchmark", "-b", help="Get results for a given benchmark"
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file to store contents. If not provided, the output will be displayed",
    ),
):
    """Displays the information of one or more results"""
    EntityView.run(
        entity_id, Execution, format, unregistered, mine, output, benchmark=benchmark
    )


@app.command("show_local_results")
@clean_except
def show_local_results(
    result_id: int = typer.Argument(..., help="Result ID"),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help="Format to display contents. Available formats: [yaml, json]",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file to store contents. If not provided, the output will be displayed",
    ),
):
    """Displays the information of one or more results"""
    ShowLocalResults.run(result_id, format, output)
