import typer
from typing import Optional

import medperf.config as config
from medperf.decorators import clean_except
from medperf.entities.asset import Asset
from medperf.commands.list import EntityList
from medperf.commands.view import EntityView
from medperf.commands.asset.submit import SubmitAsset

app = typer.Typer()


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help="Name of the asset"),
    asset_path: Optional[str] = typer.Option(
        None, "--asset-path", "-p", help="Local path to the asset file"
    ),
    asset_url: Optional[str] = typer.Option(
        None, "--asset-url", "-u", help="URL to download the asset from"
    ),
    operational: bool = typer.Option(
        False, "--operational", help="Submit the asset as OPERATIONAL"
    ),
):
    """Registers a new asset to the platform.

    The asset can be provided either as a local file path or a URL.
    The file will be hashed and stored locally. The hash and URL are
    uploaded to the server.
    """
    SubmitAsset.run(
        name=name,
        asset_path=asset_path,
        asset_url=asset_url,
        operational=operational,
    )
    config.ui.print("Done!")


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help="Get unregistered assets"
    ),
    mine: bool = typer.Option(False, "--mine", help="Get current-user assets"),
    name: str = typer.Option(None, "--name", "-n", help="Filter out by asset Name"),
    owner: int = typer.Option(None, "--owner", help="Filter by owner ID"),
    state: str = typer.Option(
        None, "--state", help="Filter by state (DEVELOPMENT/OPERATION)"
    ),
):
    """List assets"""
    EntityList.run(
        Asset,
        fields=["UID", "Name", "State", "Registered"],
        unregistered=unregistered,
        mine_only=mine,
        name=name,
        owner=owner,
        state=state,
    )


@app.command("view")
@clean_except
def view(
    entity_id: Optional[int] = typer.Argument(None, help="Asset ID"),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help="Format to display contents. Available formats: [yaml, json]",
    ),
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help="Display unregistered assets if asset ID is not provided",
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help="Display current-user assets if asset ID is not provided",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file to store contents. If not provided, the output will be displayed",
    ),
):
    """Displays the information of one or more assets"""
    EntityView.run(entity_id, Asset, format, unregistered, mine, output)
