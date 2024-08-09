"""MLCube handler file"""

import typer
import yaml
from metrics import calculate_metrics

app = typer.Typer()


@app.command("evaluate")
def evaluate(
    labels: str = typer.Option(..., "--labels"),
    predictions: str = typer.Option(..., "--predictions"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
):
    with open(parameters_file) as f:
        parameters = yaml.safe_load(f)

    calculate_metrics(labels, predictions, parameters, output_path)


@app.command("hotfix")
def hotfix():
    # NOOP command for typer to behave correctly. DO NOT REMOVE OR MODIFY
    pass


if __name__ == "__main__":
    app()
