import typer
from typing import Optional
from pathlib import Path

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.view import EntityView
from medperf.entities.report import TestReport
from medperf.commands.list import EntityList
from medperf.commands.compatibility_test.run import CompatibilityTestExecution

app = typer.Typer()


@app.command("run")
@clean_except
def run(
    benchmark_uid: int = typer.Option(
        None, "--benchmark", "-b", help="UID of the benchmark to test. Optional"
    ),
    data_uid: str = typer.Option(
        None,
        "--data_uid",
        "-d",
        help="Prepared Dataset UID. Used for dataset testing. Optional. Defaults to benchmark demo dataset.",
    ),
    data_prep: str = typer.Option(
        None,
        "--data_preparator",
        "-p",
        help=(
            "UID or local path to the data preparation container config file."
            " Optional. Defaults to benchmark data preparator."
        ),
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help=(
            "UID or local path to the model container config file."
            " Optional. Defaults to benchmark reference model."
        ),
    ),
    evaluator: str = typer.Option(
        None,
        "--evaluator",
        "-e",
        help=(
            "UID or local path to the evaluator container config file."
            " Optional. Defaults to benchmark evaluator."
        ),
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Execute the test even if results already exist"
    ),
    skip_data_preparation_step: bool = typer.Option(
        False,
        "--skip-demo-data-preparation",
        help="Use this flag if the passed demo dataset or data path is already prepared",
    ),
    model_decryption_key: Path = typer.Option(
        None,
        "--decryption-key",
        "--decryption_key",
        "-d",
        help="Only used for compatibility tests of encrypted containers. "
        "Path to the decryption key file for the encrypted container.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """
    Executes a compatibility test.
    """
    CompatibilityTestExecution.run(
        benchmark_uid,
        data_prep,
        model,
        evaluator,
        data_uid,
        no_cache=no_cache,
        skip_data_preparation_step=skip_data_preparation_step,
        model_decryption_key=model_decryption_key,
    )
    config.ui.print("✅ Done!")


@app.command("ls")
@clean_except
def list():
    """List previously executed tests reports."""
    EntityList.run(
        TestReport,
        fields=["UID", "Data Source", "Model", "Evaluator"],
        unregistered=True,
    )


@app.command("view")
@clean_except
def view(
    entity_id: Optional[str] = typer.Argument(None, help="Test report ID"),
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
    """Displays the information of one or more test reports"""
    EntityView.run(entity_id, TestReport, format, unregistered=True, output=output)
