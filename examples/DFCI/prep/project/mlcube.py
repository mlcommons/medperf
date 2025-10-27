import yaml
import typer
from prepare import prepare_data
from sanity_check import check
from stats import get_stats

app = typer.Typer()


@app.command("prepare")
def prepare(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    params_file: str = typer.Option(..., "--parameters_file"),
    out_path: str = typer.Option(..., "--output_path"),
):
    """Prepare task command. This is what gets executed when we run:
    `mlcube run --task=prepare`
    Args:
        data_path (str): Location of the data to transform. Required for Medperf Data Preparation MLCubes.
        labels_path (str): Location of the labels. Required  for Medperf Data Preparation MLCubes
        params_file (str): Location of the parameters.yaml file. Required for Medperf Data Preparation MLCubes.
        out_path (str): Location to store transformed data. Required for Medperf Data Preparation MLCubes.
    """
    prepare_data(
        data_path,
        labels_path,
        params_file,
        out_path,
    )


@app.command("sanity_check")
def sanity_check(
    data_path: str = typer.Option(..., "--data_path"),
    params_file: str = typer.Option(..., "--parameters_file"),
):
    """Sanity check task command. This is what gets executed when we run:
    `mlcube run --task=sanity_check`
    Args:
        data_path (str): Location of the prepared data. Required for Medperf Data Preparation MLCubes.
        params_file (str): Location of the parameters.yaml file. Required for Medperf Data Preparation MLCubes.
    """
    check(data_path, params_file)


@app.command("statistics")
def statistics(
    data_path: str = typer.Option(..., "--data_path"),
    params_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
):
    """Computes statistics about the data. This statistics are uploaded
    to the Medperf platform under the data owner's approval. Include
    every statistic you consider useful for determining the nature of the
    data, but keep in mind that we want to keep the data as private as
    possible.
    Args:
        data_path (str): Location of the prepared data. Required for Medperf Data Preparation MLCubes.
        params_file (str): Location of the parameters.yaml file. Required for Medperf Data Preparation MLCubes.
        output_path (str): File to store the statistics. Must be statistics.yaml. Required for Medperf Data Preparation MLCubes.
    """
    get_stats(
        data_path,
        params_file,
        output_path,
    )


if __name__ == "__main__":
    app()
