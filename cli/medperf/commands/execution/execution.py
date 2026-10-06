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
import medperf.help_texts as help_texts

app = typer.Typer()


@app.command("create")
@clean_except
def create(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help=help_texts.Benchmark.uid
    ),
    data_uid: int = typer.Option(
        ..., "--data_uid", "-d", help=help_texts.Dataset.registered_uid
    ),
    model_uid: int = typer.Option(
        ..., "--model_uid", "-m", help=help_texts.Result.model_uid
    ),
    ignore_model_errors: bool = typer.Option(
        False,
        "--ignore-model-errors",
        help=help_texts.Common.ignore_model_errors,
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help=help_texts.Common.no_cache,
    ),
    new_result: bool = typer.Option(
        False,
        "--new-result",
        help=help_texts.Result.new_result,
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
    result_uid: int = typer.Option(None, "--result", "-r", help=help_texts.Result.uid),
    benchmark_uid: int = typer.Option(
        None, "--benchmark", "-b", help=help_texts.Benchmark.uid
    ),
    data_uid: int = typer.Option(
        None, "--data_uid", "-d", help=help_texts.Dataset.registered_uid
    ),
    model_uid: int = typer.Option(
        None, "--model_uid", "-m", help=help_texts.Result.model_uid
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
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
        False, "--unregistered", help=help_texts.Result.ls_unregistered
    ),
    mine: bool = typer.Option(False, "--mine", help=help_texts.Result.ls_mine),
    benchmark: int = typer.Option(
        None, "--benchmark", "-b", help=help_texts.Result.benchmark_filter
    ),
    model: int = typer.Option(
        None, "--model", "-m", help=help_texts.Result.model_filter
    ),
    dataset: int = typer.Option(
        None, "--dataset", "-d", help=help_texts.Result.dataset_filter
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
    entity_id: Optional[str] = typer.Argument(None, help=help_texts.Result.id),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help=help_texts.Common.format,
    ),
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help=help_texts.Result.view_unregistered,
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help=help_texts.Result.view_mine,
    ),
    benchmark: int = typer.Option(
        None, "--benchmark", "-b", help=help_texts.Result.benchmark_filter
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help=help_texts.Common.output,
    ),
):
    """Displays the information of one or more results"""
    EntityView.run(
        entity_id, Execution, format, unregistered, mine, output, benchmark=benchmark
    )


@app.command("show_local_results")
@clean_except
def show_local_results(
    result_id: int = typer.Argument(..., help=help_texts.Result.id),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help=help_texts.Common.format,
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help=help_texts.Common.output,
    ),
):
    """Displays the local results of an execution"""
    ShowLocalResults.run(result_id, format, output)
