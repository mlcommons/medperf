import os
import docker.types
from medperf.exceptions import InvalidContainerSpec
import docker
from medperf.containers.parsers import load_parser
from medperf import config
from .utils import normalize_gpu_arg


class DockerRunner:
    def __init__(self, container_config_path: str):
        self.parser = load_parser(container_config_path)
        self.client = docker.from_env()

    def download(self):
        docker_image = self.parser.get_setup_args()
        self.client.images.pull(docker_image)

    def run(
        self,
        task: str,
        medperf_mounts: dict[str, str],
        timeout: int = None,
        output_logs: str = None,
    ):
        self.parser.check_task_schema(task)
        run_args = self.parser.get_run_args()
        _check_allowed_run_args(run_args)

        _add_medperf_run_args(run_args)
        _add_user_defined_run_args(run_args)

        # Add volumes and image
        input_volumes, output_volumes = self.parser.get_volumes(task, medperf_mounts)
        volumes = {}
        for host_path, bind_path in input_volumes.items():
            volumes[host_path] = {"bind": bind_path, "mode": "ro"}
        for host_path, bind_path in output_volumes.items():
            volumes[host_path] = {"bind": bind_path, "mode": "rw"}
        run_args["volumes"] = volumes
        run_args["image"] = self.parser.get_setup_args()

        # Run
        self.client.containers.run(**run_args)
        # environment="",
        # ports="",


def _check_allowed_run_args(run_args):
    allowed_keys = {"shm_size", "gpus", "command", "entrypoint"}
    given_keys = set(run_args.keys())
    not_allowed_keys = given_keys.difference(allowed_keys)
    if not_allowed_keys:
        raise InvalidContainerSpec(
            f"Run args {', '.join(not_allowed_keys)} are not allowed."
        )


def _add_medperf_run_args(run_args):
    run_args["user"] = os.geteuid()
    run_args["use_config_proxy"] = True
    run_args["network_mode"] = "none"


def _add_user_defined_run_args(run_args):
    # shm_size
    if config.shm_size is not None:
        run_args["shm_size"] = config.shm_size

    # gpus
    if config.gpus is not None:
        run_args["gpus"] = config.gpus
    gpus = run_args.pop("gpus")
    gpus = normalize_gpu_arg(gpus)
    if gpus is not None:
        if gpus == "all":
            device_request = docker.types.DeviceRequest(count=-1)
        elif isinstance(gpus, int):
            device_request = docker.types.DeviceRequest(count=gpus)
        elif isinstance(gpus, list):
            device_request = docker.types.DeviceRequest(device_ids=gpus)
        run_args["device_requests"] = [device_request]
        run_args["runtime"] = "nvidia"  # TODO: test without this?
