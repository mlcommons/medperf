from .runner import Runner
from typing import Dict
from medperf.containers.runners.airflow_runner_utils.system_runner import (
    AirflowSystemRunner,
)
from pathlib import Path
from .airflow_runner_utils.dags import constants
import os
from medperf.containers.parsers.airflow_parser import AirflowParser
from medperf.account_management import get_medperf_user_data
from .utils import (
    check_docker_image_hash,
)
from medperf.utils import run_command
from medperf.comms.entity_resources import resources
import logging
from .docker_utils import get_docker_image_hash


class AirflowRunner(Runner):

    _DAGS_FOLDER = str(Path(constants.__file__).parent.resolve())

    def __init__(
        self,
        airflow_config_parser: AirflowParser,
        container_files_base_path,
        workflow_name,
    ):
        self.parser = airflow_config_parser
        self.container_dir = container_files_base_path
        self.workflow_name = workflow_name

    def download(
        self,
        hashes_dict: Dict[str, str],
        download_timeout: int = None,
        get_hash_timeout: int = None,
        alternative_image_hash: str = None,
        container_base_dir: str = None,
    ) -> Dict[str, str]:
        # TODO currently no support for singularity user environment
        # converting a docker image to singularity
        for container in self.parser.containers:
            if container.platform == "docker":
                expected_image_hash = hashes_dict.get(container.image)
                command = ["docker", "pull", container.image]
                run_command(command, timeout=download_timeout)
                computed_image_hash = get_docker_image_hash(
                    container.image, get_hash_timeout
                )
                check_docker_image_hash(
                    computed_image_hash, expected_image_hash, alternative_image_hash
                )
                hashes_dict[container.image] = computed_image_hash
            elif container.platform == "singularity":
                expected_image_hash = hashes_dict.get(container.image)
                sif_image_path, computed_image_hash = resources.get_cube_image(
                    container.image, expected_image_hash
                )  # Hash checking happens in resources
                self.sif_image_path = sif_image_path
                hashes_dict[container.image] = computed_image_hash

        return hashes_dict

    def run(
        self,
        task: str = None,  # Not used
        tmp_folder: str = None,  # TODO implement
        output_logs: str = None,
        timeout: int = None,
        medperf_mounts: dict[str, str] = {},
        medperf_env: dict[str, str] = {},
        ports: list = [],
        disable_network: bool = True,
        container_decryption_key_file: str = None,
    ):

        email = get_medperf_user_data()["email"]
        username = email.split("@", maxsplit=1)[0]

        dataset_dir = medperf_mounts.pop("dataset_path")
        airflow_home = os.path.join(dataset_dir, "airflow_home")
        additional_files_path = medperf_mounts["additional_files"]
        self._symlink_yaml_dag_to_additional_files(additional_files_path)

        logging.debug(
            f"Starting Airflow runner with the following airflow home directory: {airflow_home}."
        )
        logging.debug(
            f"Airflow execution based on the following YAML file: {self.parser.config_file_path}"
        )
        with AirflowSystemRunner(
            airflow_home=airflow_home,
            user=username,
            dags_folder=self._DAGS_FOLDER,
            additional_files_dir=additional_files_path,
            mounts=medperf_mounts,
            project_name=self.workflow_name,
            yaml_parser=self.parser,
        ) as system_runner:
            system_runner.init_airflow()
            system_runner.wait_for_dag()

    def _symlink_yaml_dag_to_additional_files(self, additional_files_path: str):
        yaml_file_name = os.path.basename(self.parser.config_file_path)
        os.makedirs(additional_files_path, exist_ok=True)
        symlinked_yaml_file_path = os.path.join(additional_files_path, yaml_file_name)
        try:
            os.unlink(symlinked_yaml_file_path)
        except FileNotFoundError:
            pass
        os.symlink(self.parser.config_file_path, symlinked_yaml_file_path)

    @property
    def is_workflow(self):
        return True
