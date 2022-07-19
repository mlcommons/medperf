import typer

import medperf.config as config
from medperf.utils import cleanup
from medperf.decorators import clean_except
from medperf.commands.mlcube.list import CubesList
from medperf.commands.mlcube.submit import SubmitCube
from medperf.commands.mlcube.associate import AssociateCube

app = typer.Typer()


@clean_except
@app.command("ls")
def list(all: bool = typer.Option(False, help="Display all mlcubes")):
    """List mlcubes registered by the user by default.
    Use "all" to display all mlcubes in the platform
    """
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    CubesList.run(comms, ui, all)


@clean_except
@app.command("submit")
def submit():
    """Submits a new cube to the platform"""
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    SubmitCube.run(comms, ui)
    cleanup()
    ui.print("✅ Done!")


@clean_except
@app.command("associate")
def associate(
    benchmark_uid: int = typer.Option(..., "--benchmark", "-b", help="Benchmark UID"),
    model_uid: int = typer.Option(..., "--model_uid", "-m", help="Model UID"),
):
    """Associates an MLCube to a benchmark"""
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    AssociateCube.run(model_uid, benchmark_uid, comms, ui)
    ui.print("✅ Done!")
