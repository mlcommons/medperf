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


@app.command("infer")
def infer(
    data_path: str = typer.Option(..., "--data_path"),
    params_file: str = typer.Option(..., "--parameters_file"),
    model_info: str = typer.Option(..., "--model_info"),
    out_path: str = typer.Option(..., "--output_path"),
):

    print("param f", params_file)
    print("data p", data_path)
    print("model i", model_info)
    print("out p", out_path)

    with open(params_file, "r") as f:
        params = yaml.safe_load(f)

    model_file = os.path.join(model_info, "fl_round_monai1.pth")

    # names_file = os.path.join(data_path, "0024_49.npy")
    # names_file = os.path.join(data_path)
    names_file = data_path

    # uppercase = params["uppercase"]
    # data, additional files, output
    # cmd = f"python3 app.py --data_p = {data_path} --model_info={model_file} --out={out_path}"
    cmd = f"python3 app.py --names={names_file} --model_info={model_file} --out={out_path}"
    print("cmd")
    # if uppercase:
    #    cmd += f" --uppercase={uppercase}"
    print("exec cmd")
    exec_python(cmd)


@app.command("hotfix")
def hotfix():
    pass


if __name__ == "__main__":
    print("Starting app")
    app()
