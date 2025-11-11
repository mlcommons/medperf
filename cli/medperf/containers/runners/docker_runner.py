from medperf.comms.entity_resources import resources
from medperf.exceptions import MedperfException
from .utils import (
    check_allowed_run_args,
    add_medperf_run_args,
    add_user_defined_run_args,
    add_medperf_environment_variables,
    add_network_config,
    add_medperf_tmp_folder,
    check_docker_image_hash,
)
from .runner import Runner
import logging
from .docker_utils import (
    craft_docker_run_command,
    get_docker_image_hash,
    get_repo_tags_from_archive,
    load_image,
    delete_images,
)
from medperf.encryption import decrypt_gpg_file, check_gpg
from medperf.utils import remove_path, run_command, tmp_file_path_for_decryption


class DockerRunner(Runner):
    def __init__(self, container_config_parser):
        self.parser = container_config_parser
        self.image: str = None
        if self.parser.is_container_encrypted():
            check_gpg()

    def download(
        self,
        expected_image_hash,
        download_timeout: int = None,
        get_hash_timeout: int = None,
        alternative_image_hash: str = None,
    ):
        if self.parser.is_docker_archive():
            logging.debug("Downloading Docker archive")
            return self._download_docker_archive(
                expected_image_hash,
                download_timeout,
                get_hash_timeout,
            )
        else:
            logging.debug("Downloading Docker image")
            return self._download_docker_image(
                expected_image_hash,
                download_timeout,
                get_hash_timeout,
                alternative_image_hash,
            )

    def _download_docker_image(
        self,
        expected_image_hash,
        download_timeout: int = None,
        get_hash_timeout: int = None,
        alternative_image_hash: str = None,
    ):
        docker_image = self.parser.get_setup_args()
        command = ["docker", "pull", docker_image]
        logging.debug("Running pull command")
        run_command(command, timeout=download_timeout)
        computed_image_hash = get_docker_image_hash(docker_image, get_hash_timeout)
        check_docker_image_hash(
            computed_image_hash, expected_image_hash, alternative_image_hash
        )
        return computed_image_hash

    def _download_docker_archive(
        self,
        expected_image_hash,
        download_timeout: int = None,
        get_hash_timeout: int = None,
    ):
        file_url = self.parser.get_setup_args()
        image_path, computed_image_hash = resources.get_cube_image(
            file_url, expected_image_hash
        )  # Hash checking happens in resources
        self.image_archive_path = image_path
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

        # Add volumes
        input_volumes, output_volumes = self.parser.get_volumes(task, medperf_mounts)
        add_medperf_tmp_folder(output_volumes, tmp_folder)

        run_args["input_volumes"] = input_volumes
        run_args["output_volumes"] = output_volumes

        # Add network config
        add_network_config(run_args, disable_network, ports)

        # Run
        if self.parser.is_container_encrypted() and self.parser.is_docker_archive():
            self._run_encrypted_archive(
                run_args, timeout, output_logs, container_decryption_key_file
            )
        elif self.parser.is_docker_archive():
            self._run_archive(run_args, timeout, output_logs)
        else:
            self._run_image(run_args, timeout, output_logs)

    def _run_image(self, run_args, timeout, output_logs):
        logging.debug("Running unencrypted image")

        # Set Image
        image = self.parser.get_setup_args()

        # Run
        self._invoke_run(image, run_args, timeout, output_logs)

    def _run_archive(self, run_args, timeout, output_logs):
        logging.debug("Running unencrypted archive")
        if self.image_archive_path is None:
            raise MedperfException("Internal error: run was called before download.")

        # load archive
        repo_tags_list = get_repo_tags_from_archive(self.image_archive_path)
        load_image(self.image_archive_path)

        # Set Image
        image = repo_tags_list[0]

        # Run
        self._invoke_run(image, run_args, timeout, output_logs)

    def _run_encrypted_archive(
        self, run_args, timeout, output_logs, container_decryption_key_file
    ):
        logging.debug("Running encrypted archive")
        if self.image_archive_path is None:
            raise MedperfException("Internal error: run was called before download.")

        if container_decryption_key_file is None:
            raise MedperfException(
                "Container is encrypted but decryption key is not provided"
            )
        if not run_args.get("remove_container", False):
            raise MedperfException(
                "Internal error: Container should be automatically deleted after run"
            )

        decrypted_archive_path = tmp_file_path_for_decryption()
        repo_tags_list = []
        try:
            # decrypt archive
            decrypt_gpg_file(
                self.image_archive_path,
                container_decryption_key_file,
                decrypted_archive_path,
            )

            # load archive
            repo_tags_list = get_repo_tags_from_archive(decrypted_archive_path)
            load_image(decrypted_archive_path)
            remove_path(decrypted_archive_path, sensitive=True)

            # Set Image
            image = repo_tags_list[0]

            # Run
            self._invoke_run(image, run_args, timeout, output_logs)

        finally:
            remove_path(decrypted_archive_path, sensitive=True)
            delete_images(repo_tags_list)

    def _invoke_run(self, image, run_args, timeout, output_logs):
        run_args["image"] = image

        # Run
        command = craft_docker_run_command(run_args)
        logging.debug("Running docker container")
        run_command(command, timeout, output_logs)
