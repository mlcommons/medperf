import os
import typer
from model import XRVInference

app = typer.Typer()


class InferTask(object):
    """
    Task for generating inferences on data

    Arguments:
    - data_path [str]: location of prepared data
    - params_file [str]: file containing parameters for inference
    - out_path [str]: location for storing inferences
    """

    @staticmethod
    def run(data_path: str, params_file: str, weights: str, out_path: str) -> None:
        XRVInference.run(data_path, params_file, weights, out_path)


@app.command("hotfix")
def hotfix():
    pass


@app.command("infer")
def infer(
    data_path: str = typer.Option(..., "--data_path"),
    params_file: str = typer.Option(..., "--parameters_file"),
    weights: str = typer.Option(..., "--weights"),
    out_path: str = typer.Option(..., "--output_path"),
):
    out_path = os.path.join(out_path, "predictions.csv")
    InferTask.run(data_path, params_file, weights, out_path)


if __name__ == "__main__":
    app()
