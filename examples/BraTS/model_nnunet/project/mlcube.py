# MLCube Entrypoint
#
# This script shows how you can bridge your app with an MLCube interface.
# MLCubes expect the entrypoint to behave like a CLI, where tasks are
# commands, and input/output parameters and command-line arguments.
# You can provide that interface to MLCube in any way you prefer.
# Here, we show a way that requires minimal intrusion to the original code,
# By running the application through subprocesses.

import os, shutil
import typer
import subprocess

from distutils.dir_util import copy_tree

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
    data_path: str = typer.Option(
        ..., "--data_path"
    ),  # FeTS_CLI writes the output in the same path as data_path
    params_file: str = typer.Option(
        ..., "--parameters_file"
    ),  # FeTS_CLI does not need this
    out_path: str = typer.Option(
        ..., "--output_path"
    ),  # FeTS_CLI writes the output in the same path as data_path
):
    """infer task command. This is what gets executed when we run:
    `mlcube run infer`

    Args:
        data_path (str): Location of the data to run inference with. Required for Medperf Model MLCubes.
        out_path (str): Location to store prediction results. Required for Medperf Model MLCubes.
    """
    copy_tree(
        data_path, out_path
    )  # FeTS_CLI writes the output in the same path as data_path

    arch_to_consider = "nnunet"
    cmd = f"FeTS_CLI -a {arch_to_consider} -g 1 -t 0 -d {out_path}"
    exec_python(cmd)

    if os.path.isdir(os.path.join(out_path, "logs")):
        shutil.rmtree(os.path.join(out_path, "logs"))

    for subs in os.listdir(out_path):
        current_subject = os.path.join(out_path, subs)

        if os.path.isdir(current_subject):
            current_subject_qc_dir = os.path.join(current_subject, "SegmentationsForQC")
            if os.path.exists(current_subject_qc_dir):
                all_qc_files = os.listdir(current_subject_qc_dir)
                for qc_file in all_qc_files:
                    full_file = os.path.join(current_subject_qc_dir, qc_file)
                    if qc_file.endswith("_seg.nii.gz"):
                        expected_file = os.path.join(current_subject, qc_file)
                        shutil.move(full_file, expected_file)


@app.command("hotfix")
def hotfix():
    pass


if __name__ == "__main__":
    app()
