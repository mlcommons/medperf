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
from .runner import Runner
import logging
from .docker_utils import craft_docker_run_command, get_docker_image_hash


class DockerRunner(Runner):
    def download(
        self,
        expected_image_hash,
        download_timeout: int = None,
        get_hash_timeout: int = None,
        alternative_image_hash: str = None,
    ):
        docker_image = self.parser.get_setup_args()
        command = ["docker", "pull", docker_image]
        run_command(command, timeout=download_timeout)
        computed_image_hash = get_docker_image_hash(docker_image, get_hash_timeout)
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
        image: str = None,
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

        # Add images
        run_args["image"] = image or self.parser.get_setup_args()

        # Run
        command = craft_docker_run_command(run_args)
        logging.debug(f"Running command: {command}")
        run_command(command, timeout, output_logs)
