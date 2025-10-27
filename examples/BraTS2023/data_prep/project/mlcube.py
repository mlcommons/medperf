"""MLCube handler file"""

import typer
import yaml
from prepare import prepare_dataset
from sanity_check import perform_sanity_checks
from stats import generate_statistics

app = typer.Typer()


@app.command("prepare")
def prepare(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
    output_labels_path: str = typer.Option(..., "--output_labels_path"),
):
    with open(parameters_file) as f:
        parameters = yaml.safe_load(f)

    prepare_dataset(data_path, labels_path, parameters, output_path, output_labels_path)


@app.command("sanity_check")
def sanity_check(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
):
    with open(parameters_file) as f:
        parameters = yaml.safe_load(f)

    perform_sanity_checks(data_path, labels_path, parameters)


@app.command("statistics")
def statistics(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    out_path: str = typer.Option(..., "--output_path"),
):
    with open(parameters_file) as f:
        parameters = yaml.safe_load(f)

    generate_statistics(data_path, labels_path, parameters, out_path)


if __name__ == "__main__":
    app()
