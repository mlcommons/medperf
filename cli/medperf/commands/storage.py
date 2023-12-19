import typer

from medperf import config
from medperf.decorators import clean_except
from medperf.utils import cleanup
from medperf.storage.utils import move_storage

app = typer.Typer()


@app.command("move")
@clean_except
def move(path: str = typer.Option(..., "--target", "-t", help="Target path")):
    """Moves all storage folders to a target path. Folders include:
    Benchmarks, datasets, mlcubes, results, tests, ...

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
