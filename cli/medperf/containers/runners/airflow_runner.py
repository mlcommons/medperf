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
from .utils import check_docker_image_hash, get_expected_hash
from .singularity_utils import get_docker_image_hash_from_dockerhub
from medperf.utils import run_command
import logging
from .docker_utils import get_docker_image_hash
from medperf import config


class AirflowRunner(Runner):

    _DAGS_FOLDER = str(Path(constants.__file__).parent.resolve())

    def __init__(
        self,
        airflow_config_parser: AirflowParser,
        workflow_name,
    ):
        self.parser = airflow_config_parser
        self.workflow_name = workflow_name

    def download(
        self,
        hashes_dict: Dict[str, str],
        download_timeout: int = None,
        get_hash_timeout: int = None,
    ) -> Dict[str, str]:
        # TODO add support for Docker Archives, Encrypted Containers, singularity files
        if config.platform == "docker":
            self._download_containers_for_docker(
                hashes_dict, download_timeout, get_hash_timeout
            )
        elif config.platform == "singularity":
            self._check_containers_for_singularity(hashes_dict, get_hash_timeout)

    def _download_containers_for_docker(
        self, hashes_dict, download_timeout, get_hash_timeout
    ):
        for container in self.parser.containers:
            expected_image_hash = get_expected_hash(hashes_dict, container.image)
            command = ["docker", "pull", container.image]
            run_command(command, timeout=download_timeout)
            computed_image_hash = get_docker_image_hash(
                container.image, get_hash_timeout
            )
            check_docker_image_hash(computed_image_hash, expected_image_hash)
            hashes_dict[container.image] = computed_image_hash

        return hashes_dict

    def _check_containers_for_singularity(self, hashes_dict, get_hash_timeout):
        """
        Note: currently assumes image always come from some Docker registry (i.e docker hub)
        and then are converted into singularity during run
        """
        for container in self.parser.containers:
            expected_image_hash = get_expected_hash(hashes_dict, container.image)
            computed_image_hash = get_docker_image_hash_from_dockerhub(
                container.image, get_hash_timeout
            )
            check_docker_image_hash(computed_image_hash, expected_image_hash)
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

        logging.debug(
            f"Starting Airflow runner with the following airflow home directory: {airflow_home}."
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

    @property
    def is_workflow(self):
        return True
