from medperf.exceptions import ExecutionError, CommunicationError
from .utils import run_command
import os
import requests
import semver
from .docker_utils import volumes_to_cli_args as docker_volumes_to_cli_args
import shlex


def get_docker_image_hash_from_dockerhub(docker_image, timeout: int = None):
    image_splitted = docker_image.split(":")
    if len(image_splitted) == 1:
        image = docker_image
        tag = "latest"
    else:
        image = image_splitted[0]
        tag = image_splitted[1]

    auth_url = (
        "https://auth.docker.io/token?service="
        f"registry.docker.io&scope=repository:{image}:pull"
    )
    response = requests.get(auth_url, timeout=timeout)
    if response.status_code != 200:
        raise CommunicationError("Failed to get token for docker image hash.")

    token = response.json()["token"]

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.docker.distribution.manifest.v2+json",
    }
    manifest_url = f"https://registry-1.docker.io/v2/{image}/manifests/{tag}"
    response = requests.get(manifest_url, timeout=timeout, headers=headers)

    if response.status_code != 200:
        raise CommunicationError(f"Failed to get manifest: {response.status_code}")

    try:
        hash_ = response.headers['docker-content-digest']
    except KeyError:
        raise CommunicationError("Unexpected response in get manifest.")

    if not hash_.startswith("sha256:"):
        raise CommunicationError("Unexpected hash format in get manifest.")

    return hash_


def get_singularity_executable_props():
    version_output = None
    for executable in ["singularity", "apptainer"]:
        command = [executable, "--version"]
        try:
            version_output = run_command(command)
            break
        except ExecutionError:
            pass

    if version_output is None:
        raise ExecutionError("Singularity executable not found.")
    version_output = version_output.strip()

    runtime = None
    version = None

    if version_output.startswith("singularity version "):
        runtime = "singularity"
        version = semver.VersionInfo.parse(
            version_output[len("singularity version ") :]  # noqa
        )
    elif version_output.startswith("singularity-ce version "):
        runtime = "singularity"
        version = semver.VersionInfo.parse(
            version_output[len("singularity-ce version ") :]  # noqa
        )
    elif version_output.startswith("apptainer version "):
        runtime = "apptainer"
        version = semver.VersionInfo.parse(
            version_output[len("apptainer version ") :]  # noqa
        )

    return executable, runtime, version


def volumes_to_cli_args(input_volumes: dict, output_volumes: dict):
    args = docker_volumes_to_cli_args(input_volumes, output_volumes)
    return ["--bind" if arg == "--volume" else arg for arg in args]


def craft_singularity_run_command(run_args: dict, executable: str):
    command = [executable, "run", "-eC"]

    # By default, current user is used.
    _ = run_args.pop("user", None)

    input_volumes = run_args.pop("input_volumes", [])
    output_volumes = run_args.pop("output_volumes", [])
    volumes_args = volumes_to_cli_args(input_volumes, output_volumes)
    command.extend(volumes_args)

    gpus = run_args.pop("gpus", None)
    if gpus is not None:
        command.append("--nv")
        if isinstance(gpus, list):
            command.extend(["--nvccli", "-c", "--writable-tmpfs"])
            os.environ["NVIDIA_VISIBLE_DEVICES"] = ",".join(gpus)

    run_args.pop("shm_size", None)
    # NOTE: No shm size config for singularity:
    # https://github.com/ratt-ru/Stimela-classic/issues/394

    env_dict = run_args.pop("environment", {})
    for key, val in env_dict.items():
        os.environ[f"SINGULARITYENV_{key}"] = val

    network = run_args.pop("network", None)
    if network == "none":
        command.append("--net")
        command.append("--network")
        command.append(network)

    run_args.pop("ports", [])
    # Singularity will use host network

    image = run_args.pop("image")
    command.append(image)

    entrypoint = run_args.pop("entrypoint", None)
    if entrypoint is not None:
        command[1] = "exec"
        command.append(f"{entrypoint}")

    extra_command = run_args.pop("command", [])
    if isinstance(extra_command, str):
        extra_command = shlex.split(extra_command)
    command.extend(extra_command)
    return command
