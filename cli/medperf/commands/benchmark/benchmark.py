import typer

from medperf import config
from medperf.decorators import clean_except
from medperf.commands.benchmark import BenchmarksList

app = typer.Typer()


@clean_except
@app.command("ls")
def list():
    """Lists all benchmarks created by the user"""
    ui = config.ui
    comms = config.comms
    comms.authenticate()
    BenchmarksList.run(comms, ui)
