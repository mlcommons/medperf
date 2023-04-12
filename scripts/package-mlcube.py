# Tarfile creation taken from https://stackoverflow.com/questions/2032403/how-to-create-full-compressed-tar-file-using-python

import os
import argparse
import tarfile
import shutil


def get_args():
    desc = (
        "Helper script to prepare an MLCube for medperf/challenge submission.\n"
        + "This script will create a 'deploy' path with the files that need to be hosted\n"
        + "for medperf mlcube submission. Additionally, if an output path is provided,\n"
        + "all deployment files are packaged into the output tarball file. Useful for competitions"
    )

    parser = argparse.ArgumentParser(prog="PackageMLCube", description=desc)
    parser.add_argument(
        "mlcube",
        help="Path to the mlcube folder. This path is the one that contains ./mlcube.yaml and ./workspace",
    )
    parser.add_argument(
        "--output",
        help="(Optional) Output tarball path. If provided, the contents of the deploy folder are packaged into this file",
    )
    return parser.parse_args()


def validate_path(expected_paths):
    if not all([os.path.exists(path) for path in expected_paths]):
        expected_paths_str = "\n".join([f"\t- {path}" for path in expected_paths])
        msg = (
            "Couldn't find the expected paths. Please ensure the\n"
            + "provided path is a valid mlcube, and that the following files\n"
            + "exist in the given path:\n"
            + f"{expected_paths_str}"
        )
        raise RuntimeError(msg)


def make_tarfile(source_dir, output_filename):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def create_empty_file(path):
    with open(path, "w"):
        pass


def main():
    args = get_args()
    mlcube_path = args.mlcube
    mlcube_manifest_path = os.path.join(mlcube_path, "mlcube.yaml")
    workspace_path = os.path.join(mlcube_path, "workspace")
    parameters_path = os.path.join(workspace_path, "parameters.yaml")
    additional_path = os.path.join(workspace_path, "additional_files")
    expected_paths = [mlcube_manifest_path, workspace_path]

    validate_path(expected_paths)

    deploy_path = os.path.join(mlcube_path, "deploy")
    deploy_manifest_path = os.path.join(deploy_path, "mlcube.yaml")
    deploy_parameters_path = os.path.join(deploy_path, "parameters.yaml")
    deploy_additional_tarball = os.path.join(deploy_path, "additional_files.tar.gz")

    # Create deployment folder
    if not os.path.exists(deploy_path):
        os.mkdir(deploy_path)

    shutil.copyfile(mlcube_manifest_path, deploy_manifest_path)

    # Handle the possibility of non-existing parameters file
    if os.path.exists(parameters_path):
        shutil.copyfile(parameters_path, deploy_parameters_path)
    else:
        create_empty_file(deploy_parameters_path)

    # Package additional files if needed
    if os.path.exists(additional_path):
        make_tarfile(additional_path, deploy_additional_tarball)

    # Package everything to the designated output tarball
    output_path = args.output
    if output_path is not None:
        make_tarfile(deploy_path, output_path)


if __name__ == "__main__":
    main()
