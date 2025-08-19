from medperf.commands.certificate.utils import validate_exactly_one_input
import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.certificate.client_certificate import GetUserCertificate
from medperf.commands.certificate.server_certificate import GetServerCertificate
from medperf.commands.certificate.submit import SubmitCertificate


app = typer.Typer()


@app.command("get_client_certificate")
@clean_except
def get_client_certificate(
    ca_id: int = typer.Option(
        None,
        "--ca_id",
        "--ca-id",
        "-c",
        help="UID of the Certificate Authority (CA) from which a "
        "Certificate will be obtained. "
        "Exactly one ca_id, training_exp_id or model_id must be provided.",
    ),
    training_exp_id: int = typer.Option(
        None,
        "--training_exp_id",
        "-t",
        help="UID of training exp which you intend to be a part of. "
        "Exactly one ca_id, training_exp_ip or model_id must be provided.",
    ),
    model_id: int = typer.Option(
        None,
        "--model-id",
        "--model_id",
        "-m",
        help="UID of the Private container you intend to use. "
        "Exactly one ca_id training_exp_ip or model_id must be provided.",
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite cert and key if present"
    ),
):
    validate_exactly_one_input(ca_id=ca_id, model_id=model_id, training_exp_id=training_exp_id)

    GetUserCertificate.run(
        training_exp_id=training_exp_id, model_id=model_id, ca_id=ca_id, overwrite=overwrite
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
        None,
        "--ca_id",
        "--ca-id",
        "-c",
        help="UID of the Certificate Authority (CA) associated with the submitted "
        "Exactly one ca_id, training_exp_id or model_id must be provided.",
    ),
    training_exp_id: int = typer.Option(
        None,
        "--training_exp_id",
        "-t",
        help="Training experiment UID associated with the Certificate to be submitted. "
        "The relevant CA is automatically inferred from the Training Experiment UID."
        "Exactly one ca_id, training_exp_ip or model_id must be provided.",
    ),
    model_id: int = typer.Option(
        None,
        "--model-id",
        "--model_id",
        "-m",
        help="Private Model UID associated with the Certificate to be submitted. "
        "The relevant CA is automatically inferred from the Model UID."
        "Exactly one ca_id, training_exp_ip or model_id must be provided."
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """
    Upload a client certificate to the Medperf Server.
    NOTE: After uploading a certificate, your e-mail will be publicly available to other users
    associated with the same Certificate Authority (CA).
    """
    validate_exactly_one_input(ca_id=ca_id, model_id=model_id, training_exp_id=training_exp_id)
    SubmitCertificate.run(name=name, ca_id=ca_id, approved=approval)
    config.ui.print("✅ Done!")
