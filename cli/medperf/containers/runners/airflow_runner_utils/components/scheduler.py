from medperf.containers.runners.airflow_runner_utils.components.airflow_component import (
    AirflowComponentRunner,
)
from pydantic import SecretStr
from .utils import run_healthcheck, build_mounts_dict


class AirflowScheduler(AirflowComponentRunner):
    def __init__(self, user: str, password: SecretStr, mounts: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        extra_vars = {
            "_AIRFLOW_WWW_USER_USERNAME": user,
            "_AIRFLOW_WWW_USER_PASSWORD": password.get_secret_value(),
        }
        formatted_mounts = build_mounts_dict(mounts)
        self._env_vars.update(**extra_vars, **formatted_mounts)

    @property
    def logfile(self):
        return "scheduler.log"

    @property
    def component_name(self):
        return "Airflow Scheduler"

    @property
    def initialize_command(self):
        return ["airflow", "scheduler"]

    def has_successfully_started(self):
        return run_healthcheck("http://localhost:8974/health")
