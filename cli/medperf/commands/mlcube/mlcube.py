import typer
from typing import Optional

import medperf.config as config
from medperf.utils import cleanup
from medperf.decorators import clean_except
from medperf.entities.cube import Cube
from medperf.commands.view import EntityView
from medperf.commands.mlcube.list import CubesList
from medperf.commands.mlcube.submit import SubmitCube
from medperf.commands.mlcube.associate import AssociateCube

app = typer.Typer()


@app.command("ls")
@clean_except
def list(all: bool = typer.Option(False, help="Display all mlcubes")):
    """List mlcubes registered by the user by default.
    Use "all" to display all mlcubes in the platform
    """
    CubesList.run(all)


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help="Name of the mlcube"),
    mlcube_file: str = typer.Option(
        ..., "--mlcube-file", "-m", help="URL to mlcube file"
    ),
    mlcube_hash: str = typer.Option("", "--mlcube-hash", help="SHA1 of mlcube file"),
    params_file: str = typer.Option(
        "", "--parameters-file", "-p", help="URL to parameters file"
    ),
    parameters_hash: str = typer.Option(
        "", "--parameters-hash", help="SHA1 of parameters file"
    ),
    additional_file: str = typer.Option(
        "", "--additional-file", "-a", help="URL to additional files tarball"
    ),
    additional_hash: str = typer.Option(
        "", "--additional-hash", help="SHA1 of additional file"
    ),
    image_file: str = typer.Option(
        "",
        "--image-file",
        "-i",
        help="URL to image file. Expected image to be compressed inside a tarball",
    ),
    image_hash: str = typer.Option("", "--image-hash", help="SHA1 of image file"),
):
    """Submits a new cube to the platform"""
    mlcube_info = {
        "name": name,
        "mlcube_file": mlcube_file,
        "mlcube_hash": mlcube_hash,
        "params_file": params_file,
        "parameters_hash": parameters_hash,
        "image_tarball_url": image_file,
        "image_tarball_hash": image_hash,
        "additional_files_tarball_url": additional_file,
        "additional_files_tarball_hash": additional_hash,
    }
    SubmitCube.run(mlcube_info)
    cleanup()
    config.ui.print("✅ Done!")


@app.command("associate")
@clean_except
def associate(
    benchmark_uid: int = typer.Option(..., "--benchmark", "-b", help="Benchmark UID"),
    model_uid: int = typer.Option(..., "--model_uid", "-m", help="Model UID"),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
    force_test: bool = typer.Option(
        False, "--force-test", help="Execute the test even if results already exist",
    ),
):
    """Associates an MLCube to a benchmark"""
    AssociateCube.run(
        model_uid, benchmark_uid, approved=approval, force_test=force_test
    )
    config.ui.print("✅ Done!")


@app.command("view")
@clean_except
def view(
    entity_id: Optional[int] = typer.Argument(None, help="MLCube ID"),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help="Format to display contents. Available formats: [yaml, json]",
    ),
    local: bool = typer.Option(False, "--local", help="Display local mlcubes"),
    mine: bool = typer.Option(False, "--mine", help="Display current-user mlcubes"),
    output: str = typer.Option(
        None, "--output", "-o", help="Output file to store contents"
    ),
):
    """Displays the information of one or more mlcubes
    """
    EntityView.run(entity_id, Cube, format, local, mine, output)
