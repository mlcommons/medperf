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
from medperf.commands.mlcube.run import run_mlcube

app = typer.Typer()


@app.command("run")
@clean_except
def run(
    mlcube_path: str = typer.Option(
        ..., "--mlcube", "-m", help="path to mlcube folder"
    ),
    task: str = typer.Option(..., "--task", "-t", help="mlcube task to run"),
    out_logs: str = typer.Option(
        None, "--output-logs", "-o", help="where to store stdout"
    ),
    port: str = typer.Option(None, "--port", "-P", help="port to expose"),
    env: str = typer.Option(
        "", "--env", "-e", help="comma separated list of key=value pairs"
    ),
    params: str = typer.Option(
        "", "--params", "-p", help="comma separated list of key=value pairs"
    ),
):
    """List mlcubes stored locally and remotely from the user"""
    params = dict([p.split("=") for p in params.strip().strip(",").split(",") if p])
    env = dict([p.split("=") for p in env.strip().strip(",").split(",") if p])
    run_mlcube(mlcube_path, task, out_logs, params, port, env)


@app.command("ls")
@clean_except
def list(
    unregistered: bool = typer.Option(
        False, "--unregistered", help="Get unregistered mlcubes"
    ),
    mine: bool = typer.Option(False, "--mine", help="Get current-user mlcubes"),
):
    """List mlcubes"""
    EntityList.run(
        Cube,
        fields=["UID", "Name", "State", "Registered"],
        unregistered=unregistered,
        mine_only=mine,
    )


@app.command("create")
@clean_except
def create(
    template: str = typer.Argument(
        ...,
        help=f"MLCube template name. Available templates: [{' | '.join(config.templates.keys())}]",
    ),
    output_path: str = typer.Option(
        ".", "--output", "-o", help="Save the generated MLCube to the specified path"
    ),
    config_file: str = typer.Option(
        None,
        "--config-file",
        "-c",
        help="JSON Configuration file. If not present then user is prompted for configuration",
    ),
):
    """Creates an MLCube based on one of the specified templates"""
    CreateCube.run(template, output_path, config_file)


@app.command("submit")
@clean_except
def submit(
    name: str = typer.Option(..., "--name", "-n", help="Name of the mlcube"),
    mlcube_file: str = typer.Option(
        ...,
        "--mlcube-file",
        "-m",
        help="Identifier to download the mlcube file. See the description above",
    ),
    mlcube_hash: str = typer.Option("", "--mlcube-hash", help="hash of mlcube file"),
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
    image_file: str = typer.Option(
        "",
        "--image-file",
        "-i",
        help="Identifier to download the image file. See the description above",
    ),
    image_hash: str = typer.Option("", "--image-hash", help="hash of image file"),
    operational: bool = typer.Option(
        False,
        "--operational",
        help="Submit the MLCube as OPERATIONAL",
    ),
):
    """Submits a new cube to the platform.\n
    The following assets:\n
        - mlcube_file\n
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
        "image_tarball_url": image_file,
        "image_tarball_hash": image_hash,
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
    """Associates an MLCube to a benchmark"""
    AssociateCube.run(model_uid, benchmark_uid, approved=approval, no_cache=no_cache)
    config.ui.print("✅ Done!")


@app.command("view")
@clean_except
def view(
    entity_id: Optional[int] = typer.Argument(None, help="MLCube ID"),
    format: str = typer.Option(
        "yaml",
        "-f",
        "--format",
        help="Format to display contents. Available formats: [yaml, json]",
    ),
    unregistered: bool = typer.Option(
        False,
        "--unregistered",
        help="Display unregistered mlcubes if mlcube ID is not provided",
    ),
    mine: bool = typer.Option(
        False,
        "--mine",
        help="Display current-user mlcubes if mlcube ID is not provided",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file to store contents. If not provided, the output will be displayed",
    ),
):
    """Displays the information of one or more mlcubes"""
    EntityView.run(entity_id, Cube, format, unregistered, mine, output)
