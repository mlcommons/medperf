"""MLCube handler file"""

import os
import shutil
import typer
from collaborator import start_collaborator
from aggregator import start_aggregator
from plan import generate_plan
from hooks import (
    aggregator_pre_training_hook,
    aggregator_post_training_hook,
    collaborator_pre_training_hook,
    collaborator_post_training_hook,
)
from init_model import train_initial_model

app = typer.Typer()


def _setup(output_logs):
    tmp_folder = os.path.join(output_logs, ".tmp")
    os.makedirs(tmp_folder, exist_ok=True)
    # TODO: this should be set before any code imports tempfile
    os.environ["TMPDIR"] = tmp_folder


def _teardown(output_logs):
    tmp_folder = os.path.join(output_logs, ".tmp")
    shutil.rmtree(tmp_folder, ignore_errors=True)


@app.command("train")
def train(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    node_cert_folder: str = typer.Option(..., "--node_cert_folder"),
    ca_cert_folder: str = typer.Option(..., "--ca_cert_folder"),
    plan_path: str = typer.Option(..., "--plan_path"),
    output_logs: str = typer.Option(..., "--output_logs"),
    init_nnunet_directory: str = typer.Option(..., "--init_nnunet_directory"),
):
    _setup(output_logs)
    collaborator_pre_training_hook(
        data_path=data_path,
        labels_path=labels_path,
        node_cert_folder=node_cert_folder,
        ca_cert_folder=ca_cert_folder,
        plan_path=plan_path,
        output_logs=output_logs,
        init_nnunet_directory=init_nnunet_directory,
    )
    
    start_collaborator(
        data_path=data_path,
        labels_path=labels_path,
        node_cert_folder=node_cert_folder,
        ca_cert_folder=ca_cert_folder,
        plan_path=plan_path,
        output_logs=output_logs,
    )
    collaborator_post_training_hook(
        data_path=data_path,
        labels_path=labels_path,
        node_cert_folder=node_cert_folder,
        ca_cert_folder=ca_cert_folder,
        plan_path=plan_path,
        output_logs=output_logs,
    )
    
    _teardown(output_logs)


@app.command("start_aggregator")
def start_aggregator_(
    input_weights: str = typer.Option(..., "--input_weights"),
    node_cert_folder: str = typer.Option(..., "--node_cert_folder"),
    ca_cert_folder: str = typer.Option(..., "--ca_cert_folder"),
    output_logs: str = typer.Option(..., "--output_logs"),
    output_weights: str = typer.Option(..., "--output_weights"),
    plan_path: str = typer.Option(..., "--plan_path"),
    collaborators: str = typer.Option(..., "--collaborators"),
    report_path: str = typer.Option(..., "--report_path"),
):
    _setup(output_logs)
    aggregator_pre_training_hook(
        input_weights=input_weights,
        node_cert_folder=node_cert_folder,
        ca_cert_folder=ca_cert_folder,
        output_logs=output_logs,
        output_weights=output_weights,
        plan_path=plan_path,
        collaborators=collaborators,
        report_path=report_path,
    )
    start_aggregator(
        input_weights=input_weights,
        node_cert_folder=node_cert_folder,
        ca_cert_folder=ca_cert_folder,
        output_logs=output_logs,
        output_weights=output_weights,
        plan_path=plan_path,
        collaborators=collaborators,
        report_path=report_path,
    )
    aggregator_post_training_hook(
        input_weights=input_weights,
        node_cert_folder=node_cert_folder,
        ca_cert_folder=ca_cert_folder,
        output_logs=output_logs,
        output_weights=output_weights,
        plan_path=plan_path,
        collaborators=collaborators,
        report_path=report_path,
    )
    _teardown(output_logs)


@app.command("generate_plan")
def generate_plan_(
    training_config_path: str = typer.Option(..., "--training_config_path"),
    aggregator_config_path: str = typer.Option(..., "--aggregator_config_path"),
    plan_path: str = typer.Option(..., "--plan_path"),
):
    # no _setup here since there is no writable output mounted volume.
    # later if need this we think of a solution. Currently the create_plam
    # logic is assumed to not write within the container.
    generate_plan(training_config_path, aggregator_config_path, plan_path)


@app.command("train_initial_model")
def train_initial_model_(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    output_logs: str = typer.Option(..., "--output_logs"),
    init_nnunet_directory: str = typer.Option(..., "--init_nnunet_directory"),
):
    _setup(output_logs)
    train_initial_model(
        data_path=data_path,
        labels_path=labels_path,
        output_logs=output_logs,
        init_nnunet_directory=init_nnunet_directory,
    )
    _teardown(output_logs)


if __name__ == "__main__":
    app()
