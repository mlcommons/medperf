import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.certificate.client_certificate import GetUserCertificate
from medperf.commands.certificate.server_certificate import GetServerCertificate
from medperf.commands.certificate.submit import SubmitCertificate
from medperf.commands.certificate.delete_client_certificate import DeleteCertificate
from medperf.commands.certificate.check_client_certificate import CheckUserCertificate

app = typer.Typer()


@app.command("get_client_certificate")
@clean_except
def get_client_certificate(
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite cert and key if present"
    )
):

    GetUserCertificate.run(overwrite=overwrite)
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
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite cert and key if present"
    ),
):
    """Get a server certificate."""
    GetServerCertificate.run(aggregator_id, overwrite)
    config.ui.print("✅ Done!")


@app.command("submit_client_certificate")
@clean_except
def submit_client_certificate(
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """
    Upload a client certificate to the Medperf Server.
    If you are a data owner associated with a benchmark, note that after uploading a certificate,
    your e-mail will be publicly available to model owners associated with the benchmark
    """
    SubmitCertificate.run(approved=approval)
    config.ui.print("✅ Done!")


@app.command("delete_client_certificate")
@clean_except
def delete_client_certificate(
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """
    Invalidate a client certificate.
    """
    DeleteCertificate.run(approved=approval)
    config.ui.print("✅ Done!")


@app.command("check_client_certificate")
@clean_except
def check_client_certificate():
    """
    Check if the user already has a certificate (local or uploaded).
    """
    CheckUserCertificate.run()
    config.ui.print("✅ Done!")
