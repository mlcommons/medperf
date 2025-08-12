import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.certificate.client_certificate import GetUserCertificate
from medperf.commands.certificate.server_certificate import GetServerCertificate
from medperf.commands.certificate.submit import SubmitCertificate
from medperf.exceptions import InvalidArgumentError

app = typer.Typer()


@app.command("get_client_certificate")
@clean_except
def get_client_certificate(
    training_exp_id: int = typer.Option(
        None,
        "--training_exp_id",
        "-t",
        help="UID of training exp which you intend to be a part of. "
        "Only one of training_exp_ip or container_id must be provided.",
    ),
    container_id: int = typer.Option(
        None,
        "--container-id",
        "--container_id",
        "-c",
        help="UID of the Private container you intend to use. "
        "Only one of training_exp_ip or container_id must be provided.",
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite cert and key if present"
    ),
):
    """Get a client certificate."""
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
    """Get a server certificate."""
    GetServerCertificate.run(training_exp_id, overwrite)
    config.ui.print("✅ Done!")


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help="Name of the Certificate"),
    ca_id: int = typer.Option(
        ...,
        "--ca-id",
        "--ca_id",
        help="UID of the Certificate Authority (CA) that issued the certificate.\n"
        "You can view the registered CAs with the command 'medperf ca ls'. ",
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """
    Upload a client certificate to the Medperf Server.
    NOTE: After uploading a certificate, your e-mail will be publicly available to other users
    associated with the same Certificate Authority (CA).
    """
    SubmitCertificate.run(name=name, ca_id=ca_id, approved=approval)
    config.ui.print("✅ Done!")
