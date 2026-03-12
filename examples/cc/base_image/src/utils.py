import logging
import subprocess
import tarfile
import os


def run_command(command: list) -> None:
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command '{' '.join(command)}' failed with error: {result.stderr.decode()}"
        )


def untar(filepath: str, extract_to: str) -> None:
    logging.info(f"Uncompressing tar.gz at {filepath}")
    try:
        tar = tarfile.open(filepath)
        tar.extractall(extract_to)
        tar.close()
    except tarfile.ReadError as e:
        raise RuntimeError("Cannot extract tar.gz file, " + str(e))
    os.remove(filepath)


def tar(output_path: str, folder_path: str) -> None:
    logging.info(f"Compressing tar.gz at {output_path}")
    tar_arc = tarfile.open(output_path, "w:gz")
    tar_arc.add(folder_path, arcname="")
    logging.info(f"Compressing tar.gz at {output_path}: {folder_path} Added.")
    tar_arc.close()
