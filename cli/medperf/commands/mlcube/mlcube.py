import typer
from typing import Optional

import medperf.config as config
from medperf.decorators import clean_except
from medperf.entities.cube import Cube
from medperf.commands.list import EntityList
from medperf.commands.view import EntityView
from medperf.commands.edit import EntityEdit
from medperf.commands.mlcube.create import CreateCube
from medperf.commands.mlcube.submit import SubmitCube
from medperf.commands.mlcube.associate import AssociateCube

app = typer.Typer()

NAME_HELP = "Name of the mlcube"
MLCUBE_HELP = "Identifier to download the mlcube file. See the description above"
MLCUBE_HASH_HELP = "SHA1 of mlcube file"
PARAMS_HELP = "Identifier to download the parameters file. See the description above"
PARAMS_HASH_HELP = "SHA1 of parameters file"
ADD_HELP = (
    "Identifier to download the additional files tarball. See the description above"
)
ADD_HASH_HELP = "SHA1 of additional file"
IMG_HELP = "Identifier to download the image file. See the description above"
IMG_HASH_HELP = "SHA1 of image file"


@app.command("ls")
@clean_except
def list(
    local: bool = typer.Option(False, "--local", help="Get local mlcubes"),
    mine: bool = typer.Option(False, "--mine", help="Get current-user mlcubes"),
):
    """List mlcubes stored locally and remotely from the user"""
    EntityList.run(
        Cube,
        fields=["UID", "Name", "State", "Registered"],
        local_only=local,
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
    name: str = typer.Option(..., "--name", "-n", help=NAME_HELP),
    mlcube_file: str = typer.Option(
        ...,
        "--mlcube-file",
        "-m",
        help=MLCUBE_HELP,
    ),
    mlcube_hash: str = typer.Option("", "--mlcube-hash", help=MLCUBE_HASH_HELP),
    parameters_file: str = typer.Option(
        "",
        "--parameters-file",
        "-p",
        help=PARAMS_HELP,
    ),
    parameters_hash: str = typer.Option("", "--parameters-hash", help=PARAMS_HASH_HELP),
    additional_file: str = typer.Option(
        "",
        "--additional-file",
        "-a",
        help=ADD_HELP,
    ),
    additional_hash: str = typer.Option("", "--additional-hash", help=ADD_HASH_HELP),
    image_file: str = typer.Option(
        "",
        "--image-file",
        "-i",
        help=IMG_HELP,
    ),
    image_hash: str = typer.Option("", "--image-hash", help=IMG_HASH_HELP),
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
    }
    SubmitCube.run(mlcube_info)
    config.ui.print("✅ Done!")


@app.command("edit")
@clean_except
def edit(
    entity_id: int = typer.Argument(..., help="Dataset ID"),
    name: str = typer.Option(None, "--name", "-n", help=NAME_HELP),
    mlcube_file: str = typer.Option(
        None,
        "--mlcube-file",
        "-m",
        help=MLCUBE_HELP,
    ),
    mlcube_hash: str = typer.Option(None, "--mlcube-hash", help=MLCUBE_HASH_HELP),
    parameters_file: str = typer.Option(
        None,
        "--parameters-file",
        "-p",
        help=PARAMS_HELP,
    ),
    parameters_hash: str = typer.Option(
        None, "--parameters-hash", help=PARAMS_HASH_HELP
    ),
    additional_file: str = typer.Option(
        None,
        "--additional-file",
        "-a",
        help=ADD_HELP,
    ),
    additional_hash: str = typer.Option(None, "--additional-hash", help=ADD_HASH_HELP),
    image_file: str = typer.Option(
        None,
        "--image-file",
        "-i",
        help=IMG_HELP,
    ),
    image_hash: str = typer.Option(None, "--image-hash", help=IMG_HASH_HELP),
    is_valid: bool = typer.Option(
        None,
        "--valid/--invalid",
        help="Flags an MLCube valid/invalid. Invalid MLCubes can't be used for experiments",
    ),
):
    """Edits an MLCube"""
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
        "is_valid": is_valid,
    }
    EntityEdit.run(Cube, entity_id, mlcube_info)
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
    local: bool = typer.Option(
        False, "--local", help="Display local mlcubes if mlcube ID is not provided"
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
    EntityView.run(entity_id, Cube, format, local, mine, output)
