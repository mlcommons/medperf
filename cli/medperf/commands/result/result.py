import typer
from typing import Optional

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.view import EntityView
from medperf.entities.result import Result
from medperf.commands.list import EntityList
from medperf.commands.result.create import BenchmarkExecution
from medperf.commands.result.submit import ResultSubmission

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
        help="Ignore failing model cubes, allowing for possibly submitting partial results",
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Execute even if results already exist",
    ),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model
    """
    BenchmarkExecution.run(
        benchmark_uid,
        data_uid,
        [model_uid],
        no_cache=no_cache,
        ignore_model_errors=ignore_model_errors,
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
    benchmark: int = typer.Option(
        None, "--benchmark", "-b", help="Get results for a given benchmark"
    ),
):
    """List results stored locally and remotely from the user"""
    filters = {}
    if benchmark is not None:
        filters["benchmark"] = benchmark
    if mine:
        filters["owner"] = config.current_user

    EntityList.run(
        Result,
        fields=["UID", "Benchmark", "Model", "Dataset", "Registered"],
        local_only=local,
        filters=filters,
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
    local: bool = typer.Option(
        False, "--local", help="Display local results if result ID is not provided"
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
    """Displays the information of one or more results
    """
    comms_func = config.comms.get_results
    if mine:
        comms_func = config.comms.get_user_results
    if benchmark is not None:
        # Decorate the get_benchmark_results function so it doesn't need to be called with
        # any arguments.
        def benchmark_results():
            return config.comms.get_benchmark_results(benchmark)

        comms_func = benchmark_results
    EntityView.run(entity_id, Result, format, local, comms_func, output)
