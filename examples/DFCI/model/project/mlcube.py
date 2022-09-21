# MLCube Entrypoint
#
# This script shows how you can bridge your app with an MLCube interface.
# MLCubes expect the entrypoint to behave like a CLI, where tasks are
# commands, and input/output parameters and command-line arguments.
# You can provide that interface to MLCube in any way you prefer.
# Here, we show a way that requires minimal intrusion to the original code,
# By running the application through subprocesses.

import os
import yaml
import typer
from infer import run_inference

app = typer.Typer()


@app.command("infer")
def infer(
    data_path: str = typer.Option(..., "--data_path"),
    params_file: str = typer.Option(..., "--parameters_file"),
    model_info: str = typer.Option(..., "--model_info"),
    out_path: str = typer.Option(..., "--output_path"),
):

    with open(params_file, "r") as f:
        params = yaml.safe_load(f)

    run_inference(os.path.join(data_path, "images"), out_path, model_info, params)


@app.command("hotfix")
def hotfix():
    pass


if __name__ == "__main__":
    print("Starting app")
    app()
