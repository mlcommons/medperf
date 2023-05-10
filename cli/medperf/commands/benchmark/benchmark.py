import typer
from typing import Optional

import medperf.config as config
from medperf.utils import cleanup
from medperf.decorators import clean_except
from medperf.entities.benchmark import Benchmark
from medperf.commands.list import EntityList
from medperf.commands.view import EntityView
from medperf.commands.edit import EntityEdit
from medperf.commands.benchmark.submit import SubmitBenchmark
from medperf.commands.benchmark.associate import AssociateBenchmark
from medperf.commands.result.create import BenchmarkExecution

NAME_HELP = "Name of the benchmark"
DESC_HELP = "Description of the benchmark"
DOCS_HELP = "URL to documentation"
DEMO_URL_HELP = """Identifier to download the demonstration dataset tarball file.\n
    See `medperf mlcube submit --help` for more information"""
DEMO_HASH_HELP = "SHA1 of demonstration dataset tarball file"
DATA_PREP_HELP = "Data Preparation MLCube UID"
MODEL_HELP = "Reference Model MLCube UID"
EVAL_HELP = "Evaluator MLCube UID"

app = typer.Typer()


@app.command("ls")
@clean_except
def list(
    local: bool = typer.Option(False, "--local", help="Get local benchmarks"),
    mine: bool = typer.Option(False, "--mine", help="Get current-user benchmarks"),
):
    """List benchmarks stored locally and remotely from the user"""
    EntityList.run(
        Benchmark,
        fields=["UID", "Name", "Description", "State", "Approval Status", "Registered"],
        local_only=local,
        mine_only=mine,
    )


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help=NAME_HELP),
    description: str = typer.Option(..., "--description", "-d", help=DESC_HELP),
    docs_url: str = typer.Option("", "--docs-url", "-u", help=DOCS_HELP),
    demo_url: str = typer.Option("","--demo-url",help=DEMO_URL_HELP),
    demo_hash: str = typer.Option("", "--demo-hash", help=DEMO_HASH_HELP),
    data_preparation_mlcube: int = typer.Option(
        ..., "--data-preparation-mlcube", "-p", help=DATA_PREP_HELP
    ),
    reference_model_mlcube: int = typer.Option(
        ..., "--reference-model-mlcube", "-m", help=MODEL_HELP
    ),
    evaluator_mlcube: int = typer.Option(
        ..., "--evaluator-mlcube", "-e", help=EVAL_HELP
    )
):
    """Submits a new benchmark to the platform"""
    benchmark_info = {
        "name": name,
        "description": description,
        "docs_url": docs_url,
        "demo_dataset_tarball_url": demo_url,
        "demo_dataset_tarball_hash": demo_hash,
        "data_preparation_mlcube": data_preparation_mlcube,
        "reference_model_mlcube": reference_model_mlcube,
        "data_evaluator_mlcube": evaluator_mlcube,
    }
    SubmitBenchmark.run(benchmark_info)
    cleanup()
    config.ui.print("✅ Done!")


@app.command("edit")
@clean_except
def edit(
    entity_id: int = typer.Argument(..., help="Benchmark ID"),
    name: str = typer.Option(None, "--name", "-n", help=NAME_HELP),
    description: str = typer.Option(None, "--description", "-d", help=DESC_HELP),
    docs_url: str = typer.Option(None, "--docs-url", "-u", help=DOCS_HELP),
    demo_url: str = typer.Option(None,"--demo-url",help=DEMO_URL_HELP),
    demo_hash: str = typer.Option(None, "--demo-hash", help=DEMO_HASH_HELP),
    data_preparation_mlcube: int = typer.Option(
        None, "--data-preparation-mlcube", "-p", help=DATA_PREP_HELP
    ),
    reference_model_mlcube: int = typer.Option(
        None, "--reference-model-mlcube", "-m", help=MODEL_HELP
    ),
    evaluator_mlcube: int = typer.Option(
        None, "--evaluator-mlcube", "-e", help=EVAL_HELP
    )
):
    """Edits a benchmark"""
    benchmark_info = {
        "name": name,
        "description": description,
        "docs_url": docs_url,
        "demo_dataset_tarball_url": demo_url,
        "demo_dataset_tarball_hash": demo_hash,
        "data_preparation_mlcube": data_preparation_mlcube,
        "reference_model_mlcube": reference_model_mlcube,
        "data_evaluator_mlcube": evaluator_mlcube,
    }
    EntityEdit.run(Benchmark, entity_id, benchmark_info)
    cleanup()
    config.ui.print("✅ Done!")


@app.command("associate")
@clean_except
def associate(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark_uid", "-b", help="UID of benchmark to associate with"
    ),
    model_uid: int = typer.Option(
        None, "--model_uid", "-m", help="UID of model MLCube to associate"
    ),
    dataset_uid: int = typer.Option(
        None, "--data_uid", "-d", help="Server UID of registered dataset to associate"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Execute the test even if results already exist",
    ),
):
    """Associates a benchmark with a given mlcube or dataset. Only one option at a time.
    """
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
        models_uids=None,
        no_cache=no_cache,
        models_input_file=file,
        ignore_model_errors=ignore_model_errors,
        show_summary=True,
        ignore_failed_experiments=True,
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
    """Displays the information of one or more benchmarks
    """
    EntityView.run(entity_id, Benchmark, format, local, mine, output)
