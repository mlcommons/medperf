import typer

from medperf import config
from medperf.decorators import clean_except
from medperf.commands.benchmark import *
from medperf.utils import cleanup

app = typer.Typer()


@clean_except
@app.command("ls")
def list(
    all: bool = typer.Option(False, help="Display all benchmarks in the platform")
):
    """Lists all benchmarks created by the user
    If --all is used, displays all benchmarks in the platform
    """
    ui = config.ui
    comms = config.comms
    comms.authenticate()
    BenchmarksList.run(comms, ui, all)


@clean_except
@app.command("submit")
def submit():
    """Submits a new benchmark to the platform"""
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    SubmitBenchmark.run(comms, ui)
    cleanup()
    ui.print("✅ Done!")
