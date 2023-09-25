import typer
from typing import Optional

from medperf.decorators import clean_except
from medperf.commands.report.list import ListReports

app = typer.Typer()


@app.command("ls")
@clean_except
def list(
    benchmark_uid: Optional[int] = typer.Option(
        None, "--benchmark", "-b", help="Benchmark UID to get related reports from"
    ),
    mlcube_uid: Optional[int] = typer.Option(
        None, "--mlcube", "-m", help="MLCube UID to get related reports from"
    ),
    mine: Optional[bool] = typer.Option(
        False, "--mine", help="Get current user reports"
    ),
):
    """Get Data Preparation reports related to a benchmark, mlcube or current user

    Args:
        benchmark_uid (Optional[int], optional): Benchmark UID.
        mlcube_uid (Optional[int], optional): MLCube UID.
        mine (Optional[bool], optional): Wether to get reports from the current user.
    """
    ListReports.run(benchmark_uid, mlcube_uid, mine)
