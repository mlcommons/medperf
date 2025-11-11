import os

from medperf.exceptions import ExecutionError, InvalidContainerSpec, MedperfException
from medperf import config

from medperf.utils import run_command
import shlex
import tarfile
import json
import logging


def get_docker_image_hash(docker_image, timeout: int = None):
    logging.debug(f"Getting docker image hash of {docker_image}")
    command = ["docker", "inspect", "--format", "{{.Id}}", docker_image]
    logging.debug("Running docker inspect command")
    image_id = run_command(command, timeout=timeout)
    image_id = image_id.strip()
    logging.debug(f"Image ID: {image_id}")
    if image_id.startswith("sha256:"):
        image_id = image_id[len("sha256:") :]  # noqa
        return image_id
    raise InvalidContainerSpec("Invalid inspect output:", image_id)


def volumes_to_cli_args(input_volumes: list, output_volumes: list):
    logging.debug("Converting volumes to CLI args")
    args = []
    for volume in input_volumes:
        host_path = volume["host_path"]
        mount_path = volume["mount_path"]
        mount_type = volume["type"]
        if not os.path.exists(host_path):
            raise MedperfException(
                f"Internal error: input volume should exist: {host_path}"
            )
        args.append("--volume")
        args.append(f"{host_path}:{mount_path}:ro")

    for volume in output_volumes:
        host_path = volume["host_path"]
        mount_path = volume["mount_path"]
        mount_type = volume["type"]
        if mount_type == "directory":
            os.makedirs(host_path, exist_ok=True)
        else:
            dirname = os.path.dirname(host_path)
            os.makedirs(dirname, exist_ok=True)
            if not os.path.exists(host_path):
                with open(host_path, "w"):
                    pass
        args.append("--volume")
        args.append(f"{host_path}:{mount_path}:rw")
    logging.debug(f"Volumes args: {args}")
    return args


def craft_docker_run_command(run_args: dict):  # noqa: C901
    logging.debug(f"Crafting command from run args: {run_args}")
    command = ["docker", "run"]
    remove_container = run_args.pop("remove_container", False)
    if remove_container:
        command.append("--rm")
    user = run_args.pop("user", None)
    if user is not None:
        command.append("-u")
        command.append(user)

    input_volumes = run_args.pop("input_volumes", [])
    output_volumes = run_args.pop("output_volumes", [])
    volumes_args = volumes_to_cli_args(input_volumes, output_volumes)
    command.extend(volumes_args)

    network = run_args.pop("network", None)
    if network is not None:
        command.append("--network")
        command.append(network)

    gpus = run_args.pop("gpus", None)
    if gpus is not None:
        command.append("--gpus")
        if isinstance(gpus, int):
            command.append(str(gpus))
        elif gpus == "all":
            command.append("all")
        elif isinstance(gpus, list):
            command.append("device=" + ",".join(gpus))

    shm_size = run_args.pop("shm_size", None)
    if shm_size is not None:
        command.append("--shm-size")
        command.append(shm_size)

    env_dict = run_args.pop("environment", {})
    for key, val in env_dict.items():
        command.append("--env")
        command.append(f"{key}={val}")

    entrypoint = run_args.pop("entrypoint", None)
    if entrypoint is not None:
        command.append("--entrypoint")
        command.append(f"{entrypoint}")

    network = run_args.pop("network", None)
    if network is not None:
        command.append("--network")
        command.append(network)

    ports = run_args.pop("ports", [])
    for port in ports:
        command.append("-p")
        command.append(port)

    image = run_args.pop("image")
    command.append(image)
    extra_command = run_args.pop("command", [])
    logging.debug(f"Extra command: {extra_command}")
    if isinstance(extra_command, str):
        extra_command = shlex.split(extra_command)
    command.extend(extra_command)
    return command


def get_repo_tags_from_archive(image_archive: str) -> list[str]:
    """
    Ideally we should find only a single entry in the digest with a single repo tag, but this method
    should hopefully generalize for manifests with multiple entries and/or multiple RepoTag values
    """
    manifest_file = "manifest.json"
    repo_tags_key = "RepoTags"

    logging.debug(f"Getting repo tags from archive {image_archive}")
    with tarfile.open(image_archive, "r") as tar:
        with tar.extractfile(manifest_file) as index_json_obj:
            manifests_list = json.load(index_json_obj)

    logging.debug(f"Manifests list: {manifests_list}")
    repo_tags_list = []
    for manifest in manifests_list:
        repo_tags_list.extend(manifest[repo_tags_key])

    logging.debug(f"Repo tags list: {repo_tags_list}")
    return repo_tags_list


def load_image(image_archive_path):
    logging.debug(f"Loading image {image_archive_path}")
    docker_load_cmd = ["docker", "load", "-i", image_archive_path]
    logging.debug("Running docker load command")
    run_command(docker_load_cmd)


def delete_images(images):
    if len(images) == 0:
        logging.debug("No images to delete")
        return
    logging.debug(f"Deleting images {images}")
    delete_image_cmd = ["docker", "rmi", "-f"] + images
    logging.debug("Running docker rmi command")

    try:
        run_command(delete_image_cmd)
    except ExecutionError:
        config.ui.print_warning("WARNING: Failed to delete docker images.")
