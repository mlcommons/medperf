import os
from typing import Optional
from medperf.exceptions import InvalidContainerSpec, MedperfException
import shlex
from pathlib import Path
from medperf.containers.parsers.parser import Parser


class MLCubeParser(Parser):
    def __init__(self, container_config: dict, allowed_runners: list):
        self.container_config = container_config
        self.allowed_runners = allowed_runners
        self.container_type = "mlcube"

    def check_schema(self):
        container_config = self.container_config
        if (
            "docker" not in container_config
            or "image" not in container_config["docker"]
        ):
            raise InvalidContainerSpec(
                "mlcube.yaml file with only singularity section is not supported"
            )
        if "tasks" not in container_config:
            raise InvalidContainerSpec("mlcube.yaml file doesn't have a 'tasks' key")

        for task in container_config["tasks"]:
            if "parameters" not in container_config["tasks"][task]:
                raise InvalidContainerSpec(
                    f"mlcube.yaml task {task} doesn't have a 'parameters' key"
                )

    def check_task_schema(self, task: str) -> str:
        tasks = self.container_config["tasks"]
        if task not in tasks:
            raise InvalidContainerSpec(f"Task {task} is not found in container config.")

    def get_setup_args(self) -> str:
        return self.container_config["docker"]["image"]

    def get_volumes(self, task: str, medperf_mounts: dict):
        input_volumes, output_volumes, _ = _parse_task(
            self.container_config, task, medperf_mounts
        )
        return input_volumes, output_volumes

    def get_run_args(self, task: str, medperf_mounts: dict):
        _, _, run_args = _parse_task(self.container_config, task, medperf_mounts)
        return run_args

    def is_report_specified(self):
        try:
            return (
                "report_file"
                in self.container_config["tasks"]["prepare"]["parameters"]["outputs"]
            )
        except KeyError:
            return False

    def is_metadata_specified(self):
        try:
            return (
                "metadata_path"
                in self.container_config["tasks"]["prepare"]["parameters"]["outputs"]
            )
        except KeyError:
            return False


def _parse_task(container_config: dict, task: str, medperf_mounts: dict):
    workspace_path = container_config.get("workspace_path")
    if workspace_path is None:
        # Internal error
        raise MedperfException("workspace_path is not passed to mlcube config")

    task_info = container_config["tasks"][task]
    # Parse entrypoint
    entrypoint, command = _parse_entrypoint(task_info)
    if entrypoint is None:
        # MLCube's logic
        command.append(task)

    volumes = []
    mount_index = 0
    if "inputs" in task_info["parameters"]:
        args, mount_index = _parse_parameters(
            task_info["parameters"]["inputs"],
            workspace_path,
            mount_index,
            volumes,
            medperf_mounts,
            "input",
        )
        command += args
    if "outputs" in task_info["parameters"]:
        args, mount_index = _parse_parameters(
            task_info["parameters"]["outputs"],
            workspace_path,
            mount_index,
            volumes,
            medperf_mounts,
            "output",
        )
        command += args

    input_volumes = []
    output_volumes = []
    for volume in volumes:
        io_type = volume.pop("io_type")
        if io_type == "input":
            input_volumes.append(volume)
        else:
            output_volumes.append(volume)
    shm_size = _parse_shm_size(container_config)
    extra_args = {
        "shm_size": shm_size,
        "entrypoint": entrypoint,
        "command": command,
    }
    return input_volumes, output_volumes, extra_args


def _parse_entrypoint(task_info: dict):
    command: list[str] = []
    entrypoint: Optional[str] = None
    if "entrypoint" in task_info:
        entrypoint_str = task_info["entrypoint"]
        entrypoint_split = shlex.split(entrypoint_str)
        if len(entrypoint_split) > 1:
            command = entrypoint_split[1:]
        entrypoint = entrypoint_split[0]

    return entrypoint, command


def _parse_shm_size(container_config):
    if "gpu_args" not in container_config["docker"]:
        return
    gpu_args: str = container_config["docker"]["gpu_args"]
    gpu_args_list = gpu_args.split()
    if "--shm-size" not in gpu_args_list:
        return
    index = gpu_args_list.index("--shm-size")
    return gpu_args_list[index + 1]


def _parse_parameters(
    parameters: dict,
    mlcube_workspace_path: str,
    mount_index: int,
    volumes: list,
    medperf_mounts: dict,
    io_type: str,
):
    # Parse mounts/params
    # NOTE: this makes assumptions based on existing registered mlcubes
    #       this code only exists to support existing registered mlcubes
    #       users should use the new definition file schema
    # NOTE: Don't look at this code if you are a new developer!
    args = []
    for param_name, param_val in parameters.items():
        param_type, param_val = _parse_single_parameter(
            param_name,
            param_val,
            mlcube_workspace_path,
            medperf_mounts,
            io_type,
        )
        if param_type == "file":
            host_path, file_name = os.path.split(param_val)
        else:
            host_path, file_name = param_val, ""

        mount_info = None
        for v in volumes:
            if v["host_path"] == host_path:
                mount_info = v
                break
        if mount_info is None:
            # same way mlcube indexes them, to avoid problems
            # if a user has hardcoded mlcubeio*
            mount_info = {
                "host_path": host_path,
                "mount_path": f"/mlcube_io{mount_index}",
                "io_type": io_type,
                "type": param_type,
            }
            volumes.append(mount_info)
            mount_index += 1
        param_arg = os.path.join(mount_info["mount_path"], file_name)
        args.append(f"--{param_name}={param_arg}")
    return args, mount_index


def _parse_single_parameter(
    param_name, param_val, mlcube_workspace_path, medperf_mounts, io_type
):
    param_type = "unknown"
    if isinstance(param_val, dict):
        param_type, param_val = param_val["type"], param_val["default"]
    if param_val.endswith(("/", "\\")):
        param_type = "directory"
    if param_name in medperf_mounts:
        param_val = medperf_mounts[param_name]
    if param_val.endswith(("/", "\\")):
        param_type = "directory"

    param_val = _make_path_absolute(param_val, mlcube_workspace_path)

    if param_type == "unknown" and io_type == "output":
        raise InvalidContainerSpec("Misconfigured mlcube.yaml")

    if param_type == "unknown":
        if os.path.isfile(param_val):
            param_type = "file"
        elif os.path.isdir(param_val):
            param_type = "directory"
        else:
            raise InvalidContainerSpec("Misconfigured mlcube.yaml")

    return param_type, param_val


def _make_path_absolute(param_val, mlcube_workspace_path):
    # Copied from MLCube
    param_val = Path(os.path.expandvars(os.path.expanduser(param_val)))
    if not param_val.is_absolute():
        param_val = Path(mlcube_workspace_path) / param_val
    return param_val.as_posix()
