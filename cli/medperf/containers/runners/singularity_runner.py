from medperf.comms.entity_resources import resources
from medperf.exceptions import InvalidArgumentError, MedperfException
from medperf.utils import remove_path
from .utils import (
    run_command,
    check_allowed_run_args,
    add_medperf_run_args,
    add_user_defined_run_args,
    add_medperf_environment_variables,
    add_network_config,
    add_medperf_tmp_folder,
    check_docker_image_hash,
)
from .singularity_utils import (
    cleanup_singularity_cache,
    get_docker_image_hash_from_dockerhub,
    get_singularity_executable_props,
    craft_singularity_run_command,
    convert_docker_image_to_sif,
)
from .encryption_utils import decrypt_gpg_file, create_secure_folder

import os
from medperf import config
import semver
from .runner import Runner
import logging


class SingularityRunner(Runner):
    def __init__(self, container_config_parser, container_files_base_path):
        self.parser = container_config_parser
        self.container_files_base_path = container_files_base_path
        executable, runtime, version = get_singularity_executable_props()
        self.executable = executable
        self.runtime = runtime
        self.version = version
        self.image_file_path: str = None
        self.image_file_hash: str = None

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

    def download(
        self,
        expected_image_hash,
        download_timeout: int = None,
        get_hash_timeout: int = None,
        alternative_image_hash: str = None,
    ):
        if self.parser.is_docker_archive() or self.parser.is_singularity_file():
            return self._download_image_file(
                expected_image_hash,
                download_timeout,
                get_hash_timeout,
            )
        else:
            # No download; conversion happens during run
            return self._check_docker_image(
                expected_image_hash,
                get_hash_timeout,
                alternative_image_hash,
            )

    def _download_image_file(
        self,
        expected_image_hash,
        download_timeout: int = None,
        get_hash_timeout: int = None,
    ):
        image_file_url = self.parser.get_setup_args()
        image_file_path, computed_image_hash = resources.get_cube_image(
            image_file_url, expected_image_hash
        )  # Hash checking happens in resources
        self.image_file_path = image_file_path
        self.image_file_hash = computed_image_hash
        return computed_image_hash

    def _check_docker_image(
        self,
        expected_image_hash,
        get_hash_timeout: int = None,
        alternative_image_hash: str = None,
    ):
        docker_image = self.parser.get_setup_args()
        computed_image_hash = get_docker_image_hash_from_dockerhub(
            docker_image, get_hash_timeout
        )
        check_docker_image_hash(
            computed_image_hash, expected_image_hash, alternative_image_hash
        )
        return computed_image_hash

    def run(
        self,
        task: str,
        tmp_folder: str,
        output_logs: str = None,
        timeout: int = None,
        medperf_mounts: dict[str, str] = {},
        medperf_env: dict[str, str] = {},
        ports: list = [],
        disable_network: bool = True,
        container_decryption_key_file: str = None,
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
        add_medperf_tmp_folder(output_volumes, tmp_folder)

        run_args["input_volumes"] = input_volumes
        run_args["output_volumes"] = output_volumes

        # Add network config
        add_network_config(run_args, disable_network, ports)

        # Add env vars
        run_args["env"] = medperf_env

        # Run
        if self.parser.is_container_encrypted() and self.parser.is_docker_archive():
            self._run_encrypted_docker_archive(
                run_args, timeout, output_logs, container_decryption_key_file
            )
        elif self.parser.is_container_encrypted() and self.parser.is_singularity_file():
            self._run_encrypted_singularity_file(
                run_args, timeout, output_logs, container_decryption_key_file
            )
        elif self.parser.is_docker_archive():
            self._run_docker_archive(run_args, timeout, output_logs)

        elif self.parser.is_singularity_file():
            self._run_singularity_file(run_args, timeout, output_logs)
        else:
            self._run_docker_image(run_args, timeout, output_logs)

    def _run_singularity_file(self, run_args, timeout, output_logs):
        if self.image_file_path is None:
            raise MedperfException("Internal error: Run is called before download.")

        # Run
        self._invoke_run(self.image_file_path, run_args, timeout, output_logs)

    def _run_docker_archive(self, run_args, timeout, output_logs):
        if self.image_file_path is None:
            raise MedperfException("Internal error: Run is called before download.")

        sif_image_folder = os.path.join(
            self.container_files_base_path, config.image_path
        )
        sif_image_file = os.path.join(sif_image_folder, f"{self.image_file_hash}.sif")

        # convert
        convert_docker_image_to_sif(
            docker_image=self.image_file_path,
            output_sif=sif_image_file,
            singularity_executable=self.executable,
            protocol="docker-archive",
        )

        # Run
        self._invoke_run(sif_image_file, run_args, timeout, output_logs)

    def _run_docker_image(self, run_args, timeout, output_logs):
        docker_image = self.parser.get_setup_args()

        sif_image_folder = os.path.join(
            self.container_files_base_path, config.image_path
        )
        sif_image_file = os.path.join(sif_image_folder, f"{self.image_file_hash}.sif")

        # convert
        convert_docker_image_to_sif(
            docker_image=docker_image,
            output_sif=sif_image_file,
            singularity_executable=self.executable,
        )

        # Run
        self._invoke_run(sif_image_file, run_args, timeout, output_logs)

    def _run_encrypted_singularity_file(
        self, run_args, timeout, output_logs, container_decryption_key_file
    ):
        if self.image_file_path is None:
            raise MedperfException("Internal error: Run is called before download.")

        if container_decryption_key_file is None:
            raise MedperfException(
                "Container is encrypted but decryption key is not provided"
            )

        decrypted_sif_file = create_secure_folder()
        try:
            # decrypt file
            decrypt_gpg_file(
                self.image_archive_path,
                container_decryption_key_file,
                decrypted_sif_file,
            )
            # Run
            self._invoke_run(decrypted_sif_file, run_args, timeout, output_logs)
        finally:
            remove_path(decrypted_sif_file, sensitive=True)

    def _run_encrypted_docker_archive(
        self, run_args, timeout, output_logs, container_decryption_key_file
    ):
        if self.image_file_path is None:
            raise MedperfException("Internal error: Run is called before download.")

        if container_decryption_key_file is None:
            raise MedperfException(
                "Container is encrypted but decryption key is not provided"
            )
        sif_image_folder = os.path.join(
            self.container_files_base_path, config.image_path
        )
        sif_image_file = os.path.join(sif_image_folder, f"{self.image_file_hash}.sif")
        decrypted_archive_file = create_secure_folder()
        try:
            # decrypt file
            decrypt_gpg_file(
                self.image_archive_path,
                container_decryption_key_file,
                decrypted_archive_file,
            )

            # convert
            convert_docker_image_to_sif(
                docker_image=decrypted_archive_file,
                output_sif=sif_image_file,
                singularity_executable=self.executable,
                protocol="docker-archive",
            )
            remove_path(decrypted_archive_file, sensitive=True)
            cleanup_singularity_cache(self.executable)

            # Run
            self._invoke_run(sif_image_file, run_args, timeout, output_logs)

        finally:
            remove_path(sif_image_file, sensitive=True)
            remove_path(decrypted_archive_file, sensitive=True)
            cleanup_singularity_cache(self.executable)

    def _invoke_run(self, image, run_args, timeout, output_logs):
        run_args["image"] = image

        # Run
        command = craft_singularity_run_command(run_args, self.executable)
        logging.debug(f"Running command: {command}")
        run_command(command, timeout, output_logs)
