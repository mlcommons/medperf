from medperf.exceptions import (
    ExecutionError,
    InvalidContainerSpec,
    CommunicationError,
    InvalidArgumentError,
    MedperfException,
)
from medperf.utils import remove_path
from .utils import (
    run_command,
    check_allowed_run_args,
    add_medperf_run_args,
    add_user_defined_run_args,
    add_medperf_environment_variables,
)
import os
import requests
from medperf import config
import semver
from .runner import Runner


class SingularityRunner(Runner):
    def __init__(self, container_config_parser, container_files_base_path):
        self.parser = container_config_parser
        self.container_files_base_path = container_files_base_path
        executable, runtime, version = self._get_executable_properties()
        self.executable = executable
        self.runtime = runtime
        self.version = version
        self.converted_sif_file: str = None

    def _supports_nvccli(self):
        # TODO: later perhaps also check if nvidia-container-cli is installed
        singularity_310 = (
            self.runtime == "singularity"
            and self.version >= semver.VersionInfo(major=3, minor=10)
        )
        apptainer = self.runtime == "apptainer"
        # This function will be run when there is a necessity to use --nvccli (i.e. when
        # the user wishes to isolate certain GPUs). So maybe it's valuable to print a warning
        # to show the user the limitations of nvccli:
        # https://docs.sylabs.io/guides/3.10/user-guide/gpu.html#requirements-limitations
        return singularity_310 or apptainer

    def _get_executable_properties(self):
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

    def _get_image_hash(self, timeout: int = None):
        docker_image = self.parser.get_setup_args()
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
            hash_ = response.json()["config"]["digest"]
        except KeyError:
            raise CommunicationError("Unexpected response in get manifest.")

        if not hash_.startswith("sha256:"):
            raise CommunicationError("Unexpected hash format in get manifest.")

        hash_ = hash_[len("sha256:") :]  # noqa
        return hash_

    def download(
        self,
        expected_image_hash,
        download_timeout: int = None,
        get_hash_timeout: int = None,
    ):
        computed_image_hash = self._get_image_hash(get_hash_timeout)
        if expected_image_hash and expected_image_hash != computed_image_hash:
            raise InvalidContainerSpec("hash mismatch")

        sif_image_folder = os.path.join(
            self.container_files_base_path, config.image_path
        )
        sif_image_file = os.path.join(sif_image_folder, f"{computed_image_hash}.sif")
        if not os.path.exists(sif_image_file):
            # delete outdated files
            remove_path(sif_image_folder)
            os.makedirs(sif_image_folder, exist_ok=True)

            docker_image = self.parser.get_setup_args()
            command = [
                self.executable,
                "build",
                sif_image_file,
                f"docker://{docker_image}",
            ]
            run_command(command, timeout=download_timeout)

        self.converted_sif_file = sif_image_file
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
        run_args = self.parser.get_run_args(task, medperf_mounts)
        check_allowed_run_args(run_args)

        add_medperf_run_args(run_args)
        add_medperf_environment_variables(run_args, medperf_env)
        add_user_defined_run_args(run_args)

        # check if gpus arg is valid
        gpus = run_args.get("gpus", None)
        if isinstance(gpus, int):
            raise InvalidArgumentError("Cannot use gpu count when running singularity.")
        if isinstance(gpus, list) and not self._supports_nvccli():
            raise InvalidArgumentError(
                "Cannot choose specific gpus with the current singularity version."
            )

        # Add volumes
        input_volumes, output_volumes = self.parser.get_volumes(task, medperf_mounts)
        run_args["input_volumes"] = input_volumes
        run_args["output_volumes"] = output_volumes

        # Add env vars
        run_args["env"] = medperf_env

        # Add image
        if self.converted_sif_file is None:
            raise MedperfException("Internal error: Run is called before download.")
        run_args["image"] = self.converted_sif_file

        # Run
        command = _craft_singularity_run_command(run_args, self.executable)
        run_command(command, timeout, output_logs)


def _volumes_to_cli_args(input_volumes: dict, output_volumes: dict):
    args = []

    for host_path, mount_info in input_volumes.items():
        mount_path = mount_info["mount_path"]
        mount_type = mount_info["type"]
        if mount_type == "directory":
            os.makedirs(host_path, exist_ok=True)
        else:
            dirname = os.path.dirname(host_path)
            os.makedirs(dirname, exist_ok=True)
            if not os.path.exists(host_path):
                with open(host_path, "w"):
                    pass
        args.append("--volume")
        args.append(f"{host_path}:{mount_path}:ro")
    for host_path, mount_info in output_volumes.items():
        mount_path = mount_info["mount_path"]
        mount_type = mount_info["type"]
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


def _craft_singularity_run_command(run_args: dict, executable: str):
    command = [executable, "run", "-eC"]

    # By default, current user is used.
    _ = run_args.pop("user", None)

    input_volumes = run_args.pop("input_volumes", {})
    output_volumes = run_args.pop("output_volumes", {})
    volumes_args = _volumes_to_cli_args(input_volumes, output_volumes)
    command.extend(volumes_args)

    network = run_args.pop("network", None)
    if network is not None:
        command.append("--net")
        command.append("--network")
        command.append(network)

    gpus = run_args.pop("gpus", None)
    if gpus is not None:
        command.append("--nv")
        if isinstance(gpus, list):
            command.extend(["--nvccli", "-c", "--writable-tmpfs"])
            os.environ["NVIDIA_VISIBLE_DEVICES"] = ",".join(gpus)

    # NOTE: No shm size config for singularity:
    # https://github.com/ratt-ru/Stimela-classic/issues/394

    env_dict = run_args.pop("environment", {})
    for key, val in env_dict.items():
        os.environ[f"SINGULARITYENV_{key}"] = val

    image = run_args.pop("image")
    command.append(image)

    entrypoint = run_args.pop("entrypoint", None)
    if entrypoint is not None:
        command[1] = "exec"
        command.append(f"{entrypoint}")

    extra_command = run_args.pop("command", [])
    command.extend(extra_command)
    return command
