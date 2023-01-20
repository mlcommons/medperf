import typer
from typing import Optional

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.association.list import ListAssociations
from medperf.commands.association.approval import Approval
from medperf.commands.association.priority import AssociationPriority
from medperf.enums import Status

app = typer.Typer()


@clean_except
@app.command("ls")
def list(filter: Optional[str] = typer.Argument(None)):
    """Display all associations related to the current user.

    Args:
        filter (str, optional): Filter associations by approval status.
            Defaults to displaying all user associations.
    """
    ListAssociations.run(filter)


@clean_except
@app.command("approve")
def approve(
    benchmark_uid: int = typer.Option(..., "--benchmark", "-b", help="Benchmark UID"),
    dataset_uid: int = typer.Option(None, "--dataset", "-d", help="Dataset UID"),
    mlcube_uid: int = typer.Option(None, "--mlcube", "-m", help="MLCube UID"),
):
    """Approves an association between a benchmark and a dataset or model mlcube

    Args:
        benchmark_uid (int): Benchmark UID.
        dataset_uid (int, optional): Dataset UID.
        mlcube_uid (int, optional): Model MLCube UID.
    """
    Approval.run(benchmark_uid, Status.APPROVED, dataset_uid, mlcube_uid)
    config.ui.print("✅ Done!")


@clean_except
@app.command("reject")
def reject(
    benchmark_uid: int = typer.Option(..., "--benchmark", "-b", help="Benchmark UID"),
    dataset_uid: int = typer.Option(None, "--dataset", "-d", help="Dataset UID"),
    mlcube_uid: int = typer.Option(None, "--mlcube", "-m", help="MLCube UID"),
):
    """Rejects an association between a benchmark and a dataset or model mlcube

    Args:
        benchmark_uid (int): Benchmark UID.
        dataset_uid (int, optional): Dataset UID.
        mlcube_uid (int, optional): Model MLCube UID.
    """
    Approval.run(benchmark_uid, Status.REJECTED, dataset_uid, mlcube_uid)
    config.ui.print("✅ Done!")


@clean_except
@app.command("set_priority")
def set_priority(
    benchmark_uid: int = typer.Option(..., "--benchmark", "-b", help="Benchmark UID"),
    mlcube_uid: int = typer.Option(..., "--mlcube", "-m", help="MLCube UID"),
    priority: int = typer.Option(
        ...,
        "--priority",
        "-p",
        help="Priority Rank. A positive integer or -1 (for least priority)",
    ),
):
    """Updates the priority of a benchmark-model association. Priorities define
    the order of execution of the benchmark's models; a model with priority 1 will be
    executed before a model with priority 2. Setting a model's priority to -1 will
    make this model the last one being executed.

    Args:
        benchmark_uid (int): Benchmark UID.
        mlcube_uid (int): Model MLCube UID.
        priority (int): Priority Rank. A positive integer or -1 (for least priority)
    """
    AssociationPriority.run(benchmark_uid, mlcube_uid, priority)
    config.ui.print("✅ Done!")
