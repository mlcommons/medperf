from medperf.exceptions import InvalidContainerSpec
from .utils import (
    run_command,
    check_allowed_run_args,
    add_medperf_run_args,
    add_user_defined_run_args,
    add_medperf_environment_variables,
)
from .runner import Runner
import json


class DockerRunner(Runner):
    def __init__(self, container_config_parser):
        self.parser = container_config_parser

    def _get_image_hash(self, timeout: int = None):
        docker_image = self.parser.get_setup_args()
        command = ["docker", "inspect", docker_image]
        output = run_command(command, timeout=timeout)
        image_info = json.loads(output)
        if (
            not isinstance(image_info, list)
            or len(image_info) != 1
            or not isinstance(image_info[0], dict)
        ):
            raise InvalidContainerSpec("invalid hash output")
        image_id = image_info[0].get("Id", None)
        if image_id and image_id.startswith("sha256:"):
            image_id = image_id[len("sha256:") :]  # noqa
            return image_id
        raise InvalidContainerSpec("Invalid inspect output:", image_id)

    def download(
        self,
        expected_image_hash,
        download_timeout: int = None,
        get_hash_timeout: int = None,
    ):
        docker_image = self.parser.get_setup_args()
        command = ["docker", "pull", docker_image]
        run_command(command, timeout=download_timeout)
        computed_image_hash = self._get_image_hash(get_hash_timeout)
        if expected_image_hash and expected_image_hash != computed_image_hash:
            raise InvalidContainerSpec("hash mismatch")
        return computed_image_hash

    def run(
        self,
        task: str,
        output_logs: str = None,
        timeout: int = None,
        medperf_mounts: dict[str, str] = {},
        medperf_env: dict[str, str] = {},
    ):
        self.parser.check_task_schema(task)
        run_args = self.parser.get_run_args()
        check_allowed_run_args(run_args)

        add_medperf_run_args(run_args)
        add_medperf_environment_variables(run_args, medperf_env)
        add_user_defined_run_args(run_args)

        # Add volumes
        input_volumes, output_volumes = self.parser.get_volumes(task, medperf_mounts)
        volumes = {}
        for host_path, bind_path in input_volumes.items():
            volumes[host_path] = {"bind": bind_path, "mode": "ro"}
        for host_path, bind_path in output_volumes.items():
            volumes[host_path] = {"bind": bind_path, "mode": "rw"}
        run_args["volumes"] = volumes

        # Add images
        run_args["image"] = self.parser.get_setup_args()

        # Run
        command = _craft_docker_run_command(run_args)
        run_command(command, timeout, output_logs)


def _volumes_to_cli_args(input_volumes: dict, output_volumes: dict):
    args = []
    for host_path, bind_path in input_volumes.items():
        args.append("--volume")
        args.append(f"'{host_path}:{bind_path}:ro'")
    for host_path, bind_path in output_volumes.items():
        args.append("--volume")
        args.append(f"'{host_path}:{bind_path}:rw'")


def _craft_docker_run_command(run_args: dict):
    command = ["docker", "run"]
    user = run_args.pop("user", None)
    if user is not None:
        command.append("-u")
        command.append(user)

    input_volumes = run_args.pop(input_volumes, {})
    output_volumes = run_args.pop(output_volumes, {})
    volumes_args = _volumes_to_cli_args(input_volumes, output_volumes)
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
    env_args = [f"--env {key}='{val}'" for key, val in env_dict.items()]
    command.extend(env_args)

    entrypoint = run_args.pop("entrypoint", None)
    if entrypoint is not None:
        command.append("--entrypoint")
        command.append(f"'{entrypoint}'")

    image = run_args.pop("image")
    command.append(image)
    extra_command = run_args.pop("command", [])
    command.extend(extra_command)
    return command
