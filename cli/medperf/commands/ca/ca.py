from typing import Optional
from medperf.entities.ca import CA
import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.ca.submit import SubmitCA

from medperf.commands.list import EntityList
from medperf.commands.view import EntityView
import medperf.help_texts as help_texts

app = typer.Typer()


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help=help_texts.CA.name),
    config_path: str = typer.Option(
        ...,
        "--config-path",
        "-c",
        help=help_texts.CA.config_path,
    ),
    ca_mlcube: int = typer.Option(
        ..., "--ca-container", help=help_texts.CA.ca_container
    ),
    client_mlcube: int = typer.Option(
        ...,
        "--client-container",
        help=help_texts.CA.client_container,
    ),
    server_mlcube: int = typer.Option(
        ...,
        "--server-container",
        help=help_texts.CA.server_container,
    ),
):
    """Submits a ca"""
    SubmitCA.run(name, config_path, ca_mlcube, client_mlcube, server_mlcube)
    config.ui.print("✅ Done!")


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help=help_texts.CA.ls_unregistered
    ),
    mine: bool = typer.Option(False, "--mine", help=help_texts.CA.ls_mine),
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
    entity_id: Optional[int] = typer.Argument(None, help=help_texts.CA.id),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help=help_texts.Common.format,
    ),
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help=help_texts.CA.view_unregistered,
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help=help_texts.CA.view_mine,
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help=help_texts.Common.output,
    ),
):
    """Displays the information of one or more CAs"""
    EntityView.run(entity_id, CA, format, unregistered, mine, output)
