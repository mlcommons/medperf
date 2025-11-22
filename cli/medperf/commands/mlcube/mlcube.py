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
from medperf.commands.mlcube.associate import AssociateCube
from medperf.commands.mlcube.run_test import run_mlcube
from medperf.commands.mlcube.grant_access import GrantAccess
from medperf.commands.mlcube.revoke_user_access import RevokeUserAccess
from medperf.commands.mlcube.delete_keys import DeleteKeys
from medperf.commands.mlcube.check_access import CheckAccess
from medperf.exceptions import CleanExit

app = typer.Typer()


@app.command("run_test")
@clean_except
def run_test(
    mlcube_path: str = typer.Option(
        ..., "--container", "-m", help="path to container config"
    ),
    task: str = typer.Option(..., "--task", "-t", help="container task to run"),
    parameters_file_path: str = typer.Option(
        None, "--parameters_file_path", help="path to container parameters file"
    ),
    additional_files_path: str = typer.Option(
        None, "--additional_files_path", help="path to ciontainer additional files"
    ),
    output_logs: str = typer.Option(
        None, "--output_logs", "-o", help="where to store stdout"
    ),
    timeout: int = typer.Option(
        None, "--timeout", help="comma separated list of key=value pairs"
    ),
    mounts: str = typer.Option(
        "", "--mounts", "-m", help="comma separated list of key=value pairs"
    ),
    env: str = typer.Option(
        "", "--env", "-e", help="comma separated list of key=value pairs"
    ),
    ports: str = typer.Option(
        "", "--ports", "-P", help="comma separated list of ports to expose"
    ),
    allow_network: bool = typer.Option(
        False, "--allow_network", help="comma separated list of key=value pairs"
    ),
    download: int = typer.Option(
        False, "--download", help="whether to pull docker image"
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
        False, "--unregistered", help="Get unregistered containers"
    ),
    mine: bool = typer.Option(False, "--mine", help="Get current-user containers"),
    name: str = typer.Option(None, "--name", "-n", help="Filter out by container Name"),
    owner: int = typer.Option(None, "--owner", help="Filter by owner ID"),
    state: str = typer.Option(
        None, "--state", help="Filter by state (DEVELOPMENT/OPERATION)"
    ),
    is_active: bool = typer.Option(
        None, "--active/--inactive", help="Filter by active status"
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
        help=f"Container type. Available types: [{' | '.join(config.templates.keys())}]",
    ),
    image_name: str = typer.Option(
        ...,
        "--image",
        "-i",
        help="Image name",
    ),
    folder_name: str = typer.Option(
        ...,
        "--folder_name",
        "-f",
        help="Folder name of the container files template to be created",
    ),
    output_path: str = typer.Option(
        ".", "--output", "-o", help="Save the generated template to the specified path"
    ),
):
    """Creates a container files template"""
    CreateCube.run(template, image_name, folder_name, output_path)


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help="Name of the container"),
    container_config_file: str = typer.Option(
        ...,
        "--container-config-file",
        "-m",
        help="Container Config file. Preferably a local file in your computer. "
        "May optionally be a remote file. See the description above. "
        "Its contents will be uploaded to the MedPerf server.",
    ),
    parameters_file: str = typer.Option(
        "",
        "--parameters-file",
        "-p",
        help="Local parameters file. Preferably a local file in your computer. "
        "May optionally be a remote file. See the description above. "
        "Its contents will be uploaded to the MedPerf server.",
    ),
    additional_file: str = typer.Option(
        "",
        "--additional-file",
        "-a",
        help="Identifier to download the additional files tarball. See the description above",
    ),
    additional_hash: str = typer.Option(
        "", "--additional-hash", help="hash of additional file"
    ),
    image_hash: str = typer.Option("", "--image-hash", help="hash of image file"),
    operational: bool = typer.Option(
        False,
        "--operational",
        help="Submit the container as OPERATIONAL",
    ),
    decryption_key: Optional[str] = typer.Option(
        None,
        "--decryption-key",
        "--decryption_key",
        "-d",
        help="Path to the decryption key file for the encrypted container. The key "
        "will stay local. This should only be provided for encrypted container submissions.",
    ),
):
    """Submits a new container to the platform.\n
    The following assets:\n
        - additional_file\n
        - image_file\n
    are expected to be given in the following format: <source_prefix:resource_identifier>
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
    AssociateCube.run(model_uid, benchmark_uid, approved=approval, no_cache=no_cache)
    config.ui.print("✅ Done!")


@app.command("view")
@clean_except
def view(
    entity_id: Optional[int] = typer.Argument(None, help="Container ID"),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help="Format to display contents. Available formats: [yaml, json]",
    ),
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help="Display unregistered containers if container ID is not provided",
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help="Display current-user containers if container ID is not provided",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file to store contents. If not provided, the output will be displayed",
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
    container_id: int = typer.Option(
        ...,
        "-c",
        "--container-id",
        "--container_id",
        help="Container ID to delete all its keys.",
    ),
    approval: bool = typer.Option(False, "-y", help="Skip approval step"),
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
        help="Container ID to check if you have access to.",
    )
):
    """
    Check if you have access to a container.
    """
    CheckAccess.run(container_id)
