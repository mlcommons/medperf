"""MLCube handler file"""

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
    assert process.returncode == 0, f"command failed: {cmd}"


@app.command("prepare")
def prepare(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
    output_labels_path: str = typer.Option(..., "--output_labels_path"),
    report_file: str = typer.Option(..., "--report_file"),
    metadata_path: str = typer.Option(..., "--metadata_path"),
):
    cmd = f"python3 mlcube_project/prepare.py --metadata_path={metadata_path} --data_path={data_path} --labels_path={labels_path} --data_out={output_path} --labels_out={output_labels_path} --report={report_file}"
    exec_python(cmd)


@app.command("sanity_check")
def sanity_check(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
):
    # Modify the sanity_check command as needed
    cmd = f"python3 mlcube_project/sanity_check.py --data_path={data_path} --labels_path={labels_path}"
    exec_python(cmd)


@app.command("statistics")
def statistics(
    data_path: str = typer.Option(..., "--data_path"),
    labels_path: str = typer.Option(..., "--labels_path"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    out_path: str = typer.Option(..., "--output_path"),
    metadata_path: str = typer.Option(..., "--metadata_path"),
):
    # Modify the statistics command as needed
    cmd = f"python3 mlcube_project/statistics.py --metadata_path={metadata_path} --data_path={data_path} --labels_path={labels_path} --out_file={out_path}"
    exec_python(cmd)


if __name__ == "__main__":
    app()
