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
    subprocess.run(splitted_cmd, cwd=".", check=True)


@app.command("infer")
def infer(
    data_path: str = typer.Option(..., "--data_path"),
    params_file: str = typer.Option(..., "--parameters_file"),
    greetings: str = typer.Option(..., "--greetings"),
    out_path: str = typer.Option(..., "--output_path"),
):
    """infer task command. This is what gets executed when we run:
    `mlcube run infer`

    Args:
        data_path (str): Location of the data to run inference with. Required for Medperf Model MLCubes.
        params_file (str): Location of the parameters.yaml file. Required for Medperf Model MLCubes.
        greetings (str): Example of an extra parameter that uses `additional_files`.
        out_path (str): Location to store prediction results. Required for Medperf Model MLCubes.
    """
    with open(params_file, "r") as f:
        params = yaml.safe_load(f)

    names_file = os.path.join(data_path, "names.csv")
    uppercase = params["uppercase"]
    cmd = (
        f"python3 app.py --names={names_file} --greetings={greetings} --out={out_path}"
    )
    if uppercase:
        cmd += f" --uppercase={uppercase}"
    exec_python(cmd)


@app.command("hotfix")
def hotfix():
    pass


if __name__ == "__main__":
    app()
