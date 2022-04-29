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
import subprocess

app = typer.Typer()


def exec_python(cmd: str) -> None:
    """Execute a python script as a subprocess

    Args:
        cmd (str): command to run as would be written inside the terminal
    """
    splitted_cmd = cmd.split()
    process = subprocess.Popen(splitted_cmd, cwd=".")
    process.wait()


@app.command("evaluate")
def evaluate(
    labels: str = typer.Option(..., "--labels"),
    predictions: str = typer.Option(..., "--predictions"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
):
    labels_csv = labels
    preds_csv = predictions

    cmd = f"python3 app.py --labels_csv={labels_csv} --preds_csv={preds_csv} --parameters_file={parameters_file} --output_file={output_path}"
    exec_python(cmd)


"""
@app.command("infer")
def infer(
    labels: str = typer.Option(..., "--labels"),
    predictions: str = typer.Option(..., "--predictions"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
):

    
    with open(params_file, "r") as f:
        params = yaml.safe_load(f)

    #model_file = os.path.join(model_info, "unet_full.pth")
    
    #names_file = os.path.join(data_path, "0024_49.npy")
    #names_file = os.path.join(data_path)
        
    #uppercase = params["uppercase"]
    # data, additional files, output
    #cmd = f"python3 app.py --data_p = {data_path} --model_info={model_file} --out={out_path}"
    cmd = f"python3 app.py --labels_csv={labels_csv} --preds_csv={preds_csv} --parameters_file={parameters_file} --output_file={output_path}"
    exec_python(cmd)

    #if uppercase:
    #    cmd += f" --uppercase={uppercase}"
    print("exec cmd")
    exec_python(cmd)
"""


@app.command("hotfix")
def hotfix():
    pass


if __name__ == "__main__":
    print("Starting app")
    app()
