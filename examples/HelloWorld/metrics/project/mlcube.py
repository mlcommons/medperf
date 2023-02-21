# MLCube Entrypoint
#
# This script shows how you can bridge your app with an MLCube interface.
# MLCubes expect the entrypoint to behave like a CLI, where tasks are
# commands, and input/output parameters and command-line arguments.
# You can provide that interface to MLCube in any way you prefer.
# Here, we show a way that requires minimal intrusion to the original code,
# By running the application through subprocesses.
import os
import typer
import subprocess


app = typer.Typer()


def exec_python(cmd: str) -> None:
    """Execute a python script as a subprocess

    Args:
        cmd (str): command to run as would be written inside the terminal
    """
    splitted_cmd = cmd.split()
    subprocess.run(splitted_cmd, cwd=".", check=True)


@app.command("evaluate")
def evaluate(
    labels: str = typer.Option(..., "--labels"),
    predictions: str = typer.Option(..., "--predictions"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
):
    labels_csv = os.path.join(labels, "labels.csv")
    preds_csv = os.path.join(predictions, "predictions.csv")

    cmd = f"python3 app.py --labels_csv={labels_csv} --preds_csv={preds_csv} --parameters_file={parameters_file} --output_file={output_path}"
    exec_python(cmd)


@app.command("hotfix")
def hotfix():
    pass


if __name__ == "__main__":
    app()
