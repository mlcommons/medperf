import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.certificate.client_certificate import GetUserCertificate
from medperf.commands.certificate.server_certificate import GetServerCertificate

app = typer.Typer()


@app.command("get_client_certificate")
@clean_except
def get_client_certificate(
    training_exp_id: int = typer.Option(
        ...,
        "--training_exp_id",
        "-t",
        help="UID of training exp which you intend to be a part of",
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite cert and key if present"
    ),
):
    """get a client certificate"""
    GetUserCertificate.run(training_exp_id, overwrite)
    config.ui.print("✅ Done!")


@app.command("get_server_certificate")
@clean_except
def get_server_certificate(
    training_exp_id: int = typer.Option(
        ...,
        "--training_exp_id",
        "-t",
        help="UID of training exp which you intend to be a part of",
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite cert and key if present"
    ),
):
    """get a server certificate"""
    GetServerCertificate.run(training_exp_id, overwrite)
    config.ui.print("✅ Done!")
