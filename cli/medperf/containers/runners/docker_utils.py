import os

from medperf.exceptions import InvalidContainerSpec
from .utils import run_command
import shlex


def get_docker_image_hash(docker_image, timeout: int = None):
    command = ["docker", "inspect", "--format", "{{.Id}}", docker_image]
    image_id = run_command(command, timeout=timeout)
    image_id = image_id.strip()
    # docker_client = docker.APIClient()
    # image_info = docker_client.inspect_image(docker_image)
    if image_id.startswith("sha256:"):
        image_id = image_id[len("sha256:") :]  # noqa
        return image_id
    raise InvalidContainerSpec("Invalid inspect output:", image_id)


def volumes_to_cli_args(input_volumes: list, output_volumes: list):
    args = []
    for io_type, volumes_list in [("ro", input_volumes), ("rw", output_volumes)]:
        for volume in volumes_list:
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
            args.append(f"{host_path}:{mount_path}:{io_type}")

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
