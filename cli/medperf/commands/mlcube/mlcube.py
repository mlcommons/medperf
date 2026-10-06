import typer
import time
from typing import Optional
import medperf.config as config
from medperf.decorators import clean_except
from medperf.entities.cube import Cube
from medperf.commands.list import EntityList
from medperf.commands.view import EntityView
from medperf.commands.mlcube.create import CreateCube
from medperf.commands.mlcube.submit import SubmitCube
from medperf.commands.mlcube.run_test import run_mlcube
from medperf.commands.mlcube.grant_access import GrantAccess
from medperf.commands.mlcube.revoke_user_access import RevokeUserAccess
from medperf.commands.mlcube.delete_keys import DeleteKeys
from medperf.commands.mlcube.check_access import CheckAccess
from medperf.exceptions import CleanExit
import medperf.help_texts as help_texts

app = typer.Typer()


@app.command("run_test")
@clean_except
def run_test(
    mlcube_path: str = typer.Option(
        ..., "--container", "-m", help=help_texts.Container.run_test_config
    ),
    task: str = typer.Option(
        ..., "--task", "-t", help=help_texts.Container.run_test_task
    ),
    parameters_file_path: str = typer.Option(
        None,
        "--parameters_file_path",
        help=help_texts.Container.run_test_parameters_file,
    ),
    additional_files_path: str = typer.Option(
        None,
        "--additional_files_path",
        help=help_texts.Container.run_test_additional_files,
    ),
    output_logs: str = typer.Option(
        None, "--output_logs", "-o", help=help_texts.Container.run_test_output_logs
    ),
    timeout: int = typer.Option(
        None, "--timeout", help=help_texts.Container.run_test_timeout
    ),
    mounts: str = typer.Option(
        "", "--mounts", "-m", help=help_texts.Container.run_test_mounts
    ),
    env: str = typer.Option("", "--env", "-e", help=help_texts.Container.run_test_env),
    ports: str = typer.Option(
        "", "--ports", "-P", help=help_texts.Container.run_test_ports
    ),
    allow_network: bool = typer.Option(
        False, "--allow_network", help=help_texts.Container.run_test_allow_network
    ),
    download: int = typer.Option(
        False, "--download", help=help_texts.Container.run_test_download
    ),
):
    """Runs a container for testing only (developers)"""
    mounts = dict([p.split("=") for p in mounts.strip().strip(",").split(",") if p])
    env = dict([p.split("=") for p in env.strip().strip(",").split(",") if p])
    ports = [p for p in ports.split(",") if p]
    run_mlcube(
        mlcube_path,
        task,
        parameters_file_path,
        additional_files_path,
        output_logs,
        timeout,
        mounts,
        env,
        ports,
        not allow_network,
        download,
    )


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help=help_texts.Container.ls_unregistered
    ),
    mine: bool = typer.Option(False, "--mine", help=help_texts.Container.ls_mine),
    name: str = typer.Option(
        None, "--name", "-n", help=help_texts.Container.name_filter
    ),
    owner: int = typer.Option(None, "--owner", help=help_texts.Common.owner_filter),
    state: str = typer.Option(None, "--state", help=help_texts.Common.state_filter),
    is_active: bool = typer.Option(
        None, "--active/--inactive", help=help_texts.Common.active_filter
    ),
):
    """List containers"""
    EntityList.run(
        Cube,
        fields=["UID", "Name", "State", "Registered"],
        unregistered=unregistered,
        mine_only=mine,
        name=name,
        owner=owner,
        state=state,
        is_active=is_active,
    )


@app.command("create")
@clean_except
def create(
    template: str = typer.Argument(
        ...,
        help=help_texts.Container.template,
    ),
    image_name: str = typer.Option(
        ...,
        "--image",
        "-i",
        help=help_texts.Container.image_name,
    ),
    folder_name: str = typer.Option(
        ...,
        "--folder_name",
        "-f",
        help=help_texts.Container.folder_name,
    ),
    output_path: str = typer.Option(
        ".", "--output", "-o", help=help_texts.Container.output_path
    ),
):
    """Creates a container files template"""
    CreateCube.run(template, image_name, folder_name, output_path)


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help=help_texts.Container.name),
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
        help=help_texts.Container.additional_file_cli,
    ),
    additional_hash: str = typer.Option(
        "", "--additional-hash", help=help_texts.Container.additional_hash
    ),
    image_hash: str = typer.Option(
        "", "--image-hash", help=help_texts.Container.image_hash
    ),
    operational: bool = typer.Option(
        False,
        "--operational",
        help=help_texts.Container.operational,
    ),
    decryption_key: Optional[str] = typer.Option(
        None,
        "--decryption-key",
        "--decryption_key",
        "-d",
        help=help_texts.Container.decryption_key,
    ),
):
    """Submits a new container to the platform.\n
    The additional files is expected to be given in the following format: <source_prefix:resource_identifier>
    where `source_prefix` instructs the client how to download the resource, and `resource_identifier`
    is the identifier used to download the asset. The following are supported:\n
    1. A direct link: "direct:<URL>"\n
    2. An asset hosted on the Synapse platform: "synapse:<synapse ID>"\n\n

    If a URL is given without a source prefix, it will be treated as a direct download link.

    For private (encrypted) containers, the decryption key
    should be provided. Otherwise, the container will not work on the data owners' side.
    """
    mlcube_info = {
        "name": name,
        "image_hash": image_hash,
        "additional_files_tarball_url": additional_file,
        "additional_files_tarball_hash": additional_hash,
        "state": "OPERATION" if operational else "DEVELOPMENT",
    }
    SubmitCube.run(
        mlcube_info,
        container_config=container_config_file,
        parameters_config=parameters_file,
        decryption_key=decryption_key,
    )
    config.ui.print("✅ Done!")


@app.command("view")
@clean_except
def view(
    entity_id: Optional[int] = typer.Argument(None, help=help_texts.Container.id),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help=help_texts.Common.format,
    ),
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help=help_texts.Container.view_unregistered,
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help=help_texts.Container.view_mine,
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help=help_texts.Common.output,
    ),
):
    """Displays the information of one or more containers"""
    EntityView.run(entity_id, Cube, format, unregistered, mine, output)


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
    Revokes access to the container for a user by deleting the user's key.
    """
    RevokeUserAccess.run(key_id, approved=approval)
    config.ui.print("✅ Done!")


@app.command("delete_keys")
@clean_except
def delete_keys(
    container_id: int = typer.Option(
        ...,
        "-c",
        "--container-id",
        "--container_id",
        help=help_texts.Container.delete_keys_id,
    ),
    approval: bool = typer.Option(False, "-y", help=help_texts.Common.approval),
):
    """
    Revokes access to the container by deleting all its encrypted keys on the server.
    """
    DeleteKeys.run(container_id, approved=approval)
    config.ui.print("✅ Done!")


@app.command("check_access")
@clean_except
def check_access(
    container_id: int = typer.Option(
        ...,
        "-c",
        "--container-id",
        "--container_id",
        help=help_texts.Container.check_access_id,
    )
):
    """
    Check if you have access to a container.
    """
    CheckAccess.run(container_id)
