from typing import Optional
from medperf.entities.aggregator import Aggregator
import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.aggregator.submit import SubmitAggregator
from medperf.commands.aggregator.associate import AssociateAggregator
from medperf.commands.aggregator.run import StartAggregator

from medperf.commands.list import EntityList
from medperf.commands.view import EntityView

app = typer.Typer()


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help="Name of the agg"),
    address: str = typer.Option(
        ..., "--address", "-a", help="UID of benchmark to associate with"
    ),
    port: int = typer.Option(
        ..., "--port", "-p", help="UID of benchmark to associate with"
    ),
):
    """Associates a benchmark with a given mlcube or dataset. Only one option at a time."""
    SubmitAggregator.run(name, address, port)
    config.ui.print("✅ Done!")


@app.command("associate")
@clean_except
def associate(
    aggregator_id: int = typer.Option(
        ..., "--aggregator_id", "-a", help="UID of benchmark to associate with"
    ),
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of benchmark to associate with"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """Associates a benchmark with a given mlcube or dataset. Only one option at a time."""
    AssociateAggregator.run(aggregator_id, training_exp_id, approved=approval)
    config.ui.print("✅ Done!")


@app.command("start")
@clean_except
def run(
    aggregator_id: int = typer.Option(
        ..., "--aggregator_id", "-a", help="UID of benchmark to associate with"
    ),
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of benchmark to associate with"
    ),
):
    """Associates a benchmark with a given mlcube or dataset. Only one option at a time."""
    StartAggregator.run(training_exp_id, aggregator_id)
    config.ui.print("✅ Done!")


@app.command("ls")
@clean_except
def list(
    local: bool = typer.Option(False, "--local", help="Get local aggregators"),
    mine: bool = typer.Option(False, "--mine", help="Get current-user aggregators"),
):
    """List aggregators stored locally and remotely from the user"""
    EntityList.run(
        Aggregator,
        fields=["UID", "Name", "Address", "Port"],
        local_only=local,
        mine_only=mine,
    )


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
    """Displays the information of one or more aggregators"""
    EntityView.run(entity_id, Aggregator, format, local, mine, output)
