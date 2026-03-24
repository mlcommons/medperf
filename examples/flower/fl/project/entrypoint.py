"""MLCube handler file"""

import typer
import os

from collaborator import start_collaborator
from aggregator import start_aggregator
from plan import generate_plan
from utils import get_train_val_paths, get_server_connection, setup_job

app = typer.Typer()


@app.command("train")
def train(
    data_path: str = typer.Option("/mlcommons/volumes/data", "--data_path"),
    labels_path: str = typer.Option("/mlcommons/volumes/labels", "--labels_path"),
    node_cert_folder: str = typer.Option(
        "/mlcommons/volumes/node_cert_folder", "--node_cert_folder"
    ),
    ca_cert_folder: str = typer.Option(
        "/mlcommons/volumes/ca_cert_folder", "--ca_cert_folder"
    ),
    plan_path: str = typer.Option("/mlcommons/volumes/plan/plan.yaml", "--plan_path"),
    output_logs: str = typer.Option("/mlcommons/volumes/output_logs", "--output_logs"),
):
    train_data_path, train_labels_path, val_data_path, val_labels_path = (
        get_train_val_paths(data_path, labels_path)
    )
    address, port, _ = get_server_connection(plan_path)
    ca_cert_path = os.path.join(ca_cert_folder, "root.crt")
    start_collaborator(
        address,
        port,
        ca_cert_path,
        train_data_path,
        train_labels_path,
        val_data_path,
        val_labels_path,
    )


@app.command("start_aggregator")
def start_aggregator_(
    input_weights: str = typer.Option(
        "/mlcommons/volumes/additional_files", "--input_weights"
    ),
    node_cert_folder: str = typer.Option(
        "/mlcommons/volumes/node_cert_folder", "--node_cert_folder"
    ),
    ca_cert_folder: str = typer.Option(
        "/mlcommons/volumes/ca_cert_folder", "--ca_cert_folder"
    ),
    output_logs: str = typer.Option("/mlcommons/volumes/output_logs", "--output_logs"),
    output_weights: str = typer.Option(
        "/mlcommons/volumes/output_weights", "--output_weights"
    ),
    plan_path: str = typer.Option("/mlcommons/volumes/plan/plan.yaml", "--plan_path"),
    collaborators: str = typer.Option(
        "/mlcommons/volumes/collaborators/cols.yaml", "--collaborators"
    ),
    report_path: str = typer.Option(
        "/mlcommons/volumes/report/report.yaml", "--report_path"
    ),
):
    ca_cert_path = os.path.join(ca_cert_folder, "root.crt")
    cert_path = os.path.join(node_cert_folder, "crt.crt")
    key_path = os.path.join(node_cert_folder, "key.key")
    workspace_folder = setup_job(
        src_folder=os.environ["SRC_FOLDER"],
        plan_path=plan_path,
        ca_cert_path=ca_cert_path,
    )
    _, port, admin_port = get_server_connection(plan_path)
    start_aggregator(
        workspace_folder=workspace_folder,
        port=port,
        admin_port=admin_port,
        ca_cert_path=ca_cert_path,
        cert_path=cert_path,
        key_path=key_path,
        initial_weights=input_weights,
        output_weights=output_weights,
        report_path=report_path,
    )


@app.command("generate_plan")
def generate_plan_(
    training_config_path: str = typer.Option(
        "/mlcommons/volumes/training_config/training_config.yaml",
        "--training_config_path",
    ),
    aggregator_config_path: str = typer.Option(
        "/mlcommons/volumes/aggregator_config/aggregator_config.yaml",
        "--aggregator_config_path",
    ),
    plan_path: str = typer.Option("/mlcommons/volumes/plan/plan.yaml", "--plan_path"),
):
    generate_plan(training_config_path, aggregator_config_path, plan_path)


if __name__ == "__main__":
    app()
