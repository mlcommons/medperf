import typer
from typing import Optional
from pathlib import Path

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.view import EntityView
from medperf.entities.report import TestReport
from medperf.commands.list import EntityList
from medperf.commands.compatibility_test.run import CompatibilityTestExecution
import medperf.help_texts as help_texts

app = typer.Typer()


@app.command("run")
@clean_except
def run(
    benchmark_uid: int = typer.Option(
        None, "--benchmark", "-b", help=help_texts.CompatibilityTest.benchmark_uid
    ),
    data_uid: str = typer.Option(
        None,
        "--data_uid",
        "-d",
        help=help_texts.CompatibilityTest.data_uid,
    ),
    data_prep: str = typer.Option(
        None,
        "--data_preparator",
        "-p",
        help=help_texts.CompatibilityTest.data_preparation,
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help=help_texts.CompatibilityTest.model,
    ),
    evaluator: str = typer.Option(
        None,
        "--evaluator",
        "-e",
        help=help_texts.CompatibilityTest.evaluator,
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help=help_texts.CompatibilityTest.no_cache
    ),
    skip_data_preparation_step: bool = typer.Option(
        False,
        "--skip-demo-data-preparation",
        help=help_texts.CompatibilityTest.skip_data_preparation,
    ),
    model_decryption_key: Path = typer.Option(
        None,
        "--decryption-key",
        "--decryption_key",
        "-d",
        help=help_texts.CompatibilityTest.model_decryption_key,
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
    entity_id: Optional[str] = typer.Argument(
        None, help=help_texts.CompatibilityTest.id
    ),
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
    """Displays the information of one or more test reports"""
    EntityView.run(entity_id, TestReport, format, unregistered=True, output=output)
