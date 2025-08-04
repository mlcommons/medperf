import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.certificate.client_certificate import GetUserCertificate
from medperf.commands.certificate.server_certificate import GetServerCertificate
from medperf.exceptions import InvalidArgumentError

app = typer.Typer()


@app.command("get_client_certificate")
@clean_except
def get_client_certificate(
    training_exp_id: int = typer.Option(
        None,
        "--training_exp_id",
        "-t",
        help="UID of training exp which you intend to be a part of. Only one of training_exp_ip or container_id must be provided.",
    ),
    container_id: int = typer.Option(
        None,
        "--container-id",
        "--container_id",
        "-c",
        help="UID of the Private container you intend to use. Only one of training_exp_ip or container_id must be provided.",
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite cert and key if present"
    ),
):
    """get a client certificate"""
    if training_exp_id is not None and container_id is not None:
        raise InvalidArgumentError(
            "Only one of training_exp_id or container_id may be provided!"
        )

    GetUserCertificate.run(
        training_exp_id=training_exp_id, container_id=container_id, overwrite=overwrite
    )
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
