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
        "If not provided, the default configured ca will be used.",
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite cert and key if present"
    ),
):

    GetUserCertificate.run(ca_id, overwrite=overwrite)
    config.ui.print("✅ Done!")


@app.command("get_server_certificate")
@clean_except
def get_server_certificate(
    aggregator_id: int = typer.Option(
        ...,
        "--aggregator_id",
        "-a",
        help="UID of the aggregator you wish to get a certificate for.",
    ),
    ca_id: int = typer.Option(
        None,
        "--ca_id",
        "--ca-id",
        "-c",
        help="UID of the Certificate Authority (CA) from which a "
        "Certificate will be obtained. "
        "If not provided, the default configured ca will be used.",
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite cert and key if present"
    ),
):
    """Get a server certificate."""
    GetServerCertificate.run(aggregator_id, ca_id, overwrite)
    config.ui.print("✅ Done!")


@app.command("submit_client_certificate")
@clean_except
def submit_client_certificate(
    name: str = typer.Option(..., "--name", "-n", help="Name of the Certificate"),
    ca_id: int = typer.Option(
        None,
        "--ca_id",
        "--ca-id",
        "-c",
        help="UID of the Certificate Authority (CA) from which a "
        "Certificate will be obtained. "
        "If not provided, the default configured ca will be used.",
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """
    Upload a client certificate to the Medperf Server.
    If you are a data owner associated with a benchmark, note that after uploading a certificate,
    your e-mail will be publicly available to model owners associated with the benchmark
    """
    SubmitCertificate.run(name=name, ca_id=ca_id, approved=approval)
    config.ui.print("✅ Done!")
