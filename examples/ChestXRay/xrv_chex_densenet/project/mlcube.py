import os
import typer
import subprocess

app = typer.Typer()


def exec_python(cmd: str) -> None:
    splitted_cmd = cmd.split()
    process = subprocess.Popen(splitted_cmd, cwd=".")
    process.wait()


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
        cmd = f"python3 model.py --data_path={data_path} --params_file={params_file} --weights={weights} --out_path={out_path}"
        exec_python(cmd)


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
