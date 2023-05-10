import yaml
from schema import SchemaError

from .bcolors import bcolors
from .constants import PARAMS_FILE, ADD_PATH
from .schemas import schemas


def validate_and_parse_manifest(mlcube_manifest_path, mlcube_types):
    with open(mlcube_manifest_path, "r") as f:
        mlcube = yaml.safe_load(f)
    try:
        check_runners(mlcube)
        found_files = validate_tasks(mlcube, mlcube_types)
    except (RuntimeError, SchemaError) as e:
        print(f"{bcolors.FAIL}ERROR: {e}{bcolors.ENDC}")
        exit()

    required_files = {}

    required_files["singularity_image"] = False
    if "singularity" in mlcube and "image" in mlcube["singularity"]:
        required_files["singularity_image"] = mlcube["singularity"]["image"]

    required_files["parameters_file"] = PARAMS_FILE in found_files
    required_files["additional_files"] = ADD_PATH in found_files

    return required_files


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


def validate_tasks(mlcube, mlcube_types):
    tasks = mlcube["tasks"]
    found_files = set()
    schemas_list = [schemas[type_] for type_ in mlcube_types]
    for schema in schemas_list:
        files = set()
        schema.validate(tasks, files=files)
        found_files = found_files.union(files)
    return found_files
