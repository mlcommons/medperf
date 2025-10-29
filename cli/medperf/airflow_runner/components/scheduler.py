from medperf.airflow_runner.components.airflow_component import AirflowComponentRunner
from pydantic import SecretStr
from .utils import run_healthcheck


class AirflowScheduler(AirflowComponentRunner):
    def __init__(self, user: str, password: SecretStr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        extra_vars = {
            "_AIRFLOW_WWW_USER_USERNAME": user,
            "_AIRFLOW_WWW_USER_PASSWORD": password.get_secret_value(),
        }
        self._env_vars.update(extra_vars)

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
