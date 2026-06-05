"""MLCube handler file"""

import typer

app = typer.Typer()


@app.command("get_experiment_status")
def get_experiment_status_(
    node_cert_folder: str = typer.Option(
        "/mlcommons/volumes/node_cert_folder", "--node_cert_folder"
    ),
    ca_cert_folder: str = typer.Option(
        "/mlcommons/volumes/ca_cert_folder", "--ca_cert_folder"
    ),
    plan_path: str = typer.Option("/mlcommons/volumes/plan/plan.yaml", "--plan_path"),
    output_status_file: str = typer.Option(
        "/mlcommons/volumes/status/status.yaml", "--output_status_file"
    ),
):
    raise NotImplementedError(
        "Getting experiment status is not implemented for Flower containers"
    )


@app.command("update_plan")
def update_plan_(
    node_cert_folder: str = typer.Option(
        "/mlcommons/volumes/node_cert_folder", "--node_cert_folder"
    ),
    ca_cert_folder: str = typer.Option(
        "/mlcommons/volumes/ca_cert_folder", "--ca_cert_folder"
    ),
    plan_path: str = typer.Option("/mlcommons/volumes/plan/plan.yaml", "--plan_path"),
    temp_dir: str = typer.Option("/tmp", "--temp_dir"),
):
    raise NotImplementedError(
        "Updating FL plan is not implemented for Flower containers"
    )


if __name__ == "__main__":
    app()
