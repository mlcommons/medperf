import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.mlcube import CubesList

app = typer.Typer()


@clean_except
@app.command("ls")
def list():
    """List mlcubes registered by the user"""
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    CubesList.run(comms, ui)
