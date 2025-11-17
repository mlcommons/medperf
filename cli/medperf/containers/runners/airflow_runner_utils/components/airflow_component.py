import os
from abc import abstractmethod
from typing import List
from .component import ComponentRunner


class AirflowComponentRunner(ComponentRunner):

    def __init__(
        self,
        python_executable: str,
        airflow_home: str,
        container_type: str,
        yaml_dags_dir: str,
        dags_folder: os.PathLike,
    ):
        self._python_exec = python_executable
        self.process = None
        user_dags_folder = os.path.join(dags_folder, "user")
        self.airflow_home = airflow_home
        self._env_vars = {
            "AIRFLOW_HOME": airflow_home,
            "PYTHONPATH": f"{dags_folder}:{user_dags_folder}:{yaml_dags_dir}",
            "YAML_DAGS_DIR": yaml_dags_dir,
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
