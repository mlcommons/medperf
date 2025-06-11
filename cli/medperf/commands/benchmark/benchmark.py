import typer
from typing import Optional

import medperf.config as config
from medperf.decorators import clean_except
from medperf.entities.benchmark import Benchmark
from medperf.commands.list import EntityList
from medperf.commands.view import EntityView
from medperf.commands.benchmark.submit import SubmitBenchmark
from medperf.commands.benchmark.associate import AssociateBenchmark
from medperf.commands.execution.create import BenchmarkExecution

app = typer.Typer()


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help="Get unregistered benchmarks"
    ),
    mine: bool = typer.Option(False, "--mine", help="Get current-user benchmarks"),
    name: str = typer.Option(None, "--name", help="Filter by name"),
    owner: int = typer.Option(None, "--owner", help="Filter by owner"),
    state: str = typer.Option(
        None, "--state", help="Filter by state (DEVELOPMENT/OPERATION)"
    ),
    is_valid: bool = typer.Option(
        None, "--valid/--invalid", help="Filter by valid status"
    ),
    is_active: bool = typer.Option(
        None, "--active/--inactive", help="Filter by active status"
    ),
    data_prep: int = typer.Option(
        None,
        "-d",
        "--data-preparation-container",
        help="Filter by Data Preparation Container",
    ),
):
    """List benchmarks"""
    filters = {
        "name": name,
        "owner": owner,
        "state": state,
        "is_valid": is_valid,
        "is_active": is_active,
        "data_preparation_mlcube": data_prep,
    }

    EntityList.run(
        Benchmark,
        fields=[
            "UID",
            "Name",
            "Description",
            "Data Preparation Container",
            "State",
            "Approval Status",
            "Registered",
        ],
        unregistered=unregistered,
        mine_only=mine,
        **filters,
    )


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help="Name of the benchmark"),
    description: str = typer.Option(
        ..., "--description", "-d", help="Description of the benchmark"
    ),
    docs_url: str = typer.Option("", "--docs-url", "-u", help="URL to documentation"),
    demo_url: str = typer.Option(
        ...,
        "--demo-url",
        help="""Identifier to download the demonstration dataset tarball file.\n
        See `medperf container submit --help` for more information""",
    ),
    demo_hash: str = typer.Option(
        "", "--demo-hash", help="Hash of demonstration dataset tarball file"
    ),
    data_preparation_container: int = typer.Option(
        ..., "--data-preparation-container", "-p", help="Data Preparation container UID"
    ),
    reference_model_container: int = typer.Option(
        ..., "--reference-model-container", "-m", help="Reference Model container UID"
    ),
    evaluator_container: int = typer.Option(
        ..., "--evaluator-container", "-e", help="Evaluator container UID"
    ),
    skip_data_preparation_step: bool = typer.Option(
        False,
        "--skip-demo-data-preparation",
        help="Use this flag if the demo dataset is already prepared",
    ),
    operational: bool = typer.Option(
        False,
        "--operational",
        help="Submit the Benchmark as OPERATIONAL",
    ),
):
    """Submits a new benchmark to the platform"""
    benchmark_info = {
        "name": name,
        "description": description,
        "docs_url": docs_url,
        "demo_dataset_tarball_url": demo_url,
        "demo_dataset_tarball_hash": demo_hash,
        "data_preparation_mlcube": data_preparation_container,
        "reference_model_mlcube": reference_model_container,
        "data_evaluator_mlcube": evaluator_container,
        "state": "OPERATION" if operational else "DEVELOPMENT",
    }
    SubmitBenchmark.run(
        benchmark_info,
        skip_data_preparation_step=skip_data_preparation_step,
    )
    config.ui.print("✅ Done!")


@app.command("associate")
@clean_except
def associate(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark_uid", "-b", help="UID of benchmark to associate with"
    ),
    model_uid: int = typer.Option(
        None, "--model_uid", "-m", help="UID of model container to associate"
    ),
    dataset_uid: int = typer.Option(
        None, "--data_uid", "-d", help="Server UID of registered dataset to associate"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Execute the test even if results already exist",
    ),
):
    """Associates a benchmark with a given model or dataset. Only one option at a time."""
    AssociateBenchmark.run(
        benchmark_uid, model_uid, dataset_uid, approved=approval, no_cache=no_cache
    )
    config.ui.print("✅ Done!")


@app.command("run")
@clean_except
def run(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help="UID of the desired benchmark"
    ),
    data_uid: int = typer.Option(
        ..., "--data_uid", "-d", help="Registered Dataset UID"
    ),
    file: str = typer.Option(
        None,
        "--models-from-file",
        "-f",
        help="""A file containing the model UIDs to be executed.\n
        The file should contain a single line as a list of\n
        comma-separated integers corresponding to the model UIDs""",
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
    rerun_finalized: bool = typer.Option(
        False,
        "--rerun-finalized",
        help="Execute even if results have been already uploaded (this will create new records)",
    ),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model"""
    BenchmarkExecution.run(
        benchmark_uid,
        data_uid,
        models_uids=None,
        models_input_file=file,
        ignore_model_errors=ignore_model_errors,
        no_cache=no_cache,
        show_summary=True,
        ignore_failed_experiments=True,
        rerun_finalized_executions=rerun_finalized,
    )
    config.ui.print("✅ Done!")


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
    EntityView.run(entity_id, Benchmark, format, unregistered, mine, output)
