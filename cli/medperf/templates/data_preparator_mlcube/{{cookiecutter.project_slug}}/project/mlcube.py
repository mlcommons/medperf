"""MLCube handler file"""
import typer


app = typer.Typer()


@app.command("prepare")
def prepare(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
    output_labels_path: str = typer.Option(..., "--output_labels_path"),
):
    # Modify the prepare command as needed
    raise NotImplementedError("The prepare method is not yet implemented")


@app.command("sanity_check")
def sanity_check(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
):
    # Modify the sanity_check command as needed
    raise NotImplementedError("The sanity check method is not yet implemented")


@app.command("statistics")
def statistics(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    out_path: str = typer.Option(..., "--output_path"),
):
    # Modify the statistics command as needed
    raise NotImplementedError("The statistics method is not yet implemented")


if __name__ == "__main__":
    app()
