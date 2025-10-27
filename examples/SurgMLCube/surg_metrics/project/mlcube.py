"""MLCube handler file"""

import typer
import subprocess


app = typer.Typer()


class EvaluateTask(object):
    """Runs evaluation metrics given the predictions and label files

    Args:
    - preds_path: predictions location.
    - labels: location of the original data. Dummy input.
    - parameters_file: yaml file with additional parameters
    - output_file: location to the results

    """

    @staticmethod
    def run(
        preds_path: str, labels: str, parameters_file: str, output_file: str
    ) -> None:
        cmd = f"python3 metrics.py --preds_path={preds_path} --parameters_file={parameters_file} --output_file={output_file}"
        splitted_cmd = cmd.split()

        subprocess.run(splitted_cmd, cwd=".", check=True)


@app.command("evaluate")
def evaluate(
    preds_path: str = typer.Option(..., "--predictions"),
    labels: str = typer.Option(..., "--labels"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
):
    EvaluateTask.run(preds_path, labels, parameters_file, output_path)


@app.command("dummy")
def dummy():
    print(
        "This is added to avoid 'typer' throwing an error when having only one task available"
    )


if __name__ == "__main__":
    app()
