import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.association.approval import Approval

app = typer.Typer()


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
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    Approval.run(benchmark_uid, "APPROVED", comms, ui, dataset_uid, mlcube_uid)
    ui.print("✅ Done!")


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
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    Approval.run(benchmark_uid, "REJECT", comms, ui, dataset_uid, mlcube_uid)
    ui.print("✅ Done!")
