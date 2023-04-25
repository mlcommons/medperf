import os
import yaml
import shutil
import tarfile

from .constants import WSPACE_PATH, PARAMS_FILE, ADD_PATH, MLCUBE_FILE, ADD_FILE
from .bcolors import bcolors


def make_tarfile(source_dir, output_filename):
    contents = os.listdir(source_dir)
    with tarfile.open(output_filename, "w:gz") as tar:
        for rel_path in contents:
            abs_path = os.path.join(source_dir, rel_path)
            tar.add(abs_path, arcname=os.path.basename(abs_path))


def package(mlcube_path, output_path):
    workspace_path = os.path.join(mlcube_path, WSPACE_PATH)
    parameters_path = os.path.join(workspace_path, PARAMS_FILE)
    additional_path = os.path.join(workspace_path, ADD_PATH)
    mlcube_manifest_path = os.path.join(mlcube_path, MLCUBE_FILE)

    deploy_path = os.path.join(mlcube_path, "deploy")
    deploy_manifest_path = os.path.join(deploy_path, MLCUBE_FILE)
    deploy_parameters_path = os.path.join(deploy_path, PARAMS_FILE)
    deploy_additional_tarball = os.path.join(deploy_path, ADD_FILE)

    print(f"{bcolors.OKCYAN}Packaging assets into {deploy_path}{bcolors.ENDC}")

    # Create deployment folder
    if not os.path.exists(deploy_path):
        os.mkdir(deploy_path)

    shutil.copyfile(mlcube_manifest_path, deploy_manifest_path)

    # Handle the possibility of non-existing parameters file
    if os.path.exists(parameters_path):
        shutil.copyfile(parameters_path, deploy_parameters_path)

    # Package additional files if needed
    if os.path.exists(additional_path):
        make_tarfile(additional_path, deploy_additional_tarball)

    # Package singularity image if provided
    with open(mlcube_manifest_path, "r") as f:
        mlcube = yaml.safe_load(f)

    if "singularity" in mlcube and "image" in mlcube["singularity"]:
        img_name = mlcube["singularity"]["image"]
        img_path = os.path.join(workspace_path, ".image", img_name)
        deploy_img_path = os.path.join(deploy_path, img_name)
        shutil.copyfile(img_path, deploy_img_path)

    # Package everything to the designated output tarball
    if output_path is not None:
        print(f"{bcolors.OKCYAN}Packaging all assets into {output_path}{bcolors.ENDC}")
        make_tarfile(deploy_path, output_path)
