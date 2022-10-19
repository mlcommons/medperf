"""MLCube handler file"""
import os
import yaml
import typer
import shutil
import subprocess
from pathlib import Path


app = typer.Typer()


def exec_python(cmd: str) -> None:
    splitted_cmd = cmd.split()

    subprocess.run(splitted_cmd, cwd=".", check=True)
    


class PrepareTask(object):
    """
    Task for preparing the data

    Arguments:
    - data_path: data location.
    - labels_path: csv file containing the labels of the data
    - params_file: csv file with additional parameters
    - output_path: location to store prepared data
    """

    @staticmethod
    def run(
        data_path: str,
        labels_path: str,
        params_file: str,
        output_path: str,
        output_labels_path: str,
    ) -> None:
        files = next(os.walk(labels_path))[2]
        csvs = [file for file in files if file.endswith(".csv")]
        assert len(csvs) == 1, "Data path must contain only one csv file"
        labels_file = os.path.join(labels_path, csvs[0])
        cmd = f"python3 preprocess.py --img_path='{data_path}' --csv_path='{labels_file}' --params_file='{params_file}' --output_path='{output_path}' --output_labels_path='{output_labels_path}'"
        exec_python(cmd)


class SanityCheckTask(object):
    """
    Task for checking that the resulting data follows the standard

    Arguments:
    - data_path: data location.
    - params_file: location of parameters.yaml file
    """

    @staticmethod
    def run(data_path: str, labels_path: str, params_file: str) -> None:
        cmd = f"python3 check.py --data_path='{data_path}' --labels_path='{labels_path}' --params_file='{params_file}'"
        exec_python(cmd)


class StatisticsTask(object):
    """
    Task for generating and storing statistics about the prepared data

    Arguments:
    - data_path: data location.
    - params_file: location of parameters.yaml file
    """

    @staticmethod
    def run(data_path: str, labels_path: str, params_file: str, out_path: str) -> None:
        cmd = f"python3 statistics.py --data_path='{data_path}' --labels_path='{labels_path}' --params_file='{params_file}' --out_path='{out_path}'"
        exec_python(cmd)


class CleanupTask(object):
    """
    Task for returning the workspace to its initial state. It removes
    any files created by the cube, as well as the parameters file.

    Args:
    - params_file: yaml file with configuration parameters.
    - output_path: path where the cube's output is stored.
    """

    @staticmethod
    def run(params_file: str, output_path: str) -> None:
        for root, dirs, files in os.walk(output_path):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                shutil.rmtree(os.path.join(root, dir))
        os.remove(params_file)


@app.command("prepare")
def prepare(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
    output_labels_path: str = typer.Option(..., "--output_labels_path"),
):
    PrepareTask.run(
        data_path, labels_path, parameters_file, output_path, output_labels_path
    )


@app.command("sanity_check")
def sanity_check(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
):
    SanityCheckTask.run(data_path, labels_path, parameters_file)


@app.command("statistics")
def sanity_check(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    out_path: str = typer.Option(..., "--output_path"),
):
    StatisticsTask.run(data_path, labels_path, parameters_file, out_path)


@app.command("cleanup")
def cleanup(
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
):
    CleanupTask.run(parameters_file, output_path)


if __name__ == "__main__":
    app()
