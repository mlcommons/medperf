import os
import yaml
import argparse
import tarfile
import shutil

PARAMS_FILE = "parameters.yaml"
STATS_FILE = "statistics.yaml"
RESULTS_FILE = "results.yaml"
RUNNERS = ["docker", "singularity"]
TASK_DEFINITIONS = {
    "infer": {
        "inputs": {"data_path": None, "parameters_file": PARAMS_FILE},
        "outputs": {"output_path": None},
    },
    "prepare": {
        "inputs": {
            "data_path": None,
            "labels_path": None,
            "parameters_file": PARAMS_FILE,
        },
        "outputs": {"output_path": None},
    },
    "sanity_check": {"inputs": {"data_path": None, "parameters_file": PARAMS_FILE}},
    "statistics": {
        "inputs": {"data_path": None, "parameters_file": PARAMS_FILE},
        "outputs": {"output_path": STATS_FILE},
    },
    "evaluate": {
        "inputs": {"predictions": None, "labels": None, "parameters_file": PARAMS_FILE},
        "outputs": {"output_path": RESULTS_FILE},
    },
}
VALID_COMBINATIONS = [
    {"prepare", "sanity_check", "statistics"},
    {"infer",},
    {"evaluate",},
]


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
    contents = os.listdir(source_dir)
    with tarfile.open(output_filename, "w:gz") as tar:
        for rel_path in contents:
            abs_path = os.path.join(source_dir, rel_path)
            tar.add(abs_path, arcname=os.path.basename(abs_path))


def create_empty_file(path):
    with open(path, "w"):
        pass


def check_runners(mlcube):
    # To avoid ambiguity, MLCubes should only have one explicit image
    image_detected = False
    if "docker" in mlcube:
        print("Docker runner configuration identified")
        if "image" in mlcube["docker"]:
            image_detected = True
            image_name = mlcube["docker"]["image"]
            print("Remember to push your image to a registry with:")
            print(f"\tdocker push {image_name}")

    if "singularity" in mlcube:
        print("Singularity runner configuration identified")
        if "image" in mlcube["singularity"] and image_detected:
            msg = (
                "An ambiguous configuration has been detected. "
                + "Only one image can be defined across runners"
            )
            raise RuntimeError(msg)


def validate_tasks(mlcube):
    tasks = set(mlcube["tasks"])
    # Raise error if no valid task configuration was found
    if not any([combination - tasks == 0 for combination in VALID_COMBINATIONS]):
        msg = (
            "No valid task combination was found. "
            + "Could not infer any medperf MLCube type. "
            + "Please refer to the documentation on building medperf MLCubes"
        )
        raise RuntimeError("Could not infer any MLCube type")

    medperf_tasks = TASK_DEFINITIONS.keys()
    for task, contents in tasks.items():
        if task not in medperf_tasks:
            continue
        expected_parameters = medperf_tasks[task]
        if "inputs" in expected_parameters:
            for exp_input, exp_val in expected_parameters["inputs"].items():
                

def main():
    args = get_args()
    mlcube_path = args.mlcube
    mlcube_manifest_path = os.path.join(mlcube_path, "mlcube.yaml")

    with open(mlcube_manifest_path, "r") as f:
        mlcube = yaml.safe_load(f)

    check_runners(mlcube)
    validate_tasks(mlcube)

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
