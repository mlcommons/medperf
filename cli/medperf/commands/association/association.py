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
    priority: int = typer.Option(..., "--priority", "-p", help="Priority, an integer",),
):
    """Updates the priority of a benchmark-model association. Model priorities within
    a benchmark define which models need to be executed before others when
    this benchmark is run. A model with a higher priority is executed before
    a model with lower priority. The order of execution of models of the same priority
    is arbitrary.
    Examples:
    Assume there are three models of IDs (1,2,3), associated with a certain benchmark,
    all having priority = 0.
    - By setting the priority of model (2) to the value of 1, the client will make
    sure that model (2) is executed before models (1,3).
    - By setting the priority of model (1) to the value of -5, the client will make
    sure that models (2,3) are executed before model (1).

    Args:
        benchmark_uid (int): Benchmark UID.
        mlcube_uid (int): Model MLCube UID.
        priority (int): Priority, an integer
    """
    AssociationPriority.run(benchmark_uid, mlcube_uid, priority)
    config.ui.print("✅ Done!")
