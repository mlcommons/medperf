import typer
from typing import Optional

import medperf.config as config
from medperf.decorators import clean_except
from medperf.entities.model import Model
from medperf.commands.list import EntityList
from medperf.commands.view import EntityView
from medperf.commands.model.submit import SubmitModel
from medperf.commands.model.associate import AssociateModel

app = typer.Typer()


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help="Name of the model"),
    container_id: Optional[int] = typer.Option(
        None, "--container", "-c", help="Registered container ID (for CONTAINER type)"
    ),
    asset_id: Optional[int] = typer.Option(
        None, "--asset", "-a", help="Registered asset ID (for ASSET type)"
    ),
    operational: bool = typer.Option(
        False, "--operational", help="Submit the model as OPERATIONAL"
    ),
):
    """Registers a new model to the platform.

    A model wraps either a container or a file-based asset.
    For CONTAINER type, provide the container ID. For ASSET type, provide the asset ID.
    """
    SubmitModel.run(
        name=name,
        container_id=container_id,
        asset_id=asset_id,
        operational=operational,
    )
    config.ui.print("Done!")


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help="Get unregistered models"
    ),
    mine: bool = typer.Option(False, "--mine", help="Get current-user models"),
):
    """List models"""
    EntityList.run(
        Model,
        fields=["UID", "Name", "Type", "Registered"],
        unregistered=unregistered,
        mine_only=mine,
    )


@app.command("view")
@clean_except
def view(
    entity_id: Optional[int] = typer.Argument(None, help="Model ID"),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help="Format to display contents. Available formats: [yaml, json]",
    ),
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help="Display unregistered models if model ID is not provided",
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help="Display current-user models if model ID is not provided",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file to store contents. If not provided, the output will be displayed",
    ),
):
    """Displays the information of one or more models"""
    EntityView.run(entity_id, Model, format, unregistered, mine, output)


@app.command("associate")
@clean_except
def associate(
    benchmark_uid: int = typer.Option(..., "--benchmark", "-b", help="Benchmark UID"),
    model_uid: int = typer.Option(..., "--model_uid", "-m", help="Model UID"),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Execute the test even if results already exist",
    ),
):
    """Associates a model to a benchmark"""
    AssociateModel.run(model_uid, benchmark_uid, approved=approval, no_cache=no_cache)
    config.ui.print("✅ Done!")
