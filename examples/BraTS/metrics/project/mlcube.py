# MLCube Entrypoint
#
# This script shows how you can bridge your app with an MLCube interface.
# MLCubes expect the entrypoint to behave like a CLI, where tasks are
# commands, and input/output parameters and command-line arguments.
# You can provide that interface to MLCube in any way you prefer.
# Here, we show a way that requires minimal intrusion to the original code,
# By running the application through subprocesses.
import typer

import app as evaluator


app = typer.Typer()


@app.command("evaluate")
def evaluate(
    labels: str = typer.Option(..., "--labels"),
    predictions: str = typer.Option(..., "--predictions"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
    log_path: str = typer.Option(..., "--log_path"),
):
    evaluator.evaluate(
        label_dir=labels,
        prediction_dir=predictions,
        output_file=output_path,
        log_file=log_path
    )

@app.command("hotfix")
def hotfix():
    pass


if __name__ == "__main__":
    app()
