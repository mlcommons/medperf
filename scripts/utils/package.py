import os
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


def package(mlcube_manifest_path, required_files, output_path):
    mlcube_path = os.path.dirname(os.path.abspath(mlcube_manifest_path))

    workspace_path = os.path.join(mlcube_path, WSPACE_PATH)
    parameters_path = os.path.join(workspace_path, PARAMS_FILE)
    additional_path = os.path.join(workspace_path, ADD_PATH)

    assets_path = os.path.join(mlcube_path, "assets")
    target_manifest_path = os.path.join(assets_path, MLCUBE_FILE)
    target_parameters_path = os.path.join(assets_path, PARAMS_FILE)
    target_additional_tarball = os.path.join(assets_path, ADD_FILE)

    print(f"{bcolors.OKCYAN}Packaging assets into {assets_path}{bcolors.ENDC}")

    # Create assets folder
    if not os.path.exists(assets_path):
        os.mkdir(assets_path)

    shutil.copyfile(mlcube_manifest_path, target_manifest_path)

    try:
        # Package parameters file if needed
        if required_files["parameters_file"]:
            shutil.copyfile(parameters_path, target_parameters_path)

        # Package additional files if needed
        if required_files["additional_files"]:
            make_tarfile(additional_path, target_additional_tarball)

        # Package singularity image if needed
        if required_files["singularity_image"]:
            img_name = required_files["singularity_image"]
            img_path = os.path.join(workspace_path, ".image", img_name)
            target_img_path = os.path.join(assets_path, img_name)
            shutil.copyfile(img_path, target_img_path)
    except FileNotFoundError as e:
        print(f"{bcolors.FAIL}ERROR: {e}{bcolors.ENDC}")
        shutil.rmtree(assets_path)
        exit()

    # Package everything to the designated output tarball
    if output_path is not None:
        print(f"{bcolors.OKCYAN}Packaging all assets into {output_path}{bcolors.ENDC}")
        make_tarfile(assets_path, output_path)
