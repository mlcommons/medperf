import typer
from medperf.commands.dataset import DatasetsList
from medperf.decorators import clean_except

app = typer.Typer()


@clean_except
@app.command("ls")
def datasets():
    """Lists all local datasets
	"""
    ui = state["ui"]
    DatasetsList.run(ui)
