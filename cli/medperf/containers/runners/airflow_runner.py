from .runner import Runner
from typing import Dict
from medperf.containers.runners.airflow_runner_utils.system_runner import (
    AirflowSystemRunner,
)
from pathlib import Path
from .airflow_runner_utils.dags import constants
import os
import shutil
from medperf.containers.parsers.airflow_parser import AirflowParser
from medperf.account_management import get_medperf_user_data


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
        self.workflow_name = workflow_name  # TODO this needs validation!

    def download(
        self,
        hashes_dict: Dict[str, str],
        download_timeout: int = None,
        get_hash_timeout: int = None,
        alternative_image_hash: str = None,
        container_base_dir: str = None,
    ) -> Dict[str, str]:
        # TODO implement image downloads too
        pass

    def run(
        self,
        task: str = None,  # Not used
        tmp_folder: str = None,  # TODO implement
        output_logs: str = None,  # TODO currently hardcoded; figure this out
        timeout: int = None,
        medperf_mounts: dict[str, str] = {},
        medperf_env: dict[str, str] = {},
        ports: list = [],
        disable_network: bool = True,
    ):
        # TODO properly implement MedPerf mounts similar to other use cases
        # For now, assume medperf_mounts has the form of
        # medperf_mounts = {
        #     'workspace_dir': 'path/to/local/workspace',
        #     'input_data_dir': 'path/to/local/input/data/dir',
        #     'data_dir': 'path/to/local/output/data/dir'
        # }

        workspace_dir = medperf_mounts["workspace_dir"]
        input_data_dir = medperf_mounts["input_data_dir"]
        data_dir = medperf_mounts["data_dir"]

        for necessary_dir in [workspace_dir, input_data_dir, data_dir]:
            os.makedirs(necessary_dir, exist_ok=True)

        email = get_medperf_user_data()["email"]
        username = email.split("@", maxsplit=1)[0]

        airflow_home = os.path.join(self.container_dir, "airflow_home")
        additional_files_path = medperf_mounts["additional_files"]
        self._copy_yaml_dag_to_additional_files(additional_files_path)

        with AirflowSystemRunner(
            airflow_home=airflow_home,
            user=username,
            dags_folder=self._DAGS_FOLDER,
            workspace_dir=workspace_dir,
            data_dir=data_dir,
            input_data_dir=input_data_dir,
            yaml_dags_dir=additional_files_path,
            project_name=self.workflow_name,
            yaml_parser=self.parser,
        ) as system_runner:
            system_runner.init_airflow()
            system_runner.wait_for_dag()

    def _copy_yaml_dag_to_additional_files(self, additional_files_path: str):
        # TODO also needs to move the auxiliary python files; or maybe they'll be part of additional files?
        yaml_file_name = os.path.basename(self.parser.config_file_path)
        os.makedirs(additional_files_path, exist_ok=True)
        moved_yaml_file_path = os.path.join(additional_files_path, yaml_file_name)
        shutil.copy2(self.parser.config_file_path, moved_yaml_file_path)
