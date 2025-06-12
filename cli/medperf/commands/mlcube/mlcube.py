import typer
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
    """Runs a container for testing only"""
    mounts = dict([p.split("=") for p in mounts.strip().strip(",").split(",") if p])
    env = dict([p.split("=") for p in env.strip().strip(",").split(",") if p])
    ports = ports.split(",")
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
    mlcube_file: str = typer.Option(
        ...,
        "--container-config-file",
        "-m",
        help="Identifier to download the container config file. See the description above",
    ),
    mlcube_hash: str = typer.Option(
        "", "--container-config-hash", help="hash of container config file"
    ),
    parameters_file: str = typer.Option(
        "",
        "--parameters-file",
        "-p",
        help="Identifier to download the parameters file. See the description above",
    ),
    parameters_hash: str = typer.Option(
        "", "--parameters-hash", help="hash of parameters file"
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
):
    """Submits a new container to the platform.\n
    The following assets:\n
        - container config file\n
        - parameters_file\n
        - additional_file\n
        - image_file\n
    are expected to be given in the following format: <source_prefix:resource_identifier>
    where `source_prefix` instructs the client how to download the resource, and `resource_identifier`
    is the identifier used to download the asset. The following are supported:\n
    1. A direct link: "direct:<URL>"\n
    2. An asset hosted on the Synapse platform: "synapse:<synapse ID>"\n\n

    If a URL is given without a source prefix, it will be treated as a direct download link.
    """
    mlcube_info = {
        "name": name,
        "git_mlcube_url": mlcube_file,
        "git_mlcube_hash": mlcube_hash,
        "git_parameters_url": parameters_file,
        "parameters_hash": parameters_hash,
        "image_hash": image_hash,
        "additional_files_tarball_url": additional_file,
        "additional_files_tarball_hash": additional_hash,
        "state": "OPERATION" if operational else "DEVELOPMENT",
    }
    SubmitCube.run(mlcube_info)
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
