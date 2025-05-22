"""MLCube handler file"""

import os
import shutil
import typer
from utils import setup_ws
from admin import (
    get_experiment_status,
    add_collaborator,
    remove_collaborator,
    update_plan,
)

app = typer.Typer()


def _setup(temp_dir):
    tmp_folder = os.path.join(temp_dir, ".tmp")
    os.makedirs(tmp_folder, exist_ok=True)
    # TODO: this should be set before any code imports tempfile
    os.environ["TMPDIR"] = tmp_folder
    os.environ["GRPC_VERBOSITY"] = "ERROR"


def _teardown(temp_dir):
    tmp_folder = os.path.join(temp_dir, ".tmp")
    shutil.rmtree(tmp_folder, ignore_errors=True)


@app.command("get_experiment_status")
def get_experiment_status_(
    node_cert_folder: str = typer.Option(..., "--node_cert_folder"),
    ca_cert_folder: str = typer.Option(..., "--ca_cert_folder"),
    plan_path: str = typer.Option(..., "--plan_path"),
    output_status_file: str = typer.Option(..., "--output_status_file"),
    temp_dir: str = typer.Option(..., "--temp_dir"),
):
    _setup(temp_dir)
    workspace_folder, admin_cn = setup_ws(
        node_cert_folder, ca_cert_folder, plan_path, temp_dir
    )
    get_experiment_status(workspace_folder, admin_cn, output_status_file)
    _teardown(temp_dir)


@app.command("add_collaborator")
def add_collaborator_(
    node_cert_folder: str = typer.Option(..., "--node_cert_folder"),
    ca_cert_folder: str = typer.Option(..., "--ca_cert_folder"),
    plan_path: str = typer.Option(..., "--plan_path"),
    temp_dir: str = typer.Option(..., "--temp_dir"),
):
    _setup(temp_dir)
    workspace_folder, admin_cn = setup_ws(
        node_cert_folder, ca_cert_folder, plan_path, temp_dir
    )
    add_collaborator(workspace_folder, admin_cn)
    _teardown(temp_dir)


@app.command("remove_collaborator")
def remove_collaborator_(
    node_cert_folder: str = typer.Option(..., "--node_cert_folder"),
    ca_cert_folder: str = typer.Option(..., "--ca_cert_folder"),
    plan_path: str = typer.Option(..., "--plan_path"),
    temp_dir: str = typer.Option(..., "--temp_dir"),
):
    _setup(temp_dir)
    workspace_folder, admin_cn = setup_ws(
        node_cert_folder, ca_cert_folder, plan_path, temp_dir
    )
    remove_collaborator(workspace_folder, admin_cn)
    _teardown(temp_dir)


@app.command("update_plan")
def update_plan_(
    node_cert_folder: str = typer.Option(..., "--node_cert_folder"),
    ca_cert_folder: str = typer.Option(..., "--ca_cert_folder"),
    plan_path: str = typer.Option(..., "--plan_path"),
    temp_dir: str = typer.Option(..., "--temp_dir"),
):
    _setup(temp_dir)
    workspace_folder, admin_cn = setup_ws(
        node_cert_folder, ca_cert_folder, plan_path, temp_dir
    )
    update_plan(workspace_folder, admin_cn)
    _teardown(temp_dir)


if __name__ == "__main__":
    app()
