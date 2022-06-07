import typer

import medperf.config as config
from medperf.utils import cleanup
from medperf.decorators import clean_except
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
    comms = config.comms
    ui = config.ui
    CubesList.run(comms, ui, all)


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help="Name of the mlcube"),
    mlcube_file: str = typer.Option(
        ..., "--mlcube-file", "-m", help="URL to mlcube file"
    ),
    params_file: str = typer.Option(
        ..., "--parameters-file", "-p", help="URL to parameters file"
    ),
    additional_file: str = typer.Option(
        "", "--additional-file", "-a", help="URL to additional file"
    ),
    additional_hash: str = typer.Option(
        "", "--additional-hash", "-h", help="SHA1 of additional file"
    ),
):
    """Submits a new cube to the platform"""
    comms = config.comms
    ui = config.ui
    mlcube_info = {
        "name": name,
        "mlcube_file": mlcube_file,
        "params_file": params_file,
        "additional_file": additional_file,
        "additional_hash": additional_hash,
    }
    SubmitCube.run(mlcube_info, comms, ui)
    cleanup()
    ui.print("✅ Done!")


@app.command("associate")
@clean_except
def associate(
    benchmark_uid: int = typer.Option(..., "--benchmark", "-b", help="Benchmark UID"),
    model_uid: int = typer.Option(..., "--model_uid", "-m", help="Model UID"),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """Associates an MLCube to a benchmark"""
    comms = config.comms
    ui = config.ui
    AssociateCube.run(model_uid, benchmark_uid, comms, ui, approved=approval)
    ui.print("✅ Done!")
