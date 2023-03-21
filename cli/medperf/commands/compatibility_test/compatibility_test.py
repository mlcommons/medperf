import typer
from typing import Optional

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.view import EntityView
from medperf.entities.result import Result
from medperf.commands.list import EntityList
from medperf.utils import cleanup
from medperf.commands.compatibility_test.run import CompatibilityTestExecution

app = typer.Typer()


@app.command("run")
@clean_except
def run(
    benchmark_uid: int = typer.Option(
        None,
        "--benchmark",
        "-b",
        help="UID of the benchmark to test. If not passed, a temporary benchmark is created.",
    ),
    data_uid: str = typer.Option(
        None,
        "--data_uid",
        "-d",
        help="Prepared Dataset UID. Used for dataset testing. Optional. Defaults to benchmark demo dataset.",
    ),
    data_prep: str = typer.Option(
        None,
        "--data_preparation",
        "-p",
        help="UID or local path to the data preparation mlcube. Optional. Defaults to benchmark data preparation mlcube.",
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help="UID or local path to the model mlcube. Optional. Defaults to benchmark reference mlcube.",
    ),
    evaluator: str = typer.Option(
        None,
        "--evaluator",
        "-e",
        help="UID or local path to the evaluator mlcube. Optional. Defaults to benchmark evaluator mlcube",
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Execute the test even if results already exist",
    ),
):
    """
    Executes a compatibility test for a determined benchmark.
    Can test prepared datasets, remote and local models independently.
    """
    CompatibilityTestExecution.run(
        benchmark_uid, data_uid, data_prep, model, evaluator, no_cache=no_cache,
    )
    config.ui.print("✅ Done!")
    cleanup()


@app.command("ls")
@clean_except
def list(
    local: bool = typer.Option(False, "--local", help="Get local results"),
    mine: bool = typer.Option(False, "--mine", help="Get current-user results"),
):
    """List results stored locally and remotely from the user"""
    EntityList.run(
        Result,
        fields=["UID", "Benchmark", "Model", "Data", "Registered"],
        local_only=local,
        mine_only=mine,
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
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file to store contents. If not provided, the output will be displayed",
    ),
):
    """Displays the information of one or more results
    """
    EntityView.run(entity_id, Result, format, local, mine, output)
