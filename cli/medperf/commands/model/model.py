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
import medperf.help_texts as help_texts

app = typer.Typer()


@app.command("submit")
@clean_except
def submit(
    # Model options
    name: str = typer.Option(..., "--name", "-n", help=help_texts.Model.name),
    operational: bool = typer.Option(
        False, "--operational", help=help_texts.Model.operational
    ),
    # Container-backed model options
    container_config_file: str = typer.Option(
        ...,
        "--container-config-file",
        "-m",
        help=help_texts.Container.config_file,
    ),
    parameters_file: str = typer.Option(
        None,
        "--parameters-file",
        "-p",
        help=help_texts.Container.parameters_file,
    ),
    additional_file: str = typer.Option(
        "",
        "--additional-file",
        "-a",
        help=help_texts.Model.additional_file_cli,
    ),
    additional_hash: str = typer.Option(
        "", "--additional-hash", help=help_texts.Container.additional_hash
    ),
    image_hash: str = typer.Option(
        "", "--image-hash", help=help_texts.Container.image_hash
    ),
    decryption_key: Optional[str] = typer.Option(
        None,
        "--decryption-key",
        "--decryption_key",
        "-d",
        help=help_texts.Container.decryption_key,
    ),
    # Asset-backed model options
    asset_path: Optional[str] = typer.Option(
        None, "--asset-path", help=help_texts.Model.asset_path
    ),
    asset_url: Optional[str] = typer.Option(
        None, "--asset-url", help=help_texts.Model.asset_url
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
        False, "--unregistered", help=help_texts.Model.ls_unregistered
    ),
    mine: bool = typer.Option(False, "--mine", help=help_texts.Model.ls_mine),
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
    entity_id: Optional[int] = typer.Argument(None, help=help_texts.Model.id),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help=help_texts.Common.format,
    ),
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help=help_texts.Model.view_unregistered,
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help=help_texts.Model.view_mine,
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help=help_texts.Common.output,
    ),
):
    """Displays the information of one or more models"""
    EntityView.run(entity_id, Model, format, unregistered, mine, output)


@app.command("associate")
@clean_except
def associate(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help=help_texts.Benchmark.uid
    ),
    model_uid: int = typer.Option(..., "--model_uid", "-m", help=help_texts.Model.uid),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help=help_texts.Model.associate_no_cache,
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
        help=help_texts.Access.model_id,
    ),
    benchmark_id: int = typer.Option(
        ...,
        "-b",
        "--benchmark-id",
        "--benchmark_id",
        help=help_texts.Access.benchmark_id,
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
    allowed_emails: str = typer.Option(
        None,
        "-a",
        "--allowed_emails",
        help=help_texts.Access.allowed_emails_cli,
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
        help=help_texts.Access.model_id,
    ),
    benchmark_id: int = typer.Option(
        ...,
        "-b",
        "--benchmark-id",
        "--benchmark_id",
        help=help_texts.Access.benchmark_id,
    ),
    interval: int = typer.Option(
        5,
        "-i",
        "--interval",
        min=5,
        max=60,
        help=help_texts.Access.interval,
    ),
    allowed_emails: str = typer.Option(
        None,
        "-a",
        "--allowed_emails",
        help=help_texts.Access.allowed_emails_cli,
    ),
):
    """
    This command will run the 'grant_access' command every 5 minutes indefinitely.
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
        help=help_texts.Access.key_id,
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
):
    """
    Revokes access to the model for a user by deleting the user's key.
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
        help=help_texts.Model.delete_keys_id,
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
):
    """
    Revokes access to the model by deleting all its encrypted keys on the server.
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
        help=help_texts.Model.check_access_id,
    )
):
    """
    Check if you have access to a model.
    """
    CheckAccess.run(model_id)
