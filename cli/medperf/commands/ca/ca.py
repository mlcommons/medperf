from typing import Optional
from medperf.entities.ca import CA
import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.ca.submit import SubmitCA
from medperf.commands.ca.associate import AssociateCA

from medperf.commands.list import EntityList
from medperf.commands.view import EntityView

app = typer.Typer()


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help="Name of the ca"),
    config_path: str = typer.Option(
        ...,
        "--config-path",
        "-c",
        help="Path to the configuration file (JSON) of the CA",
    ),
    ca_mlcube: int = typer.Option(..., "--ca-mlcube", help="CA MLCube UID"),
    client_mlcube: int = typer.Option(
        ...,
        "--client-mlcube",
        help="MLCube UID to be used by clients to get a cert",
    ),
    server_mlcube: int = typer.Option(
        ...,
        "--server-mlcube",
        help="MLCube UID to be used by servers to get a cert",
    ),
):
    """Submits a ca"""
    SubmitCA.run(name, config_path, ca_mlcube, client_mlcube, server_mlcube)
    config.ui.print("✅ Done!")


@app.command("associate")
@clean_except
def associate(
    ca_id: int = typer.Option(..., "--ca_id", "-a", help="UID of CA to associate with"),
    training_exp_id: int = typer.Option(
        ..., "--training_exp_id", "-t", help="UID of training exp to associate with"
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """Associates a CA with a training experiment."""
    AssociateCA.run(ca_id, training_exp_id, approved=approval)
    config.ui.print("✅ Done!")


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help="Get unregistered CAs"
    ),
    mine: bool = typer.Option(False, "--mine", help="Get current-user CAs"),
):
    """List CAs"""
    EntityList.run(
        CA,
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
    """Displays the information of one or more CAs"""
    EntityView.run(entity_id, CA, format, unregistered, mine, output)
