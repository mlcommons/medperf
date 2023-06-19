"""MLCube handler file"""
import typer

app = typer.Typer()


@app.command("infer")
def prepare(
    data_path: str = typer.Option(..., "--data_path"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
    # Provide additional parameters as described in the mlcube.yaml file
    # e.g. model weights:
    # weights: str = typer.Option(..., "--weights"),
):
    # Modify the prepare command as needed
    raise NotImplementedError("The evaluate method is not yet implemented")


@app.command("hotfix")
def hotfix():
    # NOOP command for typer to behave correctly. DO NOT REMOVE OR MODIFY
    pass


if __name__ == "__main__":
    app()
