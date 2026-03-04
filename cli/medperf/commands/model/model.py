import typer
from typing import Optional

import medperf.config as config
from medperf.decorators import clean_except
from medperf.entities.model import Model
from medperf.commands.list import EntityList
from medperf.commands.view import EntityView
from medperf.commands.model.submit import SubmitModel
from medperf.commands.model.associate import AssociateModel
from medperf.commands.model.grant_access import GrantAccess
from medperf.commands.model.check_access import CheckAccess
from medperf.commands.mlcube.revoke_user_access import RevokeUserAccess
from medperf.commands.model.delete_keys import DeleteKeys
from medperf.exceptions import CleanExit
import time

app = typer.Typer()


@app.command("submit")
@clean_except
def submit(
    # Model options
    name: str = typer.Option(..., "--name", "-n", help="Name of the model"),
    operational: bool = typer.Option(
        False, "--operational", help="Submit the model as OPERATIONAL"
    ),
    # Container-backed model options
    container_config_file: str = typer.Option(
        ...,
        "--container-config-file",
        "-m",
        help="Container Config file.",
    ),
    parameters_file: str = typer.Option(
        None,
        "--parameters-file",
        "-p",
        help="container parameters file.",
    ),
    additional_file: str = typer.Option(
        None,
        "--additional-file",
        "-a",
        help="Identifier to download the additional files tarball. See the description above",
    ),
    additional_hash: str = typer.Option(
        None, "--additional-hash", help="hash of additional file"
    ),
    image_hash: str = typer.Option(None, "--image-hash", help="hash of image file"),
    decryption_key: Optional[str] = typer.Option(
        None,
        "--decryption-key",
        "--decryption_key",
        "-d",
        help="Path to the decryption key file for the encrypted container. The key "
        "will stay local. This should only be provided for encrypted container submissions.",
    ),
    # Asset-backed model options
    asset_path: Optional[str] = typer.Option(
        None, "--asset-path", help="Local path to the asset file"
    ),
    asset_url: Optional[str] = typer.Option(
        None, "--asset-url", help="URL to download the asset from"
    ),
):
    """Registers a new model to the platform.

    A model can be backed by a container or a file-based asset.
    For a container-backed model, provide --container-config (and optionally other container options).
    For an asset-backed model, provide --asset-path or --asset-url.
    """

    SubmitModel.run(
        name=name,
        operational=operational,
        container_config_file=container_config_file,
        parameters_config_file=parameters_file,
        additional_file=additional_file,
        additional_hash=additional_hash,
        image_hash=image_hash,
        decryption_key=decryption_key,
        asset_path=asset_path,
        asset_url=asset_url,
    )
    config.ui.print("✅ Done!")


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help="Get unregistered models"
    ),
    mine: bool = typer.Option(False, "--mine", help="Get current-user models"),
):
    """List models"""
    EntityList.run(
        Model,
        fields=["UID", "Name", "Type", "Registered"],
        unregistered=unregistered,
        mine_only=mine,
    )


@app.command("view")
@clean_except
def view(
    entity_id: Optional[int] = typer.Argument(None, help="Model ID"),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help="Format to display contents. Available formats: [yaml, json]",
    ),
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help="Display unregistered models if model ID is not provided",
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help="Display current-user models if model ID is not provided",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file to store contents. If not provided, the output will be displayed",
    ),
):
    """Displays the information of one or more models"""
    EntityView.run(entity_id, Model, format, unregistered, mine, output)


@app.command("associate")
@clean_except
def associate(
    benchmark_uid: int = typer.Option(..., "--benchmark", "-b", help="Benchmark UID"),
    model_uid: int = typer.Option(..., "--model_uid", "-m", help="Model UID"),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Execute the test even if results already exist",
    ),
):
    """Associates a model to a benchmark"""
    AssociateModel.run(model_uid, benchmark_uid, approved=approval, no_cache=no_cache)
    config.ui.print("✅ Done!")


@app.command("grant_access")
@clean_except
def grant_access(
    model_id: int = typer.Option(
        ...,
        "-m",
        "--model-id",
        "--model_id",
        help="Private model for which access will be granted.",
    ),
    benchmark_id: int = typer.Option(
        ...,
        "-b",
        "--benchmark-id",
        "--benchmark_id",
        help="Benchmark UID to which the Private model is associated. "
        "All data owners registered to this benchmark and have "
        "a valid certificate will be granted access to the model.",
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
    allowed_emails: str = typer.Option(
        None,
        "-a",
        "--allowed_emails",
        help="Space-separated list of emails",
    ),
):
    """
    Allows all currently registered Data Owners in a given benchmark to access
    a Private model registered to the same benchmark.
    You can filter these data owners using `allowed_emails`.
    The Private model must have already been associated with the
    benchmark for this to take effect.
    """
    GrantAccess.run(
        benchmark_id=benchmark_id,
        model_id=model_id,
        approved=approval,
        allowed_emails=allowed_emails,
    )
    config.ui.print("✅ Done!")


@app.command("auto_grant_access")
@clean_except
def auto_grant_access(
    model_id: int = typer.Option(
        ...,
        "-m",
        "--model-id",
        "--model_id",
        help="Private model for which access will be granted.",
    ),
    benchmark_id: int = typer.Option(
        ...,
        "-b",
        "--benchmark-id",
        "--benchmark_id",
        help="Benchmark UID to which the Private model is associated. "
        "All data owners registered to this benchmark and have "
        "a valid certificate will be granted access to the model.",
    ),
    interval: int = typer.Option(
        5,
        "-i",
        "--interval",
        min=5,
        max=60,
        help="Time in minutes to check for updates. Minimum 5 minutes, maximum 60 minutes "
        "(an hour). Defaults to 5 minutes if not provided.",
    ),
    allowed_emails: str = typer.Option(
        None,
        "-a",
        "--allowed_emails",
        help="Space-separated list of emails",
    ),
):
    """
    This command will run the 'grant_access' command every 5 minutes indefinetely.
    To stop this command, press CTRL+C. The time interval for checking for new data
    owners may be customized by using the -i flag.
    Allows all currently registered Data Owners in a given benchmark to access
    a Private model registered to the same benchmark.
    You can filter these data owners using `allowed_emails`.
    The private model must have already been associated with the
    benchmark for this to take effect.
    """
    interval_in_seconds = interval * 60
    while True:
        try:
            GrantAccess.run(
                benchmark_id=benchmark_id,
                model_id=model_id,
                approved=True,
                allowed_emails=allowed_emails,
            )
        except CleanExit as e:
            config.ui.print(str(e))
        except KeyboardInterrupt:
            config.ui.print("✅ Stopping at request of the user.")
            raise
        config.ui.print(f"Will check again in {interval} minutes...")
        time.sleep(interval_in_seconds)


@app.command("revoke_user_access")
@clean_except
def revoke_user_access(
    key_id: int = typer.Option(
        ...,
        "-k",
        "--key-id",
        "--key_id",
        help="Key ID to delete.",
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """
    Revokes access to the container for a user by deleting the user's key.
    """
    RevokeUserAccess.run(key_id, approved=approval)
    config.ui.print("✅ Done!")


@app.command("delete_keys")
@clean_except
def delete_keys(
    model_id: int = typer.Option(
        ...,
        "-m",
        "--model-id",
        "--model_id",
        help="Model ID to delete all its keys.",
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
):
    """
    Revokes access to the container by deleting all its encrypted keys on the server.
    """
    DeleteKeys.run(model_id, approved=approval)
    config.ui.print("✅ Done!")


@app.command("check_access")
@clean_except
def check_access(
    model_id: int = typer.Option(
        ...,
        "-m",
        "--model-id",
        "--model_id",
        help="Model ID to check if you have access to.",
    )
):
    """
    Check if you have access to a container.
    """
    CheckAccess.run(model_id)
