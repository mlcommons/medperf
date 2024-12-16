import typer
from typing import Optional

from medperf.config_management import config
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
    demo_dataset_url: str = typer.Option(
        None,
        "--demo_dataset_url",
        help="""Identifier to download the demonstration dataset tarball file.\n
            See `medperf mlcube submit --help` for more information""",
    ),
    demo_dataset_hash: str = typer.Option(
        None, "--demo_dataset_hash", help="Hash of the demo dataset, if provided."
    ),
    data_path: str = typer.Option(None, "--data_path", help="Path to raw input data."),
    labels_path: str = typer.Option(
        None,
        "--labels_path",
        help="Path to the labels of the raw input data, if provided.",
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
        False, "--no-cache", help="Execute the test even if results already exist"
    ),
    offline: bool = typer.Option(
        False,
        "--offline",
        help="Execute the test without connecting to the MedPerf server.",
    ),
    skip_data_preparation_step: bool = typer.Option(
        False,
        "--skip-demo-data-preparation",
        help="Use this flag if the passed demo dataset or data path is already prepared",
    ),
):
    """
    Executes a compatibility test for a determined benchmark.
    Can test prepared and unprepared datasets, remote and local models independently.
    """
    CompatibilityTestExecution.run(
        benchmark_uid,
        data_prep,
        model,
        evaluator,
        data_path,
        labels_path,
        demo_dataset_url,
        demo_dataset_hash,
        data_uid,
        no_cache=no_cache,
        offline=offline,
        skip_data_preparation_step=skip_data_preparation_step,
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
