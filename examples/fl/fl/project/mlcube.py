"""MLCube handler file"""

import os
import shutil
import typer
from collaborator import start_collaborator
from aggregator import start_aggregator
from hooks import (
    aggregator_pre_training_hook,
    aggregator_post_training_hook,
    collaborator_pre_training_hook,
    collaborator_post_training_hook,
)

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
    parameters_file: str = typer.Option(..., "--parameters_file"),
    node_cert_folder: str = typer.Option(..., "--node_cert_folder"),
    ca_cert_folder: str = typer.Option(..., "--ca_cert_folder"),
    network_config: str = typer.Option(..., "--network_config"),
    output_logs: str = typer.Option(..., "--output_logs"),
):
    _setup(output_logs)
    collaborator_pre_training_hook(
        data_path=data_path,
        labels_path=labels_path,
        parameters_file=parameters_file,
        node_cert_folder=node_cert_folder,
        ca_cert_folder=ca_cert_folder,
        network_config=network_config,
        output_logs=output_logs,
    )
    start_collaborator(
        data_path=data_path,
        labels_path=labels_path,
        parameters_file=parameters_file,
        node_cert_folder=node_cert_folder,
        ca_cert_folder=ca_cert_folder,
        network_config=network_config,
        output_logs=output_logs,
    )
    collaborator_post_training_hook(
        data_path=data_path,
        labels_path=labels_path,
        parameters_file=parameters_file,
        node_cert_folder=node_cert_folder,
        ca_cert_folder=ca_cert_folder,
        network_config=network_config,
        output_logs=output_logs,
    )
    _teardown(output_logs)


@app.command("start_aggregator")
def start_aggregator_(
    input_weights: str = typer.Option(..., "--input_weights"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    node_cert_folder: str = typer.Option(..., "--node_cert_folder"),
    ca_cert_folder: str = typer.Option(..., "--ca_cert_folder"),
    output_logs: str = typer.Option(..., "--output_logs"),
    output_weights: str = typer.Option(..., "--output_weights"),
    network_config: str = typer.Option(..., "--network_config"),
    collaborators: str = typer.Option(..., "--collaborators"),
):
    _setup(output_logs)
    aggregator_pre_training_hook(
        input_weights=input_weights,
        parameters_file=parameters_file,
        node_cert_folder=node_cert_folder,
        ca_cert_folder=ca_cert_folder,
        output_logs=output_logs,
        output_weights=output_weights,
        network_config=network_config,
        collaborators=collaborators,
    )
    start_aggregator(
        input_weights=input_weights,
        parameters_file=parameters_file,
        node_cert_folder=node_cert_folder,
        ca_cert_folder=ca_cert_folder,
        output_logs=output_logs,
        output_weights=output_weights,
        network_config=network_config,
        collaborators=collaborators,
    )
    aggregator_post_training_hook(
        input_weights=input_weights,
        parameters_file=parameters_file,
        node_cert_folder=node_cert_folder,
        ca_cert_folder=ca_cert_folder,
        output_logs=output_logs,
        output_weights=output_weights,
        network_config=network_config,
        collaborators=collaborators,
    )
    _teardown(output_logs)


if __name__ == "__main__":
    app()
