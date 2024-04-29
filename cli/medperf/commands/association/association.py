import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.association.list import ListAssociations
from medperf.commands.association.approval import Approval
from medperf.commands.association.priority import AssociationPriority
from medperf.enums import Status

app = typer.Typer()


@app.command("ls")
@clean_except
def list(
    benchmark: bool = typer.Option(False, "-b", help="list benchmark associations"),
    training_exp: bool = typer.Option(False, "-t", help="list training associations"),
    dataset: bool = typer.Option(False, "-d", help="list dataset associations"),
    mlcube: bool = typer.Option(False, "-m", help="list mlcube associations"),
    aggregator: bool = typer.Option(False, "-a", help="list aggregator associations"),
    ca: bool = typer.Option(False, "-c", help="list ca associations"),
    approval_status: str = typer.Option(
        None, "--approval-status", help="Approval status"
    ),
):
    """Display all associations related to the current user.

    Args:
        filter (str, optional): Filter associations by approval status.
            Defaults to displaying all user associations.
    """
    ListAssociations.run(
        benchmark,
        training_exp,
        dataset,
        mlcube,
        aggregator,
        ca,
        approval_status,
    )


@app.command("approve")
@clean_except
def approve(
    benchmark_uid: int = typer.Option(..., "--benchmark", "-b", help="Benchmark UID"),
    training_exp_uid: int = typer.Option(
        ..., "--training_exp", "-t", help="Training exp UID"
    ),
    dataset_uid: int = typer.Option(None, "--dataset", "-d", help="Dataset UID"),
    mlcube_uid: int = typer.Option(None, "--mlcube", "-m", help="MLCube UID"),
    aggregator_uid: int = typer.Option(
        None, "--aggregator", "-a", help="Aggregator UID"
    ),
    ca_uid: int = typer.Option(None, "--ca", "-c", help="CA UID"),
):
    """Approves an association between a benchmark and a dataset or model mlcube

    Args:
        benchmark_uid (int): Benchmark UID.
        dataset_uid (int, optional): Dataset UID.
        mlcube_uid (int, optional): Model MLCube UID.
    """
    Approval.run(
        Status.APPROVED,
        benchmark_uid,
        training_exp_uid,
        dataset_uid,
        mlcube_uid,
        aggregator_uid,
        ca_uid,
    )
    config.ui.print("✅ Done!")


@app.command("reject")
@clean_except
def reject(
    benchmark_uid: int = typer.Option(..., "--benchmark", "-b", help="Benchmark UID"),
    training_exp_uid: int = typer.Option(
        ..., "--training_exp", "-t", help="Training exp UID"
    ),
    dataset_uid: int = typer.Option(None, "--dataset", "-d", help="Dataset UID"),
    mlcube_uid: int = typer.Option(None, "--mlcube", "-m", help="MLCube UID"),
    aggregator_uid: int = typer.Option(
        None, "--aggregator", "-a", help="Aggregator UID"
    ),
    ca_uid: int = typer.Option(None, "--ca", "-c", help="CA UID"),
):
    """Rejects an association between a benchmark and a dataset or model mlcube

    Args:
        benchmark_uid (int): Benchmark UID.
        dataset_uid (int, optional): Dataset UID.
        mlcube_uid (int, optional): Model MLCube UID.
    """
    Approval.run(
        Status.REJECTED,
        benchmark_uid,
        training_exp_uid,
        dataset_uid,
        mlcube_uid,
        aggregator_uid,
        ca_uid,
    )
    config.ui.print("✅ Done!")


@app.command("set_priority")
@clean_except
def set_priority(
    benchmark_uid: int = typer.Option(..., "--benchmark", "-b", help="Benchmark UID"),
    mlcube_uid: int = typer.Option(..., "--mlcube", "-m", help="MLCube UID"),
    priority: int = typer.Option(..., "--priority", "-p", help="Priority, an integer"),
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
