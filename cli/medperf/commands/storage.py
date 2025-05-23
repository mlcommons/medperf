import typer

from medperf import config
from medperf.decorators import clean_except
from medperf.utils import cleanup
from medperf.storage.utils import move_storage
from tabulate import tabulate

app = typer.Typer()


@app.command("ls")
@clean_except
def ls():
    """Show the location of the current medperf assets"""
    headers = ["Asset", "Location"]
    info = []
    for folder in config.storage:
        info.append((folder, config.storage[folder]["base"]))

    tab = tabulate(info, headers=headers)
    config.ui.print(tab)


@app.command("move")
@clean_except
def move(path: str = typer.Option(..., "--target", "-t", help="Target path")):
    """Moves all storage folders to a target base path. Folders include:
    Benchmarks, datasets, containers, results, tests, ...

    Args:
        path (str): target path
    """
    move_storage(path)


@app.command("cleanup")
def clean():
    """Cleans up clutter paths"""

    # Force cleanup to be true
    config.cleanup = True
    cleanup()
