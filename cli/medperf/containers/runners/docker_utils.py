import os

from medperf.exceptions import InvalidContainerSpec, MedperfException
from .utils import run_command
import shlex
from typing import Optional
import json


def get_docker_image_hash(docker_image, timeout: int = None):
    command = [
        "docker",
        "buildx",
        "imagetools",
        "inspect",
        docker_image,
        "--format",
        '"{{json .Manifest}}"',
    ]
    image_manifest_str = run_command(command, timeout=timeout)
    image_manifest_str = image_manifest_str.strip().strip("\"'")
    image_manifest_dict = json.loads(image_manifest_str)

    image_hash = image_manifest_dict.get("digest", "")
    if not image_hash.startswith("sha256:"):
        raise InvalidContainerSpec(
            "Invalid 'docker buildx imagetools inspect' output:", image_manifest_dict
        )

    return image_hash


def extract_docker_image_name(image_name_with_tag_and_hash: str) -> str:
    hash_separator = "@"
    tag_separator = ":"

    if hash_separator in image_name_with_tag_and_hash:
        image_name_with_tag = image_name_with_tag_and_hash.rsplit(
            hash_separator, maxsplit=1
        )[0]
    else:
        image_name_with_tag = image_name_with_tag_and_hash

    try:
        image_name = image_name_with_tag.rsplit(tag_separator, maxsplit=1)[0]
        return image_name
    except ValueError:
        # If something unexpected happens, use name as is
        return image_name_with_tag_and_hash


def generate_unique_image_name(
    image_name_with_tag: str, image_hash: Optional[str] = None
):

    if image_hash is None:
        # If no hash (for example, when first uploading a container) use the name with tag as is
        return image_name_with_tag

    image_name = extract_docker_image_name(image_name_with_tag)

    if image_name == image_name_with_tag:
        return image_name

    image_name_with_hash = f"{image_name}@{image_hash}"
    return image_name_with_hash


def volumes_to_cli_args(input_volumes: list, output_volumes: list):
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

    return args


def craft_docker_run_command(run_args: dict):  # noqa: C901
    command = ["docker", "run"]
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
    if isinstance(extra_command, str):
        extra_command = shlex.split(extra_command)
    command.extend(extra_command)
    return command
