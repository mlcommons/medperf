"""MLCube handler file"""
import typer
import yaml

from infer import run_inference

app = typer.Typer()


@app.command("infer")
def prepare(
    data_path: str = typer.Option(..., "--data_path"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
    weights: str = typer.Option(..., "--weights"),
):
    with open(parameters_file) as f:
        parameters = yaml.safe_load(f)

    run_inference(data_path, parameters, output_path, weights)


@app.command("hotfix")
def hotfix():
    # NOOP command for typer to behave correctly. DO NOT REMOVE OR MODIFY
    pass


if __name__ == "__main__":
    app()
