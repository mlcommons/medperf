"""MLCube handler  file"""

import typer
from prepare import prepare_dataset
from sanity_check import perform_sanity_checks
from stats import generate_statistics

app = typer.Typer()


@app.command("prepare")
def prepare(
    data_path: str = typer.Option("/mlcommon/volumes/raw_data", "--data_path"),
    labels_path: str = typer.Option("/mlcommon/volumes/raw_labels", "--labels_path"),
    output_path: str = typer.Option("/mlcommon/volumes/data", "--output_path"),
    output_labels_path: str = typer.Option(
        "/mlcommon/volumes/labels", "--output_labels_path"
    ),
):
    prepare_dataset(data_path, labels_path, output_path, output_labels_path)


@app.command("sanity_check")
def sanity_check(
    data_path: str = typer.Option("/mlcommon/volumes/data", "--data_path"),
    labels_path: str = typer.Option("/mlcommon/volumes/labels", "--labels_path"),
):
    perform_sanity_checks(data_path, labels_path)


@app.command("statistics")
def statistics(
    data_path: str = typer.Option("/mlcommon/volumes/data", "--data_path"),
    labels_path: str = typer.Option("/mlcommon/volumes/labels", "--labels_path"),
    out_path: str = typer.Option(
        "/mlcommon/volumes/statistics/statistics.yaml", "--output_path"
    ),
):
    generate_statistics(data_path, labels_path, out_path)


if __name__ == "__main__":
    app()
