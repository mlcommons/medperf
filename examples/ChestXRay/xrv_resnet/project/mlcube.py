import os
import typer
import subprocess

app = typer.Typer()


def exec_python(cmd: str) -> None:
    splitted_cmd = cmd.split()
    subprocess.run(splitted_cmd, cwd=".", check=True)


class InferTask(object):
    """
    Task for generating inferences on data

    Arguments:
    - data_path [str]: location of prepared data
    - out_path [str]: location for storing inferences
    """

    @staticmethod
    def run(data_path: str, weights: str, out_path: str) -> None:
        cmd = f"python3 model.py --data_path={data_path} --weights={weights} --out_path={out_path}"
        exec_python(cmd)


@app.command("hotfix")
def hotfix():
    pass


@app.command("infer")
def infer(
    data_path: str = typer.Option(..., "--data_path"),
    weights: str = typer.Option(..., "--weights"),
    out_path: str = typer.Option(..., "--output_path"),
):
    out_path = os.path.join(out_path, "predictions.csv")
    InferTask.run(data_path, weights, out_path)


if __name__ == "__main__":
    app()
