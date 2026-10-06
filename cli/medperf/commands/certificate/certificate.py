import typer

import medperf.config as config
from medperf.decorators import clean_except
from medperf.commands.certificate.client_certificate import GetUserCertificate
from medperf.commands.certificate.server_certificate import GetServerCertificate
from medperf.commands.certificate.submit import SubmitCertificate
from medperf.commands.certificate.delete_client_certificate import DeleteCertificate
from medperf.commands.certificate.check_client_certificate import CheckUserCertificate
from medperf.enums import CryptoKeyType
import medperf.help_texts as help_texts

app = typer.Typer()


@app.command("get_client_certificate")
@clean_except
def get_client_certificate(
    key_type: CryptoKeyType = typer.Option(
        ..., "--key_type", help=help_texts.Certificate.get_key_type
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help=help_texts.Certificate.overwrite
    ),
):
    """Get a client certificate."""
    GetUserCertificate.run(key_type=key_type, overwrite=overwrite)
    config.ui.print("✅ Done!")


@app.command("get_server_certificate")
@clean_except
def get_server_certificate(
    aggregator_id: int = typer.Option(
        ...,
        "--aggregator_id",
        "-a",
        help=help_texts.Certificate.aggregator_id,
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help=help_texts.Certificate.overwrite
    ),
):
    """Get a server certificate."""
    GetServerCertificate.run(aggregator_id, overwrite)
    config.ui.print("✅ Done!")


@app.command("submit_client_certificate")
@clean_except
def submit_client_certificate(
    key_type: CryptoKeyType = typer.Option(
        ..., "--key_type", help=help_texts.Certificate.submit_key_type
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
):
    """
    Upload a client certificate to the Medperf Server.
    If you are a data owner associated with a benchmark, note that after uploading a certificate,
    your e-mail will be publicly available to model owners associated with the benchmark
    """
    SubmitCertificate.run(key_type=key_type, approved=approval)
    config.ui.print("✅ Done!")


@app.command("delete_client_certificate")
@clean_except
def delete_client_certificate(
    key_type: CryptoKeyType = typer.Option(
        ..., "--key_type", help=help_texts.Certificate.delete_key_type
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
):
    """
    Invalidate a client certificate.
    """
    DeleteCertificate.run(key_type=key_type, approved=approval)
    config.ui.print("✅ Done!")


@app.command("check_client_certificate")
@clean_except
def check_client_certificate(
    key_type: CryptoKeyType = typer.Option(
        ..., "--key_type", help=help_texts.Certificate.check_key_type
    ),
):
    """
    Check if the user already has a certificate (local or uploaded).
    """
    CheckUserCertificate.run(key_type=key_type)
    config.ui.print("✅ Done!")
