import os
from abc import abstractmethod
from typing import List, Literal
from .component import ComponentRunner


class AirflowComponentRunner(ComponentRunner):

    def __init__(
        self,
        python_executable: os.PathLike,
        airflow_home: os.PathLike,
        container_type: Literal["docker", "singularity"],
        workflow_yaml_file: os.PathLike,
        additional_files_dir: os.PathLike,
        dags_folder: os.PathLike,
    ):
        self._python_exec = python_executable
        self.process = None
        user_dags_folder = os.path.join(dags_folder, "user")
        self.airflow_home = airflow_home
        self._env_vars = {
            "AIRFLOW_HOME": airflow_home,
            "PYTHONPATH": f"{dags_folder}:{user_dags_folder}:{additional_files_dir}",
            "WORKFLOW_YAML_FILE": workflow_yaml_file,
            "CONTAINER_TYPE": container_type,
        }

    @property
    def _run_env(self):
        base_env = os.environ.copy()
        base_env.update(**self._env_vars)
        return base_env

    @property
    @abstractmethod
    def initialize_command(self) -> List[str]:
        pass

    async def start_logic(self):
        actual_command = [self._python_exec, "-m", *self.initialize_command]

        logfile_path = os.path.join(self.airflow_home, "logs", self.logfile)
        self.run_command_with_logging(
            command=actual_command, logfile_path=logfile_path, env=self._run_env
        )
        await self.wait_for_start()
