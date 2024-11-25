from medperf.exceptions import InvalidArgumentError
from medperf import config
import yaml


def get_config(cube_path: str, identifier: str):
    """
    Returns the output parameter specified in the mlcube.yaml file

    Args:
        identifier (str): `.` separated keys to traverse the mlcube dict
    Returns:
        str: the parameter value, None if not found
    """
    with open(cube_path, "r") as f:
        cube = yaml.safe_load(f)

    keys = identifier.split(".")
    for key in keys:
        if key not in cube:
            return
        cube = cube[key]

    return cube


def add_docker_args(
    cmd: str, cube_path: str, port: int, publish_on: str, env_args_string: str
):
    # TODO: we should override run args instead of what we are doing below
    #       we shouldn't allow arbitrary run args unless our client allows it

    # use current user
    cpu_args = get_config(cube_path, "docker.cpu_args") or ""
    gpu_args = get_config(cube_path, "docker.gpu_args") or ""
    cpu_args = " ".join([cpu_args, "-u $(id -u):$(id -g)"]).strip()
    gpu_args = " ".join([gpu_args, "-u $(id -u):$(id -g)"]).strip()
    if port is not None:
        if publish_on:
            cpu_args += f" -p {publish_on}:{port}:{port}"
            gpu_args += f" -p {publish_on}:{port}:{port}"
        else:
            cpu_args += f" -p {port}:{port}"
            gpu_args += f" -p {port}:{port}"
    cmd += f' -Pdocker.cpu_args="{cpu_args}"'
    cmd += f' -Pdocker.gpu_args="{gpu_args}"'
    if env_args_string:  # TODO: why MLCube UI is so brittle?
        env_args = get_config(cube_path, "docker.env_args") or ""
        env_args = " ".join([env_args, env_args_string]).strip()
        cmd += f' -Pdocker.env_args="{env_args}"'
    return cmd


def add_singularity_args(
    cmd: str,
    cube_path: str,
    env_args_string: str,
    converted_singularity_image_name: str,
):
    # TODO: we should override run args instead of what we are doing below
    #       we shouldn't allow arbitrary run args unless our client allows it

    # use -e to discard host env vars, -C to isolate the container (see singularity run --help)
    run_args = get_config(cube_path, "singularity.run_args") or ""
    run_args = " ".join([run_args, "-eC"]).strip()
    run_args += " " + env_args_string
    cmd += f' -Psingularity.run_args="{run_args}"'
    # TODO: check if ports are already exposed. Think if this is OK
    # TODO: check about exposing to specific network interfaces
    # TODO: check if --env works

    # set image name in case of running docker image with singularity
    # Assuming we only accept mlcube.yamls with either singularity or docker sections
    # TODO: make checks on submitted mlcubes
    singularity_config = get_config(cube_path, "singularity")
    if singularity_config is None:
        cmd += f' -Psingularity.image="{converted_singularity_image_name}"'
    return cmd


def craft_cube_command(
    cube_path: str,
    task: str,
    read_protected_input: bool,
    kwargs: dict,
    env_dict: dict,
    port: int,
    publish_on: str,
    converted_singularity_image_name: str,
):
    cmd = f"mlcube --log-level {config.loglevel} run"

    # Add mlcube path, task, and platform
    cmd += f' --mlcube="{cube_path}" --task={task} --platform={config.platform}'

    # Add network argument if needed
    if task not in [
        "train",
        "start_aggregator",
        "trust",
        "get_client_cert",
        "get_server_cert",
        "get_experiment_status",
        "add_collaborator",
        "remove_collaborator",
        "update_plan",
    ]:
        cmd += " --network=none"

    # Add gpus
    if config.gpus is not None:
        cmd += f" --gpus={config.gpus}"

    # Add mount option for input volumes
    if read_protected_input:
        cmd += " --mount=ro"

    # Add keywords arguments (i.e., arguments passed to the task runner)
    for k, v in kwargs.items():
        cmd_arg = f'{k}="{v}"'
        cmd = " ".join([cmd, cmd_arg])

    # Add container loglevel to env dict
    container_loglevel = config.container_loglevel
    if container_loglevel:
        env_dict["MEDPERF_LOGLEVEL"] = container_loglevel.upper()

    # convert env dict to string to pass it to the cmd
    env_args_string = ""
    for key, val in env_dict.items():
        env_args_string += f"--env {key}={val} "
    env_args_string = env_args_string.strip()

    # Add container technology specific args
    if config.platform == "docker":
        cmd = add_docker_args(cmd, cube_path, port, publish_on, env_args_string)
    elif config.platform == "singularity":
        cmd = add_singularity_args(
            cmd, cube_path, env_args_string, converted_singularity_image_name
        )
    else:
        raise InvalidArgumentError("Unsupported platform")

    # set accelerator count to zero to avoid unexpected behaviours and
    # force mlcube to only use --gpus to figure out GPU config
    cmd += " -Pplatform.accelerator_count=0"
    return cmd
