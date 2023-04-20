import os
import yaml

from .bcolors import bcolors
from .constants import *


def is_valid(mlcube_path):
    workspace_path = os.path.join(mlcube_path, "workspace")
    mlcube_manifest_path = os.path.join(mlcube_path, "mlcube.yaml")
    expected_paths = [mlcube_manifest_path, workspace_path]

    try:
        validate_path(expected_paths)

        with open(mlcube_manifest_path, "r") as f:
            mlcube = yaml.safe_load(f)

        validate_tasks(mlcube)
        check_runners(mlcube)
        validate_singularity_image(mlcube, workspace_path)
    except RuntimeError as e:
        print(f"{bcolors.FAIL}ERROR: {e}{bcolors.ENDC}")
        return False
    return True


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


def validate_tasks(mlcube):
    tasks = set(mlcube["tasks"])
    # Raise error if no valid task configuration was found
    if not any([len(combination - tasks) == 0 for combination in VALID_COMBINATIONS]):
        msg = (
            "No valid task combination was found. "
            + "Could not infer any medperf MLCube type. "
            + "Please refer to the documentation on building medperf MLCubes"
        )
        raise RuntimeError(msg)

    medperf_tasks = TASK_DEFINITIONS.keys()
    for task, contents in mlcube["tasks"].items():
        if task not in medperf_tasks:
            continue
        expected_parameters = TASK_DEFINITIONS[task]
        validate_task(task, contents, expected_parameters)


def validate_task(task, task_contents, expected_parameters):
    parameter_types = ["input", "output"]
    for parameter_type in parameter_types:
        type = parameter_type + "s"
        if type in expected_parameters:
            for exp_key, exp_val in expected_parameters[type].items():
                validate_key_val(exp_key, exp_val, task, task_contents, parameter_type)


def validate_singularity_image(mlcube, workspace_path):
    if "singularity" not in mlcube or "image" not in mlcube["singularity"]:
        return

    img_name = mlcube["singularity"]["image"]
    img_path = os.path.join(workspace_path, ".image", img_name)
    if not os.path.exists(img_path):
        raise RuntimeError(f"Singularity image {img_path} not found.")


def validate_key_val(key, val, task, task_contents, parameter_type):
    type = parameter_type + "s"
    error_msg = f'Task "{task}" requires {parameter_type} "{key}"'
    if key not in task_contents["parameters"][type]:
        raise RuntimeError(error_msg + " to be defined")

    if val:
        retrieved_val = task_contents["parameters"][type][key]
        if isinstance(retrieved_val, dict):
            retrieved_val = retrieved_val["default"]

        if retrieved_val != val:
            raise RuntimeError(error_msg + f' to be assigned to "{val}"')


def check_runners(mlcube):
    # To avoid ambiguity, MLCubes should only have one explicit image
    image_detected = False
    if "docker" in mlcube:
        print(f"{bcolors.OKCYAN}Docker runner configuration identified{bcolors.ENDC}")
        if "image" in mlcube["docker"]:
            image_detected = True
            image_name = mlcube["docker"]["image"]
            print(
                f"{bcolors.WARNING}Remember to push your image to a registry with:{bcolors.ENDC}"
            )
            print(f"\t{bcolors.UNDERLINE}docker push {image_name}{bcolors.ENDC}")

    if "singularity" in mlcube:
        print(
            f"{bcolors.OKCYAN}Singularity runner configuration identified{bcolors.ENDC}"
        )
        if "image" in mlcube["singularity"] and image_detected:
            msg = (
                "An ambiguous configuration has been detected. "
                + "Only one image can be defined across runners"
            )
            raise RuntimeError(msg)
