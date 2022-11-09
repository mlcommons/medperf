import typer

import medperf.config as config
from medperf.decorators import clean_except
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
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help="UID of the executed benchmark"
    ),
    data_uid: str = typer.Option(
        ..., "--data_uid", "-d", help="UID of the dataset used for results"
    ),
    model_uid: int = typer.Option(
        ..., "--model_uid", "-m", help="UID of the executed model"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """Submits already obtained results to the server"""
    ResultSubmission.run(benchmark_uid, data_uid, model_uid, approved=approval)
    config.ui.print("✅ Done!")


@app.command("ls")
@clean_except
def list():
    """List results stored locally and remotely from the user"""
    ResultsList.run()
