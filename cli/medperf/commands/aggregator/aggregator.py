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
    name: str = typer.Option(..., "--name", "-n", help="Name of the aggregator"),
    address: str = typer.Option(
        ..., "--address", "-a", help="Address/domain of the aggregator"
    ),
    port: int = typer.Option(
        ..., "--port", "-p", help="The port which the aggregator will use"
    ),
    aggregation_mlcube: int = typer.Option(
        ..., "--aggregation-mlcube", "-m", help="Aggregation MLCube UID"
    ),
):
    """Submits an aggregator"""
    SubmitAggregator.run(name, address, port, aggregation_mlcube)
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
    training_exp_id: int = typer.Option(
        ...,
        "--training_exp_id",
        "-t",
        help="UID of training experiment whose aggregator to be run",
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite outputs if present"
    ),
):
    """Starts the aggregation server of a training experiment"""
    StartAggregator.run(training_exp_id, overwrite)
    config.ui.print("✅ Done!")


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help="Get unregistered aggregators"
    ),
    mine: bool = typer.Option(False, "--mine", help="Get current-user aggregators"),
):
    """List aggregators"""
    EntityList.run(
        Aggregator,
        fields=["UID", "Name", "Address", "Port"],
        unregistered=unregistered,
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
    """Displays the information of one or more aggregators"""
    EntityView.run(entity_id, Aggregator, format, unregistered, mine, output)
